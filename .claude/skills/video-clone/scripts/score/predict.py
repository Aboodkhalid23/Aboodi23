"""Predict what perception will measure for a score's camera — without rendering a frame.

The score fully determines the camera, and perception's camera model is the same similarity transform, so the
per-frame trajectory perception would recover can be computed directly:

    stage camera (cx, cy, zoom, rot), world → screen  s = C + zoom · R(rot) · (p − c)
    perception (frame widths / log scale / radians, camera terms):
        (x, y) += zoom · R(rot) · (Δcx, Δcy) / W      z = ln(zoom / zoom₀)      r = −(rot − rot₀)

(rot turns the image clockwise as canvas rotate() does; perception reports a clockwise *camera* roll as +, which turns
the image the other way.) The predicted trajectory goes through the same describe_shot() and is compared with the
reference shot by the same camera_pair() as a rendered film: the director sees "the push in S3 is 1.8× slower than ref
#4" before anything is built, and the optimizer (stage 3) can search camera parameters without rendering at all.
"""
from __future__ import annotations

import numpy as np

from perception import curves, distance

from .runtime import Score

W = 1920.0


def trajectory(score: Score, sid: str, fps: float | None = None) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    t, c = score.camera_series(sid, fps)
    z, rot = c["zoom"], c["rot"]
    dcx, dcy = np.r_[0.0, np.diff(c["x"])], np.r_[0.0, np.diff(c["y"])]
    mid = lambda v: np.r_[v[0], (v[1:] + v[:-1]) / 2]
    zm, rm = mid(z), mid(rot)
    # a world move seen through a rolled camera moves the picture along the rolled axes (screen = zoom · R(rot) · world)
    sx = zm * (np.cos(rm) * dcx - np.sin(rm) * dcy) / W
    sy = zm * (np.sin(rm) * dcx + np.cos(rm) * dcy) / W
    return t, {"x": np.cumsum(sx), "y": np.cumsum(sy), "z": np.log(z / z[0]), "r": -(rot - rot[0])}


def predicted_shots(score: Score) -> list[dict]:
    out = []
    for sid, s in score.shots.items():
        t, traj = trajectory(score, sid)
        if len(t) < 2:
            continue
        out.append({"id": sid, "ref_shot": s.get("ref_shot"), "start": s["start"], "end": s["end"], "move": curves.describe_shot(t, traj)})
    return out


def against_reference(score: Score, ref_fp: dict) -> dict:
    """Camera-only style distance of the score against the reference fingerprint, per mapped shot."""
    from perception.fingerprint import reference_for
    preds = predicted_shots(score)
    answers = reference_for(ref_fp, [(p["id"], p["ref_shot"], p["end"] - p["start"]) for p in sorted(preds, key=lambda p: p["start"])])
    shots, findings, scores = [], [], []
    for p in preds:
        rs = answers.get(p["id"])
        if rs is None:
            shots.append({"id": p["id"], "ref_shot": p["ref_shot"], "move": p["move"]["kind"], "note": "no reference shot mapped"})
            continue
        sc, detail, f = distance.camera_pair(rs, p)
        scores.append(sc)
        findings += f
        shots.append({"id": p["id"], "ref_shot": rs["id"], "score": sc, **detail})
    return {"camera_score": round(float(np.mean(scores)), 1) if scores else None, "shots": shots,
            "findings": sorted(findings, key=lambda x: x["severity"] != "major")}
