"""More sound effects, made here from code (owner, 2026-10-25: "الأصوات قليلة ومو واضحة… أريدها محملة"). Ours, no
copyright, nothing to download: each one is written once into the cache the first time it's asked for.

Built from noise, swept sines, envelopes, filters and a small reverb; levelled like the rest (sfx.py)."""
from pathlib import Path

import numpy as np

SR = 48000


def _t(d):
    return np.arange(int(d * SR)) / SR


def _env(n, a, r, curve=4.0):
    e = np.ones(n)
    ai, ri = max(1, int(a * SR)), max(1, int(r * SR))
    e[:ai] = np.linspace(0, 1, ai) if ai < n else np.linspace(0, 1, n)[:ai]
    if ri < n:
        e[-ri:] *= np.exp(-curve * np.linspace(0, 1, ri))
    return e


def _noise(d, rng, color="white"):
    x = rng.standard_normal(int(d * SR))
    if color == "pink":
        x = np.cumsum(x) * 0.02
        x -= np.convolve(x, np.ones(400) / 400, "same")
    elif color == "brown":
        x = np.cumsum(x)
        x -= np.convolve(x, np.ones(2000) / 2000, "same")
    return x / (np.abs(x).max() or 1)


def _bandpass(x, lo, hi):
    f = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    f[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(f, len(x))


def _sweep(f0, f1, d, shape=1.0):
    t = _t(d)
    f = f0 + (f1 - f0) * (t / d) ** shape
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def _reverb(x, seconds, mix, rng):
    n = int(seconds * SR)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 7, n))
    out = np.concatenate([x, np.zeros(n)])
    wet = np.convolve(x, ir)[: len(out)]
    wet = np.pad(wet, (0, len(out) - len(wet)))
    return out * (1 - mix) + wet / (np.abs(wet).max() or 1) * mix * np.abs(x).max()


def _moving_band_noise(d, f0, f1, rng, width=0.6):
    """Noise whose colour slides from f0 to f1 (the sound of air moving past)."""
    x = _noise(d, rng)
    chunks, n = 24, len(x)
    out = np.zeros(n)
    for k in range(chunks):
        a, b = k * n // chunks, (k + 1) * n // chunks
        fc = f0 * (f1 / f0) ** (k / (chunks - 1))
        seg = _bandpass(x, fc * (1 - width), fc * (1 + width))[a:b]
        out[a:b] = seg
    return out


def make(name: str, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if name == "whoosh_soft":
        x = _moving_band_noise(0.7, 400, 2200, rng); x *= np.sin(np.pi * np.linspace(0, 1, len(x))) ** 2
    elif name == "whoosh_fast":
        x = _moving_band_noise(0.35, 600, 4500, rng); x *= np.sin(np.pi * np.linspace(0, 1, len(x))) ** 3
    elif name == "whoosh_heavy":
        x = _moving_band_noise(0.9, 120, 1400, rng) + 0.4 * _sweep(90, 40, 0.9) * _env(int(0.9 * SR), 0.3, 0.5)
        x *= np.sin(np.pi * np.linspace(0, 1, len(x))) ** 2
    elif name == "impact":   # cinematic hit: sub drop + noise crack + tail
        d = 2.2
        sub = _sweep(90, 32, d, 0.5) * np.exp(-2.2 * _t(d))
        crack = _bandpass(_noise(d, rng), 200, 6000) * np.exp(-28 * _t(d))
        x = _reverb(1.0 * sub + 0.6 * crack, 1.6, 0.35, rng)
    elif name == "impact_metal":
        d = 1.8
        t = _t(d)
        x = sum(np.sin(2 * np.pi * f * t) * np.exp(-a * t) for f, a in ((220, 3), (563, 4), (1187, 6), (2310, 9)))
        x += _bandpass(_noise(d, rng), 1500, 9000) * np.exp(-40 * t)
        x = _reverb(x, 1.2, 0.3, rng)
    elif name == "riser_long":
        d = 3.0
        x = 0.5 * _sweep(120, 1600, d, 2.0) * _env(int(d * SR), 2.6, 0.05) + \
            0.5 * _moving_band_noise(d, 300, 7000, rng, 0.3) * np.linspace(0, 1, int(d * SR)) ** 2
    elif name == "downlifter":
        d = 2.0
        x = 0.6 * _sweep(1200, 60, d, 0.6) * np.exp(-1.2 * _t(d)) + 0.4 * _moving_band_noise(d, 6000, 200, rng, 0.3) * np.exp(-1.5 * _t(d))
    elif name == "shutter":   # camera
        d = 0.22
        t = _t(d)
        x = _bandpass(_noise(d, rng), 1500, 9000) * (np.exp(-90 * t) + 0.8 * np.exp(-90 * np.clip(t - 0.09, 0, None)) * (t > 0.09))
    elif name == "flash_pop":
        d = 0.5
        x = _bandpass(_noise(d, rng), 2000, 12000) * np.exp(-30 * _t(d)) + 0.5 * _sweep(3000, 800, d) * np.exp(-12 * _t(d))
    elif name == "typewriter":
        x = np.zeros(int(0.9 * SR))
        for k, at in enumerate((0.0, 0.12, 0.25, 0.33, 0.47, 0.58)):
            n0 = int(at * SR); seg = _bandpass(_noise(0.05, rng), 800, 7000) * np.exp(-140 * _t(0.05))
            x[n0:n0 + len(seg)] += seg * (0.7 + 0.3 * rng.random())
        n0 = int(0.72 * SR); bell = np.sin(2 * np.pi * 2093 * _t(0.18)) * np.exp(-14 * _t(0.18)); x[n0:n0 + len(bell)] += 0.5 * bell
    elif name == "keyboard":
        x = np.zeros(int(1.2 * SR))
        at = 0.0
        while at < 1.1:
            n0 = int(at * SR); seg = _bandpass(_noise(0.03, rng), 1500, 8000) * np.exp(-200 * _t(0.03))
            x[n0:n0 + len(seg)] += seg * (0.5 + 0.5 * rng.random()); at += 0.06 + 0.08 * rng.random()
    elif name == "cash":   # register: bell + coins
        d = 1.2
        t = _t(d)
        x = 0.6 * (np.sin(2 * np.pi * 1568 * t) + 0.5 * np.sin(2 * np.pi * 3136 * t)) * np.exp(-5 * t)
        for at in (0.18, 0.24, 0.31, 0.36, 0.45):
            n0 = int(at * SR); c = np.sin(2 * np.pi * (4200 + 900 * rng.random()) * _t(0.12)) * np.exp(-35 * _t(0.12))
            x[n0:n0 + len(c)] += 0.35 * c
    elif name == "heartbeat":
        x = np.zeros(int(1.6 * SR))
        for at, g in ((0.0, 1.0), (0.24, 0.7), (0.8, 1.0), (1.04, 0.7)):
            n0 = int(at * SR); b = np.sin(2 * np.pi * 52 * _t(0.2)) * np.exp(-22 * _t(0.2)); x[n0:n0 + len(b)] += g * b
    elif name == "clock_tick":
        x = np.zeros(int(2.0 * SR))
        for k in range(4):
            n0 = int(k * 0.5 * SR); c = _bandpass(_noise(0.02, rng), 2500, 9000) * np.exp(-250 * _t(0.02)); x[n0:n0 + len(c)] += c * (1 if k % 2 else 0.7)
    elif name == "notification":
        x = np.concatenate([np.sin(2 * np.pi * 988 * _t(0.12)) * _env(int(0.12 * SR), 0.005, 0.1),
                            np.sin(2 * np.pi * 1319 * _t(0.35)) * _env(int(0.35 * SR), 0.005, 0.33)])
    elif name == "error_buzz":
        t = _t(0.45); x = np.sign(np.sin(2 * np.pi * 110 * t)) * 0.5 * _env(len(t), 0.005, 0.1); x = _bandpass(x, 80, 2500)
    elif name == "glitch_digital":
        x = np.zeros(int(0.7 * SR))
        at = 0.0
        while at < 0.65:
            d = 0.02 + 0.06 * rng.random(); n0 = int(at * SR)
            kind = rng.integers(0, 3)
            seg = (_bandpass(_noise(d, rng), 500, 9000) if kind == 0 else
                   np.sign(np.sin(2 * np.pi * rng.choice([180, 440, 1200, 2600]) * _t(d))) * 0.6 if kind == 1 else np.zeros(int(d * SR)))
            x[n0:n0 + len(seg)] += seg[: len(x) - n0]; at += d
    elif name == "static_tv":
        x = _bandpass(_noise(1.2, rng), 300, 10000) * _env(int(1.2 * SR), 0.02, 0.2)
    elif name == "tape_stop":
        d = 1.0
        x = _sweep(440, 30, d, 0.4) * np.exp(-1.0 * _t(d)) + 0.3 * _sweep(660, 40, d, 0.4) * np.exp(-1.0 * _t(d))
    elif name == "record_scratch":
        d = 0.45
        t = _t(d)
        x = _bandpass(_noise(d, rng), 300, 3000) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)) * _env(len(t), 0.01, 0.15)
        x += 0.4 * _sweep(900, 200, d) * _env(len(t), 0.01, 0.2)
    elif name == "swipe_ui":
        x = _moving_band_noise(0.22, 2500, 7000, rng, 0.25) * np.sin(np.pi * np.linspace(0, 1, int(0.22 * SR)))
    elif name == "bubble_pop":
        d = 0.18; x = _sweep(300, 1400, d, 0.5) * np.exp(-25 * _t(d))
    elif name == "bell":
        t = _t(2.5); x = sum(np.sin(2 * np.pi * f * t) * np.exp(-a * t) * g for f, a, g in ((523, 1.5, 1), (1046, 2.2, 0.5), (1567, 3, 0.3), (2637, 4, 0.2)))
    elif name == "gong":
        t = _t(4.0); x = sum(np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 3 * t)) * np.exp(-a * t) * g
                              for f, a, g in ((98, 0.6, 1), (196, 0.8, 0.6), (311, 1.1, 0.4), (523, 1.6, 0.25)))
    elif name == "drum_hit":
        d = 0.8; x = _sweep(140, 50, d, 0.3) * np.exp(-7 * _t(d)) + 0.3 * _bandpass(_noise(d, rng), 1000, 6000) * np.exp(-30 * _t(d))
    elif name == "laser":
        d = 0.4; x = _sweep(2500, 300, d, 0.6) * np.exp(-6 * _t(d))
    elif name == "sparkle":
        x = np.zeros(int(1.0 * SR))
        for k in range(10):
            n0 = int(rng.random() * 0.8 * SR); f = 2000 + 3000 * rng.random()
            s = np.sin(2 * np.pi * f * _t(0.15)) * np.exp(-25 * _t(0.15)); x[n0:n0 + len(s)] += 0.4 * s
    elif name == "page_flip":
        d = 0.45; x = _bandpass(_noise(d, rng), 800, 7000) * (np.sin(np.pi * np.linspace(0, 1, int(d * SR))) ** 3)
        x += 0.5 * _bandpass(_noise(d, rng), 1500, 5000) * np.exp(-60 * np.clip(_t(d) - 0.33, 0, None)) * (_t(d) > 0.33)
    elif name == "thunder":
        d = 3.5; x = _bandpass(_noise(d, rng, "brown"), 30, 400) * _env(int(d * SR), 0.05, 3.0, 3) * (1 + 0.5 * _noise(d, rng, "brown"))
    elif name == "wind":
        d = 3.0; x = _moving_band_noise(d, 300, 900, rng, 0.5) * _env(int(d * SR), 0.8, 1.2, 2)
    elif name == "phone_vibrate":
        x = np.zeros(int(1.0 * SR))
        for at in (0.0, 0.55):
            n0 = int(at * SR); t = _t(0.35); s = np.sign(np.sin(2 * np.pi * 160 * t)) * 0.4 * _env(len(t), 0.01, 0.05); x[n0:n0 + len(s)] += _bandpass(s, 80, 1500)
    elif name == "door_slam":
        d = 1.2; x = _reverb(_bandpass(_noise(0.15, rng), 60, 2500) * np.exp(-30 * _t(0.15)) + 0.8 * _sweep(80, 45, 0.15) * np.exp(-20 * _t(0.15)), 0.9, 0.4, rng)
    elif name == "suspense_hit":   # low brass-like stab with tail (the reveal)
        d = 2.6; t = _t(d)
        x = sum(np.sign(np.sin(2 * np.pi * f * t)) * g for f, g in ((55, 1), (82.4, 0.6), (110, 0.4))) * np.exp(-1.6 * t)
        x = _reverb(_bandpass(x, 40, 1800), 1.8, 0.4, rng)
    elif name == "transition_sweep":
        d = 1.2; x = _moving_band_noise(d, 200, 8000, rng, 0.4) * np.sin(np.pi * np.linspace(0, 1, int(d * SR))) ** 2 + \
            0.3 * _sweep(200, 2000, d, 1.5) * np.sin(np.pi * np.linspace(0, 1, int(d * SR)))
    # 2.1 (owner: "اصوات… ساوند افيكت اكثر")
    elif name == "boom_deep":   # trailer boom: very low sine drop with a long tail
        d = 3.0
        x = _reverb(_sweep(70, 26, d, 0.4) * np.exp(-1.4 * _t(d)) + 0.3 * _bandpass(_noise(d, rng), 30, 300) * np.exp(-6 * _t(d)), 2.0, 0.3, rng)
    elif name == "braam":   # the big brass blast of trailers
        d = 2.6
        t = _t(d)
        x = sum(np.sign(np.sin(2 * np.pi * f * t)) * 0.25 for f in (55, 55.6, 82.4, 110.3)) * _env(int(d * SR), 0.05, 1.8)
        x = _reverb(_bandpass(x, 40, 2200), 1.8, 0.35, rng)
    elif name == "reverse_cymbal":
        d = 2.2
        x = (_bandpass(_noise(d, rng), 3000, 12000) * np.exp(-2.2 * _t(d)))[::-1]
    elif name == "whoosh_reverse":
        x = _moving_band_noise(0.8, 2500, 300, rng)[::-1] * np.linspace(0, 1, int(0.8 * SR)) ** 2
    elif name == "tick_soft":
        d = 0.08
        x = np.sin(2 * np.pi * 2400 * _t(d)) * np.exp(-90 * _t(d))
    elif name == "pop_soft":
        d = 0.18
        x = _sweep(900, 300, d, 0.5) * np.exp(-30 * _t(d))
    elif name == "ui_click":
        d = 0.05
        x = _bandpass(_noise(d, rng), 2000, 8000) * np.exp(-140 * _t(d))
    elif name == "coin":
        d = 0.5
        t = _t(d)
        x = (np.sin(2 * np.pi * 988 * t) * (t < 0.08) + np.sin(2 * np.pi * 1319 * t) * (t >= 0.08)) * np.exp(-5 * t)
    elif name == "level_up":
        d = 0.9
        t = _t(d)
        notes = [523, 659, 784, 1047]
        x = np.concatenate([np.sin(2 * np.pi * f * _t(d / 4)) * np.exp(-6 * _t(d / 4)) for f in notes])[:len(t)]
    elif name == "magic_chime":
        d = 1.6
        t = _t(d)
        x = sum(np.sin(2 * np.pi * f * t) * np.exp(-a * t) * (t > k * 0.07) for k, (f, a) in enumerate(((1568, 3), (2093, 3.5), (2637, 4), (3136, 5))))
        x = _reverb(x, 1.4, 0.4, rng)
    elif name == "camera_flash":
        d = 0.9
        x = 0.6 * _sweep(2500, 7000, d, 0.3) * np.exp(-9 * _t(d)) + 0.4 * _bandpass(_noise(d, rng), 1500, 9000) * np.exp(-30 * _t(d))
    elif name == "paper_slide":
        d = 0.5
        x = _bandpass(_noise(d, rng, "pink"), 800, 5000) * np.sin(np.pi * np.linspace(0, 1, int(d * SR))) ** 2
    elif name == "stamp":
        d = 0.4
        x = _bandpass(_noise(d, rng), 80, 1200) * np.exp(-35 * _t(d)) + 0.5 * np.sin(2 * np.pi * 95 * _t(d)) * np.exp(-25 * _t(d))
    elif name == "pen_scribble":
        d = 0.8
        t = _t(d)
        x = _bandpass(_noise(d, rng), 2500, 7000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 9 * t))) * np.sin(np.pi * t / d)
    elif name == "radar_ping":
        d = 1.5
        x = _reverb(np.sin(2 * np.pi * 1480 * _t(d)) * np.exp(-7 * _t(d)), 1.2, 0.45, rng)
    elif name == "sonar":
        d = 2.0
        x = _reverb(_sweep(880, 840, d) * np.exp(-3 * _t(d)), 1.6, 0.5, rng)
    elif name == "crowd_gasp":
        d = 1.0
        x = _bandpass(_noise(d, rng, "pink"), 300, 3000) * _env(int(d * SR), 0.15, 0.7)
    elif name == "heartbeat_fast":
        d = 1.6
        t = _t(d)
        x = sum(np.sin(2 * np.pi * 55 * t) * np.exp(-30 * np.clip(t - k, 0, None)) * (t >= k) for k in (0, 0.18, 0.75, 0.93))
    elif name == "breath_in":
        d = 1.1
        x = _bandpass(_noise(d, rng, "pink"), 500, 4000) * _env(int(d * SR), 0.8, 0.25)
    elif name == "rumble":
        d = 3.0
        x = _bandpass(_noise(d, rng, "brown"), 25, 160) * _env(int(d * SR), 0.8, 1.2)
    elif name == "glass_break":
        d = 1.2
        t = _t(d)
        x = _bandpass(_noise(d, rng), 3000, 12000) * np.exp(-8 * t) + 0.4 * sum(np.sin(2 * np.pi * f * t) * np.exp(-12 * t) for f in (2731, 3911, 5207))
    elif name == "power_down":
        d = 1.4
        x = _sweep(440, 40, d, 0.7) * np.exp(-1.5 * _t(d))
    elif name == "swoosh_up":
        x = _moving_band_noise(0.6, 300, 6000, rng) * np.sin(np.pi * np.linspace(0, 1, int(0.6 * SR)))
    elif name == "drop_bass":
        d = 1.8
        x = _sweep(160, 35, d, 0.3) * np.exp(-1.2 * _t(d))
    else:
        raise KeyError(name)
    x = np.asarray(x, dtype=np.float64)
    x[: int(0.002 * SR)] *= np.linspace(0, 1, len(x[: int(0.002 * SR)]))
    tail = min(len(x), int(0.01 * SR)); x[-tail:] *= np.linspace(1, 0, tail)
    return x / (np.abs(x).max() or 1) * 0.9


NAMES = ["whoosh_soft", "whoosh_fast", "whoosh_heavy", "impact", "impact_metal", "riser_long", "downlifter", "shutter",
         "flash_pop", "typewriter", "keyboard", "cash", "heartbeat", "clock_tick", "notification", "error_buzz",
         "glitch_digital", "static_tv", "tape_stop", "record_scratch", "swipe_ui", "bubble_pop", "bell", "gong",
         "drum_hit", "laser", "sparkle", "page_flip", "thunder", "wind", "phone_vibrate", "door_slam", "suspense_hit",
         "transition_sweep", "boom_deep", "braam", "reverse_cymbal", "whoosh_reverse", "tick_soft", "pop_soft", "ui_click", "coin",
         "level_up", "magic_chime", "camera_flash", "paper_slide", "stamp", "pen_scribble", "radar_ping", "sonar", "crowd_gasp",
         "heartbeat_fast", "breath_in", "rumble", "glass_break", "power_down", "swoosh_up", "drop_bass"]


def write(name: str, out: Path) -> Path:
    import wave
    x = (make(name) * 32767).astype(np.int16)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.tobytes())
    return out
