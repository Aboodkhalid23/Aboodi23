"""Ease specs: what authors write, and the one normalised form both runtimes evaluate.

    "power3.out"                         a GSAP name (the formulas in perception.curves.NAMED)
    "back.out(2.2)"                      GSAP's back with its overshoot parameter
    {"bezier": [x1, y1, x2, y2]}         CSS cubic-bezier
    {"spring": {"omega": 18, "zeta": .4}}  damped spring in seconds; the move has no fixed end (it settles in ≈ 4/(ζω))
    "hold"                               jump at the end of the move (a cut-like snap)

Normalised: {"kind": "named", "name": …} | {"kind": "back", "s": …} | {"kind": "bezier", "p": […]} |
            {"kind": "spring", "omega": …, "zeta": …} | {"kind": "hold"}
"""
from __future__ import annotations

import re

import numpy as np

from perception import curves

ALIASES = {"linear": "none", "ease": "power1.inOut", "easeIn": "power2.in", "easeOut": "power2.out", "easeInOut": "power2.inOut"}


class EaseError(ValueError):
    pass


def normalise(spec) -> dict:
    if spec is None:
        return {"kind": "named", "name": "power2.inOut"}
    if isinstance(spec, str):
        name = ALIASES.get(spec, spec)
        if name == "hold":
            return {"kind": "hold"}
        m = re.fullmatch(r"back\.(in|out|inOut)\(([\d.]+)\)", name)
        if m:
            return {"kind": "back", "dir": m.group(1), "s": float(m.group(2))}
        if name not in curves.NAMED:
            raise EaseError(f"unknown ease {spec!r}; use a GSAP name ({', '.join(sorted(curves.NAMED))}), back.out(s), "
                            f"{{'bezier': [x1, y1, x2, y2]}} or {{'spring': {{'omega', 'zeta'}}}}")
        return {"kind": "named", "name": name}
    if isinstance(spec, dict) and "bezier" in spec:
        p = [float(v) for v in spec["bezier"]]
        if len(p) != 4 or not (0 <= p[0] <= 1 and 0 <= p[2] <= 1):
            raise EaseError(f"bezier needs [x1, y1, x2, y2] with x1, x2 in 0..1, got {spec['bezier']}")
        return {"kind": "bezier", "p": p}
    if isinstance(spec, dict) and "spring" in spec:
        s = spec["spring"]
        omega, zeta = float(s.get("omega", 12)), float(s.get("zeta", 0.5))
        if omega <= 0 or not 0 < zeta < 1:
            raise EaseError(f"spring needs omega > 0 and 0 < zeta < 1, got {s}")
        return {"kind": "spring", "omega": omega, "zeta": zeta}
    if isinstance(spec, dict) and spec.get("kind"):
        return spec   # already normalised
    raise EaseError(f"cannot read ease {spec!r}")


def _back(dir_: str, s: float, u: np.ndarray) -> np.ndarray:
    if dir_ == "in":
        return (s + 1) * u ** 3 - s * u ** 2
    if dir_ == "out":
        return 1 + (s + 1) * (u - 1) ** 3 + s * (u - 1) ** 2
    s2 = s * 1.525   # GSAP's inOut back
    return np.where(u < 0.5, (2 * u) ** 2 * ((s2 + 1) * 2 * u - s2) / 2, ((2 * u - 2) ** 2 * ((s2 + 1) * (2 * u - 2) + s2) + 2) / 2)


def progress(e: dict, u: np.ndarray | float, elapsed: np.ndarray | float | None = None) -> np.ndarray:
    """0→1 progress of a move: u = normalised time (clamped) for timed eases, elapsed seconds for springs."""
    u = np.clip(np.asarray(u, float), 0, 1)
    k = e["kind"]
    if k == "named":
        return np.asarray(curves.NAMED[e["name"]](u), float)
    if k == "back":
        return _back(e["dir"], e["s"], u)
    if k == "bezier":
        return curves.bezier(u, *e["p"])
    if k == "hold":
        return (u >= 1).astype(float)
    if k == "spring":
        return curves.spring(np.asarray(elapsed, float), e["omega"], e["zeta"])
    raise EaseError(f"unknown ease kind {k!r}")


def settle_time(e: dict) -> float | None:
    """How long a spring takes to settle (≈ 2 % band); None for timed eases."""
    return 4.0 / (e["zeta"] * e["omega"]) if e["kind"] == "spring" else None
