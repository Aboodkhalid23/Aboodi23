"""Colour: per-frame CIELAB means (the colour arc of the film) and per-shot Lab histograms.

Histograms are compared with the 1-D Wasserstein (earth mover's) distance per channel: unlike bin-by-bin distances it
knows that a slightly warmer orange is close to orange, so a grade that drifted a little scores a little worse.
"""
from __future__ import annotations

import cv2
import numpy as np

BINS = 32


def lab(bgr: np.ndarray) -> np.ndarray:
    """float Lab, L in 0–100, a and b in −128…127 (OpenCV's 8-bit Lab rescaled)."""
    x = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    x[..., 0] *= 100 / 255
    x[..., 1:] -= 128
    return x


RANGES = ((0.0, 100.0), (-128.0, 128.0), (-128.0, 128.0))


def hist(lab_px: np.ndarray) -> np.ndarray:
    """(3, BINS) marginal histograms, each summing to 1."""
    px = lab_px.reshape(-1, 3)
    return np.stack([np.histogram(px[:, c], BINS, RANGES[c])[0] for c in range(3)]).astype(float)


def normalise(h: np.ndarray) -> np.ndarray:
    s = h.sum(axis=1, keepdims=True)
    return np.divide(h, s, out=np.zeros_like(h), where=s > 0)


def wasserstein(h1: np.ndarray, h2: np.ndarray) -> list[float]:
    """W1 per channel, in that channel's units (L: lightness points, a/b: colour points)."""
    out = []
    for c in range(3):
        lo, hi = RANGES[c]
        out.append(float(np.abs(np.cumsum(h1[c]) - np.cumsum(h2[c])).sum() * (hi - lo) / BINS))
    return out


def mean(h: np.ndarray, c: int) -> float:
    """Mean value of channel c of a normalised histogram (bin centres weighted by the histogram)."""
    lo, hi = RANGES[c]
    centres = lo + (np.arange(BINS) + 0.5) * (hi - lo) / BINS
    return float(np.sum(h[c] * centres))
