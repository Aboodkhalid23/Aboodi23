"""Stage 2: speech → words with timestamps (Whisper: on the Mac's chip with mlx, else faster-whisper on the CPU)."""
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .media import MediaError, probe
from .paths import Episode


@dataclass
class Word:
    text: str
    start: float
    end: float
    p: float = 1.0   # Whisper's confidence in the word (low on names he says unclearly: names.py looks there)


def save_words(words: list[Word], path: Path) -> None:
    data = [{"t": w.text, "s": round(w.start, 3), "e": round(w.end, 3), **({"p": round(w.p, 2)} if w.p < 0.995 else {})}
            for w in words]
    Path(path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def load_words(path: Path) -> list[Word]:
    return [Word(d["t"], d["s"], d["e"], d.get("p", 1.0)) for d in json.loads(Path(path).read_text(encoding="utf-8"))]


IRAQI_PROMPT = "هلا بيكم، اليوم راح نحچي عن قصة غريبة. شلون صار هيچ؟ خلي نشوف شنو الي صار بالضبط."


def hotwords(ep: Episode) -> str | None:
    """Words Whisper should expect: edit/vocab.txt plus every name in edit/entities.json."""
    from .entities import entity_vocab
    vocab = ep.edit / "vocab.txt"
    words = vocab.read_text(encoding="utf-8").split() if vocab.exists() else []
    words += entity_vocab(ep)
    return " ".join(dict.fromkeys(w for w in words if w)) or None


# large-v3-turbo: ~4x faster than large-v3 on the CPU; large-v3 hears Iraqi words better (see _model_for_length).
WHISPER_MODEL = os.environ.get("ABOODI_WHISPER", "large-v3-turbo")
MLX_MODEL = "mlx-community/whisper-large-v3-turbo"


def mlx_ready() -> bool:
    """Apple Silicon with mlx-whisper: the same turbo model on the Mac's GPU (owner, 2026-10-26: "أريد سرعة")."""
    import platform
    import sys
    if sys.platform != "darwin" or platform.machine() != "arm64" or os.environ.get("ABOODI_NO_MLX"):
        return False
    try:
        import mlx_whisper  # noqa: F401
        return True
    except Exception:
        return False


SR = 16000
CHUNK_MAX = 14.0     # seconds of talk per piece
CHUNK_GAP = 0.3      # a pause this long ends a stretch of sound
SPLIT_GAP = 0.5      # a pause this long always starts a new piece: a retake comes after a stop


def load_audio(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def speech_chunks(audio: np.ndarray, most: float = CHUNK_MAX, gap: float = CHUNK_GAP,
                  split: float = SPLIT_GAP) -> list[tuple[float, float]]:
    """Pieces of talk cut at his pauses (owner, 2026-10-26: his retakes never reached the timeline).
    Whisper reads up to 30 s at once and quietly skips a sentence it hears twice ("it's a retake, write it once"),
    so the first take was never written down and nothing could cut it. Short pieces, each read on its own, keep
    every take. Every pause of `split` seconds starts a new piece; shorter ones join, up to `most` seconds."""
    hop = SR // 100
    n = len(audio) // hop
    if n == 0:
        return []
    env = np.sqrt((audio[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    floor, peak = float(np.percentile(env, 10)), float(np.percentile(env, 98))
    loud = env > max(floor * 3, peak * 0.05, 3e-4)
    # stretches of sound, with pauses shorter than `gap` filled in
    runs, start, quiet = [], None, 0
    for i, on in enumerate(loud):
        if on:
            if start is None:
                start = i
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet >= gap * 100:
                runs.append((start, i - quiet + 1))
                start, quiet = None, 0
    if start is not None:
        runs.append((start, n - quiet))
    runs = [(a, b) for a, b in runs if b - a >= 8]          # clicks and breaths shorter than 80 ms
    out = []
    for a, b in runs:
        if out and (a - out[-1][1]) / 100 < split and (b - out[-1][0]) / 100 <= most:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    pad = 0.12
    total = len(audio) / SR
    return [(max(0.0, a / 100 - pad), min(total, b / 100 + pad)) for a, b in out]


# what Whisper writes when it hears nothing useful (YouTube subtitle credits it learnt from)
HALLUCINATIONS = ("اشتركوا في القناة", "اشترك في القناة", "ترجمة نانسي", "شكرا للمشاهدة", "شكراً للمشاهدة",
                  "نانسي قنقر", "المترجم للقناة", "موسيقى", "Subtitles", "Amara")


def _clean_piece(words: list[Word]) -> list[Word]:
    text = " ".join(w.text for w in words)
    if any(h in text for h in HALLUCINATIONS) and (len(words) <= 6 or sum(w.p for w in words) / len(words) < 0.5):
        return []
    return words


def _words_of(segments, offset: float, end: float) -> list[Word]:
    out = []
    for seg in segments:
        ws = seg.get("words") if isinstance(seg, dict) else seg.words
        for w in ws or []:
            text = (w["word"] if isinstance(w, dict) else w.word).strip()
            if not text:
                continue
            g = (lambda k: w[k]) if isinstance(w, dict) else (lambda k: getattr(w, k))
            ws_, we = float(g("start")) + offset, float(g("end")) + offset
            prob = float((w.get("probability") if isinstance(w, dict) else getattr(w, "probability", 1.0)) or 1.0)
            out.append(Word(text, round(min(ws_, end), 3), round(min(we, end), 3), round(prob, 2)))
    return out


def _model_for_length(seconds: float) -> tuple[str, str]:
    """(faster-whisper name, mlx repo). The full large-v3 hears Iraqi words better; turbo is ~3x faster.
    Up to 20 minutes: the full model (a few minutes at most on the Mac's chip); longer talks: turbo, unless
    ABOODI_WHISPER says otherwise."""
    forced = os.environ.get("ABOODI_WHISPER")
    name = forced or ("large-v3" if seconds <= 20 * 60 else "large-v3-turbo")
    return name, f"mlx-community/whisper-{name}"


def _script_text(ep: Episode) -> str:
    for name in ("04-script.md", "02-draft.md"):
        f = ep.root / name
        if f.exists():
            return f.read_text(encoding="utf-8")
    return ""


def pick_dialect(ep: Episode, sample=None) -> str:
    """His setting; else his script; else the first pieces of his talk heard without any example (`sample()`)."""
    from . import dialects
    key, how = dialects.chosen(), "setting"
    if key == "auto":
        text, how = _script_text(ep), "script"
        if not text.strip() and sample is not None:
            text, how = sample(), "voice"
        key = dialects.detect(text) if text.strip() else dialects.DEFAULT
    dialects.save(ep.edit, key, how)
    print(f"🗣️ اللهجة: {dialects.name(key)}", flush=True)
    return key


def _run_chunks(ep: Episode, read_piece) -> list[Word]:
    """`read_piece(audio, example sentence or None)` → segments. The dialect is found on the first pieces, then
    every piece is read with that dialect's example (owner, 2026-10-26: every Arabic dialect)."""
    from . import dialects
    audio = load_audio(ep.source)
    chunks = speech_chunks(audio)
    total = len(audio) / SR or 1.0
    piece = lambda s, e: audio[int(s * SR):int(e * SR)]

    def sample() -> str:
        got = []
        for s, e in chunks[:4]:
            got += [w.text for w in _words_of(read_piece(piece(s, e), None), s, e)]
        return " ".join(got)
    hw = hotwords(ep)
    example = dialects.prompt(pick_dialect(ep, sample)) + (" " + hw if hw else "")
    show = os.environ.get("ABOODI_PROGRESS")
    words, last = [], -1
    for s, e in chunks:
        got = read_piece(piece(s, e), example)
        words += [w for w in _clean_piece(_words_of(got, s, e)) if not words or w.start >= words[-1].start]
        pct = min(99, int(100 * e / total))
        if show and pct > last:
            print(f"@@ {pct}", flush=True)
            last = pct
    return words


def _transcribe_mlx(ep: Episode, repo: str) -> list[Word]:
    import mlx_whisper
    print("⚡ التفريغ على شريحة الماك، جملة جملة حتى ما تضيع أي إعادة", flush=True)
    return _run_chunks(ep, lambda piece, example: mlx_whisper.transcribe(
        piece, path_or_hf_repo=repo, language="ar", word_timestamps=True, initial_prompt=example,
        condition_on_previous_text=False, temperature=0.0, verbose=None).get("segments", []))


def transcribe(ep: Episode, model_name: str | None = None, model=None) -> list[Word]:
    info = probe(ep.source)
    if not info.has_audio:
        raise MediaError("الصوت فارغ أو مو واضح")
    auto_name, repo = _model_for_length(info.duration or 0)
    model_name = model_name or auto_name
    if model is None and mlx_ready():
        try:
            words = _transcribe_mlx(ep, repo)
            if words:
                save_words(words, ep.transcript)
                return words
        except Exception as exc:   # any trouble: the CPU model below does it
            print(f"⚠️ التفريغ السريع ما زبط ({exc}). أكمّل بالعادي", flush=True)
    if model is None:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
    hw = hotwords(ep)

    def read(piece, example):
        segs, _ = model.transcribe(piece, language="ar", word_timestamps=True, vad_filter=False,
                                   initial_prompt=example, hotwords=hw if example else None, beam_size=5,
                                   condition_on_previous_text=False)
        return list(segs)
    words = _run_chunks(ep, read)
    if not words:
        raise MediaError("الصوت فارغ أو مو واضح")
    save_words(words, ep.transcript)
    return words
