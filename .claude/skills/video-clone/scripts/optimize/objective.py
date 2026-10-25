"""What the optimizer minimises, computed without rendering.

    cost = Σ_shots camera_cost(shot)            100 − camera_pair score against the mapped reference shot
         + w_peaks · Σ_peaks peak_cost(peak)     predicted tension around each plan peak vs the reference's peak shape
         + w_reg · ‖u − u₀‖²                      stay near what the director wrote
         + penalties                             a score that no longer resolves, moves pushed outside their shot

Predicted tension is multi-fidelity: the sound is the film's own (fixed), camera speed and cuts come exactly from the
score, and in-frame motion (local motion, frame difference, flashes) comes from the last render's fingerprint when
there is one — the optimizer moves the camera, not the characters, so those stay as measured.

The peak cost is one-sided: a breath deeper than the reference's, a hit that lands faster, a peak that stands out more
cost nothing. The goal is to beat the reference at its best moment, not to copy its numbers.
"""
from __future__ import annotations

import os
import subprocess
import tempfile

import numpy as np

from perception import curves, distance, tension
from perception.video import ensure_ffmpeg
from score import model, predict
from score.runtime import Score

from .space import Space

W = 1920.0


# ---------- predicted tension ----------
def audio_features(path: str | None, n: int, fps: float, offset: float = 0.0) -> dict[str, np.ndarray]:
    """Loudness and flux of the film's sound; `offset` = where the film starts in the file (a song's chosen section)."""
    if not path or not os.path.exists(path):
        return {}
    ensure_ffmpeg()
    fd, wav = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "22050", wav], capture_output=True)
        return tension.audio_features(wav, n, fps, t0=offset) if r.returncode == 0 else {}
    finally:
        os.remove(wav)


def visual_features(fp: dict | None, n: int, fps: float) -> dict[str, np.ndarray]:
    """In-frame motion from the last render, resampled to n frames from 0 s."""
    if not fp:
        return {}
    s = fp["series"]
    t_src = fp["start"] + np.arange(fp["frames"]) / fp["fps"]
    t = np.arange(n) / fps
    get = lambda v: np.interp(t, t_src, np.asarray(v, float))
    return {"local": get(s["local"]) * fp["fps"], "diff": get(s["diff"]), "flash": tension.flashes(get(s["lab"][0]), fps)}


def camera_speed(score: Score, n: int, fps: float) -> tuple[np.ndarray, list[int]]:
    """Per-frame camera speed in perception units, and the frames where a new shot starts."""
    speed, cuts = np.zeros(n), []
    shots = sorted(score.shots.values(), key=lambda s: s["start"])
    for k, s in enumerate(shots):
        f0, f1 = int(round(s["start"] * fps)), min(n, int(round(s["end"] * fps)))
        if f1 - f0 < 2:
            continue
        if k:
            cuts.append(f0)
        t, traj = predict.trajectory(score, s["id"])
        m = min(len(t), f1 - f0)
        d = np.sqrt(sum(np.diff(traj[a][:m], prepend=traj[a][0]) ** 2 for a in ("x", "y", "z", "r"))) * fps
        speed[f0:f0 + m] = d
    return speed, cuts


def predicted_tension(score: Score, n: int, fps: float, audio: dict, visual: dict) -> np.ndarray:
    speed, cuts = camera_speed(score, n, fps)
    return tension.curve({**audio, **visual, "camera": speed, "cuts": tension.cut_density(cuts, n, fps)}, fps)


def peak_cost(T: np.ndarray, fps: float, target_t: float, ref: dict) -> tuple[float, dict | None]:
    """One-sided distance from our predicted peak near target_t to the reference peak's shape."""
    ours = [p for p in tension.describe_peaks(T, fps, n=8, min_gap_s=1.0) if abs(p["t"] - target_t) <= 1.0]
    if not ours:
        return 40.0, None
    q = min(ours, key=lambda p: abs(p["t"] - target_t))
    c = (20 * abs(q["t"] - target_t)
         + 60 * max(0.0, ref["breath_depth"] - q["breath_depth"])
         + 2.0 * max(0, q["rise_frames"] - ref["rise_frames"])
         + 60 * max(0.0, ref["prominence"] - q["prominence"])
         + 15 * max(0.0, ref["hold_s"] - q["hold_s"]))
    return float(c), q


# ---------- the objective ----------
class Objective:
    def __init__(self, space: Space, ref_fp: dict, shots: list[str], *, w_reg: float = 30.0,
                 peaks: list[dict] | None = None, w_peaks: float = 1.0, audio: dict | None = None, visual: dict | None = None):
        self.space, self.shots = space, shots
        from perception.fingerprint import reference_for
        ordered = sorted(space.resolved["shots"], key=lambda s: s["start"])
        self.ref_shots = reference_for(ref_fp, [(s["id"], s.get("ref_shot"), s["end"] - s["start"]) for s in ordered])   # by OUR shot id
        self.w_reg, self.peaks, self.w_peaks = w_reg, peaks or [], w_peaks
        self.audio, self.visual = audio or {}, visual or {}
        self.u0 = space.u0
        self.evals = 0

    def verified_camera_costs(self, u: np.ndarray) -> dict[str, float] | None:
        """The camera cost the way a rendered film is measured (ease fits, frame sampling), for the final check: the
        search reads shapes straight off the exact curve, which can reward a curve no fitted model describes."""
        r, diag = model.resolve_score(self.space.apply(u))
        if not diag.ok:
            return None
        score, out = Score(r), {}
        for p in predict.predicted_shots(score):
            rs = self.ref_shots.get(p["id"])
            if p["id"] in self.shots and rs is not None:
                out[p["id"]] = 100.0 - distance.camera_pair(rs, p)[0]
        return out

    def camera_costs(self, score: Score) -> dict[str, float]:
        out = {}
        for sid in self.shots:
            s = score.shots[sid]
            rs = self.ref_shots.get(sid)
            if rs is None:
                continue
            # exact and 10× finer than the frames: read the shape off the curve, no fitting (≈ 100× faster)
            t, traj = predict.trajectory(score, sid, 10 * float(score.r["fps"]))
            if len(t) < 2:
                continue
            sc, _, _ = distance.camera_pair(rs, {"id": sid, "start": s["start"], "end": s["end"], "move": curves.describe_shot(t, traj, fit=False)})
            out[sid] = 100.0 - sc
        return out

    def evaluate(self, u: np.ndarray) -> dict:
        authored = self.space.apply(u)
        r, diag = model.resolve_score(authored)
        if not diag.ok:
            return {"cost": 1000.0 + 50 * len(diag.errors), "errors": diag.errors}
        outside = sum(1 for w in diag.warnings if "outside the shot" in w and any(w.startswith(f"{sid}.") for sid in self.shots))
        score = Score(r)
        cam = self.camera_costs(score)
        out = {"camera": cam, "camera_cost": float(sum(cam.values())), "outside": outside}
        cost = out["camera_cost"] + 25.0 * outside + self.w_reg * float(np.sum((u - self.u0) ** 2))
        if self.peaks:
            fps = float(r["fps"])
            n = int(round(float(r["duration"]) * fps))
            T = predicted_tension(score, n, fps, self.audio, self.visual)
            pk = [peak_cost(T, fps, p["t"], p["ref"]) for p in self.peaks]
            out["peaks"] = [{"target": p["t"], "cost": round(c, 2), "ours": q, "ref": p["ref"]} for p, (c, q) in zip(self.peaks, pk)]
            cost += self.w_peaks * sum(c for c, _ in pk)
        out["cost"] = float(cost)
        return out

    def __call__(self, u: np.ndarray) -> float:
        self.evals += 1
        return self.evaluate(u)["cost"]
