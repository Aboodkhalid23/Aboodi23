"""Motion Score: load the authored score, check it, and resolve it to plain numbers for the runtimes.

Authored (what directors, builders and tools write), as one file or as a folder with one file per shot so parallel
builders never edit the same file:

    build/score/film.json        { "version": 1, "fps": 24, "bpm": 123.05, "offset": 0, "duration": 30,
                                   "cues": { "drop": "B28", "slap": "5.80" } }
    build/score/shots/S3.json    { "id": "S3", "start": "B8", "end": "B12", "ref_shot": 3, "cadence": 1,
                                   "camera": { "base": { "x": 960, "y": 540, "zoom": 1, "rot": 0 },
                                               "moves": [ { "at": "S+2f", "dur": "1b", "to": { "zoom": 1.2 }, "ease": "expo.out" },
                                                          { "at": "B10", "until": "E", "by": { "x": 60 }, "ease": { "bezier": [.4, 0, .2, 1] } } ],
                                               "shakes": [ { "at": "slap", "amp": 12, "decay": 12 } ] },
                                   "tracks": { "reach": { "base": 0, "moves": [ { "at": "B8", "dur": "3f", "to": 1, "ease": "power2.out" } ] } } }

A move marked "past_cut": true is meant to be interrupted by a cut — begun before the shot, or still going at its
end — as real footage often cuts mid-move.

Camera: world coordinates of a 1920×1080 stage; x, y = the world point at the centre of the frame, zoom = scale
(> 1 = pushed in), rot = roll in radians (+ = the image turns clockwise, as canvas rotate()). A move sets channels "to"
a value or changes them "by" an amount (zoom "by" multiplies: by 1.2 = a 20 % push). Moves on one channel run one after
the other; a spring may be interrupted by the next move. "drift" ({"by": {...}, "ease": "none"}) is a slow change over
the whole shot layered under the moves (zoom multiplies): the slow push a reference keeps going while it also does
quicker moves. Tracks are any other named numbers a shot animates.

Resolved (what score.js and runtime.py evaluate): every time in seconds, every move a segment
{ t0, t1, v0, v1, ease } per channel, in time order.
"""
from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, field

from perception.fingerprint import ref_shot_id

from . import eases
from .timeexpr import Clock, TimeError, resolve

VERSION = 1
CHANNELS = ("x", "y", "zoom", "rot")
DEFAULT_BASE = {"x": 960.0, "y": 540.0, "zoom": 1.0, "rot": 0.0}


@dataclass
class Diagnostics:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, where: str, msg: str):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str):
        self.warnings.append(f"{where}: {msg}")

    @property
    def ok(self) -> bool:
        return not self.errors


class ScoreError(ValueError):
    def __init__(self, diag: Diagnostics):
        super().__init__("\n".join(diag.errors))
        self.diag = diag


# ---------- loading ----------
def _read(p: str, label: str) -> dict:
    try:
        with open(p, encoding="utf-8-sig") as f:   # -sig: a byte-order mark from a Windows editor is not an error
            return json.load(f)
    except json.JSONDecodeError as e:
        d = Diagnostics()
        d.error(label, f"not valid JSON at line {e.lineno}, column {e.colno}: {e.msg} (no comments, trailing commas or single quotes)")
        raise ScoreError(d) from None


def load(path: str) -> tuple[dict, dict[str, str]]:
    """The authored score as one dict ({…film, "shots": [...]}) and where each shot came from (for messages)."""
    if os.path.isdir(path):
        film = _read(os.path.join(path, "film.json"), "film.json")
        shots, origin = [], {}
        for p in sorted(glob.glob(os.path.join(path, "shots", "*.json"))):
            rel = os.path.relpath(p, path).replace("\\", "/")
            s = _read(p, rel)
            shots.append(s)
            origin[str(s.get("id"))] = rel
        return {**film, "shots": shots}, origin
    score = _read(path, os.path.basename(path))
    return score, {str(s.get("id")): f"shots[{i}]" for i, s in enumerate(score.get("shots", []))}


def save_shot(path: str, shot: dict):
    """Write one shot file of a score folder (atomic: a builder reading it never sees half a file)."""
    p = os.path.join(path, "shots", f"{shot['id']}.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(shot, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


# ---------- resolving ----------
def _segments(moves: list, base: dict[str, float], channels: tuple[str, ...] | None, ctx, where: str, diag: Diagnostics,
              shot_span: tuple[float, float], times: list | None = None) -> dict[str, list[dict]]:
    """Moves → per-channel segments. ctx(expr, length) resolves a time inside this shot. `times`, if given, receives
    each move's resolved [t0, t1] by index (None where the move could not be read) — the optimizer edits moves by it."""
    segs: dict[str, list[dict]] = {}
    if times is not None:
        times[:] = [None] * len(moves or [])
    for i, mv in enumerate(moves or []):
        w = f"{where}.moves[{i}]"
        try:
            t0 = ctx(mv["at"], False)
        except (KeyError, TimeError) as e:
            diag.error(w + ".at", str(e) if isinstance(e, TimeError) else "missing")
            continue
        try:
            ease = eases.normalise(mv.get("ease"))
        except eases.EaseError as e:
            diag.error(w + ".ease", str(e))
            continue
        try:
            if "until" in mv:
                t1 = ctx(mv["until"], False)
            elif "dur" in mv:
                t1 = t0 + ctx(mv["dur"], True)
            elif ease["kind"] == "spring":
                t1 = t0 + eases.settle_time(ease)
            else:
                diag.error(w, "needs \"dur\" or \"until\" (only a spring may leave its length out)")
                continue
        except TimeError as e:
            diag.error(w + (".until" if "until" in mv else ".dur"), str(e))
            continue
        if t1 < t0:
            diag.error(w, f"ends ({t1:.3f}s) before it starts ({t0:.3f}s)")
            continue
        if (t0 < shot_span[0] - 1e-6 or t1 > shot_span[1] + 1e-6) and not mv.get("past_cut"):
            diag.warn(w, f"runs {t0:.3f}–{t1:.3f}s, outside the shot ({shot_span[0]:.3f}–{shot_span[1]:.3f}s)"
                         ' (if a cut is meant to interrupt it, mark it "past_cut": true)')
        if times is not None:
            times[i] = [round(t0, 6), round(t1, 6)]
        to, by = mv.get("to"), mv.get("by")
        if (to is None) == (by is None):
            diag.error(w, "needs exactly one of \"to\" or \"by\"")
            continue
        targets = (to if isinstance(to, dict) else {"value": to}) if to is not None else (by if isinstance(by, dict) else {"value": by})
        for ch, v in targets.items():
            if channels is not None and ch not in channels:
                diag.error(f"{w}.{'to' if to is not None else 'by'}.{ch}", f"unknown channel (camera has {', '.join(channels)})")
                continue
            prev = segs.setdefault(ch, [])
            if prev and prev[-1]["t1"] > t0 + 1e-9 and prev[-1]["ease"]["kind"] != "spring":
                diag.error(w, f"{ch} is still moving until {prev[-1]['t1']:.3f}s (moves[{prev[-1]['_i']}]); start at or after it")
                continue
            v0 = value_at(prev, base.get(ch, 0.0), t0)
            v1 = float(v) if to is not None else (v0 * float(v) if ch == "zoom" else v0 + float(v))
            if ch == "zoom" and v1 <= 0:
                diag.error(f"{w}.{ch}", f"zoom must stay > 0, got {v1}")
                continue
            prev.append({"t0": round(t0, 6), "t1": round(t1, 6), "v0": round(v0, 6), "v1": round(v1, 6), "ease": ease, "_i": i})
    for L in segs.values():
        for s in L:
            s.pop("_i", None)
    return segs


def value_at(segs: list[dict], base: float, t: float) -> float:
    """Channel value at t (the resolver needs it to know where a move starts from; runtime.py is the full evaluator)."""
    from .runtime import channel
    return channel(segs, base, t)


def resolve_score(score: dict, origin: dict[str, str] | None = None) -> tuple[dict, Diagnostics]:
    diag, origin = Diagnostics(), origin or {}
    if score.get("version", VERSION) != VERSION:
        diag.error("film", f"version {score.get('version')} is not supported (this tool reads {VERSION})")
    try:
        clock = Clock(bpm=float(score.get("bpm", 120)), offset=float(score.get("offset", 0)), fps=float(score.get("fps", 24)))
    except (TypeError, ValueError):
        diag.error("film", "bpm, offset and fps must be numbers")
        return {}, diag
    cues: dict[str, float] = {}
    for name, expr in (score.get("cues") or {}).items():   # in order: a cue may use the ones before it
        try:
            cues[name] = round(resolve(expr, clock, cues), 6)
        except TimeError as e:
            diag.error(f"film.cues.{name}", str(e))
    out_shots = []
    for s in score.get("shots", []):
        sid = str(s.get("id", "?"))
        where = origin.get(sid, sid)
        try:
            span = (resolve(s["start"], clock, cues), resolve(s["end"], clock, cues))
        except KeyError:
            diag.error(where, "needs \"start\" and \"end\"")
            continue
        except TimeError as e:
            diag.error(where, str(e))
            continue
        if span[1] <= span[0]:
            diag.error(where, f"ends ({span[1]:.3f}s) before it starts ({span[0]:.3f}s)")
            continue
        ctx = lambda expr, length, span=span: resolve(expr, clock, cues, span, length)
        cam = s.get("camera") or {}
        base = {**DEFAULT_BASE, **{k: float(v) for k, v in (cam.get("base") or {}).items() if k in CHANNELS}}
        for k in (cam.get("base") or {}):
            if k not in CHANNELS:
                diag.error(f"{where}.camera.base.{k}", f"unknown channel (camera has {', '.join(CHANNELS)})")
        move_times: list = []
        channels = _segments(cam.get("moves"), base, CHANNELS, ctx, f"{where}.camera", diag, span, move_times)
        shakes = []
        for i, sh in enumerate(cam.get("shakes") or []):
            try:
                shakes.append({"t0": round(ctx(sh["at"], False), 6), "amp": float(sh.get("amp", 10)), "decay": float(sh.get("decay", 10)),
                               "rate": float(sh.get("rate", clock.fps)), "seed": float(sh.get("seed", i))})
            except (KeyError, TimeError) as e:
                diag.error(f"{where}.camera.shakes[{i}]", str(e) if isinstance(e, TimeError) else "needs \"at\"")
        drift = None
        if cam.get("drift"):
            dr = cam["drift"]
            try:
                by = {k: float(v) for k, v in (dr.get("by") or {}).items()}
                bad = [k for k in by if k not in CHANNELS]
                if bad:
                    diag.error(f"{where}.camera.drift.by.{bad[0]}", f"unknown channel (camera has {', '.join(CHANNELS)})")
                elif by.get("zoom", 1.0) <= 0:
                    diag.error(f"{where}.camera.drift.by.zoom", "a zoom drift multiplies: it must be > 0")
                else:
                    drift = {"t0": round(span[0], 6), "t1": round(span[1], 6), "by": by, "ease": eases.normalise(dr.get("ease", "none"))}
            except (TypeError, ValueError):
                diag.error(f"{where}.camera.drift", "needs \"by\": {channel: number}")
            except eases.EaseError as e:
                diag.error(f"{where}.camera.drift.ease", str(e))
        tracks = {}
        for name, tr in (s.get("tracks") or {}).items():
            tb = float(tr.get("base", 0))
            tracks[name] = {"base": tb, "segs": _segments(tr.get("moves"), {"value": tb}, None, ctx, f"{where}.tracks.{name}", diag, span).get("value", [])}
        cad = int(s.get("cadence", 1))
        if cad not in (1, 2, 3, 4):
            diag.error(f"{where}.cadence", "must be 1, 2, 3 or 4 (frames each drawing is held)")
        out_shots.append({"id": sid, "start": round(span[0], 6), "end": round(span[1], 6), "ref_shot": ref_shot_id(s.get("ref_shot")), "cadence": cad,
                          "camera": {"base": base, "channels": channels, "shakes": shakes, "drift": drift, "move_times": move_times}, "tracks": tracks})
    out_shots.sort(key=lambda x: x["start"])
    for a, b in zip(out_shots, out_shots[1:]):
        gap = b["start"] - a["end"]
        if abs(gap) > 0.5 / clock.fps:
            diag.warn(f"{origin.get(b['id'], b['id'])}", f"{'gap' if gap > 0 else 'overlap'} of {abs(gap):.3f}s after {a['id']}")
    dur = float(score.get("duration", out_shots[-1]["end"] if out_shots else 0))
    if out_shots and out_shots[-1]["end"] > dur + 1e-6:
        diag.warn("film", f"the last shot ends at {out_shots[-1]['end']:.3f}s, after the film's duration {dur:.3f}s")
    ids = [s["id"] for s in out_shots]
    for d in {x for x in ids if ids.count(x) > 1}:
        diag.error("film", f"shot id {d!r} is used more than once")
    size = [int(v) for v in score.get("size", [1920, 1080])]
    return {"version": VERSION, "fps": clock.fps, "bpm": clock.bpm, "offset": clock.offset, "duration": dur, "size": size,
            "cues": cues, "shots": out_shots}, diag


def compile_path(path: str) -> dict:
    """Load + resolve, raising ScoreError with every problem listed when the score is not valid."""
    score, origin = load(path)
    resolved, diag = resolve_score(score, origin)
    if not diag.ok:
        raise ScoreError(diag)
    resolved["_warnings"] = diag.warnings
    return resolved

