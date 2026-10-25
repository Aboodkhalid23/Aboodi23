"""The search space: which numbers of a score the optimizer may change, their bounds, and how a point in the unit box
becomes an edited score again.

Per camera move of a tuned shot:
    at      start, within ±max_shift of where the author put it (and inside the shot)
    dur     duration × 2^v, v ∈ [−1, 1]
    ease    the curve as cubic-bezier (x1, y1, x2, y2), started from the author's ease converted to a bezier;
            springs tune ω (× 2^v) and ζ instead; "hold" (a jump) has no curve to tune
    by.*    only with tune_amounts: ±30 % (zoom: of the push itself). Amounts are the director's framing intent, so
            they are locked by default
Per shake: amplitude (0–3× and able to reach 0, which removes it) and decay (× 2^v).
Optional *proposed* shakes at plan peaks (amplitude starts at 0): structure the optimizer may add, never forced.

Written back in the author's terms where nothing changed: an unchanged start keeps "B12", an unchanged ease keeps
"power3.out"; every changed move records what it was in "tuned".
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

from perception import curves
from score import eases

MIN_SHAKE_PX = 4.0   # stage pixels at 1080p: below this a shake is not visible
BEZ_LO, BEZ_HI = (0.0, -0.15, 0.0, -0.15), (1.0, 1.25, 1.0, 1.25)   # eases a viewer reads as eases (modest overshoot at most);
# wider, the search found curves no fitted model describes — great on the exact trajectory, unrecognisable once measured


def to_bezier(e: dict) -> list[float]:
    """The cubic-bezier closest to a normalised ease (least squares on 60 samples)."""
    if e["kind"] == "bezier":
        return list(e["p"])
    u = np.linspace(0, 1, 60)
    v = eases.progress(e, u)
    r = min((least_squares(lambda p: curves.bezier(u, *p) - v, x0, bounds=(BEZ_LO, BEZ_HI))
             for x0 in [(0.25, 0.1, 0.25, 1.0), (0.42, 0.0, 0.58, 1.0), (0.16, 1.0, 0.3, 1.0)]), key=lambda r: r.cost)
    return [float(x) for x in r.x]


@dataclass
class Param:
    shot: str
    kind: str          # at | dur | bez0..3 | omega | zeta | by:<ch> | amp | decay
    index: int         # move index, or shake index
    lo: float
    hi: float
    x0: float          # in natural units
    log2: bool = False

    def to_unit(self, x: float) -> float:
        return (x - self.lo) / (self.hi - self.lo)

    def from_unit(self, u: float) -> float:
        return self.lo + float(np.clip(u, 0, 1)) * (self.hi - self.lo)


class Space:
    def __init__(self, authored: dict, resolved: dict, shots: list[str], *, tune_amounts: bool = False, max_shift: float = 0.25,
                 propose_shakes: dict[str, list[float]] | None = None):
        self.authored, self.resolved = authored, resolved
        self.res = {s["id"]: s for s in resolved["shots"]}
        self.src = {str(s["id"]): s for s in authored["shots"]}
        self.params: list[Param] = []
        self.bez0: dict[tuple[str, int], list[float]] = {}   # each move's starting curve as a bezier (fitted once)
        self.proposed: dict[str, list[float]] = {k: v for k, v in (propose_shakes or {}).items() if k in shots}
        for sid in shots:
            self._shot_params(sid, tune_amounts, max_shift)

    # ---------- building the space ----------
    def _shot_params(self, sid: str, tune_amounts: bool, max_shift: float):
        src, res = self.src[sid], self.res[sid]
        s, e = res["start"], res["end"]
        P = self.params
        for i, mv in enumerate((src.get("camera") or {}).get("moves") or []):
            tt = res["camera"]["move_times"][i] if i < len(res["camera"]["move_times"]) else None
            if not tt:
                continue
            t0, t1 = tt
            ease = eases.normalise(mv.get("ease"))
            shift = min(max_shift, 0.25 * (e - s))
            lo, hi = max(s, t0 - shift), min(e, t0 + shift)
            P.append(Param(sid, "at", i, lo, max(hi, lo + 1e-3), t0))
            if ease["kind"] != "spring":
                P.append(Param(sid, "dur", i, -1.0, 1.0, 0.0, log2=True))
            if ease["kind"] == "spring":
                P.append(Param(sid, "omega", i, -1.0, 1.0, 0.0, log2=True))
                P.append(Param(sid, "zeta", i, 0.1, 0.95, min(0.95, max(0.1, ease["zeta"]))))
            elif ease["kind"] != "hold":
                self.bez0[(sid, i)] = to_bezier(ease)
                for k, (v, lo, hi) in enumerate(zip(self.bez0[(sid, i)], BEZ_LO, BEZ_HI)):
                    P.append(Param(sid, f"bez{k}", i, lo, hi, float(np.clip(v, lo, hi))))
            if tune_amounts and isinstance(mv.get("by"), dict):
                for ch in mv["by"]:
                    P.append(Param(sid, f"by:{ch}", i, -0.3, 0.3, 0.0))
        for j, sh in enumerate((src.get("camera") or {}).get("shakes") or []):
            P.append(Param(sid, "amp", j, 0.0, 3.0 * float(sh.get("amp", 10)), float(sh.get("amp", 10))))
            P.append(Param(sid, "decay", j, -1.0, 1.0, 0.0, log2=True))
        n0 = len((src.get("camera") or {}).get("shakes") or [])
        for k, _ in enumerate(self.proposed.get(sid, [])):
            P.append(Param(sid, "amp", n0 + k, 0.0, 40.0, 0.0))
            P.append(Param(sid, "decay", n0 + k, -1.0, 1.0, 0.0, log2=True))

    @property
    def u0(self) -> np.ndarray:
        return np.array([p.to_unit(p.x0) for p in self.params])

    # ---------- applying a point ----------
    def apply(self, u: np.ndarray) -> dict:
        out = copy.deepcopy(self.authored)
        shots = {str(s["id"]): s for s in out["shots"]}
        clock_fps = float(self.resolved["fps"])
        beat, offset = 60.0 / float(self.resolved["bpm"]), float(self.resolved["offset"])
        by_move: dict[tuple[str, int], dict[str, float]] = {}
        by_shake: dict[tuple[str, int], dict[str, float]] = {}
        for p, x in zip(self.params, u):
            v = p.from_unit(x)
            (by_shake if p.kind in ("amp", "decay") else by_move).setdefault((p.shot, p.index), {})[p.kind] = v
        for (sid, i), vals in by_move.items():
            shot, res = shots[sid], self.res[sid]
            mv = shot["camera"]["moves"][i]
            old = {k: copy.deepcopy(mv[k]) for k in ("at", "dur", "until", "ease", "by") if k in mv}
            t0, t1 = res["camera"]["move_times"][i]
            changed = False
            if "at" in vals and abs(vals["at"] - t0) > 0.25 / clock_fps:
                k = round((vals["at"] - offset) / beat)
                tb = offset + k * beat
                mv["at"] = f"B{k}" if abs(tb - vals["at"]) <= 0.5 / clock_fps else f"S+{vals['at'] - res['start']:.4f}s"
                changed = True
            if "dur" in vals and abs(vals["dur"]) > 0.01:
                mv.pop("until", None)
                mv["dur"] = f"{(t1 - t0) * 2 ** vals['dur']:.4f}s"
                changed = True
            bez = [vals.get(f"bez{k}") for k in range(4)]
            if all(b is not None for b in bez):
                p0 = self.bez0[(sid, i)]
                if max(abs(a - b) for a, b in zip(bez, p0)) > 0.02:
                    mv["ease"] = {"bezier": [round(b, 3) for b in bez]}
                    changed = True
            if "omega" in vals or "zeta" in vals:
                e = eases.normalise(old.get("ease"))
                w, z = e["omega"] * 2 ** vals.get("omega", 0.0), vals.get("zeta", e["zeta"])
                if abs(w - e["omega"]) > 0.05 * e["omega"] or abs(z - e["zeta"]) > 0.02:
                    mv["ease"] = {"spring": {"omega": round(w, 2), "zeta": round(z, 3)}}
                    changed = True
            for key, v in vals.items():
                if key.startswith("by:") and abs(v) > 0.01:
                    ch = key[3:]
                    a = float(mv["by"][ch])
                    mv["by"][ch] = round(a ** (1 + v), 4) if ch == "zoom" and a > 0 else round(a * (1 + v), 2)
                    changed = True
            if changed:
                mv["tuned"] = {"from": old}
        for (sid, j), vals in by_shake.items():
            shakes = shots[sid]["camera"].setdefault("shakes", [])
            n0 = len((self.src[sid].get("camera") or {}).get("shakes") or [])
            if j >= n0:   # a proposed shake at a plan peak
                hit = self.proposed[sid][j - n0]
                shakes.append({"at": f"{hit:.4f}", "amp": round(vals.get("amp", 0.0), 2), "decay": round(10 * 2 ** vals.get("decay", 0.0), 2),
                               "tuned": {"proposed": "shake at a plan peak"}})
            else:
                sh = shakes[j]
                old = {k: sh.get(k) for k in ("amp", "decay")}
                sh["amp"] = round(vals.get("amp", sh.get("amp", 10)), 2)
                sh["decay"] = round(float(sh.get("decay", 10)) * 2 ** vals.get("decay", 0.0), 2)
                if abs(sh["amp"] - (old["amp"] or 0)) > 0.5 or abs(sh["decay"] - (old["decay"] or 10)) > 0.2:
                    sh["tuned"] = {"from": old}
        for sid in shots:   # a shake too small to see is no shake (and must not count for anything)
            cam = shots[sid].get("camera") or {}
            if cam.get("shakes"):
                cam["shakes"] = [sh for sh in cam["shakes"] if float(sh.get("amp", 0)) >= MIN_SHAKE_PX]
        return out

    def changes(self, u: np.ndarray) -> list[dict]:
        """What a point changes in this space's shots, move by move, in words a director reads."""
        tuned = self.apply(u)
        mine = {p.shot for p in self.params}
        out = []
        for s in tuned["shots"]:
            if str(s["id"]) not in mine:
                continue
            for i, mv in enumerate((s.get("camera") or {}).get("moves") or []):
                if "tuned" in mv:
                    out.append({"shot": s["id"], "move": i, "from": mv["tuned"]["from"], "to": {k: mv[k] for k in ("at", "dur", "until", "ease", "by") if k in mv}})
            for j, sh in enumerate((s.get("camera") or {}).get("shakes") or []):
                if "tuned" in sh:
                    out.append({"shot": s["id"], "shake": j, "from": sh["tuned"].get("from") or sh["tuned"].get("proposed"),
                                "to": {"at": sh["at"], "amp": sh["amp"], "decay": sh["decay"]}})
        return out

