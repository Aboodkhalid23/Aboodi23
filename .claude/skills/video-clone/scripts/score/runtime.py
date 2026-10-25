"""Evaluate a resolved score — the Python twin of assets/score/score.js.

Both must give the same numbers (tests/test_score.py runs the JS one under Node and compares): the JS one draws the film,
this one predicts what the film's camera will measure as without rendering a frame (predict.py).
"""
from __future__ import annotations

import math

import numpy as np

from . import eases


def _hash(i: float) -> float:
    """Same stable noise as kit.js: fract(sin(i · 127.1 + 311.7) · 43758.5453)."""
    x = math.sin(i * 127.1 + 311.7) * 43758.5453
    return x - math.floor(x)


def channel(segs: list[dict], base: float, t: float) -> float:
    """The value of one channel at t: base before the first move, then each move from its v0 to its v1."""
    cur = None
    for s in segs:
        if s["t0"] <= t:
            cur = s
        else:
            break
    if cur is None:
        return base
    e, span = cur["ease"], cur["t1"] - cur["t0"]
    if e["kind"] == "spring":
        p = float(eases.progress(e, 0, t - cur["t0"]))
    else:
        p = 1.0 if span <= 0 else float(eases.progress(e, (t - cur["t0"]) / span))
    return cur["v0"] + (cur["v1"] - cur["v0"]) * p


def channel_array(segs: list[dict], base: float, t: np.ndarray) -> np.ndarray:
    """channel() over many times at once (same numbers; tests check it against the scalar twin of score.js)."""
    t = np.asarray(t, float)
    out = np.full(t.shape, float(base))
    for k, s in enumerate(segs):
        nxt = segs[k + 1]["t0"] if k + 1 < len(segs) else np.inf
        m = (t >= s["t0"]) & (t < nxt)
        if not m.any():
            continue
        e, span = s["ease"], s["t1"] - s["t0"]
        if e["kind"] == "spring":
            p = eases.progress(e, 0, t[m] - s["t0"])
        else:
            p = np.ones(int(m.sum())) if span <= 0 else eases.progress(e, (t[m] - s["t0"]) / span)
        out[m] = s["v0"] + (s["v1"] - s["v0"]) * p
    return out


def _hash_array(i: np.ndarray) -> np.ndarray:
    x = np.sin(i * 127.1 + 311.7) * 43758.5453
    return x - np.floor(x)


def shake(sh: dict, t: float) -> tuple[float, float]:
    if t < sh["t0"]:
        return 0.0, 0.0
    f = math.floor(t * sh["rate"] + 1e-6)
    k = sh["amp"] * math.exp(-sh["decay"] * (t - sh["t0"]))
    return (_hash(f * 1.7 + sh["seed"]) - 0.5) * 2 * k, (_hash(f * 2.3 + 9 + sh["seed"]) - 0.5) * 2 * k


class Score:
    def __init__(self, resolved: dict):
        self.r = resolved
        self.shots = {s["id"]: s for s in resolved["shots"]}

    def shot_at(self, t: float) -> dict:
        cur = self.r["shots"][0]
        for s in self.r["shots"]:
            if s["start"] <= t:
                cur = s
        return cur

    def cam(self, sid: str, t: float) -> dict[str, float]:
        s = self.shots[sid]
        c = s["camera"]
        v = {ch: channel(c["channels"].get(ch, []), c["base"][ch], t) for ch in ("x", "y", "zoom", "rot")}
        d = c.get("drift")
        if d:
            span = d["t1"] - d["t0"]
            p = float(eases.progress(d["ease"], (t - d["t0"]) / span if span > 0 else 1.0))
            for ch, by in d["by"].items():
                v[ch] = v[ch] * by ** p if ch == "zoom" else v[ch] + by * p
        for sh in c["shakes"]:
            dx, dy = shake(sh, t)
            v["x"] += dx
            v["y"] += dy
        return v

    def track(self, sid: str, name: str, t: float) -> float:
        tr = self.shots[sid]["tracks"][name]
        return channel(tr["segs"], tr["base"], t)

    def held(self, sid: str, t: float) -> float:
        """t snapped to the shot's cadence (on twos: each drawing held for two frames)."""
        s, fps = self.shots[sid], self.r["fps"]
        n = s["cadence"]
        if n <= 1:
            return t
        f = max(0, math.floor((t - s["start"]) * fps + 1e-6))   # ≥ 0: Python and JS disagree on % of negatives
        return s["start"] + (f - f % n) / fps

    def cam_array(self, sid: str, t: np.ndarray) -> dict[str, np.ndarray]:
        """cam() at many times at once."""
        c = self.shots[sid]["camera"]
        v = {ch: channel_array(c["channels"].get(ch, []), c["base"][ch], t) for ch in ("x", "y", "zoom", "rot")}
        d = c.get("drift")
        if d:
            span = d["t1"] - d["t0"]
            p = eases.progress(d["ease"], (t - d["t0"]) / span if span > 0 else np.ones_like(t))
            for ch, by in d["by"].items():
                v[ch] = v[ch] * by ** p if ch == "zoom" else v[ch] + by * p
        for sh in c["shakes"]:
            on = t >= sh["t0"]
            f = np.floor(t * sh["rate"] + 1e-6)
            k = np.where(on, sh["amp"] * np.exp(-sh["decay"] * np.maximum(0.0, t - sh["t0"])), 0.0)
            v["x"] = v["x"] + (_hash_array(f * 1.7 + sh["seed"]) - 0.5) * 2 * k
            v["y"] = v["y"] + (_hash_array(f * 2.3 + 9 + sh["seed"]) - 0.5) * 2 * k
        return v

    def camera_series(self, sid: str, fps: float | None = None) -> tuple[np.ndarray, dict[str, np.ndarray]]:
        """The camera at every frame of the shot (times, {x, y, zoom, rot} arrays)."""
        s, fps = self.shots[sid], fps or self.r["fps"]
        t = s["start"] + np.arange(int(round((s["end"] - s["start"]) * fps))) / fps
        return t, self.cam_array(sid, t)
