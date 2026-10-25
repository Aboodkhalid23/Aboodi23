"""Pictures of fingerprints, drawn with OpenCV (no plotting dependency): one film, or ours with the reference warped
onto our clock by the tension DTW, so "where are we early, late, flat" is one look."""
from __future__ import annotations

import cv2
import numpy as np

from .fingerprint import times

W, LANE, PAD, AXIS = 1600, 120, 46, 26
REF, OURS, GRID, INK, BG = (40, 140, 245), (230, 190, 40), (70, 70, 70), (225, 225, 225), (24, 24, 24)


def _lane(img, y0: int, label: str):
    cv2.rectangle(img, (PAD, y0), (W - 12, y0 + LANE), GRID, 1)
    cv2.putText(img, label, (PAD + 6, y0 + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, INK, 1, cv2.LINE_AA)


def _poly(img, y0: int, t: np.ndarray, v: np.ndarray, t0: float, t1: float, color, vmax: float | None = None):
    if len(t) < 2:
        return
    vmax = vmax or (float(np.percentile(v, 99)) or 1.0)
    x = PAD + (t - t0) / max(1e-9, t1 - t0) * (W - 12 - PAD)
    y = y0 + LANE - 4 - np.clip(v / vmax, 0, 1) * (LANE - 24)
    cv2.polylines(img, [np.stack([x, y], 1).astype(np.int32)], False, color, 2, cv2.LINE_AA)


def _ticks(img, y0: int, ts, t0: float, t1: float, color, h: int):
    for s in ts:
        if t0 <= s <= t1:
            x = int(PAD + (s - t0) / max(1e-9, t1 - t0) * (W - 12 - PAD))
            cv2.line(img, (x, y0 + LANE - h), (x, y0 + LANE), color, 1)


def _axis(img, y: int, t0: float, t1: float):
    step = 1 if t1 - t0 <= 12 else 5 if t1 - t0 <= 90 else 15
    for s in np.arange(np.ceil(t0 / step) * step, t1 + 1e-9, step):
        x = int(PAD + (s - t0) / max(1e-9, t1 - t0) * (W - 12 - PAD))
        cv2.putText(img, f"{s:.0f}s", (x - 10, y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, INK, 1, cv2.LINE_AA)


def _speed(fp: dict) -> np.ndarray:
    c = fp["series"]["camera"]
    return np.sqrt(sum(np.asarray(c[k]) ** 2 for k in ("dx", "dy", "dz", "dr"))) * fp["fps"]


def single(fp: dict, out: str):
    t, t0, t1 = times(fp), fp["start"], fp["end"]
    img = np.full((PAD + 4 * (LANE + 8) + AXIS, W, 3), BG, np.uint8)
    lanes = [("tension (peaks marked)", np.asarray(fp["series"]["tension"]), 1.0), ("camera speed", _speed(fp), None),
             ("local motion", np.asarray(fp["series"]["local"]), None), ("frame difference", np.asarray(fp["series"]["diff"]), None)]
    for k, (name, v, vmax) in enumerate(lanes):
        y0 = PAD + k * (LANE + 8)
        _lane(img, y0, name)
        _ticks(img, y0, fp["beats"], t0, t1, GRID, 10)
        _ticks(img, y0, fp["cuts"], t0, t1, (120, 120, 200), LANE)
        _poly(img, y0, t, v, t0, t1, REF, vmax)
    for p in fp["peaks"]:
        x = int(PAD + (p["t"] - t0) / max(1e-9, t1 - t0) * (W - 12 - PAD))
        cv2.circle(img, (x, PAD + LANE - 4 - int(p["height"] * (LANE - 24))), 6, (60, 60, 255), 2)
    cv2.putText(img, f"{fp['video']}  {t1 - t0:.1f}s  {len(fp['cuts'])} cuts  {len(fp['beats'])} beats  (red ticks: cuts, grey: beats)",
                (PAD, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, INK, 1, cv2.LINE_AA)
    _axis(img, PAD + 4 * (LANE + 8) - 6, t0, t1)
    cv2.imwrite(out, img)


def overlay(ref: dict, ours: dict, mapping: list[tuple[float, float]], out: str):
    """Reference curves warped onto our timeline through the DTW mapping (ref time → our time)."""
    t, t0, t1 = times(ours), ours["start"], ours["end"]
    tr = times(ref)
    img = np.full((PAD + 2 * (LANE + 8) + AXIS, W, 3), BG, np.uint8)
    m = np.asarray(sorted({(o, r) for r, o in mapping}))   # our time → reference time
    warp = (lambda tt: np.interp(tt, m[:, 0], m[:, 1])) if len(m) > 1 else (lambda tt: tt)
    for k, (name, rv, ov, vmax) in enumerate([("tension", np.asarray(ref["series"]["tension"]), np.asarray(ours["series"]["tension"]), 1.0),
                                              ("camera speed", _speed(ref), _speed(ours), None)]):
        y0 = PAD + k * (LANE + 8)
        _lane(img, y0, name)
        _ticks(img, y0, ours["cuts"], t0, t1, (120, 120, 200), LANE)
        vmax = vmax or float(max(np.percentile(rv, 99), np.percentile(ov, 99), 1e-6))
        _poly(img, y0, t, np.interp(warp(t), tr, rv), t0, t1, REF, vmax)
        _poly(img, y0, t, ov, t0, t1, OURS, vmax)
    cv2.putText(img, "orange: reference (time-warped onto ours)   cyan: ours   red ticks: our cuts", (PAD, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, INK, 1, cv2.LINE_AA)
    _axis(img, PAD + 2 * (LANE + 8) - 6, t0, t1)
    cv2.imwrite(out, img)
