"""Synthetic films with a known camera: a textured plate filmed by a virtual camera whose position, zoom and roll are
set per frame. What perception measures can then be checked against what was rendered."""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


def plate(seed: int, w: int = 1800, h: int = 1100) -> np.ndarray:
    """Texture at several scales plus coloured discs: corners everywhere, distinct colours per plate (cuts are visible)."""
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.float32)
    for s in (3, 9, 27):
        n = cv2.resize(rng.random((h // s + 1, w // s + 1, 3)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        img += n / 3
    tint = rng.random(3).astype(np.float32)
    img = 0.55 * img + 0.45 * tint
    for _ in range(160):
        c = tuple(int(v) for v in rng.integers(0, 255, 3))
        cv2.circle(img, (int(rng.integers(0, w)), int(rng.integers(0, h))), int(rng.integers(6, 40)), [v / 255 for v in c], -1, cv2.LINE_AA)
    return np.clip(img * 255, 0, 255).astype(np.uint8)


@dataclass
class Cam:
    x: float = 0.0       # camera centre offset from the plate centre, in output frame widths
    y: float = 0.0
    scale: float = 1.0   # > 1 = pushed in
    roll: float = 0.0    # radians, + = clockwise camera roll (image turns counter-clockwise)
    plate: int = 0


def render(path: str, cams: list[Cam], fps: int = 24, size: tuple[int, int] = (640, 360)) -> None:
    W, H = size
    plates: dict[int, np.ndarray] = {}
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    for c in cams:
        P = plates.setdefault(c.plate, plate(c.plate))
        ph, pw = P.shape[:2]
        cx, cy = pw / 2 + c.x * W, ph / 2 + c.y * W
        # frame = scale · R(−roll) · (plate − cam) + frame centre   (camera rolls clockwise → image turns counter-clockwise)
        a, b = c.scale * np.cos(-c.roll), c.scale * np.sin(-c.roll)
        M = np.array([[a, -b, W / 2 - (a * cx - b * cy)], [b, a, H / 2 - (b * cx + a * cy)]], np.float32)
        vw.write(cv2.warpAffine(P, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))
    vw.release()


def move(n: int, start: int, length: int, ease, a: float, b: float) -> list[float]:
    """Per-frame value going from a to b over [start, start + length) with `ease`, held before and after."""
    out = []
    for f in range(n):
        u = min(1.0, max(0.0, (f - start) / length))
        out.append(a + (b - a) * float(ease(np.asarray(u))))
    return out
