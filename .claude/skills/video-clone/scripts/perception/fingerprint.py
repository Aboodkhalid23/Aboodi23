"""Style Fingerprint: every measurable signal of one film on one frame clock.

    fp = extract("analysis/proxy.mp4", shots=report["shots"], audio="analysis/audio.wav", beats=report["audio"]["beats"])

One streaming pass over the frames computes camera motion, local motion, frame difference, the Lab colour of each frame
and a small descriptor; then per shot the camera trajectory is integrated and its move described (curves.py); then the
sound is folded in and the tension curve and its peaks are computed (tension.py), and the cut/beat phase (rhythm.py).
All times in the output are seconds on the video's own timeline.
"""
from __future__ import annotations

import math
import os
from typing import Iterable

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d

from . import camera, curves, look, rhythm, tension
from .video import extract_audio, frame_size, frames, probe, static_mask

VERSION = 15
DESC_FPS = 2.0            # frame descriptors per second
DESC_GRID = (8, 4)        # descriptor = this grid of Lab means → 96 numbers
THUMB_W = 96              # colour, difference and descriptors are measured on a thumbnail this wide


def _spans(shots: Iterable | None) -> list[dict] | None:
    """Accepts [[a, b], …] (analyze.py), [{"id", "start_s", "end_s"}, …] (plan.json) or [{"start", "end"}, …]."""
    if shots is None:
        return None
    out = []
    for k, s in enumerate(shots):
        if isinstance(s, dict):
            a, b = s.get("start_s", s.get("start")), s.get("end_s", s.get("end"))
            out.append({"id": s.get("id", k + 1), "start": float(a), "end": float(b)})
        else:
            out.append({"id": k + 1, "start": float(s[0]), "end": float(s[1])})
    return out


HOLD_DIFF = 0.004         # mean abs difference (0–1) below which a frame repeats the previous drawing
MAX_HOLD = 3              # a longer still stretch is the scene standing still, not a held drawing
CUT_SNAP = 3              # frames: a given cut this close to a detected one is that cut


def held_frames(diff: np.ndarray, cut_frames: list[int]) -> np.ndarray:
    """Frames that repeat the previous drawing inside motion — limited animation (on twos, threes) or a duplicated frame:
    runs of at most MAX_HOLD still frames with a *real* change on both sides. The first frame (nothing before it) and a
    cut (a change, but not motion) do not count as that change: a camera that rests three frames after a cut and then
    moves is resting, and spreading its first step back over the rest would start the move early."""
    still = diff < HOLD_DIFF
    moved = ~still
    moved[0] = False
    cuts = set(cut_frames)
    for f in cuts:
        moved[f] = False
    hold, n, k = np.zeros_like(still), len(diff), 1
    while k < n:
        if not still[k] or k in cuts:
            k += 1
            continue
        e = k
        while e + 1 < n and still[e + 1] and e + 1 not in cuts:
            e += 1
        if e - k + 1 <= MAX_HOLD and moved[k - 1] and e + 1 < n and moved[e + 1]:
            hold[k:e + 1] = True
        k = e + 1
    return hold


def spread_over_holds(delta: np.ndarray, hold: np.ndarray) -> np.ndarray:
    """Per-frame motion with each held run sharing the step that ends it (the trajectory itself is unchanged)."""
    out, n, k = delta.copy(), len(delta), 1
    while k < n:
        if not hold[k]:
            k += 1
            continue
        e = k
        while e + 1 < n and hold[e + 1]:
            e += 1
        if e + 1 < n:
            out[k:e + 2] = delta[k:e + 2].sum() / (e + 2 - k)
        k = e + 2
    return out


def cadence(diff: np.ndarray, hold: np.ndarray, cut_frames: list[int], fps: float) -> dict:
    """How many new drawings per second while things move: 'on ones' (every frame new), 'on twos' (each drawing held
    for two frames) … A strong style trait of 2D animation that no single frame shows."""
    moving = gaussian_filter1d(diff, 2.0) > 0.008
    moving[list(cut_frames)] = False
    if moving.sum() < fps / 2:
        return {"moving_frames": int(moving.sum())}
    ratio = float(hold[moving].mean())
    per = 1 / max(1e-6, 1 - ratio)   # frames each drawing stays on screen, on average
    label = "on ones" if per < 1.25 else "mixed ones and twos" if per < 1.75 else "on twos" if per < 2.5 else "on threes"
    return {"moving_frames": int(moving.sum()), "hold_ratio": round(ratio, 3), "frames_per_drawing": round(per, 2),
            "drawings_per_second": round(fps / per, 1), "label": label}


def extract(video: str, *, shots: Iterable | None = None, audio: str | None = None, beats: list[float] | None = None,
            fps: float = 24.0, width: int = 320, start: float = 0.0, end: float | None = None) -> dict:
    info = probe(video)
    end = info.duration if end is None else min(end, info.duration)
    spans = _spans(shots)
    if spans is not None:
        spans = [s for s in spans if s["end"] > start and s["start"] < end]
    # frame index where each given shot starts; cuts are detected anyway and the given ones snap to them (a plan's
    # times can be a frame off the real cut, and a step measured across a cut is a huge fake camera move)
    given_cuts = {max(0, round((s["start"] - start) * fps)) for s in (spans or [])} - {0}

    overlay = static_mask(video, frame_size(info, width), start, end)   # phone UI, watermark, letterbox: never tracked

    cols = {k: [] for k in ("dx", "dy", "dz", "dr", "local", "ok", "diff", "L", "a", "b")}
    desc, detected, frame_hists = [], [], []
    prev_gray = prev_hist = prev_thumb = None
    desc_every = max(1, round(fps / DESC_FPS))
    n = 0
    for i, bgr in enumerate(frames(video, fps=fps, width=width, start=start, end=end)):
        n = i + 1
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        th = cv2.resize(bgr, (THUMB_W, round(THUMB_W * bgr.shape[0] / bgr.shape[1])), interpolation=cv2.INTER_AREA)
        th_gray = cv2.cvtColor(th, cv2.COLOR_BGR2GRAY)
        hist = camera.hsv_hist(th)
        cut = prev_gray is not None and camera.looks_like_cut(prev_hist, hist, prev_thumb, th_gray)
        if cut:
            detected.append(i)
        step = camera.estimate(prev_gray, gray, overlay) if prev_gray is not None and not cut and i not in given_cuts else camera.Step()
        for k in ("dx", "dy", "dz", "dr", "local"):
            cols[k].append(getattr(step, k))
        cols["ok"].append(int(step.ok))
        cols["diff"].append(float(np.mean(cv2.absdiff(prev_thumb, th_gray))) / 255 if prev_thumb is not None else 0.0)
        lab = look.lab(th)
        for c, k in enumerate("Lab"):
            cols[k].append(float(lab[..., c].mean()))
        frame_hists.append(look.hist(lab))
        if i % desc_every == 0:
            g = cv2.resize(lab, DESC_GRID, interpolation=cv2.INTER_AREA) / np.array([100, 128, 128], np.float32)
            desc.append(g.ravel())
        prev_gray, prev_hist, prev_thumb = gray, hist, th_gray
    if n < 2:
        raise ValueError(f"no frames decoded from {video}")

    if spans is None:
        cut_frames = detected
    else:
        snap = lambda g: min((d for d in detected if abs(d - g) <= CUT_SNAP), key=lambda d: abs(d - g), default=g)
        cut_frames = sorted({snap(g) for g in given_cuts})
    for k in ("dx", "dy", "dz", "dr", "local"):   # no motion across any cut, given or found
        for f in set(detected) | set(cut_frames):
            cols[k][f] = 0.0
    S = {k: np.asarray(v, float) for k, v in cols.items()}
    t = start + np.arange(n) / fps
    hold = held_frames(S["diff"], sorted(set(detected) | set(cut_frames)))
    for k in ("dx", "dy", "dz", "dr", "local"):   # a held drawing moves nothing, the next one moves for both: share it out
        S[k] = spread_over_holds(S[k], hold)

    # ---------- shots: integrate the camera, describe the move ----------
    bounds = [0, *cut_frames, n]

    def shot_id(f0: int, f1: int, k: int):
        """The given shot that contains the middle of this frame range (keeps plan ids like "s3"), else its number."""
        mid = start + (f0 + f1) / 2 / fps
        return next((s["id"] for s in spans or [] if s["start"] <= mid < s["end"]), k + 1)

    shot_out = []
    for k, (f0, f1) in enumerate(zip(bounds, bounds[1:])):
        if f1 - f0 < 2:
            continue
        sl = slice(f0, f1)
        traj = {"x": S["dx"][sl], "y": S["dy"][sl], "z": S["dz"][sl], "r": S["dr"][sl]}
        traj = {a: np.cumsum(np.r_[0.0, v[1:]]) for a, v in traj.items()}   # first frame of a shot has no motion into it
        h = look.normalise(np.sum(frame_hists[f0:f1], axis=0))
        shot_out.append({
            "id": shot_id(f0, f1, k), "start": round(float(t[f0]), 3), "end": round(float(start + f1 / fps), 3),
            "move": curves.describe_shot(t[sl], traj),
            "local_motion": round(float(S["local"][sl].mean()), 5),
            "tracked": round(float(S["ok"][sl][1:].mean()) if f1 - f0 > 1 else 0.0, 3),
            "look": {"L": round(float(S["L"][sl].mean()), 2), "a": round(float(S["a"][sl].mean()), 2), "b": round(float(S["b"][sl].mean()), 2),
                     "hist": np.round(h, 4).tolist()},
        })

    # ---------- sound, tension, rhythm ----------
    tmp = None
    if audio is None and info.has_audio:
        audio = tmp = extract_audio(video)
    try:
        feats: dict[str, np.ndarray] = {}
        if audio and os.path.exists(audio):
            feats.update(tension.audio_features(audio, n, fps, t0=start))
            if beats is None:
                beats = tension.beats(audio)
    finally:
        if tmp:
            os.remove(tmp)
    speed = np.sqrt(S["dx"] ** 2 + S["dy"] ** 2 + S["dz"] ** 2 + S["dr"] ** 2) * fps
    feats.update({"camera": speed, "local": S["local"] * fps, "diff": S["diff"],
                  "cuts": tension.cut_density(cut_frames, n, fps), "flash": tension.flashes(S["L"] / 100, fps)})
    T = tension.curve(feats, fps)
    beats_in = [b for b in (beats or []) if start <= b <= end]
    peaks = tension.describe_peaks(T, fps, [b - start for b in beats_in])
    for p in peaks:
        p["t"] = round(p["t"] + start, 3)
    cut_times = [round(start + f / fps, 3) for f in cut_frames]

    r5 = lambda a: [round(float(x), 5) for x in a]
    return {
        "version": VERSION, "video": os.path.basename(video), "fps": fps, "start": round(start, 3), "end": round(float(start + n / fps), 3),
        "frames": n, "size": [info.width, info.height], "static_overlay": round(float((overlay == 0).mean()), 3) if overlay is not None else 0.0,
        "series": {"camera": {k: r5(S[k]) for k in ("dx", "dy", "dz", "dr")}, "tracked": S["ok"].astype(int).tolist(),
                   "local": r5(S["local"]), "diff": r5(S["diff"]), "lab": [r5(S["L"] / 100), r5(S["a"] / 128), r5(S["b"] / 128)],
                   "tension": r5(T), "features": sorted(k for k in feats if np.ptp(feats[k]) > 1e-9)},
        "cuts": cut_times, "beats": [round(float(b), 3) for b in beats_in],
        "shots": shot_out, "peaks": peaks, "rhythm": rhythm.cut_phase(cut_times, beats_in, fps), "cadence": cadence(S["diff"], hold, cut_frames, fps),
        "descriptors": {"fps": round(fps / desc_every, 3), "grid": list(DESC_GRID), "data": [[round(float(x), 3) for x in d] for d in desc]},
    }


def ref_shot_id(v) -> int | None:
    """A plan's ref_shot as the reference shot number: 6, "6" and "#6" all mean shot 6 (plans are written by agents)."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, str) and v.strip().lstrip("#").isdigit():
        return int(v.strip().lstrip("#"))
    return None


def describe_span(fp: dict, a: float, b: float, sid=None) -> dict:
    """A stretch of a fingerprint described like a shot: its camera move from the stored per-frame camera."""
    f0 = max(0, int(round((a - fp["start"]) * fp["fps"])))
    f1 = min(fp["frames"], int(round((b - fp["start"]) * fp["fps"])))
    c = {k: np.asarray(v[f0:f1], float) for k, v in fp["series"]["camera"].items()}
    t = fp["start"] + np.arange(f0, f1) / fp["fps"]
    traj = {ax: np.cumsum(np.r_[0.0, c[k][1:]]) for ax, k in (("x", "dx"), ("y", "dy"), ("z", "dz"), ("r", "dr"))} if f1 - f0 > 1 else None
    move = curves.describe_shot(t, traj) if traj else {"kind": ["static"], "amount": {x: 0.0 for x in curves.AXES}}
    return {"id": sid, "start": round(a, 3), "end": round(b, 3), "move": move}


def reference_for(ref_fp: dict, ours: list[tuple]) -> dict:
    """Our shot id → the reference shot it answers, from [(our id, ref shot id, our duration), …] in plan order.

    A plan often cuts one long reference take into several shots (a real run mapped four shots to one 12 s take, and
    every one of them was then given — and compared against — the whole take). Consecutive shots that share a
    reference shot each get their share of it, in order and in proportion to their length, re-described from the
    reference's per-frame camera; the look of the whole shot is kept. Used by the transfer, the comparison, the
    prediction and the optimizer alike, so they always agree on what a shot answers."""
    by = {s["id"]: s for s in ref_fp["shots"]}
    out, i = {}, 0
    while i < len(ours):
        j = i
        while j + 1 < len(ours) and ours[j + 1][1] is not None and ours[j + 1][1] == ours[i][1]:
            j += 1
        rs = by.get(ours[i][1])
        run = ours[i:j + 1]
        if rs is None:
            pass
        elif len(run) == 1:
            out[run[0][0]] = rs
        else:
            total = sum(max(1e-6, float(d or 0)) for _, _, d in run)
            a = rs["start"]
            for oid, _, d in run:
                b = a + (rs["end"] - rs["start"]) * max(1e-6, float(d or 0)) / total
                part = describe_span(ref_fp, a, b, rs["id"])
                out[oid] = {**rs, **part, "part_of": [rs["start"], rs["end"]]}
                a = b
        i = j + 1
    return out


def times(fp: dict) -> np.ndarray:
    return fp["start"] + np.arange(fp["frames"]) / fp["fps"]


def window(fp: dict, a: float, b: float) -> dict:
    """The part of a fingerprint between a and b seconds (shots, cuts, beats and peaks inside it; series cut to it)."""
    f0 = max(0, math.floor((a - fp["start"]) * fp["fps"]))
    f1 = min(fp["frames"], math.ceil((b - fp["start"]) * fp["fps"]))
    s = fp["series"]
    cut = lambda v: v[f0:f1]
    d = fp["descriptors"]
    d0, d1 = int(f0 / fp["fps"] * d["fps"]), int(math.ceil(f1 / fp["fps"] * d["fps"]))
    inside = lambda x: a <= x <= b
    new_start = fp["start"] + f0 / fp["fps"]
    cut_f = [round((c - new_start) * fp["fps"]) for c in fp["cuts"] if inside(c) and 0 < round((c - new_start) * fp["fps"]) < f1 - f0]
    diff = np.asarray(cut(s["diff"]), float)
    return {**fp, "cadence": cadence(diff, held_frames(diff, cut_f), cut_f, fp["fps"]) if len(diff) else {}, "start": round(fp["start"] + f0 / fp["fps"], 3), "end": round(fp["start"] + f1 / fp["fps"], 3), "frames": f1 - f0,
            "series": {**s, "camera": {k: cut(v) for k, v in s["camera"].items()}, "tracked": cut(s["tracked"]), "local": cut(s["local"]),
                       "diff": cut(s["diff"]), "lab": [cut(v) for v in s["lab"]], "tension": cut(s["tension"])},
            "cuts": [c for c in fp["cuts"] if inside(c)], "beats": [x for x in fp["beats"] if inside(x)],
            "shots": [x for x in fp["shots"] if x["end"] > a and x["start"] < b], "peaks": [p for p in fp["peaks"] if inside(p["t"])],
            "rhythm": rhythm.cut_phase([c for c in fp["cuts"] if inside(c)], [x for x in fp["beats"] if inside(x)], fp["fps"]),
            "descriptors": {**d, "data": d["data"][d0:d1]}}
