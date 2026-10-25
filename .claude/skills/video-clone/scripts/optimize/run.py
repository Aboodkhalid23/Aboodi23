"""Optimise a project's score against its reference, render-free (motion_score.py optimize).

Shots are independent for the camera objective, so each is searched on its own (few dimensions, fast convergence);
with --peaks, the shots around each plan peak are searched together, because the tension curve they shape is shared.
A group's result is kept only if it beats the author's version; the next group starts from the improved score.
"""
from __future__ import annotations

import json
import os
import time

import numpy as np

from perception import tension
from score import model

from . import cmaes
from .objective import Objective, audio_features, visual_features
from .space import Space


def _load(p: str):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def peak_targets(P: str, ref_fp: dict, plan: dict) -> list[dict]:
    """Each plan peak's hit time, with the shape of the reference peak it answers (from the reference tension curve)."""
    ref_peaks_p = os.path.join(P, "analysis", "peaks.json")
    agent_peaks = {p.get("id"): p for p in (_load(ref_peaks_p) if os.path.exists(ref_peaks_p) else [])}
    T = np.asarray(ref_fp["series"]["tension"], float)
    found = tension.describe_peaks(T, ref_fp["fps"], n=12, min_gap_s=1.0)
    for p in found:
        p["t"] += ref_fp["start"]
    out = []
    for pk in plan.get("peaks") or []:
        if pk.get("hit_s") is None:
            continue
        ref_hit = (agent_peaks.get(pk.get("ref_peak")) or {}).get("hit")
        cands = [q for q in found if ref_hit is None or abs(q["t"] - float(ref_hit)) <= 1.5]
        if not cands:
            continue
        ref = min(cands, key=lambda q: abs(q["t"] - float(ref_hit))) if ref_hit is not None else max(cands, key=lambda q: q["prominence"])
        out.append({"id": pk.get("id"), "t": float(pk["hit_s"]), "ref": ref})
    return out


def optimize_project(P: str, score_dir: str, *, shots: list[str] | None = None, budget: int = 240, peaks: bool = False,
                     tune_amounts: bool = False, seed: int = 0, log=print) -> dict:
    t_start = time.time()
    authored, origin = model.load(score_dir)
    resolved, diag = model.resolve_score(authored, origin)
    if not diag.ok:
        raise model.ScoreError(diag)
    from perception.cli import ensure_reference
    ref_fp = ensure_reference(P)
    plan = _load(os.path.join(P, "plan.json"))
    ref_ids = {s["id"] for s in ref_fp["shots"]}
    movable = [s["id"] for s in resolved["shots"] if s.get("ref_shot") in ref_ids and (s["camera"]["move_times"] or s["camera"]["shakes"])]
    shots = [s for s in (shots or movable) if s in {x["id"] for x in resolved["shots"]}]

    targets, audio, visual, hero = [], {}, {}, []
    if peaks:
        targets = peak_targets(P, ref_fp, plan)
        fps = float(resolved["fps"])
        n = int(round(float(resolved["duration"]) * fps))
        video = os.path.join(P, "out", "video.mp4")
        music = (plan.get("music") or {})
        if os.path.exists(video):
            audio = audio_features(video, n, fps)
        elif music.get("file"):
            audio = audio_features(os.path.join(P, music["file"]), n, fps, offset=float((music.get("section") or {}).get("start_s") or 0))
        fp_p = os.path.join(P, "out", "check", "fingerprint.json")
        visual = visual_features(_load(fp_p), n, fps) if os.path.exists(fp_p) else {}
        for tg in targets:
            for s in resolved["shots"]:
                if s["end"] > tg["t"] - 1.5 and s["start"] < tg["t"] + 1.0 and s["id"] not in hero:
                    hero.append(s["id"])
        log(f"peaks: {[(t['id'], t['t']) for t in targets]} → shots {hero}; audio {'yes' if audio else 'no'}, in-frame motion {'from the last render' if visual else 'none'}")

    groups = ([hero] if hero else []) + [[s] for s in shots if s not in hero]
    current, cur_res = authored, resolved
    report = {"groups": [], "changes": []}
    for g in groups:
        propose = {}
        if peaks and g is hero:
            for tg in targets:
                sh = next((s for s in cur_res["shots"] if s["start"] <= tg["t"] < s["end"]), None)
                if sh and not any(abs(x["t0"] - tg["t"]) < 0.2 for x in sh["camera"]["shakes"]):
                    propose.setdefault(sh["id"], []).append(tg["t"])
        space = Space(current, cur_res, g, tune_amounts=tune_amounts, propose_shakes=propose)
        if not space.params:
            continue
        obj = Objective(space, ref_fp, g, peaks=targets if g is hero else None, audio=audio, visual=visual)
        before = obj.evaluate(space.u0)
        res = cmaes.minimize(obj, space.u0, sigma0=0.15, budget=budget * (2 if g is hero else 1), seed=seed)
        after = obj.evaluate(res.x)
        kept = after["cost"] < before["cost"] - 0.5
        if kept:   # gate: the gain must hold measured the way a rendered film is (fitted eases, frames), not only on the search's fast path
            vb, va = obj.verified_camera_costs(space.u0), obj.verified_camera_costs(res.x)
            if vb is not None and va is not None and sum(va.values()) > sum(vb.values()) - 0.5 * len(va):
                kept = False
            after["verified"] = {"before": vb, "after": va}
        entry = {"shots": g, "dims": len(space.params), "evals": res.evals, "kept": kept,
                 "before": _brief(before), "after": _brief(after), "history": [round(h, 2) for h in res.history]}
        report["groups"].append(entry)
        log(f"{'+'.join(g)}: {len(space.params)} params, {res.evals} evals, cost {before['cost']:.1f} → {after['cost']:.1f}{'' if kept else ' (kept the original)'}")
        if kept:
            report["changes"] += space.changes(res.x)
            current = space.apply(res.x)
            cur_res, d = model.resolve_score(current)
    report["seconds"] = round(time.time() - t_start, 1)
    report["score"] = current
    return report


def _brief(ev: dict) -> dict:
    out = {"cost": round(ev["cost"], 2)}
    if "camera" in ev:
        out["camera"] = {k: round(v, 1) for k, v in ev["camera"].items()}
    if "peaks" in ev:
        out["peaks"] = [{"target": p["target"], "cost": p["cost"], "ours": p["ours"] and {k: p["ours"][k] for k in ("t", "breath_depth", "rise_frames", "prominence", "hold_s")},
                         "ref": {k: p["ref"][k] for k in ("t", "breath_depth", "rise_frames", "prominence", "hold_s")}} for p in ev["peaks"]]
    if "errors" in ev:
        out["errors"] = ev["errors"][:5]
    return out
