"""Motion Score: time expressions, resolving, the JS/Python runtimes agreeing, prediction matching measurement, and
motion transfer closing the loop (reference → measured → score → predicted ≈ reference)."""
import json
import math
import shutil
import subprocess

import numpy as np
import pytest

import synth
from perception import curves, fingerprint
from score import model, predict, transfer
from score.cli import RUNTIME_JS
from score.runtime import Score
from score.timeexpr import Clock, TimeError, resolve

FPS = 24
CLOCK = Clock(bpm=120, offset=0.1, fps=FPS)   # a beat is 0.5 s; beat n at 0.1 + n/2


# ---------- time expressions ----------
@pytest.mark.parametrize("expr, want", [("B4", 2.1), ("B4-2f", 2.1 - 2 / 24), ("B4+1b", 2.6), ("3.95", 3.95), ("3.95s", 3.95),
                                        ("drop+0.5s", 7.5), ("S+1b", 10.5), ("E-1f", 12 - 1 / 24)])
def test_instants(expr, want):
    assert resolve(expr, CLOCK, {"drop": 7.0}, (10.0, 12.0)) == pytest.approx(want)


def test_lengths_and_errors():
    assert resolve("1b-2f", CLOCK, length=True) == pytest.approx(0.5 - 2 / 24)
    for bad, kw in [("B4+B5", {}), ("2f", {}), ("B4", {"length": True}), ("nope", {}), ("S", {}), ("B4 2f", {})]:
        with pytest.raises(TimeError):
            resolve(bad, CLOCK, {"drop": 7.0}, **kw)


# ---------- resolving ----------
def film(*shots, cues=None):
    return {"version": 1, "fps": FPS, "bpm": 120, "offset": 0.1, "duration": 10, "cues": cues or {}, "shots": list(shots)}


def test_moves_chain_and_zoom_multiplies():
    r, d = model.resolve_score(film({"id": "A", "start": 0, "end": 4, "camera": {"base": {"zoom": 1.2}, "moves": [
        {"at": "S", "dur": "1b", "by": {"zoom": 1.5, "x": 100}, "ease": "power3.out"},
        {"at": "B2", "dur": "4f", "to": {"x": 0}, "ease": "hold"}]}}))
    assert d.ok, d.errors
    ch = r["shots"][0]["camera"]["channels"]
    assert ch["zoom"][0]["v0"] == 1.2 and ch["zoom"][0]["v1"] == pytest.approx(1.8)
    assert ch["x"][1]["v0"] == pytest.approx(1060) and ch["x"][1]["v1"] == 0
    s = Score(r)
    assert s.cam("A", 0.25)["zoom"] == pytest.approx(1.2 + 0.6 * curves.NAMED["power3.out"](np.asarray(0.5)))
    assert s.cam("A", 1.0)["x"] == pytest.approx(1060) and s.cam("A", 1.1 + 3 / 24)["x"] == pytest.approx(1060) and s.cam("A", 1.3)["x"] == 0


def test_problems_are_reported_with_their_place():
    _, d = model.resolve_score(film({"id": "A", "start": 0, "end": 2, "camera": {"moves": [
        {"at": "S", "dur": "1s", "to": {"x": 1}},
        {"at": "S+0.5s", "dur": "1s", "to": {"x": 2}},            # x still moving
        {"at": "S", "dur": "1s", "to": {"pan": 2}},               # no such channel
        {"at": "S", "to": {"y": 2}},                              # no length
        {"at": "S", "dur": "1s", "to": {"y": 2}, "ease": "wobbly"}]}}))
    text = "\n".join(d.errors)
    assert "A.camera.moves[1]: x is still moving" in text
    assert "moves[2].to.pan: unknown channel" in text
    assert "moves[3]: needs \"dur\" or \"until\"" in text
    assert "moves[4].ease: unknown ease 'wobbly'" in text


def test_a_spring_can_be_interrupted_and_gaps_warn():
    r, d = model.resolve_score(film({"id": "A", "start": 0, "end": 2, "camera": {"moves": [
        {"at": "S", "to": {"zoom": 1.3}, "ease": {"spring": {"omega": 14, "zeta": 0.3}}},
        {"at": "S+0.4s", "dur": "0.5s", "to": {"zoom": 1.0}}]}}, {"id": "B", "start": 2.5, "end": 3}))
    assert d.ok, d.errors
    assert any("gap of 0.500s after A" in w for w in d.warnings)
    z = r["shots"][0]["camera"]["channels"]["zoom"]
    assert z[1]["v0"] == pytest.approx(1 + 0.3 * curves.spring(np.asarray(0.4), 14, 0.3))   # starts from where the spring was


# ---------- the two runtimes agree ----------
EVERYTHING = film(
    {"id": "A", "start": "B0", "end": "B6", "cadence": 2, "camera": {"base": {"x": 900, "rot": 0.02}, "moves": [
        {"at": "S", "dur": "1b", "by": {"x": 120}, "ease": "expo.out"},
        {"at": "B1", "dur": "0.7s", "to": {"zoom": 1.4}, "ease": {"bezier": [0.16, 1, 0.3, 1]}},
        {"at": "B3", "to": {"rot": -0.05}, "ease": {"spring": {"omega": 20, "zeta": 0.35}}},
        {"at": "B2", "dur": "3f", "by": {"y": -40}, "ease": "back.out(2.2)"},
        {"at": "B4", "dur": "1b", "by": {"y": 40}, "ease": "sine.inOut"}],
        "shakes": [{"at": "hit", "amp": 14, "decay": 9}], "drift": {"by": {"zoom": 1.08, "x": -30}, "ease": "sine.inOut"}},
     "tracks": {"reach": {"base": 0, "moves": [{"at": "B1", "dur": "2f", "to": 1, "ease": "power2.out"}, {"at": "B2", "dur": "1b", "to": 0, "ease": "circ.in"}]}}},
    {"id": "B", "start": "B6", "end": 5, "camera": {"moves": [{"at": "S", "until": "E", "by": {"zoom": 0.8}, "ease": "power4.inOut"}]}},
    cues={"hit": "B5+1f"})


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_and_python_runtimes_agree(tmp_path):
    r, d = model.resolve_score(EVERYTHING)
    assert d.ok, d.errors
    times = [round(x, 4) for x in np.arange(0, 5, 1 / 48)]
    py = Score(r)
    want = {"A": [py.cam("A", t) for t in times], "B": [py.cam("B", t) for t in times],
            "reach": [py.track("A", "reach", t) for t in times], "held": [py.held("A", t) for t in times]}
    js = tmp_path / "eval.js"
    js.write_text(f"""
const Score = require({json.dumps(RUNTIME_JS)});
Score.load({json.dumps(r)});
const T = {json.dumps(times)};
const out = {{ A: T.map(t => Score.cam('A', t)), B: T.map(t => Score.cam('B', t)), reach: T.map(t => Score.track('A', 'reach', t)),
              held: T.map(t => Score.held('A', t)) }};
process.stdout.write(JSON.stringify(out));
""", encoding="utf-8")
    got = json.loads(subprocess.run(["node", str(js)], capture_output=True, text=True, check=True).stdout)
    for sid in ("A", "B"):
        for w, g in zip(want[sid], got[sid]):
            for k in ("x", "y", "zoom", "rot"):
                assert g[k] == pytest.approx(w[k], rel=1e-9, abs=1e-9), (sid, k)
    assert got["reach"] == pytest.approx(want["reach"], abs=1e-12)
    assert got["held"] == pytest.approx(want["held"], abs=1e-12)


def test_vectorised_evaluation_matches_the_scalar_twin():
    r, d = model.resolve_score(EVERYTHING)
    sc = Score(r)
    t = np.arange(0, 5, 1 / 96)
    for sid in ("A", "B"):
        v = sc.cam_array(sid, t)
        for i, x in enumerate(t):
            c = sc.cam(sid, float(x))
            for k in ("x", "y", "zoom", "rot"):
                assert v[k][i] == pytest.approx(c[k], rel=1e-12, abs=1e-12), (sid, k, x)


# ---------- prediction = measurement ----------
def _render_score(score: Score, sid: str, path: str):
    """Film the score's camera with the synthetic plate: stage px → frame widths, canvas roll → synth roll."""
    t, c = score.camera_series(sid, FPS)
    cams = [synth.Cam(x=(x - 960) / 1920, y=(y - 540) / 1920, scale=z, roll=-r) for x, y, z, r in zip(c["x"], c["y"], c["zoom"], c["rot"])]
    synth.render(path, cams, FPS)


def test_prediction_matches_what_perception_measures(tmp_path):
    r, d = model.resolve_score(film({"id": "A", "start": 0, "end": 3, "camera": {"moves": [
        {"at": "S+0.25s", "dur": "0.75s", "by": {"zoom": 1.3}, "ease": "power3.out"},
        {"at": "S+1.6s", "dur": "1s", "by": {"x": 300}, "ease": "sine.inOut"}]}}))
    assert d.ok
    sc = Score(r)
    path = str(tmp_path / "s.mp4")
    _render_score(sc, "A", path)
    measured = fingerprint.extract(path, fps=FPS)["shots"][0]["move"]
    predicted = predict.predicted_shots(sc)[0]["move"]
    assert set(measured["kind"]) == set(predicted["kind"]) == {"push_in", "move_right"}
    for ax in ("x", "z"):
        assert measured["amount"][ax] == pytest.approx(predicted["amount"][ax], rel=0.06)
    assert measured["duration"] == pytest.approx(predicted["duration"], rel=0.12)
    assert np.sqrt(np.mean((np.asarray(measured["progress"]) - np.asarray(predicted["progress"])) ** 2)) < 0.05


# ---------- motion transfer closes the loop ----------
def test_transfer_reproduces_the_reference_camera(tmp_path):
    """A 'reference' with a fast expo push then a slow pan: measure it, transfer it into a plan whose shot is a bit
    longer, and the predicted camera must match the reference move for move."""
    n = 72
    zoom = synth.move(n, 5, 12, curves.NAMED["expo.out"], 1.0, 1.35)
    pan = synth.move(n, 36, 30, curves.NAMED["sine.inOut"], 0.0, -0.2)
    ref_path = str(tmp_path / "ref.mp4")
    synth.render(ref_path, [synth.Cam(scale=z, x=x) for z, x in zip(zoom, pan)], FPS)
    ref = fingerprint.extract(ref_path, fps=FPS)
    plan = {"shots": [{"id": "S1", "start_s": 0.0, "end_s": 3.5, "ref_shot": 1}]}
    authored = transfer.from_reference(plan, ref, bpm=120, offset=0.0)
    moves = authored["shots"][0]["camera"]["moves"]
    assert len(moves) == 2 and "zoom" in moves[0]["by"] and "x" in moves[1]["by"]
    r, d = model.resolve_score(authored)
    assert d.ok, d.errors
    res = predict.against_reference(Score(r), ref)
    assert res["camera_score"] > 80, res
    assert not [f for f in res["findings"] if f["severity"] == "major"], res["findings"]


def test_a_slow_drift_under_a_quick_move_is_transferred(tmp_path):
    """Reference: a slow push through the whole shot plus a quick pan in the middle. Segmentation alone keeps the pan
    and loses most of the push (seen on a real reference); the drift must carry it over."""
    n = 96
    zoom = [1.0 + 0.2 * f / (n - 1) for f in range(n)]                        # +20 % over 4 s, linear
    pan = synth.move(n, 40, 10, curves.NAMED["power2.inOut"], 0.0, 0.2)
    ref_path = str(tmp_path / "ref.mp4")
    synth.render(ref_path, [synth.Cam(scale=z, x=x) for z, x in zip(zoom, pan)], FPS)
    ref = fingerprint.extract(ref_path, fps=FPS)
    m = ref["shots"][0]["move"]
    assert "drift" in m and m["drift"]["z"] == pytest.approx(math.log(1.2), rel=0.25), m.get("drift")
    authored = transfer.from_reference({"shots": [{"id": "S1", "start_s": 0, "end_s": 4, "ref_shot": 1}]}, ref, bpm=120)
    assert "drift" in authored["shots"][0]["camera"]
    r, d = model.resolve_score(authored)
    assert d.ok, d.errors
    p = predict.predicted_shots(Score(r))[0]["move"]
    assert p["amount"]["z"] == pytest.approx(m["amount"]["z"], rel=0.1) and p["amount"]["x"] == pytest.approx(m["amount"]["x"], rel=0.1)


def test_a_hand_edited_shot_file_that_is_not_json_is_named(tmp_path):
    d = tmp_path / "score"
    (d / "shots").mkdir(parents=True)
    (d / "film.json").write_text("﻿" + json.dumps({"version": 1, "bpm": 120}), encoding="utf-8")   # BOM: fine
    (d / "shots" / "S3.json").write_text('{ "id": "S3", "start": 0, "end": 1, }', encoding="utf-8")
    with pytest.raises(model.ScoreError) as e:
        model.load(str(d))
    assert "shots/S3.json: not valid JSON at line 1" in str(e.value)


def test_a_much_shorter_shot_keeps_the_biggest_moves_at_their_pace():
    """Twelve seconds of slow moves into a two-second shot: keep the biggest, at ≤ 2× speed — not every move as a whip."""
    t = np.arange(12 * FPS) / FPS
    sine = curves.NAMED["sine.inOut"]
    y = 0.15 * sine(np.clip(t / 3, 0, 1)) - 0.06 * sine(np.clip((t - 4) / 3, 0, 1)) + 0.03 * sine(np.clip((t - 8) / 3, 0, 1))
    traj = {"x": np.zeros_like(t), "y": y, "z": np.zeros_like(t), "r": np.zeros_like(t)}
    ref = {"shots": [{"id": 1, "start": 0.0, "end": 12.0, "move": curves.describe_shot(t, traj)}], "cadence": {}}
    moves = transfer.shot_moves(ref["shots"][0], 0.0, 2.0, CLOCK)
    assert len(moves) == 1 and moves[0]["by"]["y"] > 0                      # the big first move down
    assert float(moves[0]["dur"][:-1]) >= 0.5 * 3 * 0.9                     # at no more than ~2× its speed
    assert moves[0]["from_ref"].get("left_out")


def test_shots_sharing_one_long_reference_take_each_get_their_part(tmp_path):
    """A real plan cut one 12 s reference take into four shots and every shot got the take's moves. Three shots on one
    9 s take with a pan only in its middle third: only the middle shot pans, and each is compared with its part."""
    n = 9 * FPS
    pan = synth.move(n, 3 * FPS + 6, 2 * FPS, curves.NAMED["sine.inOut"], 0.0, 0.25)
    path = str(tmp_path / "take.mp4")
    synth.render(path, [synth.Cam(x=x) for x in pan], FPS)
    ref = fingerprint.extract(path, fps=FPS)
    plan = {"shots": [{"id": f"S{i + 1}", "start_s": 2.0 * i, "end_s": 2.0 * (i + 1), "ref_shot": 1} for i in range(3)]}
    moves = {s["id"]: s["camera"]["moves"] for s in transfer.from_reference(plan, ref, bpm=120)["shots"]}
    assert not moves["S1"] and not moves["S3"], moves
    assert moves["S2"] and moves["S2"][0]["by"].get("x", 0) > 0
    r, d = model.resolve_score(transfer.from_reference(plan, ref, bpm=120))
    res = predict.against_reference(Score(r), ref)
    assert all(s.get("score", 100) > 80 for s in res["shots"]), res["shots"]
