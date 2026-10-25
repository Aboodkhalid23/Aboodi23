"""style_distance: how far our film is from the reference, per component, per shot, and in words.

Components (each 0–100, higher = closer):

    tension   DTW between the two tension curves (8 Hz): same build-and-release shape, allowing the timing to stretch
    peaks     the reference's climax against ours at the DTW-aligned moment: breath, how fast the hit lands, height, hold
    camera    per mapped shot pair: same kind of move, easing curve RMSE, duration and amount ratios
    rhythm    cut/beat phase: on-beat ratio, where in the beat cuts land, cuts per beat
    look      per mapped shot pair: Wasserstein distance of the Lab histograms
    frames    DTW over frame descriptors (layout of light and colour), a weak signal across media

Scores are exp(−cost / scale) with hand-set scales — a calibration that a learned critic will replace (docs/COMPILER.md,
stage 5). Findings are the point: concrete, numeric, and tied to a shot or a time, so a builder knows what to change.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.spatial.distance import cdist

from . import curves, tension
from . import look as look_
from .fingerprint import times, window

# Two questions, two scores. STYLE: does it look and move like the reference (palette, pace, camera, colour per shot,
# cut rhythm)? STRUCTURE: does it follow the arc of the section it clones (tension, peaks)? Validated by split-half
# retrieval on the references (docs/COMPILER.md): palette and pace pick a window's own reference far above chance,
# rhythm and frames weakly, tension and peaks not at all — they describe *this* stretch's content, so they are only
# meaningful against the mapped window, never as "style".
STYLE = {"camera": 0.30, "palette": 0.20, "pace": 0.20, "look": 0.15, "rhythm": 0.10, "frames": 0.05}
STRUCTURE = {"tension": 0.5, "peaks": 0.5}
OVERALL = {"style": 0.65, "structure": 0.35}
WEIGHTS = {**{k: OVERALL["style"] * w for k, w in STYLE.items()}, **{k: OVERALL["structure"] * w for k, w in STRUCTURE.items()}}
CURVE_HZ = 8.0


# ---------- DTW ----------
def dtw(a: np.ndarray, b: np.ndarray, band: float = 0.2, metric: str = "cityblock") -> tuple[float, list[tuple[int, int]]]:
    """Dynamic time warping with a Sakoe–Chiba band (fraction of the longer series) around the scaled diagonal.

    Each row is solved in vectorised form: with x_j = min(D[i−1, j], D[i−1, j−1]) the recurrence
    d_j = c_j + min(d_{j−1}, x_j) unrolls to d_j = S_j + min_{k ≤ j}(x_k − S_{k−1}), S = cumsum(c),
    i.e. one cumsum and one running minimum per row. Returns (mean cost along the path, path)."""
    a, b = np.asarray(a, float).reshape(len(a), -1), np.asarray(b, float).reshape(len(b), -1)
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return float("inf"), []
    C = cdist(a, b, metric)
    r = max(2, int(band * max(n, m)))
    D = np.full((n, m), np.inf)
    for i in range(n):
        centre = i * (m - 1) / max(1, n - 1)
        lo, hi = max(0, int(centre - r)), min(m - 1, int(centre + r))
        c = C[i, lo:hi + 1]
        S = np.cumsum(c)
        S_prev = np.r_[0.0, S[:-1]]
        if i == 0:
            x = np.full(len(c), np.inf)
            x[0] = 0.0 if lo == 0 else np.inf
        else:
            up = D[i - 1, lo:hi + 1]
            diag = np.r_[D[i - 1, lo - 1] if lo > 0 else np.inf, D[i - 1, lo:hi]]
            x = np.minimum(up, diag)
        D[i, lo:hi + 1] = S + np.minimum.accumulate(x - S_prev)
    if not np.isfinite(D[-1, -1]):
        return float("inf"), []
    path, i, j = [(n - 1, m - 1)], n - 1, m - 1
    while i > 0 or j > 0:
        steps = [(i - 1, j - 1), (i - 1, j), (i, j - 1)]
        i, j = min((s for s in steps if s[0] >= 0 and s[1] >= 0), key=lambda s: D[s])
        path.append((i, j))
    path.reverse()
    return float(sum(C[p] for p in path) / len(path)), path


def resample(fp: dict, values: list[float], hz: float = CURVE_HZ) -> tuple[np.ndarray, np.ndarray]:
    t = times(fp)
    tt = np.arange(t[0], t[-1], 1 / hz) if len(t) > 1 else t
    return tt, np.interp(tt, t, np.asarray(values, float))


def _score(cost: float, scale: float) -> float:
    return round(100 * math.exp(-cost / scale), 1) if math.isfinite(cost) else 0.0


def _finding(component: str, where: str, severity: str, text: str) -> dict:
    return {"component": component, "where": where, "severity": severity, "text": text}


# ---------- components ----------
def tension_component(ref: dict, ours: dict) -> tuple[dict, list[dict], list[tuple[float, float]]]:
    tr, R = resample(ref, ref["series"]["tension"])
    to, O = resample(ours, ours["series"]["tension"])
    cost, path = dtw(R, O, band=0.25)
    mapping = [(float(tr[i]), float(to[j])) for i, j in path]
    findings = []
    if len(R) and len(O):
        # where our film sits clearly below the reference's energy for a stretch (≥ 1 s at the aligned moment)
        gap = np.array([R[i] - O[j] for i, j in path])
        low = gap > 0.25
        k = 0
        while k < len(low):
            if low[k]:
                e = k
                while e + 1 < len(low) and low[e + 1]:
                    e += 1
                if (e - k + 1) / CURVE_HZ >= 1.0:
                    a, b = to[path[k][1]], to[path[e][1]]
                    findings.append(_finding("tension", f"{a:.1f}–{b:.1f}s", "major" if gap[k:e + 1].mean() > 0.4 else "minor",
                                             f"energy is {gap[k:e + 1].mean():.2f} below the reference at the aligned moment "
                                             f"(ref {tr[path[k][0]]:.1f}–{tr[path[e][0]]:.1f}s): more motion, cuts or sound there"))
                k = e + 1
            else:
                k += 1
    return {"score": _score(cost, 0.12), "dtw_cost": round(cost, 4)}, findings, mapping


def _map(mapping: list[tuple[float, float]], t_ref: float) -> float | None:
    if not mapping:
        return None
    k = int(np.argmin([abs(a - t_ref) for a, _ in mapping]))
    return mapping[k][1]


def peaks_component(ref: dict, ours: dict, mapping: list[tuple[float, float]]) -> tuple[dict, list[dict]]:
    rp = sorted(ref["peaks"], key=lambda p: -p["prominence"] * p["height"])
    if not rp:
        return {"score": None, "note": "the reference has no clear peak in this window"}, []
    findings, pairs, costs = [], [], []
    for p in rp[:2]:
        at = _map(mapping, p["t"])
        cand = [q for q in ours["peaks"] if at is not None and abs(q["t"] - at) <= 1.5]
        if not cand:
            findings.append(_finding("peaks", f"{at:.1f}s" if at is not None else "-", "major",
                                     f"the reference peaks at {p['t']:.1f}s (height {p['height']:.2f}); ours has no peak within 1.5 s of the aligned moment"))
            costs.append(1.0)
            continue
        q = min(cand, key=lambda q: abs(q["t"] - at))
        pairs.append({"ref": p, "ours": q})
        where = f"{q['t']:.1f}s"
        c = 0.0
        if p["breath_depth"] >= 0.1 and q["breath_depth"] < 0.5 * p["breath_depth"]:
            c += 0.35
            findings.append(_finding("peaks", where, "major", f"no held breath before the hit: dip {q['breath_depth']:.2f} vs {p['breath_depth']:.2f} in the reference "
                                     f"({p['breath_s']:.2f}s before its hit) — pull energy down right before the hit"))
        if q["rise_frames"] > 1.8 * p["rise_frames"] + 2:
            c += 0.25
            findings.append(_finding("peaks", where, "major", f"the hit lands slowly: {q['rise_frames']} frames to 90 % vs {p['rise_frames']} in the reference — make it land on one frame"))
        if q["prominence"] < 0.6 * p["prominence"]:
            c += 0.25
            findings.append(_finding("peaks", where, "major" if q["prominence"] < 0.4 * p["prominence"] else "minor",
                                     f"the hit stands out less: prominence {q['prominence']:.2f} vs {p['prominence']:.2f}"))
        if p["hold_s"] > 0.3 and q["hold_s"] < 0.5 * p["hold_s"]:
            c += 0.15
            findings.append(_finding("peaks", where, "minor", f"the hit lets go too soon: holds {q['hold_s']:.2f}s vs {p['hold_s']:.2f}s"))
        if "beat_offset_frames" in p and "beat_offset_frames" in q and abs(p["beat_offset_frames"]) <= 1 < abs(q["beat_offset_frames"]):
            c += 0.15
            findings.append(_finding("peaks", where, "major", f"the hit is {q['beat_offset_frames']:+.0f} frames off the beat; the reference's is on it"))
        costs.append(min(1.0, c))
    return {"score": round(100 * (1 - float(np.mean(costs))), 1), "pairs": pairs}, findings


def _pct(z: float) -> str:
    return f"{(math.exp(z) - 1) * 100:+.0f}%"


def _amount(axis: str, v: float) -> str:
    return _pct(v) if axis == "z" else f"{math.degrees(v):+.1f}°" if axis == "r" else f"{v:+.2f} frame widths"


def _does(kinds: list[str]) -> str:
    """'holds still' / 'pushes in and moves left' — move kinds as words."""
    if kinds == ["static"]:
        return "holds still"
    verbs = {"push_in": "pushes in", "pull_out": "pulls out", "move_left": "moves left", "move_right": "moves right", "move_up": "moves up",
             "move_down": "moves down", "roll_cw": "rolls clockwise", "roll_ccw": "rolls counter-clockwise", "shake": "shakes"}
    words = [verbs.get(k, k.replace("_", " ")) for k in kinds]
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def _ease_name(m: dict) -> str:
    return (m.get("ease") or {}).get("named") or "an unfitted curve"


def _membership(move: dict) -> dict[str, float]:
    """How clearly a move goes each way, 0–1: an amount at half the 'still' threshold counts 0, at twice it 1. Kinds are
    thresholds; comparing them as sets made 0.0149 vs 0.0151 of roll a different kind of move (89 → 53 points)."""
    out = {}
    for a, v in move.get("amount", {}).items():
        lim = curves.MIN_AMOUNT.get(a, 0.015)
        w = float(np.clip((abs(v) - 0.5 * lim) / (1.5 * lim), 0, 1))
        if w > 0:
            out[f"{a}{'+' if v > 0 else '-'}"] = w
    if "shake" in move.get("kind", []):
        out["shake"] = 1.0
    return out


def kind_similarity(a: dict, b: dict) -> float:
    """Soft Jaccard of what two camera moves do (1 = the same kinds of move, 0 = nothing in common)."""
    ma, mb = _membership(a), _membership(b)
    keys = set(ma) | set(mb)
    if not keys:
        return 1.0
    return sum(min(ma.get(k, 0), mb.get(k, 0)) for k in keys) / sum(max(ma.get(k, 0), mb.get(k, 0)) for k in keys)


def time_available(rs: dict, os_: dict) -> float:
    """How fast our shot has to move compared with the reference shot (≤ 1). A plan may make a shot shorter than the
    reference's moves; then the moves that fit (curves.moves_that_fit — the transfer's own rule) are expected to be
    that much faster, instead of being "too fast". Penalising that pushed the optimizer to bend eases into fake
    longer moves."""
    rm = rs["move"]
    our_len = float(os_.get("end", 0) or 0) - float(os_.get("start", 0) or 0)
    moves = [{"duration": rm.get("duration"), "visible": rm.get("visible"), "cut_off": rm.get("cut_off"),
              "lead_in": rm.get("lead_in"), "amount": rm.get("move_amount", rm["amount"])}] + list(rm.get("other_moves") or [])
    total = sum(curves.on_screen(m) for m in curves.moves_that_fit(moves, our_len)) if our_len > 0 else 0.0
    if total <= 0 or our_len <= 0:
        return 1.0
    return min(1.0, our_len / total)


def _frac(shot: dict, t: float) -> float:
    a, b = float(shot.get("start", 0) or 0), float(shot.get("end", 0) or 0)
    return float(np.clip((t - a) / (b - a), 0, 1)) if b > a else 0.0


def placement_gap(rs: dict, os_: dict, k: float = 1.0) -> float:
    """Where in the shot the main move happens — at the start, through it, at the end — as the share of the shot at
    which its travel reaches 5 % and 95 %. A push in the first half and the same push in the second half feel different,
    and nothing else in the comparison saw it (an optimizer moved one and a held-out check caught it).

    The expectation follows the transfer's own time mapping, so the two rules never fight: the move starts at the same
    share of the shot, and lasts its reference length × k seconds (k = time_available)."""
    rm, om = rs["move"], os_["move"]
    if "t5" not in rm or "t5" not in om:
        return 0.0
    our_len = float(os_.get("end", 0) or 0) - float(os_.get("start", 0) or 0)
    want5 = _frac(rs, rm["t5"])
    want95 = min(1.0, want5 + (rm["t95"] - rm["t5"]) * k / our_len) if our_len > 0 else _frac(rs, rm["t95"])
    return abs(want5 - _frac(os_, om["t5"])) + abs(want95 - _frac(os_, om["t95"]))


def camera_pair(rs: dict, os_: dict) -> tuple[float, dict, list[dict]]:
    rm, om = rs["move"], os_["move"]
    jac = kind_similarity(rm, om)
    where = f"{os_['id']} ↔ ref #{rs['id']}"
    detail, findings, cost = {"ref": rm["kind"], "ours": om["kind"], "kind_match": round(jac, 2)}, [], (1 - jac) * 1.5
    if jac < 0.6 and set(rm["kind"]) != set(om["kind"]):   # say it only when the kinds a person reads differ
        amount = f" ({_amount(rm['axis'], rm['amount'][rm['axis']])})" if "axis" in rm else ""
        findings.append(_finding("camera", where, "major" if jac < 0.25 else "minor",
                                 f"the reference camera {_does(rm['kind'])}{amount}; ours {_does(om['kind'])}"))
    if "progress" in rm and "progress" in om and rm["axis"] != om["axis"]:
        cost += 1.0   # the main moves are on different axes: their timing and easing are not comparable (the kind finding says it)
    elif "progress" in rm and "progress" in om and (rm.get("snap") or om.get("snap")) and rm.get("snap") != om.get("snap"):
        cost += 1.0
        snapped, eased = (om, rm) if om.get("snap") else (rm, om)
        findings.append(_finding("camera", where, "major", f"{'ours' if snapped is om else 'the reference'} jumps in one frame where "
                                 f"{'the reference' if snapped is om else 'ours'} moves over {eased['duration']:.2f}s ({_ease_name(eased)})"))
    elif "progress" in rm and "progress" in om:
        e = float(np.sqrt(np.mean((np.asarray(rm["progress"]) - np.asarray(om["progress"])) ** 2)))
        ax = rm["axis"]
        dur_r, dur_o = rm.get("span90", rm["duration"]), om.get("span90", om["duration"])   # the 5–95 % travel time
        k = time_available(rs, os_)
        dur = math.log2(max(dur_o, 1e-3) / max(dur_r * k, 1e-3))
        amt = math.log2(max(abs(om["amount"][ax]), 1e-3) / max(abs(rm["amount"][ax]), 1e-3))
        place = placement_gap(rs, os_, k)
        cost += e / 0.15 + abs(dur) / 1.5 + abs(amt) / 1.5 + place / 0.4
        if place > 0.3:
            fr = lambda s_, m_: f"{_frac(s_, m_['t5']):.0%}–{_frac(s_, m_['t95']):.0%}"
            findings.append(_finding("camera", where, "major" if place > 0.6 else "minor",
                                     f"the move happens at another point of the shot: {fr(os_, om)} of ours vs {fr(rs, rm)} of the reference's"
                                     f"{' (its pace kept in this shorter shot)' if k < 0.99 else ''}"))
        detail.update({"placement": round(place, 3), "ease_rmse": round(e, 3), "duration_log2": round(dur, 2), "amount_log2": round(amt, 2),
                       "ref_ease": _ease_name(rm), "ours_ease": _ease_name(om), "ref_bezier": (rm.get("ease") or {}).get("bezier")})
        if e > 0.08:
            same = _ease_name(om) == _ease_name(rm)
            what = (f"both read as {_ease_name(rm)} but the curves still differ by {e:.2f}" if same
                    else f"ours ≈ {_ease_name(om)}, reference ≈ {_ease_name(rm)}")
            re_ = rm.get("ease") or {}
            over = f", overshoot {re_['overshoot']:.0%}" if re_.get("overshoot", 0) > 0.02 else ""
            use = f" — use cubic-bezier({', '.join(map(str, re_['bezier']))}){over}" if re_.get("bezier") else ""
            findings.append(_finding("camera", where, "major" if e > 0.15 else "minor", f"easing differs: {what}{use}"))
        if abs(dur) > 0.5:
            findings.append(_finding("camera", where, "major" if abs(dur) > 1 else "minor",
                                     f"the move takes {dur_o:.2f}s vs {dur_r * k:.2f}s in the reference"
                                     f"{f' (its {dur_r:.2f}s scaled to this shorter shot)' if k < 0.99 else ''} ({2 ** dur:.1f}× {'slower' if dur > 0 else 'faster'})"))
        if abs(amt) > 0.6:
            findings.append(_finding("camera", where, "major" if abs(amt) > 1.2 else "minor",
                                     f"the move goes {_amount(ax, om['amount'][ax])} vs {_amount(ax, rm['amount'][ax])} in the reference"))
    elif "progress" in rm and "progress" not in om:
        cost += 1.0
    return _score(cost, 1.5), detail, findings


def look_pair(rs: dict, os_: dict) -> tuple[float, dict, list[dict]]:
    wL, wa, wb = look_.wasserstein(np.asarray(rs["look"]["hist"]), np.asarray(os_["look"]["hist"]))
    dL, db = os_["look"]["L"] - rs["look"]["L"], os_["look"]["b"] - rs["look"]["b"]
    where, findings = f"{os_['id']} ↔ ref #{rs['id']}", []
    if wL > 10:
        findings.append(_finding("look", where, "major" if wL > 20 else "minor", f"{'brighter' if dL > 0 else 'darker'} than the reference (mean L {os_['look']['L']:.0f} vs {rs['look']['L']:.0f}, EMD {wL:.1f})"))
    if abs(db) > 8:
        findings.append(_finding("look", where, "minor", f"{'warmer' if db > 0 else 'cooler'} than the reference (Lab b {os_['look']['b']:+.0f} vs {rs['look']['b']:+.0f})"))
    return _score(wL / 12 + (wa + wb) / 10, 1.0), {"emd_L": round(wL, 2), "emd_a": round(wa, 2), "emd_b": round(wb, 2)}, findings


def cadence_finding(ref: dict, ours: dict) -> tuple[float, list[dict]]:
    """Drawings per second while things move: animating on ones vs. twos changes the whole feel of 2D motion."""
    r, o = ref.get("cadence", {}), ours.get("cadence", {})
    if "frames_per_drawing" not in r or "frames_per_drawing" not in o:
        return 0.0, []
    gap = abs(math.log2(o["frames_per_drawing"] / r["frames_per_drawing"]))
    if gap < 0.25:
        return gap, []
    advice = (f"hold drawings longer: about {r['frames_per_drawing']:.1f} frames per drawing" if r["frames_per_drawing"] > o["frames_per_drawing"]
              else "draw new frames more often")
    return gap, [_finding("rhythm", "whole film", "major" if gap > 0.5 else "minor",
                          f"the reference animates {r['label']} (~{r['drawings_per_second']:.0f} new drawings/s while things move); "
                          f"ours {o['label']} (~{o['drawings_per_second']:.0f}/s) — {advice}")]


def rhythm_component(ref: dict, ours: dict) -> tuple[dict, list[dict]]:
    r, o = ref["rhythm"], ours["rhythm"]
    cad_cost, findings = cadence_finding(ref, ours)
    if "on_beat_ratio" not in r or "on_beat_ratio" not in o:
        if findings:
            return {"score": _score(cad_cost, 1.5), "note": "cadence only (no beats or no cuts on one side)"}, findings
        return {"score": None, "note": "no beats or no cuts on one side"}, []
    cost = cad_cost
    d_on = o["on_beat_ratio"] - r["on_beat_ratio"]
    cost += abs(d_on) / 0.3
    if d_on < -0.25:
        findings.append(_finding("rhythm", "cuts", "major", f"the reference cuts on the beat {r['on_beat_ratio']:.0%} of the time (±1 frame); ours {o['on_beat_ratio']:.0%}"))
    if r["phase_R"] > 0.5:   # the reference has a consistent place in the beat where it cuts
        dphi = abs(((o["phase_mean"] - r["phase_mean"]) + 0.5) % 1.0 - 0.5)
        cost += dphi * r["phase_R"] / 0.15
        if dphi > 0.15:
            findings.append(_finding("rhythm", "cuts", "minor", f"the reference cuts consistently at {r['phase_mean']:.2f} of the beat (R={r['phase_R']:.2f}); ours at {o['phase_mean']:.2f}"))
    dens = math.log2(max(o["cuts_per_beat"], 1e-3) / max(r["cuts_per_beat"], 1e-3))
    cost += abs(dens) / 1.0
    if abs(dens) > 0.6:
        findings.append(_finding("rhythm", "cuts", "major" if abs(dens) > 1 else "minor",
                                 f"{'more' if dens > 0 else 'fewer'} cuts per beat than the reference ({o['cuts_per_beat']:.2f} vs {r['cuts_per_beat']:.2f})"))
    return {"score": _score(cost, 1.5), "ref": {k: r[k] for k in ("on_beat_ratio", "phase_mean", "phase_R", "cuts_per_beat")},
            "ours": {k: o[k] for k in ("on_beat_ratio", "phase_mean", "phase_R", "cuts_per_beat")}}, findings


def film_palette(fp: dict) -> np.ndarray:
    """The whole stretch's Lab histogram, each shot weighted by how long it is on screen."""
    h = np.zeros((3, look_.BINS))
    for s in fp["shots"]:
        on = max(0.0, min(s["end"], fp["end"]) - max(s["start"], fp["start"]))
        h += np.asarray(s["look"]["hist"]) * on
    return look_.normalise(h)


def palette_component(ref: dict, ours: dict) -> tuple[dict, list[dict]]:
    if not ref["shots"] or not ours["shots"]:
        return {"score": None}, []
    pr, po = film_palette(ref), film_palette(ours)
    wl, wa, wb = look_.wasserstein(pr, po)
    centre = look_.mean
    dL, da, db = (centre(po, c) - centre(pr, c) for c in range(3))
    findings = []
    if wl > 8:
        findings.append(_finding("palette", "whole film", "major" if wl > 15 else "minor",
                                 f"overall {'brighter' if dL > 0 else 'darker'} than the reference (mean L {centre(po, 0):.0f} vs {centre(pr, 0):.0f}, EMD {wl:.1f})"))
    if wa + wb > 10:
        hue = ("warmer" if db > 0 else "cooler") if abs(db) >= abs(da) else ("redder" if da > 0 else "greener")
        findings.append(_finding("palette", "whole film", "major" if wa + wb > 18 else "minor",
                                 f"overall {hue} than the reference (Lab a {centre(po, 1):+.0f} vs {centre(pr, 1):+.0f}, b {centre(po, 2):+.0f} vs {centre(pr, 2):+.0f})"))
    return {"score": _score(wl / 12 + (wa + wb) / 10, 1.0), "emd_L": round(wl, 2), "emd_a": round(wa, 2), "emd_b": round(wb, 2)}, findings


@dataclass(frozen=True)
class PaceFeature:
    """One number describing how busy a film is: its raw value, how it is compared (a compressed scale, so that 2 vs 4
    cuts counts like 4 vs 8), how big a gap is worth a finding, and how to print it."""
    name: str
    raw: Callable[[dict], float]
    scale: Callable[[float], float]
    limit: float
    fmt: str


def _cuts_per_10s(fp: dict) -> float:
    return len(fp["cuts"]) / max(1e-6, fp["end"] - fp["start"]) * 10


def _moving_share(fp: dict) -> float:
    """Share of shots where the camera visibly moves (≥ a quarter of their frames above the dead zone). A shot's total
    travel would not do: in a long shot, measurement noise and line boil add up to a "move" no viewer sees."""
    if not fp["shots"]:
        return 0.0
    c = fp["series"]["camera"]
    v = np.sqrt(sum(np.asarray(c[k], float) ** 2 for k in ("dx", "dy", "dz", "dr"))) * fp["fps"]
    t = fp["start"] + np.arange(len(v)) / fp["fps"]
    seen = [float(np.mean(v[(t >= s["start"]) & (t < s["end"])] > tension.DEADZONE["camera"])) for s in fp["shots"]
            if np.any((t >= s["start"]) & (t < s["end"]))]
    return float(np.mean([x >= 0.25 for x in seen])) if seen else 0.0


def _camera_speed(fp: dict) -> float:
    """Typical *visible* camera speed: speeds under the dead zone a viewer does not see are 0. Without it this measured
    each source's noise floor (compression, line boil) — a signature of the file, not of its style."""
    c = fp["series"]["camera"]
    v = np.sqrt(sum(np.asarray(c[k], float) ** 2 for k in ("dx", "dy", "dz", "dr"))) * fp["fps"]
    return float(np.median(np.maximum(0.0, v - tension.DEADZONE["camera"])))


PACE = (
    PaceFeature("cuts per 10 s", _cuts_per_10s, np.log1p, 0.4, "{:.1f}"),
    PaceFeature("share of shots with a moving camera", _moving_share, float, 0.3, "{:.0%}"),
    PaceFeature("frames per drawing", lambda fp: (fp.get("cadence") or {}).get("frames_per_drawing") or 1.0, np.log2, 0.35, "{:.1f}"),
    PaceFeature("typical camera speed (frame widths/s)", _camera_speed, lambda v: np.log1p(v * 50), 0.5, "{:.3f}"),
    PaceFeature("motion inside the frame", lambda fp: float(np.mean(fp["series"]["local"])), lambda v: np.log1p(v * 2000), 0.5, "{:.4f}"),
)


def pace_vector(fp: dict) -> np.ndarray:
    return np.array([f.scale(f.raw(fp)) for f in PACE], float)


def pace_component(ref: dict, ours: dict) -> tuple[dict, list[dict]]:
    """How busy the film is: cut rate, how much the camera moves, cadence, how much moves inside the frame."""
    r, o = pace_vector(ref), pace_vector(ours)
    gap = np.abs(o - r)
    findings = []
    for f, g, ov, rv in zip(PACE, gap, o, r):
        if g > f.limit:
            findings.append(_finding("pace", "whole film", "major" if g > 2 * f.limit else "minor",
                                     f"{'more' if ov > rv else 'less'} {f.name} than the reference "
                                     f"({f.fmt.format(f.raw(ours))} vs {f.fmt.format(f.raw(ref))})"))
    return {"score": _score(float(gap.sum()), 1.5), "ref": [round(float(x), 3) for x in r], "ours": [round(float(x), 3) for x in o]}, findings


def frames_component(ref: dict, ours: dict) -> dict:
    a, b = np.asarray(ref["descriptors"]["data"]), np.asarray(ours["descriptors"]["data"])
    if not len(a) or not len(b):
        return {"score": None}
    cost, _ = dtw(a, b, band=0.25, metric="cosine")
    return {"score": _score(cost, 0.25), "dtw_cost": round(cost, 4)}


# ---------- the whole comparison ----------
def style_distance(ref: dict, ours: dict, pairs: list[dict] | None = None, ref_window: tuple[float, float] | None = None) -> dict:
    """pairs: [{"id": our shot id, "ref_shot": reference shot number}, …] (plan.json shots). Without a window, the
    reference is cut to the span of the shots the plan maps to (a 30 s film is compared to the 30 s it clones)."""
    by_ref = {s["id"]: s for s in ref["shots"]}
    if ref_window is None and pairs:
        mapped = [by_ref[p["ref_shot"]] for p in pairs if p.get("ref_shot") in by_ref]
        if mapped:
            ref_window = (min(s["start"] for s in mapped), max(s["end"] for s in mapped))
    R = window(ref, *ref_window) if ref_window else ref
    comps, findings = {}, []
    comps["tension"], f, mapping = tension_component(R, ours)
    findings += f
    comps["peaks"], f = peaks_component(R, ours, mapping)
    findings += f
    comps["rhythm"], f = rhythm_component(R, ours)
    findings += f
    comps["frames"] = frames_component(R, ours)
    comps["palette"], f = palette_component(R, ours)
    findings += f
    comps["pace"], f = pace_component(R, ours)
    findings += f
    by_ours = {s["id"]: s for s in ours["shots"]}
    from .fingerprint import reference_for
    answers = reference_for(ref, [(p.get("id"), p.get("ref_shot"),
                                   (by_ours[p["id"]]["end"] - by_ours[p["id"]]["start"]) if p.get("id") in by_ours else 1.0) for p in pairs or []])
    shots, cam_scores, look_scores = [], [], []
    for p in pairs or []:
        rs, os_ = answers.get(p.get("id")), by_ours.get(p.get("id"))
        if not rs or not os_:
            continue
        cs, cd, cf = camera_pair(rs, os_)
        ls, ld, lf = look_pair(rs, os_)
        cam_scores.append(cs)
        look_scores.append(ls)
        findings += cf + lf
        shots.append({"id": os_["id"], "ref_shot": rs["id"], "camera": {"score": cs, **cd}, "look": {"score": ls, **ld}})
    comps["camera"] = {"score": round(float(np.mean(cam_scores)), 1) if cam_scores else None, "pairs": len(cam_scores)}
    comps["look"] = {"score": round(float(np.mean(look_scores)), 1) if look_scores else None, "pairs": len(look_scores)}
    def mix(weights):
        used = {k: w for k, w in weights.items() if comps.get(k, {}).get("score") is not None}
        return round(sum(w * comps[k]["score"] for k, w in used.items()) / sum(used.values()), 1) if used else None
    style, structure = mix(STYLE), mix(STRUCTURE)
    parts = {k: v for k, v in (("style", style), ("structure", structure)) if v is not None}
    overall = round(sum(OVERALL[k] * v for k, v in parts.items()) / sum(OVERALL[k] for k in parts), 1) if parts else None
    findings.sort(key=lambda x: (x["severity"] != "major", x["component"]))
    return {"version": 2, "ref_window": [round(x, 3) for x in ref_window] if ref_window else None,
            "overall": overall, "style": style, "structure": structure, "components": comps, "shots": shots, "findings": findings}
