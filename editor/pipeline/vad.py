"""Where he really talks: Silero VAD (MIT licence, ~2 MB, it ships inside faster-whisper and runs on onnxruntime).

A model trained on speech tells talk from room noise, breaths, a chair or a hum; the old loudness threshold could not
(owner, 2026-10-30: "ما يشيل السكتات"). Both the reading pieces (transcribe.py) and the cut (clean.py) use it.
When it can't run, or it hears no speech at all in clearly loud sound (test tones, music), callers fall back to
loudness: every function here returns None then."""
from functools import lru_cache

import numpy as np

SR = 16000
FRAME = 512                  # samples per Silero frame (32 ms)
HOP = 0.01                   # s per value of a speech mask (the same grid as clean.loudness)


@lru_cache(maxsize=1)
def _model():
    try:
        from faster_whisper.vad import get_vad_model
        return get_vad_model()
    except Exception:   # noqa: BLE001 — no faster-whisper / onnxruntime: loudness takes over
        return None


def islands(audio: np.ndarray, min_silence: float = 0.1, min_speech: float = 0.08,
            threshold: float = 0.5) -> list[tuple[float, float]] | None:
    """(start, end) seconds of every stretch of speech; a pause shorter than `min_silence` stays inside it."""
    if _model() is None or len(audio) < FRAME * 4:
        return None
    try:
        from faster_whisper.vad import VadOptions, get_speech_timestamps
        ts = get_speech_timestamps(audio.astype(np.float32), VadOptions(
            threshold=threshold, min_silence_duration_ms=int(min_silence * 1000),
            min_speech_duration_ms=int(min_speech * 1000), speech_pad_ms=0))
    except Exception:   # noqa: BLE001
        return None
    out = [(round(t["start"] / SR, 3), round(t["end"] / SR, 3)) for t in ts]
    if not out and _clearly_loud(audio):
        return None      # tones or music: not speech, but not silence either — the caller's loudness rule decides
    return out


def _clearly_loud(audio: np.ndarray) -> bool:
    n = len(audio) // 160
    env = np.sqrt((audio[: n * 160].reshape(n, 160) ** 2).mean(axis=1)) if n else np.zeros(1)
    return float(np.percentile(env, 90)) > 0.01


def mask(audio: np.ndarray, env: np.ndarray, tail: float = 0.2, head: float = 0.12) -> np.ndarray | None:
    """Speech per 10 ms (aligned with `env`, clean.loudness of the same sound). Silero's edges sit on 32 ms frames
    and it lets go a little early on a soft word ending ("ـه", a fading vowel), so each stretch grows outwards
    while the sound itself stays above the quiet level: at most `head` s before it and `tail` s after it."""
    spans = islands(audio)
    if spans is None:
        return None
    n = len(env)
    m = np.zeros(n, bool)
    if not spans:
        return m
    floor, peak = float(np.percentile(env, 10)), float(np.percentile(env, 95))
    quiet = max(floor * 3, peak * 0.04, 1e-4)
    for s, e in spans:
        a, b = max(0, int(s / HOP)), min(n, int(np.ceil(e / HOP)))
        lo = a
        while lo > 0 and a - lo < head / HOP and env[lo - 1] > quiet:
            lo -= 1
        hi = b
        while hi < n and hi - b < tail / HOP and env[hi] > quiet:
            hi += 1
        m[lo:hi] = True
    return m
