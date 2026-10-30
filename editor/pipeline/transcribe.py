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
    global MLX_PROBLEM
    """Apple Silicon with mlx-whisper: the same turbo model on the Mac's GPU (owner, 2026-10-26: "أريد سرعة")."""
    import platform
    import sys
    if sys.platform != "darwin" or platform.machine() != "arm64" or os.environ.get("ABOODI_NO_MLX"):
        MLX_PROBLEM = f"not an Apple chip here ({sys.platform} {platform.machine()} no_mlx={bool(os.environ.get('ABOODI_NO_MLX'))})"
        return False
    try:
        import mlx_whisper  # noqa: F401
        return True
    except Exception as exc:
        MLX_PROBLEM = f"{type(exc).__name__}: {exc}"[:300]
        return False


MLX_PROBLEM = ""   # why the Mac chip's model would not load (shown in the app's report)


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
    from .vad import islands
    spans = islands(audio, min_silence=gap)      # speech by a model (room noise and breaths are not talk)
    runs = [(int(s * 100), int(np.ceil(e * 100))) for s, e in spans] if spans is not None else _loud_runs(audio, gap)
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


def _loud_runs(audio: np.ndarray, gap: float) -> list[tuple[int, int]]:
    """Without the speech model: stretches of sound (10 ms steps), pauses shorter than `gap` filled in."""
    hop = SR // 100
    n = len(audio) // hop
    env = np.sqrt((audio[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    floor, peak = float(np.percentile(env, 10)), float(np.percentile(env, 98))
    loud = env > max(floor * 3, peak * 0.05, 3e-4)
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
    return runs


# what Whisper writes when it hears nothing useful (YouTube subtitle credits it learnt from)
HALLUCINATIONS = ("اشتركوا في القناة", "اشترك في القناة", "ترجمة نانسي", "شكرا للمشاهدة", "شكراً للمشاهدة",
                  "نانسي قنقر", "المترجم للقناة", "موسيقى", "Subtitles", "Amara")


def _clean_piece(words: list[Word]) -> list[Word]:
    text = " ".join(w.text for w in words)
    if any(h in text for h in HALLUCINATIONS) and (len(words) <= 6 or sum(w.p for w in words) / len(words) < 0.5):
        return []
    # Whisper stuck in a loop on a short try ("وماته وماته وماته" for a 0.6 s "متو…"): one word, over the same time
    bare = lambda w: w.text.strip(".,،؟?!")
    groups: list[list[Word]] = []
    for w in words:
        if groups and bare(w) == bare(groups[-1][0]):
            groups[-1].append(w)
        else:
            groups.append([w])
    return [w for g in groups for w in ([Word(g[0].text, g[0].start, g[-1].end, min(x.p for x in g))]
                                        if len(g) >= 3 else g)]


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
    """(faster-whisper name, mlx repo): turbo always. Measured 2026-10-28 on a talk with six retakes: turbo kept every
    take in the right order in 7 reads; the full large-v3 dropped a take and swapped two sentences in long windows,
    and is ~3x slower (owner: "ترتيب الجمل فاشل… نص ساعة"). ABOODI_WHISPER can still force another model."""
    name = os.environ.get("ABOODI_WHISPER") or "large-v3-turbo"
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


WINDOW = 25.0     # seconds per reading window (Whisper always pays for a 30 s window, however short the piece)
VERBATIM_SPLIT = 0.35   # verbatim reading: every pause this long starts a new piece (a retake comes after a stop)


def verbatim_wanted() -> bool:
    """Every stretch of talk read on its own, so each take is written down (owner, 2026-10-30: "شال الصحيح وخلّى
    الغلط من كررت"). On the Mac's chip a piece costs a fraction of a second; on the CPU it is ~4x slower than
    reading 25 s windows, so there it is only on when asked (ABOODI_VERBATIM=1)."""
    flag = os.environ.get("ABOODI_VERBATIM")
    return flag != "0" if flag is not None else mlx_ready()


def _run_chunks(ep: Episode, read_piece, verbatim: bool = False) -> list[Word]:
    """`read_piece(audio, example sentence or None)` → segments.
    Verbatim: every stretch of talk between two pauses is read alone (Whisper writes a sentence it hears twice in one
    window only once, so the failed take never reached the cut). Otherwise pass 1 reads windows of up to 25 s cut at
    pauses: as fast as Whisper gets on the CPU (owner, 2026-10-28 "التفريغ… نص ساعة").
    Pass 2 finds every stretch of voice that still got no words and reads only those again, alone.
    The dialect is found on the first pieces first (owner, 2026-10-26)."""
    from . import dialects
    audio = load_audio(ep.source)
    total = len(audio) / SR or 1.0
    pieces = speech_chunks(audio)                                   # every breath-to-pause stretch
    windows = speech_chunks(audio, split=VERBATIM_SPLIT) if verbatim else \
        speech_chunks(audio, most=WINDOW, split=10 ** 9)            # the same, packed into reading windows
    if verbatim:
        print(f"🔎 أقرا كل مقطع كلام لحاله ({len(windows)} مقطع) حتى تنكتب كل إعادة", flush=True)
    cut = lambda s, e: audio[int(s * SR):int(e * SR)]

    def sample() -> str:   # one reading of the first window, with no example, tells the dialect
        if not windows:
            return ""
        s, e = windows[0]
        return " ".join(w.text for w in _words_of(read_piece(cut(s, e), None), s, e))
    hw = hotwords(ep)
    example = dialects.prompt(pick_dialect(ep, sample)) + (" " + hw if hw else "")
    show = os.environ.get("ABOODI_PROGRESS")
    words, last = [], -1
    for s, e in windows:
        got = _clean_piece(_words_of(read_piece(cut(s, e), example), s, e))
        if e - s < 0.6 and got and sum(w.p for w in got) / len(got) < 0.5:
            got = []          # a cough or a breath read alone: Whisper guesses words that were never said
        words += got
        pct = min(90, int(90 * e / total))
        if show and pct > last:
            print(f"@@ {pct}", flush=True)
            last = pct
    words.sort(key=lambda w: w.start)
    # pass 2: voice with no words in it (a skipped take) is read again on its own
    mids = [(w.start + w.end) / 2 for w in words]
    missed = [(s, e) for s, e in pieces if e - s >= 0.6 and not any(s <= m <= e for m in mids)]
    if missed:
        print(f"🔁 {len(missed)} مقطع صوت ما انكتب (إعادات غالباً): أقراها وحدها", flush=True)
    for s, e in missed:
        words += _clean_piece(_words_of(read_piece(cut(s, e), example), s, e))
    words.sort(key=lambda w: w.start)
    if show:
        print("@@ 99", flush=True)
    return words


def _transcribe_mlx(ep: Episode, repo: str) -> list[Word]:
    import mlx_whisper
    print("⚡ التفريغ على شريحة الماك، جملة جملة حتى ما تضيع أي إعادة", flush=True)
    return _run_chunks(ep, lambda piece, example: mlx_whisper.transcribe(
        piece, path_or_hf_repo=repo, language="ar", word_timestamps=True, initial_prompt=example,
        condition_on_previous_text=False, temperature=0.0, verbose=None).get("segments", []),
        verbatim=verbatim_wanted())


def _exact_edges(ep: Episode, words: list[Word]) -> list[Word]:
    """Every word on the moment the sound shows (wordtimes.py); the old times if anything goes wrong."""
    try:
        from .wordtimes import refine_times
        heard: list = []
        out = refine_times(load_audio(ep.source), words, heard=heard)
        if heard:
            ep.heard.write_text(json.dumps([[round(s, 3), round(e, 3), t] for s, e, t in heard], ensure_ascii=False),
                                encoding="utf-8")
        return out
    except Exception as exc:   # noqa: BLE001 — a nicety: Whisper's times still cut
        print(f"⚠️ ضبط حدود الكلمات ما زبط ({str(exc)[:120]})", flush=True)
        return words


SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"


def _scribe(ep: Episode, key: str, session=None) -> list[Word]:
    """ElevenLabs Scribe: the talk is heard on their servers (owner, 2026-10-28: "ادوات اشتريها… بس نحل هل مشاكل").
    Verbatim (every retake and slip is written, so the cut can remove it), every Arabic dialect, word times, and
    nothing heavy runs on his Mac. Only a small voice-only copy is sent (mono, 32 kb/s), never the picture."""
    import math
    import requests
    voice = ep.work / "scribe_voice.ogg"
    voice.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ep.source), "-vn", "-ac", "1", "-ar", "16000",
                    "-c:a", "libopus", "-b:a", "32k", str(voice)], check=True, capture_output=True)
    print("☁️ التفريغ على سيرفرات إلفن لابس (سريع، وما يحمّي الماك)", flush=True)
    sess = session or requests.Session()
    with open(voice, "rb") as fh:
        r = sess.post(SCRIBE_URL, headers={"xi-api-key": key}, timeout=900,
                      data={"model_id": "scribe_v2", "language_code": "ara", "timestamps_granularity": "word",
                            "tag_audio_events": "false", "diarize": "false"},
                      files={"file": ("voice.ogg", fh, "audio/ogg")})
    voice.unlink(missing_ok=True)
    if r.status_code != 200:
        raise RuntimeError(f"إلفن لابس رفض ({r.status_code}): {r.text[:200]}")
    words = []
    for w in r.json().get("words", []):
        if w.get("type") != "word" or w.get("start") is None or not str(w.get("text", "")).strip():
            continue
        lp = w.get("logprob")
        words.append(Word(str(w["text"]).strip(), round(float(w["start"]), 3), round(float(w["end"]), 3),
                          round(min(1.0, math.exp(lp)), 2) if isinstance(lp, (int, float)) else 1.0))
    return words


def cloud_key() -> str | None:
    """His ElevenLabs key when he chose (or left on «تلقائي») cloud hearing; the app passes it as ELEVENLABS_API_KEY."""
    return os.environ.get("ELEVENLABS_API_KEY") or None


def transcribe(ep: Episode, model_name: str | None = None, model=None) -> list[Word]:
    info = probe(ep.source)
    if not info.has_audio:
        raise MediaError("الصوت فارغ أو مو واضح")
    auto_name, repo = _model_for_length(info.duration or 0)
    model_name = model_name or auto_name
    key = cloud_key() if model is None else None
    if key:
        try:
            words = _scribe(ep, key)
            if words:
                from . import dialects
                dialects.save(ep.edit, dialects.detect(" ".join(w.text for w in words[:400])), "cloud")
                words = _exact_edges(ep, words)
                save_words(words, ep.transcript)
                return words
        except Exception as exc:   # no internet, no balance: the Mac does it as before
            print(f"⚠️ التفريغ السحابي ما زبط ({str(exc)[:160]}). أكمّل على الماك", flush=True)
    if model is None and mlx_ready():
        try:
            words = _transcribe_mlx(ep, repo)
            if words:
                words = _exact_edges(ep, words)
                save_words(words, ep.transcript)
                return words
        except Exception as exc:   # any trouble: the CPU model below does it
            print(f"⚠️ التفريغ السريع ما زبط ({exc}). أكمّل بالعادي", flush=True)
    real = model is None
    if real:
        from faster_whisper import WhisperModel
        print(f"🎧 التفريغ على المعالج ({model_name})", flush=True)
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
    hw = hotwords(ep)

    def read(piece, example):
        segs, _ = model.transcribe(piece, language="ar", word_timestamps=True, vad_filter=False,
                                   initial_prompt=example, hotwords=hw if example else None, beam_size=5,
                                   condition_on_previous_text=False)
        return list(segs)
    words = _run_chunks(ep, read, verbatim=real and verbatim_wanted())
    if not words:
        raise MediaError("الصوت فارغ أو مو واضح")
    if real:
        words = _exact_edges(ep, words)
    save_words(words, ep.transcript)
    return words
