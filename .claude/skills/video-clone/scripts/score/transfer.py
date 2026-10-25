"""Motion transfer: write a score whose camera does what the reference camera measurably did.

For every plan shot mapped to a reference shot (plan.json "ref_shot"), each move perception found in that reference shot
— the main one and any other_moves — becomes a score move with the same pace (seconds), amount (converted from frame
widths to stage pixels at the current zoom) and ease (the fitted curve). Shots whose plan already defines a camera
start from it. Moves that started on a beat in the reference start on a beat here, written as "B<n>".

The result is a starting point the director edits, not a verdict: the plan's own intent (a push to the eyes, a reveal)
may need different targets. Every generated move records where it came from ("from_ref") so a reviewer can tell
transferred motion from authored motion.
"""
from __future__ import annotations

import math

from perception import curves
from perception.fingerprint import ref_shot_id

from .timeexpr import Clock

W = 1920.0
AXIS_CH = {"x": "x", "y": "y", "z": "zoom", "r": "rot"}


def ease_spec(m: dict) -> tuple[object, float | None, float | None]:
    """The fitted ease as a score ease, with the start and duration *of that fit* (each model has its own window).
    A GSAP name when it fits nearly as well as the best: easier to read and to tweak."""
    e, tm = m["ease"], m.get("timing") or {}
    if m.get("snap"):
        return "hold", None, None
    pick = e.get("pick") or e.get("best") or "named"   # the model perception chose for builders; its own window
    t0, d = (tm.get(pick) or (None, None))[:2] if tm.get(pick) else (None, None)
    if pick == "named":
        return e["named"], t0, d
    if pick == "spring" and e.get("spring"):
        return {"spring": {"omega": e["spring"]["omega"], "zeta": min(0.95, e["spring"]["zeta"])}}, t0, None
    return {"bezier": e["bezier"]}, t0, d


def _by(amount: dict[str, float], zoom: float) -> dict[str, float]:
    by = {}
    for ax, v in amount.items():
        if abs(v) < curves.MIN_AMOUNT[ax]:
            continue
        if ax == "z":
            by["zoom"] = round(math.exp(v), 4)
        elif ax == "r":
            by["rot"] = round(-v, 4)
        else:
            by[AXIS_CH[ax]] = round(v * W / zoom, 1)
    return by


def schedule(want: list[float], durs: list[float], start: float, end: float) -> tuple[list[float], list[float], float]:
    """Place moves one after another inside [start, end]: each as close to where it was wanted as possible, never
    overlapping, never outside the shot. Pace (duration) is kept when the moves fit; when they do not, every move is
    compressed by the same factor (returned) and they run back to back."""
    L, total = end - start, sum(durs)
    if total > L:
        k = L / total
        durs = [d * k for d in durs]
        starts, t = [], start
        for d in durs:
            starts.append(t)
            t += d
        return starts, durs, k
    s = [min(max(w, start), end) for w in want]
    for i in range(len(s)):                      # forward: after the previous one
        if i:
            s[i] = max(s[i], s[i - 1] + durs[i - 1])
    for i in reversed(range(len(s))):            # backward: finish before the next one / the shot's end
        s[i] = min(s[i], (s[i + 1] if i + 1 < len(s) else end) - durs[i])
    return s, durs, 1.0


def _at(t: float, lo: float, hi: float, clock: Clock, shot_start: float) -> str:
    """'B<n>' when a beat within 1.5 frames keeps the move inside [lo, hi], else seconds into the shot."""
    k = round((t - clock.offset) / clock.beat)
    tb = clock.offset + k * clock.beat
    if abs(tb - t) <= 1.5 / clock.fps and lo - 1e-9 <= tb <= hi + 1e-9:
        return f"B{k}"
    return f"S+{max(0.0, t - shot_start):.3f}s"


def shot_moves(ref_shot: dict, our_start: float, our_end: float, clock: Clock, zoom: float = 1.0) -> list[dict]:
    rm = ref_shot["move"]
    if "axis" not in rm:
        return []   # still, or a shake (transferred as camera.shakes, see shot_shakes)
    r0, r1 = ref_shot["start"], ref_shot["end"]
    scale = (our_end - our_start) / max(1e-6, r1 - r0)
    main = {"start": rm["start"], "duration": rm["duration"], "amount": rm.get("move_amount", rm["amount"]), "ease": rm["ease"],
            "snap": rm.get("snap"), "axis": rm["axis"], "timing": rm.get("timing"), "which": "main",
            "cut_off": (bool(rm.get("cut_off")) or (rm.get("lead_in") or 0) > 0.05) and (rm.get("seen") or 0) > 0.05,
            "visible": rm.get("visible"), "seen": rm.get("seen"), "lead_in": rm.get("lead_in") or 0.0}
    if isinstance(main["ease"], dict):   # the chosen model's own window
        _, t0, d = ease_spec(main)
        if t0 is not None:
            main["start"] = max(r0, t0)   # where it is first on screen; lead_in says how long it had been moving
        if d:
            main["duration"] = d
    found = [m for m in sorted([main] + [{**o, "which": i} for i, o in enumerate(rm.get("other_moves") or [])], key=lambda m: m["start"])
             if _by(m["amount"], 1.0)]
    if not found:
        return []
    # where in the shot a move happens scales with the shot; how fast it moves (its duration) is kept when it fits
    # a much shorter shot keeps the biggest moves at ≤ 2× their speed instead of squeezing them all into whip pans
    kept = curves.moves_that_fit(found, our_end - our_start)
    dropped = [round(m["start"] - r0, 3) for m in found if m not in kept]
    found = kept
    room_of = curves.on_screen
    want = [our_start + (m["start"] - r0) * scale for m in found]
    # a move the reference's cut interrupts only needs room for what was on screen; the rest runs past our cut too
    room = [room_of(m) for m in found]
    starts, roomy, k = schedule(want, room, our_start, our_end)
    durs = [m["duration"] * k if m.get("cut_off") else d for m, d in zip(found, roomy)]
    frame = 1 / clock.fps
    moves = []
    for i, (m, t0, d) in enumerate(zip(found, starts, durs)):
        d = max(frame, math.floor(d * 1000) / 1000)          # round down: never spill past the next move or the cut
        hi = (starts[i + 1] if i + 1 < len(starts) else our_end) - (roomy[i] if m.get("cut_off") else d)
        lo = (starts[i - 1] + roomy[i - 1]) if i else our_start
        amount = m["amount"]
        if m.get("cut_off"):   # the amount seen is part of the whole move: the whole move is what we write
            amount = {ax: v / m["seen"] for ax, v in amount.items()}
        by = _by(amount, zoom)
        if "zoom" in by:
            zoom *= by["zoom"]
        ref_ease = m["ease"]["named"] if isinstance(m["ease"], dict) else m["ease"]
        src = {"shot": ref_shot["id"], "move": m["which"], "ease": ref_ease, "duration": round(m["duration"], 3)}
        if k < 1:
            src["compressed"] = round(k, 3)   # the plan's shot is shorter than the reference's moves: all sped up by 1/k
        if dropped and i == 0:
            src["left_out"] = dropped        # reference moves (seconds into its shot) this shorter shot has no room for
        lead = float(m.get("lead_in") or 0.0) * (k if m.get("cut_off") else 1.0)
        at = _at(t0, lo, hi, clock, our_start) if lead <= 1e-3 else f"S{t0 - lead - our_start:+.3f}s"   # it began before our cut in, too
        mv = {"at": at, "dur": f"{d:.3f}s", "by": by,
              "ease": ease_spec(m)[0] if isinstance(m["ease"], dict) else m["ease"], "from_ref": src}
        if m.get("cut_off"):
            mv["past_cut"] = True   # like the reference, a cut interrupts it: only part of it is on screen
            src["seen"] = m["seen"]
        moves.append(mv)
    return moves


def shot_shakes(ref_shot: dict, our_start: float, zoom: float = 1.0) -> list[dict]:
    sh = ref_shot["move"].get("shake")
    if not sh:
        return []
    # the score's shake jitters the frame position: express the measured swing as how far the picture edge moves
    edge = {"x": W / 2, "y": W / 2, "z": W / 4, "r": 540.0}[sh["axis"]]   # frame widths · W/2, log-zoom · W/4, radians · H/2
    return [{"at": f"S+{0.0:.3f}s", "amp": round(sh["swing"] * edge / zoom, 1), "decay": 3.0,
             "from_ref": {"shot": ref_shot["id"], "swing": sh["swing"], "axis": sh["axis"]}}]


def cadence_from(fp: dict) -> int:
    per = fp.get("cadence", {}).get("frames_per_drawing")
    return 1 if not per or per < 1.75 else 2 if per < 2.5 else 3


def from_reference(plan: dict, ref_fp: dict, bpm: float, offset: float = 0.0, fps: float = 24.0) -> dict:
    """A whole authored score (film + shots) from the plan's shot list and the reference fingerprint."""
    clock = Clock(bpm=bpm, offset=offset, fps=fps)
    from perception.fingerprint import reference_for
    timed = [s for s in plan.get("shots", []) if s.get("start_s") is not None and s.get("end_s") is not None]
    answers = reference_for(ref_fp, [(s["id"], ref_shot_id(s.get("ref_shot")), float(s["end_s"]) - float(s["start_s"])) for s in timed])
    cad = cadence_from(ref_fp)
    cues = {}
    for pk in plan.get("peaks") or []:
        if pk.get("id") and pk.get("hit_s") is not None:
            cues[f"{pk['id']}_hit"] = f"{float(pk['hit_s']):.3f}"
    shots = []
    for s in plan.get("shots", []):
        if s.get("start_s") is None or s.get("end_s") is None:
            continue
        a, b = float(s["start_s"]), float(s["end_s"])
        cam = s.get("camera") if isinstance(s.get("camera"), dict) else {}
        frm = cam.get("from") if isinstance(cam.get("from"), dict) else {}
        base = {k: float(frm[k]) for k in ("x", "y", "zoom") if isinstance(frm.get(k), (int, float))}
        if isinstance(frm.get("rot"), (int, float)):
            base["rot"] = math.radians(float(frm["rot"]))   # plans write roll in degrees
        shot = {"id": s["id"], "start": f"{a:.3f}", "end": f"{b:.3f}",   # cuts stay where the plan put them
                "ref_shot": ref_shot_id(s.get("ref_shot")), "cadence": cad, "camera": {"base": base, "moves": [], "shakes": []}}
        rs = answers.get(s["id"])
        if rs:
            shot["camera"]["moves"] = shot_moves(rs, a, b, clock, base.get("zoom", 1.0))
            shot["camera"]["shakes"] = shot_shakes(rs, a, base.get("zoom", 1.0))
            drift = _by(rs["move"].get("drift") or {}, base.get("zoom", 1.0))
            if drift:   # the slow push / pan under the whole reference shot (its pace per second kept: scaled to our length)
                k = (b - a) / max(1e-6, rs["end"] - rs["start"])
                drift = {ch: (round(v ** k, 4) if ch == "zoom" else round(v * k, 4 if ch == "rot" else 1)) for ch, v in drift.items()}
                shot["camera"]["drift"] = {"by": drift, "ease": "none", "from_ref": {"shot": rs["id"], "drift": rs["move"]["drift"]}}
        shots.append(shot)
    end = max((float(s["end_s"]) for s in plan.get("shots", []) if s.get("end_s") is not None), default=0.0)
    return {"version": 1, "fps": fps, "bpm": bpm, "offset": offset, "duration": float(plan.get("duration_s") or end), "cues": cues, "shots": shots}
