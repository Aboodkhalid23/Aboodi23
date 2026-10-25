"""The shape of a camera move: when it starts and stops, how far it goes, and the easing curve it follows.

The whole shot trajectory x(t) of the dominant axis is fitted with a *timed* ease model

    x(t) = B + A · E( clip((t − t0) / D, 0, 1) )

so start time t0, duration D, amount A, offset B and the ease shape E are estimated together. Cutting the move out by a
speed threshold first would bias the shape: a power3.out spends its last quarter below 8 % of peak speed and would be
clipped and stretched. E is described three ways:

    named    the nearest GSAP ease (power1–4, sine, expo, circ, back), so a builder can type it directly
    bezier   CSS cubic-bezier(x1, y1, x2, y2), with x(s) = u solved per sample
    spring   damped oscillator x(t) = B + A·(1 − e^(−ζωτ)(cos ω_d τ + ζω/ω_d · sin ω_d τ)), τ = t − t0, ω in rad/s

plus overshoot (how far past the target it goes before settling) and the measured progress curve on the fitted
[t0, t0 + D] window, which is what two moves are compared on.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import least_squares
from scipy.signal import find_peaks

PROGRESS_SAMPLES = 21
Ease = Callable[[np.ndarray], np.ndarray]


# ---------- named eases (GSAP's formulas) ----------
def _power(p: float) -> dict[str, Ease]:
    return {"in": lambda t: t ** p, "out": lambda t: 1 - (1 - t) ** p,
            "inOut": lambda t: np.where(t < 0.5, (2 * t) ** p / 2, 1 - (2 * (1 - t)) ** p / 2)}


def _named() -> dict[str, Ease]:
    out: dict[str, Ease] = {"none": lambda t: t}
    for n in (1, 2, 3, 4):
        for k, f in _power(n + 1).items():
            out[f"power{n}.{k}"] = f
    out.update({
        "sine.in": lambda t: 1 - np.cos(t * np.pi / 2), "sine.out": lambda t: np.sin(t * np.pi / 2),
        "sine.inOut": lambda t: -(np.cos(np.pi * t) - 1) / 2,
        "expo.in": lambda t: np.where(t <= 0, 0.0, 2.0 ** (10 * (t - 1))), "expo.out": lambda t: np.where(t >= 1, 1.0, 1 - 2.0 ** (-10 * t)),
        "expo.inOut": lambda t: np.where(t < 0.5, 2.0 ** (20 * t - 10) / 2, (2 - 2.0 ** (-20 * t + 10)) / 2),
        "circ.in": lambda t: 1 - np.sqrt(np.clip(1 - t ** 2, 0, 1)), "circ.out": lambda t: np.sqrt(np.clip(1 - (t - 1) ** 2, 0, 1)),
        "back.out": lambda t: 1 + 2.70158 * (t - 1) ** 3 + 1.70158 * (t - 1) ** 2,
        "back.in": lambda t: 2.70158 * t ** 3 - 1.70158 * t ** 2,
    })
    return out


NAMED = _named()


# ---------- cubic bezier ----------
def bezier(u: np.ndarray, x1: float, y1: float, x2: float, y2: float) -> np.ndarray:
    """CSS cubic-bezier easing evaluated at progress u (x1, x2 ∈ [0, 1] keep x(s) monotonic; bisection on s)."""
    u = np.clip(np.asarray(u, float), 0, 1)
    lo, hi = np.zeros_like(u), np.ones_like(u)
    for _ in range(30):
        s = (lo + hi) / 2
        x = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s ** 2 * x2 + s ** 3
        lo, hi = np.where(x < u, s, lo), np.where(x < u, hi, s)
    s = (lo + hi) / 2
    return 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s ** 2 * y2 + s ** 3


_BEZIER_STARTS = [(0.25, 0.1, 0.25, 1.0), (0.42, 0.0, 0.58, 1.0), (0.16, 1.0, 0.3, 1.0), (0.34, 1.56, 0.64, 1.0)]


def spring(tau: np.ndarray, omega: float, zeta: float) -> np.ndarray:
    """Unit step response of a damped oscillator after tau seconds (0 before)."""
    zeta = min(zeta, 0.999)
    tau = np.clip(tau, 0, None)
    wd = omega * np.sqrt(1 - zeta ** 2)
    return 1 - np.exp(-zeta * omega * tau) * (np.cos(wd * tau) + zeta * omega / wd * np.sin(wd * tau))


# ---------- timed fits ----------
def _initial_timing(t: np.ndarray, x: np.ndarray) -> tuple[float, float, float, float]:
    """t0, D, A, B from where the trajectory crosses 2 % and 98 % of its net travel."""
    B, A = float(x[0]), float(x[-1] - x[0])
    p = (x - B) / A
    i0 = int(np.argmax(p >= 0.02))
    i1 = int(np.argmax(p >= 0.98)) if (p >= 0.98).any() else len(x) - 1
    dt = float(t[1] - t[0])
    return float(t[i0]) - dt, max(2 * dt, float(t[i1] - t[i0]) / 0.96), A, B


def _fit(t: np.ndarray, x: np.ndarray, shape: Callable, shape0: tuple, shape_lo: tuple, shape_hi: tuple, init) -> tuple[np.ndarray, float]:
    """Least squares for x(t) = B + A·shape(u, *params), u = clip((t − t0)/D); residual relative to |A|."""
    t0, D, A, B = init
    span, dt, scale = float(t[-1] - t[0]), float(t[1] - t[0]), abs(A) or 1.0
    k = len(shape0)

    def res(p):
        u = np.clip((t - p[k]) / p[k + 1], 0, 1)
        return (p[k + 3] + p[k + 2] * shape(u, *p[:k]) - x) / scale

    lo = [*shape_lo, t[0] - span, dt, -np.inf, -np.inf]
    hi = [*shape_hi, t[-1], 2 * span + dt, np.inf, np.inf]
    p0 = np.clip([*shape0, t0, D, A, B], np.array(lo) + 1e-9, np.array(hi) - 1e-9)
    r = least_squares(res, p0, bounds=(lo, hi), x_scale="jac")
    return r.x, float(np.sqrt(np.mean(r.fun ** 2)))


def fit_named(t: np.ndarray, x: np.ndarray, init) -> tuple[str, np.ndarray, float]:
    best = ("none", np.asarray(init), float("inf"))
    for name, f in NAMED.items():
        p, err = _fit(t, x, lambda u, f=f: f(u), (), (), (), init)
        if err < best[2]:
            best = (name, p, err)
    return best


def fit_bezier(t: np.ndarray, x: np.ndarray, init) -> tuple[np.ndarray, float]:
    best = (np.asarray([0.0, 0.0, 1.0, 1.0, *init]), float("inf"))
    for s0 in _BEZIER_STARTS:
        p, err = _fit(t, x, bezier, s0, (0, -1, 0, -1), (1, 2, 1, 2), init)
        if err < best[1]:
            best = (p, err)
    return best


def fit_spring(t: np.ndarray, x: np.ndarray, init) -> tuple[dict[str, float], float]:
    t0, D, A, B = init
    scale = abs(A) or 1.0
    best: tuple[dict[str, float], float] = ({}, float("inf"))
    for w0, z0 in [(6.0, 0.9), (10.0, 0.5), (16.0, 0.3)]:
        p0 = [np.clip(t0, t[0] - 1 + 1e-6, t[-1] - 1e-6), A, B, np.clip(w0 / max(D, 0.05), 0.6, 199), z0]
        r = least_squares(lambda p: (p[2] + p[1] * spring(t - p[0], p[3], p[4]) - x) / scale, p0,
                          bounds=([t[0] - 1, -np.inf, -np.inf, 0.5, 0.05], [t[-1], np.inf, np.inf, 200, 0.999]))
        err = float(np.sqrt(np.mean(r.fun ** 2)))
        if err < best[1]:
            w, z = float(r.x[3]), float(r.x[4])
            best = ({"omega": round(w, 2), "zeta": round(z, 3), "start": round(float(r.x[0]), 3),
                     "settle_s": round(4 / (z * w), 3), "_A": float(r.x[1]), "_B": float(r.x[2])}, err)
    return best


# ---------- moves ----------
AXES = ("x", "y", "z", "r")
KIND = {"x": ("move_right", "move_left"), "y": ("move_down", "move_up"), "z": ("push_in", "pull_out"), "r": ("roll_cw", "roll_ccw")}
MIN_AMOUNT = {"x": 0.015, "y": 0.015, "z": 0.015, "r": 0.015}   # below this an axis counts as still
SHAKE_RATE = 1.5                                                  # direction changes per second for a shake
SNAP_S = 2.5 / 24                                                 # a move done this fast is a jump cut / impact jolt
STILL_S, PAD_S, MIN_MOVE_S = 0.25, 0.125, 0.2                     # move segmentation, in seconds (any sampling rate)


def describe_move(t: np.ndarray, traj: dict[str, np.ndarray], fit: bool = True) -> dict:
    """traj: cumulative camera position per axis (x, y in frame widths, z log-scale, r radians), starting at 0.
    fit=False skips the ease fits (≈ 300 ms) and reads timing and shape straight off the curve: for exact, finely
    sampled trajectories (a score's predicted camera) that is the same answer, and it is what the optimizer needs."""
    amount = {a: float(traj[a][-1] - traj[a][0]) for a in AXES}
    swing = {a: float(np.ptp(traj[a])) for a in AXES}
    kinds = [KIND[a][0 if amount[a] > 0 else 1] for a in AXES if abs(amount[a]) >= MIN_AMOUNT[a]]
    out: dict = {"kind": kinds or ["static"], "amount": {a: round(amount[a], 4) for a in AXES}}
    axis = max(AXES, key=lambda a: swing[a])
    if swing[axis] < MIN_AMOUNT[axis] or len(t) < 6:
        return out
    # turns back on itself at least twice by a third of its swing: a shake, not a move to somewhere (a move with an
    # overshoot turns once; a spring's later wobbles are smaller than that)
    # … and quickly: a camera that drifts down and back up over twelve seconds is several moves, not a shake
    turns = sum(len(find_peaks(s * traj[axis], prominence=swing[axis] / 3)[0]) for s in (1, -1))
    rate = turns / max(1e-6, float(t[-1] - t[0]))
    if (turns >= 2 or abs(amount[axis]) < 0.2 * swing[axis]) and rate >= SHAKE_RATE:
        out["kind"] = kinds + ["shake"] if kinds else ["shake"]
        out["shake"] = {"axis": axis, "swing": round(swing[axis], 4)}
        return out
    # engines tween scale, not log-scale: fit the ease on the scale itself so "power3.out" means what a builder types
    x = np.exp(traj[axis]) if axis == "z" else traj[axis]
    if not fit:
        t5, t95, prog = canonical_progress(t, x)
        p = (x - x[0]) / ((x[-1] - x[0]) or 1.0)
        out.update({"snap": t95 - t5 <= SNAP_S, "axis": axis, "start": round(t5, 3), "end": round(t95, 3), "t5": round(t5, 3), "t95": round(t95, 3),
                    "duration": round((t95 - t5) / 0.9, 3), "span90": round(t95 - t5, 3),
                    "overshoot": round(max(0.0, float(p.max()) - 1), 4), "progress": [round(float(v), 4) for v in prog]})
        return out
    init = _initial_timing(t, x)
    name, pn, err_n = fit_named(t, x, init)
    pb, err_b = fit_bezier(t, x, tuple(pn[-4:]))
    sp, err_s = fit_spring(t, x, tuple(pn[-4:]))
    t0, D, A, B = (float(v) for v in pn[-4:])
    # What two moves are compared on: the curve between the 5 % and 95 % points of its travel. This window does not
    # depend on which model fitted best ("flat start + ease" and "later start + another ease" are the same motion, and
    # fitted windows would make them look different). It is read off the best-fitting model sampled 10× finer than the
    # frames: a fast move spans only a few frames, and where those frames fall would otherwise change its shape.
    best = min((("named", err_n), ("bezier", err_b), ("spring", err_s)), key=lambda p: p[1])[0]
    # The model a builder (and the transfer) uses: a GSAP name when it fits nearly as well as the best — easier to read
    # and tweak — else the best. Its curve and its own window are the move's shape, start and duration, so every reader
    # (transfer, comparison, reports) shares one description of the move.
    pick = "named" if err_n <= 1.1 * min(err_n, err_b, err_s) + 0.002 else best
    timing = {"named": (t0, D), "bezier": (float(pb[4]), float(pb[5])),
              "spring": (float(sp.get("start", t0)), float(sp.get("settle_s", D)))}
    m0, mD = timing[pick]
    fine = np.linspace(t[0], t[-1], 10 * len(t))
    if pick == "named":
        xm = B + A * NAMED[name](np.clip((fine - t0) / D, 0, 1))
    elif pick == "bezier":
        xm = pb[7] + pb[6] * bezier(np.clip((fine - pb[4]) / pb[5], 0, 1), *pb[:4])
    else:
        xm = sp["_B"] + sp["_A"] * spring(fine - sp["start"], sp["omega"], sp["zeta"])
    t5, t95, prog = canonical_progress(fine, xm)
    # A move the edit cuts off (real footage often cuts mid-move): how much of it is on screen, in time and in progress
    shape = {"named": lambda u: NAMED[name](u), "bezier": lambda u: bezier(u, *pb[:4]),
             "spring": lambda u: spring(u * mD, sp["omega"], sp["zeta"]) if sp else u}[pick]
    u_in, u_out = max(0.0, (float(t[0]) - m0) / mD), min(1.0, (float(t[-1]) - m0) / mD)
    seen = float(shape(np.asarray(u_out)) - shape(np.asarray(u_in))) if u_out > u_in else 0.0
    after = (x[t >= t0] - B) / A
    speed = np.abs(np.gradient(x, t))
    out.update({
        "snap": t95 - t5 <= SNAP_S,   # done within a couple of frames: a jump, its "ease" means nothing
        "axis": axis, "start": round(max(m0, float(t[0])), 3), "end": round(min(m0 + mD, float(t[-1])), 3), "duration": round(mD, 3),
        "hold_before": round(max(0.0, m0 - float(t[0])), 3), "hold_after": round(max(0.0, float(t[-1]) - m0 - mD), 3),
        "peak_speed": round(float(speed.max()), 4),
        "ease": {"named": name, "named_rmse": round(err_n, 4),
                 "bezier": [round(float(v), 3) for v in pb[:4]], "bezier_rmse": round(err_b, 4),
                 "spring": {k: v for k, v in sp.items() if not k.startswith("_")}, "spring_rmse": round(err_s, 4), "best": best, "pick": pick,
                 "overshoot": round(max(0.0, float(after.max()) - 1) if len(after) else 0.0, 4)},
        "timing": {k: [round(a, 4), round(b, 4)] for k, (a, b) in timing.items()},
        "span90": round(t95 - t5, 3), "t5": round(t5, 3), "t95": round(t95, 3),
        "progress": [round(float(v), 4) for v in prog],
        "visible": round(max(0.0, min(m0 + mD, float(t[-1])) - max(m0, float(t[0]))), 3),
        "cut_off": m0 + mD > float(t[-1]) + float(t[1] - t[0]),   # still moving at the cut out
        "lead_in": round(max(0.0, float(t[0]) - m0), 3),            # already moving this long at the cut in
        "seen": round(seen, 4),   # share of the move's travel that is on screen (< 1 when the cut interrupts it)
    })
    return out


def canonical_progress(t: np.ndarray, x: np.ndarray, lo: float = 0.05, hi: float = 0.95) -> tuple[float, float, np.ndarray]:
    """Times where the travel first reaches lo and hi of its net amount, and the curve between them rescaled to 0–1."""
    p = (x - x[0]) / ((x[-1] - x[0]) or 1.0)
    def cross(level):
        i = int(np.argmax(p >= level))
        if i == 0:
            return float(t[0])
        return float(np.interp(level, [p[i - 1], p[i]], [t[i - 1], t[i]])) if p[i] != p[i - 1] else float(t[i])
    t5, t95 = cross(lo), cross(hi)
    if t95 <= t5:
        t95 = t5 + float(t[1] - t[0])
    u = np.linspace(0, 1, PROGRESS_SAMPLES)
    prog = (np.interp(t5 + u * (t95 - t5), t, p) - lo) / (hi - lo)
    return t5, t95, prog


MIN_PACE = 0.5   # a move may be sped up to 2× to fit a shorter shot; beyond that the smaller moves are left out


def on_screen(m: dict) -> float:
    """How long a move is on screen (a move a cut interrupts shows only part of its length)."""
    partial = m.get("cut_off") or (m.get("lead_in") or 0) > 0.05
    return float((m.get("visible") if partial and m.get("visible") is not None else m.get("duration")) or 0.0)


def moves_that_fit(moves: list[dict], length: float) -> list[dict]:
    """The moves a shot of `length` seconds keeps from a reference shot: all of them when they fit at ≥ MIN_PACE of
    their speed, else the biggest ones (squeezing twelve seconds of slow drifting into two makes whip pans). Shared by
    the transfer (what it writes) and the comparison (what pace it expects), so the two never disagree."""
    kept = list(moves)
    while len(kept) > 1 and sum(on_screen(m) for m in kept) > length / MIN_PACE:
        kept.remove(min(kept, key=lambda m: max(abs(v) / MIN_AMOUNT[a] for a, v in m["amount"].items())))
    return kept


def moving_segments(t: np.ndarray, traj: dict[str, np.ndarray]) -> list[tuple[int, int]]:
    """Index ranges where the camera moves, split where it stays still for at least STILL_S seconds."""
    if len(t) < 4:
        return []
    dt = float(t[1] - t[0])
    min_still, pad, min_len = max(1, round(STILL_S / dt)), max(1, round(PAD_S / dt)), max(2, round(MIN_MOVE_S / dt))
    speed = gaussian_filter1d(np.sqrt(sum(np.gradient(traj[a], t) ** 2 for a in AXES)), 0.0625 / dt)
    active = speed > max(0.12 * float(speed.max()), 0.02)
    segs, k, n = [], 0, len(t)
    while k < n:
        if not active[k]:
            k += 1
            continue
        e = k
        while e + 1 < n and (active[e + 1] or active[e + 2:e + 1 + min_still].any()):
            e += 1
        segs.append((max(0, k - pad), min(n - 1, e + pad)))
        k = e + 1
    return [(a, b) for a, b in segs if b - a >= min_len and max(np.ptp(traj[x][a:b + 1]) for x in AXES) >= min(MIN_AMOUNT.values())]


def describe_shot(t: np.ndarray, traj: dict[str, np.ndarray], fit: bool = True) -> dict:
    """The shot's camera as a whole (kind, total amount) plus each separate move inside it; the top-level ease, timing
    and progress are those of the biggest move, which is what a shot is compared on.

    Travel that no move accounts for is a *drift*: a slow push or pan running under the whole shot, too slow next to
    its quick moves to be segmented as one (seen on a real reference: a 16 % push of which segmentation kept half).
    Its rate comes from the travel outside the moves; each move's own amount has the drift during it taken out."""
    whole = describe_move(t, traj, fit)
    if "axis" not in whole:          # still, or a shake
        net = {x: float(whole["amount"][x]) for x in AXES if abs(whole["amount"][x]) >= MIN_AMOUNT[x]}
        if "shake" in whole["kind"] and net:   # a shake that also travels: the travel is a drift under it
            whole = {**whole, "drift": {x: round(v, 4) for x, v in net.items()}}
        return whole
    segs = moving_segments(t, traj)
    moves = []
    for a, b in segs:
        sub = describe_move(t[a:b + 1], {x: traj[x][a:b + 1] - traj[x][a] for x in AXES}, fit)
        if "axis" in sub:
            # a segment's edges inside the shot are not cuts: only a segment touching the shot's start or end can be
            # interrupted by one
            if a > 0 and "lead_in" in sub:
                sub["lead_in"] = 0.0
            if b < len(t) - 1 and "cut_off" in sub:
                sub["cut_off"] = False
            if "seen" in sub and not sub.get("cut_off") and not sub.get("lead_in"):
                sub["seen"], sub["visible"] = 1.0, sub["duration"]
            moves.append((sub, float(t[b] - t[a])))
    total_t = float(t[-1] - t[0])
    moving_t = sum(d for _, d in moves)
    residual = {x: float(whole["amount"][x]) - sum(m["amount"][x] for m, _ in moves) for x in AXES}
    drift = {x: v for x, v in residual.items() if abs(v) >= MIN_AMOUNT[x]} if moves and total_t - moving_t > 0.25 * total_t else {}
    if len(moves) <= 1 and not drift:
        return {**whole, "moves": 1}
    rate = {x: v / max(1e-6, total_t - moving_t) for x, v in drift.items()}   # per second, outside the moves
    for m, d in moves:
        m["amount"] = {x: round(m["amount"][x] - rate.get(x, 0.0) * d, 4) for x in AXES}
    moves = [m for m, _ in moves]
    if not moves:
        return {**whole, "moves": 1}
    main = max(moves, key=lambda m: abs(m["amount"][m["axis"]]) / MIN_AMOUNT[m["axis"]])
    others = [{k: m[k] for k in ("kind", "axis", "start", "duration", "amount")} | {"ease": m["ease"]["named"] if "ease" in m else None} for m in moves if m is not main]
    out = {**main, "kind": whole["kind"], "amount": whole["amount"], "move_amount": main["amount"], "moves": len(moves), "other_moves": others}
    if drift:
        out["drift"] = {x: round(r * total_t, 4) for x, r in rate.items()}
    return out
