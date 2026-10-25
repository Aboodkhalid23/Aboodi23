"""Command line for perception (run through scripts/fingerprint.py).

    fingerprint.py extract <video> --out fp.json [--shots report.json|plan.json] [--audio a.wav] [--plot fp.png]
    fingerprint.py compare <ref_fp.json> <our_fp.json> --out style_distance.json [--plan plan.json] [--window a:b] [--plot overlay.png]
    fingerprint.py plan-check <projects/id>
        before building: the plan's cutting against the stretch of reference it clones (slower is flagged, faster is
        the brief's call), and which shots are too short for the reference camera movement they answer
    fingerprint.py project <projects/id> [--video out/video.mp4]
        reference fingerprint (analysis/fingerprint.json, made if missing) + ours (out/check/fingerprint.json)
        + out/check/style_distance.json + out/check/fingerprint_overlay.png, and the findings printed
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import curves, distance, fingerprint, plot


def _load(p: str):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _save(obj, p: str):
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def _shots_from(path: str | None):
    if not path:
        return None
    j = _load(path)
    return j.get("shots") if isinstance(j, dict) else j


def reference(analysis: str, report: dict | None = None) -> dict:
    """Fingerprint of the analysed reference, using analyze.py's cuts and beats (one source of truth for both)."""
    report = report or _load(os.path.join(analysis, "report.json"))
    video = os.path.join(analysis, report.get("analysed") or "source.mp4")
    wav = os.path.join(analysis, "audio.wav")
    au = report.get("audio") or {}
    return fingerprint.extract(video, shots=report.get("shots") or None, audio=wav if os.path.exists(wav) else None,
                               beats=au.get("beats") if au.get("beats") else None)


def ensure_reference(P: str) -> dict:
    """The project's reference fingerprint, made (or remade) when missing or written by an older version of this code:
    projects analysed before perception existed, or before its last change, work without re-running analyze.py."""
    an = os.path.join(P, "analysis")
    ref_p = os.path.join(an, "fingerprint.json")
    if os.path.exists(ref_p):
        ref = _load(ref_p)
        if ref.get("version") == fingerprint.VERSION:
            return ref
    ref = reference(an)
    _save(ref, ref_p)
    plot.single(ref, os.path.join(an, "fingerprint.png"))
    return ref


def pairs_from_plan(plan: dict) -> list[dict]:
    return [{"id": s["id"], "ref_shot": fingerprint.ref_shot_id(s.get("ref_shot"))} for s in plan.get("shots", [])
            if s.get("id") is not None and fingerprint.ref_shot_id(s.get("ref_shot")) is not None]


def project(P: str, video: str = "out/video.mp4") -> dict:
    chk = os.path.join(P, "out", "check")
    ref = ensure_reference(P)
    plan = _load(os.path.join(P, "plan.json"))
    shots = [s for s in plan.get("shots", []) if s.get("start_s") is not None and s.get("end_s") is not None]
    ours = fingerprint.extract(os.path.join(P, video), shots=shots or None)
    _save(ours, os.path.join(chk, "fingerprint.json"))
    sd = distance.style_distance(ref, ours, pairs_from_plan(plan))
    _save(sd, os.path.join(chk, "style_distance.json"))
    R = fingerprint.window(ref, *sd["ref_window"]) if sd["ref_window"] else ref
    _, _, mapping = distance.tension_component(R, ours)
    plot.overlay(R, ours, mapping, os.path.join(chk, "fingerprint_overlay.png"))
    return sd


def plan_check(P: str) -> dict:
    """How the plan's cutting compares with the stretch of reference it clones, before anything is built: too slow is
    flagged; faster is reported (with shots too short for the reference's camera movement, whose moves get sped up or
    left out) but left to the brief — the picture should change at least as often as the reference's does."""
    plan, ref = _load(os.path.join(P, "plan.json")), ensure_reference(P)
    shots = [s for s in plan.get("shots", []) if s.get("start_s") is not None and s.get("end_s") is not None]
    answers = fingerprint.reference_for(ref, [(s.get("id"), fingerprint.ref_shot_id(s.get("ref_shot")), float(s["end_s"]) - float(s["start_s"]))
                                              for s in shots])
    mapped = [(s, answers.get(s.get("id"))) for s in shots]
    refs_used = [r for _, r in mapped if r is not None]
    if not shots or not refs_used:
        return {"ok": True, "note": "no shots mapped to the reference"}
    a = min((r.get("part_of") or [r["start"]])[0] for r in refs_used)
    b = max((r.get("part_of") or [0, r["end"]])[1] for r in refs_used)
    R = fingerprint.window(ref, a, b)
    ours_len = max(float(s["end_s"]) for s in shots) - min(float(s["start_s"]) for s in shots)
    ref_rate = len(R["cuts"]) / max(1e-6, R["end"] - R["start"]) * 10
    our_rate = (len(shots) - 1) / max(1e-6, ours_len) * 10
    squeezed = []
    for s, r in mapped:
        if r is None:
            continue
        mv = r["move"]
        moving = curves.on_screen(mv) + sum(float(o.get("duration") or 0) for o in mv.get("other_moves") or [])
        length = float(s["end_s"]) - float(s["start_s"])
        if moving > 0 and length < curves.MIN_PACE * moving:
            squeezed.append({"shot": s.get("id"), "ref_shot": r["id"], "shot_s": round(length, 2), "ref_moving_s": round(moving, 2)})
    ratio = our_rate / ref_rate if ref_rate > 0 else None
    # Only *slower* than the reference is a problem. An A/B run showed the other side: held to the reference's hard-cut
    # count, a plan went from 14 shots to 8 and lost variety — the reference changes scene inside its shots (curtains,
    # smoke, an iris), so its cuts undercount how often the picture changes. Faster cutting is the brief's call.
    return {"ok": ratio is None or ratio >= 1 / 1.3, "cuts_per_10s": {"plan": round(our_rate, 2), "reference": round(ref_rate, 2)},
            "ratio": round(ratio, 2) if ratio else None, "ref_window": [round(a, 2), round(b, 2)], "squeezed": squeezed}


def report(sd: dict) -> str:
    c = sd["components"]
    lines = [f"style distance: overall {sd['overall']}  = style {sd['style']} (looks and moves like it) + structure {sd['structure']} "
             f"(follows its arc)  (ref window {sd['ref_window']})",
             "  " + "  ".join(f"{k} {c[k]['score'] if c[k].get('score') is not None else '-'}" for k in distance.WEIGHTS)]
    lines += [f"  [{f['severity']}] {f['component']} {f['where']}: {f['text']}" for f in sd["findings"]]
    return "\n".join(lines)


def main(argv: list[str] | None = None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="fingerprint.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("video")
    e.add_argument("--out", required=True)
    e.add_argument("--shots", help="report.json (analyze.py) or plan.json: use these shot boundaries instead of detecting cuts")
    e.add_argument("--audio")
    e.add_argument("--fps", type=float, default=24.0)
    e.add_argument("--start", type=float, default=0.0)
    e.add_argument("--end", type=float)
    e.add_argument("--plot")
    c = sub.add_parser("compare")
    c.add_argument("ref")
    c.add_argument("ours")
    c.add_argument("--out", required=True)
    c.add_argument("--plan")
    c.add_argument("--window", help="a:b seconds of the reference")
    c.add_argument("--plot")
    pc = sub.add_parser("plan-check")
    pc.add_argument("dir")
    p = sub.add_parser("project")
    p.add_argument("dir")
    p.add_argument("--video", default="out/video.mp4")
    a = ap.parse_args(argv)

    if a.cmd == "extract":
        fp = fingerprint.extract(a.video, shots=_shots_from(a.shots), audio=a.audio, fps=a.fps, start=a.start, end=a.end)
        _save(fp, a.out)
        if a.plot:
            plot.single(fp, a.plot)
        print(f"{len(fp['shots'])} shots, {len(fp['cuts'])} cuts, peaks at {[p['t'] for p in fp['peaks']]} → {a.out}")
    elif a.cmd == "compare":
        ref, ours = _load(a.ref), _load(a.ours)
        win = tuple(map(float, a.window.split(":"))) if a.window else None
        sd = distance.style_distance(ref, ours, pairs_from_plan(_load(a.plan)) if a.plan else None, win)
        _save(sd, a.out)
        if a.plot:
            R = fingerprint.window(ref, *sd["ref_window"]) if sd["ref_window"] else ref
            plot.overlay(R, ours, distance.tension_component(R, ours)[2], a.plot)
        print(report(sd))
    elif a.cmd == "plan-check":
        r = plan_check(a.dir)
        if "cuts_per_10s" in r:
            c = r["cuts_per_10s"]
            verdict = "slower than the reference: add cuts or in-shot scene changes" if not r["ok"] else "ok" if r["ratio"] <= 1.3 else "faster than the reference: fine when the brief asks for energy"
            print(f"cutting: plan {c['plan']} cuts / 10 s, reference {c['reference']} hard cuts (×{r['ratio']}) — {verdict}")
        for q in r.get("squeezed", []):
            print(f"  note {q['shot']}: {q['shot_s']} s for ref #{q['ref_shot']}'s {q['ref_moving_s']} s of camera movement — the transfer will keep its biggest moves")
        if "note" in r:
            print(r["note"])
    else:
        print(report(project(a.dir, a.video)))
