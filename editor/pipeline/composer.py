"""The channel's own music, composed by code for every episode (owner, 2026-10-22: "موسيقى خاصة إلنا، بلا حقوق").

Nobody else has these tracks, so YouTube's Content ID can never claim them, and no money is spent. Each cue of
the plan (plan.music: t, mood) gets a piece of exactly its length, written from the mood:
  tension  minor, low drone, ticking pulse          wonder   major/lydian pads, soft bell arpeggio
  sad      slow minor pads, sparse piano-like notes  drive    pulsing bass, steady arpeggio, more energy
  dark     sub drone, distant hits, almost no melody calm     warm pads, very slow, no rhythm
Built from additive synthesis (band-limited saws for pads, sines with partials for plucks and bells), a long
synthetic reverb and gentle stereo, then peak-normalised (compose levels it under the voice). A seed from the
episode and cue makes every episode's music different but rebuildable.
"""
import hashlib
import json
import wave
from pathlib import Path

import numpy as np

SR = 48000
NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

# progressions: (root note, chord intervals) per bar
PROGRESSIONS = {
    "tension": [("A", (0, 3, 7, 10)), ("F", (0, 4, 7, 11)), ("D", (0, 3, 7, 10)), ("E", (0, 3, 7, 10))],
    "wonder": [("D", (0, 4, 7, 11, 14)), ("A", (0, 4, 7, 14)), ("B", (0, 3, 7, 10)), ("G", (0, 4, 6, 11))],
    "sad": [("A", (0, 3, 7)), ("F", (0, 4, 7, 11)), ("C", (0, 4, 7)), ("G", (0, 4, 7, 9))],
    "drive": [("E", (0, 3, 7)), ("C", (0, 4, 7)), ("G", (0, 4, 7)), ("D", (0, 4, 7))],
    "dark": [("C", (0, 3, 7)), ("C#", (0, 4, 7)), ("C", (0, 3, 7)), ("G#", (0, 4, 7))],
    "calm": [("F", (0, 4, 7, 11)), ("C", (0, 4, 7, 14)), ("A", (0, 3, 7, 10)), ("G", (0, 5, 7))],
}
TEMPO = {"tension": 76, "wonder": 84, "sad": 64, "drive": 108, "dark": 60, "calm": 70}
KEYWORDS = {
    "tension": ("tension", "suspense", "investig", "mystery", "thriller", "توتر", "تشويق", "غموض"),
    "wonder": ("wonder", "curious", "discovery", "inspir", "hope", "light", "pizzicato", "فضول", "دهشة", "اكتشاف"),
    "sad": ("sad", "emotional", "melanchol", "loss", "حزن", "عاطف", "مؤثر"),
    "drive": ("drive", "energetic", "upbeat", "action", "fast", "epic", "حماس", "سريع", "طاقة"),
    "dark": ("dark", "ominous", "war", "danger", "horror", "مظلم", "خطر", "حرب", "رعب"),
    "calm": ("calm", "ambient", "soft", "warm", "هادئ", "هدوء", "دافي"),
}


def pick_mood(text: str) -> str:
    t = (text or "").lower()
    scores = {m: sum(k in t for k in ks) for m, ks in KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "tension"


def _hz(note: str, octave: int, semis: int = 0) -> float:
    n = NOTE[note] + semis + 12 * (octave + 1)
    return 440.0 * 2 ** ((n - 69) / 12)


def _saw(f: float, t: np.ndarray, harmonics: int = 14) -> np.ndarray:
    """Band-limited saw (additive): warm, no aliasing."""
    out = np.zeros_like(t)
    for k in range(1, harmonics + 1):
        if f * k > SR / 2.2:
            break
        out += np.sin(2 * np.pi * f * k * t) / k
    return out


def _env(n: int, a: float, r: float) -> np.ndarray:
    e = np.ones(n)
    na = min(int(a * SR), n)
    nr = min(int(r * SR), n - na)
    if na:
        e[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    if nr:
        e[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return e


def _pluck(f: float, dur: float, rng) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-6 * t)
            + 0.15 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-9 * t))
    return tone * np.exp(-3.2 * t) * (1 - np.exp(-t * 400))


def _reverb(x: np.ndarray, seconds: float, rng, mix: float) -> np.ndarray:
    from scipy.signal import fftconvolve
    n = int(seconds * SR)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 7, n))
    ir[: int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    wet = fftconvolve(x, ir)[: len(x)]
    return (1 - mix) * x + mix * wet * 0.9


def _lowpass(x: np.ndarray, hz: float) -> np.ndarray:
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, hz, "low", fs=SR, output="sos"), x)


def compose(duration: float, mood: str, seed: int) -> np.ndarray:
    """Stereo float array (n, 2) of `duration` seconds."""
    rng = np.random.default_rng(seed)
    prog = PROGRESSIONS[mood]
    shift = int(rng.integers(-2, 3))                  # every episode in a slightly different key
    bpm = TEMPO[mood] * (1 + rng.uniform(-0.04, 0.04))
    beat = 60 / bpm
    bar = beat * 4 * (2 if mood in ("sad", "dark", "calm") else 1)
    n = int((duration + 2.5) * SR)
    t_all = np.arange(n) / SR
    pad = np.zeros(n)
    bass = np.zeros(n)
    lead = np.zeros(n)
    order = list(range(len(prog)))
    bars = int(np.ceil(duration / bar)) + 1
    for b in range(bars):
        root, iv = prog[order[b % len(order)]]
        s0 = int(b * bar * SR)
        s1 = min(n, int((b + 1) * bar * SR + 0.8 * SR))   # chords overlap a little: a soft change
        if s0 >= n:
            break
        t = np.arange(s1 - s0) / SR
        chord = np.zeros(s1 - s0)
        for k, i in enumerate(iv):
            f = _hz(root, 3, i + shift)
            det = [1.0, 2 ** (6 / 1200), 2 ** (-6 / 1200)]  # three slightly detuned voices: width, life
            chord += sum(_saw(f * d, t + rng.uniform(0, 1), 10) for d in det) / (3 * len(iv))
        chord *= _env(len(t), min(1.6, bar * 0.4), 0.8)
        pad[s0:s1] += chord
        # bass: the root, as a pulse (drive/tension) or held (the rest)
        fb = _hz(root, 1, shift)
        if mood in ("drive", "tension"):
            step = beat / (2 if mood == "drive" else 1)
            k = 0
            while b * bar + k * step < (b + 1) * bar:
                p0 = int((b * bar + k * step) * SR)
                p1 = min(n, p0 + int(step * 0.9 * SR))
                tt = np.arange(p1 - p0) / SR
                bass[p0:p1] += (np.sin(2 * np.pi * fb * tt) + 0.3 * np.sin(2 * np.pi * 2 * fb * tt)) * np.exp(-4.5 * tt) * 0.8
                k += 1
        else:
            bass[s0:s1] += np.sin(2 * np.pi * fb * t) * _env(len(t), 0.8, 0.8) * 0.55
        # lead: plucks / bells on chord tones (none in dark)
        if mood != "dark":
            notes = int(bar / (beat / (2 if mood in ("drive", "wonder") else 1)))
            for k in range(notes):
                if mood in ("sad", "calm") and rng.random() < 0.55:   # sparse: space is the emotion
                    continue
                i = iv[int(rng.integers(0, len(iv)))] + (12 if rng.random() < 0.4 else 0)
                p0 = s0 + int(k * bar / notes * SR)
                note = _pluck(_hz(root, 5, i + shift), 1.4, rng) * (0.5 + 0.5 * rng.random())
                p1 = min(n, p0 + len(note))
                if p0 < n:
                    lead[p0:p1] += note[: p1 - p0]
    # textures by mood
    tex = np.zeros(n)
    if mood in ("tension", "dark"):
        tick = beat / 2
        k = 0
        while k * tick < duration:
            p0 = int(k * tick * SR)
            m = min(n - p0, int(0.03 * SR))
            if m > 0:
                tex[p0:p0 + m] += rng.standard_normal(m) * np.exp(-np.linspace(0, 8, m)) * (0.18 if k % 2 else 0.1)
            k += 1
        tex = np.convolve(tex, [1, -0.95], "same")      # thin, high tick
    if mood == "dark":
        tex += np.sin(2 * np.pi * _hz("C", 0, shift) * t_all) * 0.25 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t_all))
    pad = _lowpass(pad, 1400 + 600 * rng.random())
    mixes = {"pad": 0.55, "bass": 0.45 if mood != "calm" else 0.3, "lead": 0.28 if mood != "drive" else 0.33, "tex": 0.35}
    mono = mixes["pad"] * pad + mixes["bass"] * bass + mixes["tex"] * tex
    left = mono + mixes["lead"] * np.roll(lead, int(0.011 * SR))
    right = mono + mixes["lead"] * lead
    left = _reverb(left, 3.2, rng, 0.35)
    right = _reverb(right, 3.4, np.random.default_rng(seed + 1), 0.35)
    st = np.stack([left, right], axis=1)[: int(duration * SR)]
    fade = min(len(st), int(2.0 * SR))
    st[:int(0.6 * SR)] *= np.linspace(0, 1, min(len(st), int(0.6 * SR)))[:, None]
    st[-fade:] *= np.linspace(1, 0, fade)[:, None]
    peak = np.abs(st).max() or 1.0
    return st / peak * 10 ** (-3 / 20)


def write_wav(x: np.ndarray, path: Path) -> Path:
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


def compose_music(ep, total: float) -> list[str]:
    """assets/music_<k>.wav for every music cue still empty (or one bed, assets/music.wav, when the plan names none).
    Returns what it wrote, for the log."""
    from .music import music_asset, segments
    from .plan import load_plan
    from .styles import load_style
    plan = load_plan(ep.plan)
    style_mood = load_style(plan.style["primary"]).music_mood or ""
    wanted = [(str(k), music_asset(ep, k), ep.assets / f"music_{k}.wav", plan.music[k], e - s)
              for k, s, e in segments(plan, total)]
    if not plan.music:
        have = next(iter(sorted(ep.assets.glob("music.*"))), None)
        wanted = [("bed", have, ep.assets / "music.wav", {}, total)]
    credits_file = ep.work / "music_credits.json"
    credits = json.loads(credits_file.read_text(encoding="utf-8")) if credits_file.exists() else {}
    done = []
    for key, have, out, m, length in wanted:
        if have:
            continue
        mood = pick_mood(f"{m.get('mood', '')} {m.get('prompt', '')} {m.get('search', '')} {style_mood}")
        seed = int(hashlib.sha1(f"{ep.root.name}:{key}".encode()).hexdigest()[:8], 16)
        write_wav(compose(max(4.0, length), mood, seed), out)
        credits[key] = {"url": "", "credit": f"موسيقى مؤلفة بالكود خاصة بالقناة ({mood})"}
        done.append(f"{key}:{mood}")
    credits_file.write_text(json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")
    return done
