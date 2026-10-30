"""Exact word edges (owner, 2026-10-30: "مثل أدوبي بريمير"): a small Arabic speech model is made to say the very
words Whisper wrote, letter by letter, and every word gets the moment it really starts and ends (WhisperX does the
same; Premiere's text-based editing works this way too).

Whisper's own times drift by tenths of a second and stretch a word over a pause or a retake ("والعقد" 3.6 s,
"لكن" 4.5 s on his test clip), so a cut on them lands inside a word and a skipped take hides under a stretched word.
With real edges, any voice that no written word covers (a take Whisper wrote once) falls out of the kept talk.

Model: wav2vec2 base, Arabic letters (Apache 2.0, onnx-community, 4-bit, ~90 MB), on onnxruntime: downloaded once into
~/.cache/aboodi-models, never into the repo. Each stretch of speech (vad.islands) is aligned on its own, so no word can
cross a pause. A stretch the model can't place with confidence keeps Whisper's times; without the model (no network)
everything does."""
import json
import os
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

from .transcribe import SR, Word

REPO = "https://huggingface.co/onnx-community/wav2vec2-base-arabic-without-reused-en-token-ids-v1-ONNX/resolve/main/"
FILES = {"wav2vec2_ar_q4.onnx": ("onnx/model_q4.onnx", 80_000_000), "wav2vec2_ar_vocab.json": ("vocab.json", 300)}
MODEL_DIR = Path(os.environ.get("ABOODI_MODELS") or Path.home() / ".cache" / "aboodi-models")
PAD = 0.1          # s of sound kept around each stretch of speech while aligning
MIN_SCORE = -4.0   # mean log-probability of the letters on their frames: below it the text doesn't fit the sound
TAIL = 3           # frames (60 ms) a word's end may reach past its last letter (letters are short spikes)

_TASHKEEL = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ی": "ي", "ة": "ه", "ھ": "ه", "گ": "ك",
                      "ک": "ك", "چ": "ج", "پ": "ب", "ڤ": "ف", "ڨ": "ق"})


def model_files() -> tuple[Path, Path] | None:
    if os.environ.get("ABOODI_NO_WORDTIMES"):
        return None
    paths = {}
    try:
        for name, (remote, least) in FILES.items():
            path = MODEL_DIR / name
            if not (path.exists() and path.stat().st_size >= least):
                import requests
                MODEL_DIR.mkdir(parents=True, exist_ok=True)
                part = path.with_suffix(".part")
                with requests.get(REPO + remote, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    with open(part, "wb") as fh:
                        for block in r.iter_content(1 << 20):
                            fh.write(block)
                if part.stat().st_size < least:
                    part.unlink(missing_ok=True)
                    return None
                part.rename(path)
            paths[name] = path
    except Exception:   # noqa: BLE001 — no network / blocked: Whisper's times stay
        return None
    return paths["wav2vec2_ar_q4.onnx"], paths["wav2vec2_ar_vocab.json"]


@lru_cache(maxsize=1)
def _load():
    files = model_files()
    if files is None:
        return None
    try:
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.log_severity_level = 3
        sess = ort.InferenceSession(str(files[0]), so, providers=["CPUExecutionProvider"])
        vocab = json.loads(files[1].read_text(encoding="utf-8"))
    except Exception:   # noqa: BLE001
        return None
    return sess, vocab


def letters(text: str, vocab: dict) -> list[int]:
    t = _TASHKEEL.sub("", text).translate(_MAP)
    return [vocab[c] for c in t if c in vocab and len(c) == 1 and c != "|"]


def viterbi(logp: np.ndarray, tokens: list[int], blank: int) -> list[tuple[int, int]] | None:
    """CTC forced alignment: (first frame, frame after the last) of every token, or None if they can't fit."""
    T, n = len(logp), len(tokens)
    need = n + sum(a == b for a, b in zip(tokens, tokens[1:]))
    if n == 0 or T < need:
        return None
    ext = np.full(2 * n + 1, blank)
    ext[1::2] = tokens
    S = len(ext)
    skip = np.zeros(S, bool)
    skip[3::2] = ext[3::2] != ext[1:-2:2]      # a letter may follow the previous letter straight (not the same one)
    emit = logp[:, ext]                          # T × S
    alpha = np.full(S, -np.inf)
    alpha[0], alpha[1] = emit[0, 0], emit[0, 1]
    back = np.zeros((T, S), np.int8)
    neg = np.array([-np.inf])
    for t in range(1, T):
        a1 = np.concatenate([neg, alpha[:-1]])
        a2 = np.concatenate([neg, neg, alpha[:-2]])
        a2[~skip] = -np.inf
        stack = np.stack([alpha, a1, a2])
        best = stack.argmax(0)
        alpha = stack[best, np.arange(S)] + emit[t]
        back[t] = best
    s = S - 1 if alpha[S - 1] >= alpha[S - 2] else S - 2
    if not np.isfinite(alpha[s]):
        return None
    states = np.empty(T, int)
    for t in range(T - 1, -1, -1):
        states[t] = s
        s -= back[t, s]
    spans = []
    for k in range(n):
        f = np.flatnonzero(states == 2 * k + 1)
        if not len(f):
            return None
        spans.append((int(f[0]), int(f[-1]) + 1))
    return spans


def _logits(sess, piece: np.ndarray) -> np.ndarray:
    x = (piece - piece.mean()) / np.sqrt(piece.var() + 1e-7)
    out = sess.run(None, {sess.get_inputs()[0].name: x[None].astype(np.float32)})[0][0]
    out = out - out.max(-1, keepdims=True)
    return out - np.log(np.exp(out).sum(-1, keepdims=True))


def _align_island(sess, vocab, audio: np.ndarray, s: float, e: float, words: list[Word],
                  heard: list | None = None) -> list[Word] | None:
    a, b = max(0, int((s - PAD) * SR)), min(len(audio), int((e + PAD) * SR))
    piece = audio[a:b]
    if len(piece) < SR // 10:
        return None
    logp = _logits(sess, piece)
    if heard is not None:
        heard.append((s, e, _greedy(logp, vocab)))
    step = len(piece) / SR / len(logp)
    toks, owner = [], []
    for i, w in enumerate(words):
        ls = letters(w.text, vocab)
        toks += ls
        owner += [i] * len(ls)
    spans = viterbi(logp, toks, vocab["<pad>"])
    if spans is None:
        return None
    score = float(np.mean([logp[f0:f1, t].max() for (f0, f1), t in zip(spans, toks)]))
    if os.environ.get("ABOODI_DEBUG"):
        print(f"   {s:6.2f}-{e:6.2f} score={score:.2f} " + " ".join(w.text for w in words))
    if score < MIN_SCORE:
        return None
    first, last = {}, {}
    for (f0, f1), i in zip(spans, owner):
        first.setdefault(i, f0)
        last[i] = f1
    t0 = a / SR
    out, frames = [], len(logp)
    for i, w in enumerate(words):
        if i in first:
            nxt = next((first[j] for j in range(i + 1, len(words)) if j in first), frames)
            out.append(Word(w.text, round(t0 + first[i] * step, 3), round(t0 + min(nxt, last[i] + TAIL) * step, 3), w.p))
        else:
            out.append(None)      # no Arabic letters (a number, a Latin name): placed between its neighbours below
    for i, w in enumerate(out):
        if w is None:
            lo = next((x.end for x in reversed(out[:i]) if x is not None), max(s, words[i].start))
            hi = next((x.start for x in out[i + 1:] if x is not None), min(e, words[i].end))
            out[i] = Word(words[i].text, round(lo, 3), round(max(lo, hi), 3), words[i].p)
    return out


def _greedy(logp: np.ndarray, vocab: dict) -> str:
    inv = {v: k for k, v in vocab.items()}
    out, prev = [], -1
    for i in logp.argmax(-1):
        if i != prev and i != vocab["<pad>"] and inv.get(int(i), "|") != "|":
            out.append(inv[int(i)])
        prev = i
    return "".join(c for c in out if len(c) == 1)


def refine_times(audio: np.ndarray, words: list[Word], spans: list[tuple[float, float]] | None = None,
                 heard: list | None = None) -> list[Word]:
    """The same words, with the edges the sound shows. Untouched when the model or the speech map is missing.
    `heard` (a list) gets (start, end, letters the model itself hears) for every stretch of speech: the cut compares
    these to find a false start Whisper spelled differently from the take that followed ("متوو… ام… ام توها متوفي")."""
    if not words:
        return words
    model = _load()
    if model is None:
        return words
    if spans is None:
        from .vad import islands
        spans = islands(audio, min_silence=0.2)
    if not spans:
        return words
    sess, vocab = model
    words = sorted(words, key=lambda w: w.start)
    groups: dict[int, list[int]] = {}
    k = 0
    for i, w in enumerate(words):
        # Whisper's starts are close; its ends stretch over pauses: the stretch where the word starts owns it,
        # else the one it overlaps most, else the nearest one when it is close
        pick = next((n for n in range(k, len(spans)) if spans[n][0] - 0.05 <= w.start < spans[n][1]), None)
        best = 0.0
        for n in range(k, len(spans)) if pick is None else ():
            s, e = spans[n]
            if s > w.end + 0.5:
                break
            ov = min(w.end, e) - max(w.start, s)
            if ov > best:
                best, pick = ov, n
        if pick is None:
            near = min(range(k, len(spans)), key=lambda n: min(abs(w.start - spans[n][1]), abs(w.end - spans[n][0])),
                       default=None)
            if near is not None and min(abs(w.start - spans[near][1]), abs(w.end - spans[near][0])) <= 1.0:
                pick = near
        if pick is not None:
            groups.setdefault(pick, []).append(i)
            k = pick           # the spoken order never goes backwards
    out = list(words)
    placed = 0
    for n in range(len(spans)) if heard is not None else ():
        if n not in groups:
            try:
                a, b = max(0, int((spans[n][0] - PAD) * SR)), int((spans[n][1] + PAD) * SR)
                if b - a >= SR // 10:
                    heard.append((spans[n][0], spans[n][1], _greedy(_logits(sess, audio[a:b]), vocab)))
            except Exception:   # noqa: BLE001
                pass
    for n, idx in groups.items():
        s, e = spans[n]
        try:
            got = _align_island(sess, vocab, audio, s, e, [words[i] for i in idx], heard)
        except Exception:   # noqa: BLE001 — one stretch failing never stops the rest
            got = None
        if got is None:
            continue
        for i, w in zip(idx, got):
            out[i] = w
        placed += len(idx)
    if heard is not None:
        heard.sort()
    print(f"📐 حدود الكلمات من الصوت نفسه: {placed} من {len(words)} كلمة", flush=True)
    return out
