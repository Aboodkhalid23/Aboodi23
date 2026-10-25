"""Tension: one curve per film that rises as it builds, dips when it holds its breath, and spikes at the hit.

    tension(t) = smooth( Σ w_k · robust01(feature_k(t)) ) / Σ w_k        (features that are missing drop out)

Features, all on the frame clock: loudness (RMS dB) and spectral flux from the sound; camera speed, local (in-frame)
motion and frame difference from the picture; cut density; flashes (luminance jumping above its running median).
robust01 maps the 5th–95th percentile of each feature in *this* film to 0–1, so a quiet film and a loud one are compared
on shape, not on mastering level — but never stretches a range smaller than what a viewer can notice (JND).

A peak is then described the way an editor would: how long and steep the build is, whether there is a held breath
(a dip right before the hit) and how deep, how many frames the hit takes to land, how long it holds and decays.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
from scipy.signal import find_peaks

WEIGHTS = {"loudness": 0.28, "flux": 0.20, "camera": 0.14, "local": 0.10, "diff": 0.10, "cuts": 0.10, "flash": 0.08}
# Just-noticeable ranges: a feature that varies less than this over the whole film is not stretched to fill 0–1.
# Without a floor, robust01 makes any wobble in a still film "the strongest motion": an optimizer found that a 1-pixel
# shake at the hit moved the predicted climax onto its target — invisible to a viewer, decisive for the number.
JND = {"loudness": 6.0,   # dB
       "flux": 1.0,       # onset strength units
       "camera": 0.08,    # frame widths per second (≈ 150 px/s at 1080p)
       "local": 0.03,     # frame widths per second of motion inside the frame
       "diff": 0.02,      # mean absolute frame difference (0–1)
       "cuts": 0.5,       # cuts per second
       "flash": 0.05}     # luminance jump above the running median (0–1)
# Motion below these is not seen at all (dead zone, subtracted before normalising): a ±1 px jitter is 0.025 frame
# widths per second, a slow but visible drift ≈ 0.05. Loudness and flux have no meaningful zero, so no dead zone.
DEADZONE = {"camera": 0.04, "local": 0.015, "diff": 0.005, "flash": 0.02}
SMOOTH_S = 0.15


def robust01(x: np.ndarray, jnd: float = 0.0) -> np.ndarray:
    """5th–95th percentile → 0–1, but never stretching a range smaller than `jnd` (what a viewer can notice)."""
    lo, hi = np.percentile(x, 5), np.percentile(x, 95)
    span = max(hi - lo, jnd)
    return np.clip((x - lo) / span, 0, 1) if span > 1e-9 else np.zeros_like(x, dtype=float)


def audio_features(wav: str, n: int, fps: float, t0: float = 0.0) -> dict[str, np.ndarray]:
    """Loudness and spectral flux resampled to the n frames at t0 + i / fps."""
    import librosa
    y, sr = librosa.load(wav, sr=22050, mono=True)
    hop = 512
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop)[0]
    flux = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    ta = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    tf = librosa.frames_to_time(np.arange(len(flux)), sr=sr, hop_length=hop)
    t = t0 + np.arange(n) / fps
    return {"loudness": np.interp(t, ta, 20 * np.log10(rms + 1e-6)), "flux": np.interp(t, tf, flux)}


def beats(wav: str) -> list[float]:
    import librosa
    y, sr = librosa.load(wav, sr=22050, mono=True)
    _, b = librosa.beat.beat_track(y=y, sr=sr, units="time")
    return [round(float(x), 3) for x in b]


def cut_density(cut_frames: list[int], n: int, fps: float) -> np.ndarray:
    imp = np.zeros(n)
    for k in cut_frames:
        if 0 <= k < n:
            imp[k] = 1.0
    return gaussian_filter1d(imp, 0.75 * fps) * fps   # cuts per second, smoothed


def flashes(lum: np.ndarray, fps: float) -> np.ndarray:
    base = median_filter(lum, size=max(3, int(fps)) | 1, mode="nearest")
    return np.clip(lum - base, 0, None)


def curve(features: dict[str, np.ndarray], fps: float) -> np.ndarray:
    # a feature that was measured but never changes contributes 0 — it is not dropped, or the other weights would jump
    # the moment it moves at all; only features that were not measured (no sound track) leave the mix
    used = {k: w for k, w in WEIGHTS.items() if k in features and features[k] is not None and len(features[k])}
    if not used:
        n = len(next(iter(features.values()))) if features else 0
        return np.zeros(n)
    seen = {k: np.maximum(0.0, np.asarray(features[k], float) - DEADZONE[k]) if k in DEADZONE else features[k] for k in used}
    mix = sum(w * robust01(seen[k], JND.get(k, 0.0)) for k, w in used.items()) / sum(used.values())
    return gaussian_filter1d(mix, SMOOTH_S * fps)


def describe_peaks(T: np.ndarray, fps: float, beat_times: list[float] | None = None, n: int = 3, min_gap_s: float = 4.0) -> list[dict]:
    """The n most prominent peaks, each with the shape of its build, breath, hit and release."""
    if len(T) < int(fps):
        return []
    idx, props = find_peaks(T, prominence=0.12, distance=max(1, int(min_gap_s * fps)))
    order = np.argsort(-(props["prominences"] * T[idx]))[:n]
    beats_ = np.asarray(beat_times or [])
    out = []
    for k in sorted(idx[order]):
        f = int(k)
        while f > 0 and T[f - 1] >= 0.97 * T[k]:   # the hit is where the peak starts, not the middle of its plateau
            f -= 1
        a = max(0, f - int(2.0 * fps))
        dip = f - 1 - int(np.argmin(T[a:f][::-1])) if f > a else f   # the last low point before the hit
        pre = T[max(0, dip - int(4 * fps)):dip + 1]
        breath_depth = float(pre.max() - T[dip]) if len(pre) else 0.0
        b_start = dip   # the held breath starts where the curve first fell to near its bottom
        while b_start > 0 and T[b_start - 1] <= T[dip] + 0.2 * breath_depth:
            b_start -= 1
        b0 = max(0, b_start - int(8 * fps))
        build = np.polyfit(np.arange(b0, b_start + 1) / fps, T[b0:b_start + 1], 1)[0] if b_start - b0 >= 4 else 0.0
        top, low = float(T[k]), float(T[dip])
        rise = int(np.argmax(T[dip:f + 1] >= low + 0.9 * (top - low)))   # frames from the bottom of the breath to 90 % of the hit
        after = T[f:]
        hold = int(np.argmax(after < 0.9 * top)) if (after < 0.9 * top).any() else len(after)
        half = top - 0.5 * (top - low)
        decay = int(np.argmax(after < half)) if (after < half).any() else len(after)
        p = {"t": round(f / fps, 3), "height": round(top, 3), "prominence": round(float(props["prominences"][list(idx).index(k)]), 3),
             "build_slope": round(float(build), 4), "breath_s": round((f - b_start) / fps, 3), "breath_depth": round(breath_depth, 3),
             "rise_frames": rise, "hold_s": round(hold / fps, 3), "decay_s": round(decay / fps, 3)}
        if len(beats_):
            nb = beats_[np.argmin(np.abs(beats_ - f / fps))]
            p["beat_offset_frames"] = round(float((f / fps - nb) * fps), 1)
        out.append(p)
    return out
