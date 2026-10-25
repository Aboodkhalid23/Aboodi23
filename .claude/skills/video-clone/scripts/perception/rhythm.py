"""Where cuts land against the beat.

Each cut gets a signed offset to the nearest beat (in frames: one frame early reads differently from one frame late) and
a phase within its beat interval (0 = on the beat, 0.5 = on the "and"). The summary uses circular statistics on the
phase: the mean direction says *where* in the beat this editor cuts, the resultant length R (0–1) says how consistently.
"""
from __future__ import annotations

import numpy as np

ON_BEAT_FRAMES = 1.0


def cut_phase(cuts: list[float], beats: list[float], fps: float) -> dict:
    b = np.asarray(beats, float)
    if len(b) < 2 or not cuts:
        return {"cuts": len(cuts), "beats": len(b)}
    offsets, phases = [], []
    for c in cuts:
        nearest = b[np.argmin(np.abs(b - c))]
        offsets.append((c - nearest) * fps)
        k = int(np.clip(np.searchsorted(b, c, side="right") - 1, 0, len(b) - 2))
        phases.append(((c - b[k]) / (b[k + 1] - b[k])) % 1.0)
    off, ph = np.asarray(offsets), np.asarray(phases)
    z = np.exp(2j * np.pi * ph).mean()
    span = (b[-1] - b[0]) or 1.0
    return {
        "cuts": len(cuts), "beats": len(b),
        "on_beat_ratio": round(float((np.abs(off) <= ON_BEAT_FRAMES).mean()), 3),
        "mean_abs_offset_frames": round(float(np.abs(off).mean()), 2),
        "mean_offset_frames": round(float(off.mean()), 2),   # < 0: cuts tend to come early, before the beat
        "phase_mean": round(float(np.angle(z) / (2 * np.pi)) % 1.0, 3),
        "phase_R": round(float(abs(z)), 3),
        "cuts_per_beat": round(len(cuts) / (span / float(np.median(np.diff(b)))), 3),
        "offsets_frames": [round(float(x), 1) for x in off],
    }
