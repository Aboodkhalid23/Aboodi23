"""Stage 3: CMA-ES itself, the search space round trip, the one-sided peak cost, and the optimizer recovering a
reference camera from a deliberately wrong score — render-free."""
import json
import os

import numpy as np
import pytest

import synth
from optimize import cmaes
from optimize.objective import peak_cost
from optimize.run import optimize_project
from optimize.space import Space
from perception import curves, fingerprint
from score import model

FPS = 24


# ---------- CMA-ES ----------
def test_sphere_and_rosenbrock():
    sphere = lambda x: float(np.sum((x - 0.3) ** 2))
    r = cmaes.minimize(sphere, np.full(6, 0.8), sigma0=0.3, budget=1500, seed=1)
    assert r.f < 1e-6 and np.allclose(r.x, 0.3, atol=1e-3)
    rosen = lambda x: float(sum(100 * (4 * x[1:] - 2 - (4 * x[:-1] - 2) ** 2) ** 2 + (1 - (4 * x[:-1] - 2)) ** 2))   # min at x = 0.75
    r = cmaes.minimize(rosen, np.full(4, 0.2), sigma0=0.3, budget=6000, seed=2)
    assert r.f < 1e-4, r.f
    assert r.history == sorted(r.history, reverse=True)   # best-so-far never gets worse


def test_optimum_outside_the_box_ends_on_its_edge_and_runs_repeat():
    f = lambda x: float(np.sum((x - np.array([1.4, -0.3, 0.5])) ** 2))
    a = cmaes.minimize(f, np.full(3, 0.5), budget=900, seed=7)
    b = cmaes.minimize(f, np.full(3, 0.5), budget=900, seed=7)
    assert np.allclose(a.x, [1, 0, 0.5], atol=1e-3)
    assert np.array_equal(a.x, b.x) and a.f == b.f


# ---------- the search space ----------
AUTH = {"version": 1, "fps": FPS, "bpm": 120, "offset": 0.0, "duration": 4, "cues": {},
        "shots": [{"id": "S1", "start": 0, "end": 4, "ref_shot": 1, "camera": {"moves": [
            {"at": "B1", "dur": "1b", "by": {"zoom": 1.3}, "ease": "power3.out"},
            {"at": "B4", "dur": "0.8s", "by": {"x": 200}, "ease": {"spring": {"omega": 12, "zeta": 0.6}}}],
            "shakes": [{"at": "B6", "amp": 12, "decay": 8}]}}]}


def test_the_starting_point_writes_back_unchanged():
    r, d = model.resolve_score(AUTH)
    assert d.ok
    sp = Space(AUTH, r, ["S1"])
    kinds = [p.kind for p in sp.params]
    assert kinds == ["at", "dur", "bez0", "bez1", "bez2", "bez3", "at", "omega", "zeta", "amp", "decay"]
    assert sp.apply(sp.u0) == AUTH and sp.changes(sp.u0) == []


def test_a_changed_point_records_what_it_was_and_keeps_amounts():
    r, _ = model.resolve_score(AUTH)
    sp = Space(AUTH, r, ["S1"])
    u = sp.u0.copy()
    u[0] = 1.0   # start as late as allowed
    u[1] = 1.0   # twice as long
    out = sp.apply(u)["shots"][0]["camera"]["moves"][0]
    assert out["tuned"]["from"]["at"] == "B1" and out["by"] == {"zoom": 1.3}
    assert out["dur"] == "1.0000s"
    rr, d = model.resolve_score(sp.apply(u))
    assert d.ok and rr["shots"][0]["camera"]["move_times"][0][0] == pytest.approx(0.75, abs=1e-3)


def test_peak_cost_is_one_sided():
    ref = {"breath_depth": 0.3, "rise_frames": 3, "prominence": 0.4, "hold_s": 0.5}
    n = 6 * FPS
    T = np.full(n, 0.2)
    T[FPS:3 * FPS - 12] = 0.5                           # a build …
    T[3 * FPS - 12:3 * FPS] = 0.05                      # … a deep breath
    T[3 * FPS:3 * FPS + FPS] = 1.0                       # hits on one frame, holds a second
    T[3 * FPS + FPS:] = 0.2
    c, q = peak_cost(T, FPS, 3.0, ref)
    assert q is not None and c == pytest.approx(0.0, abs=0.5)   # better than the reference everywhere: free
    flat = np.full(n, 0.2)
    assert peak_cost(flat, FPS, 3.0, ref)[0] == 40.0


# ---------- the optimizer recovers the reference camera ----------
def test_optimizer_recovers_a_reference_move(tmp_path):
    """Reference: an expo.out push in 0.5 s starting at 0.2 s. The author wrote the right push but slow, late and
    linear. Optimising (render-free) must bring timing and shape back without touching the amount."""
    zoom = synth.move(72, 5, 12, curves.NAMED["expo.out"], 1.0, 1.3)
    ref_path = str(tmp_path / "ref.mp4")
    synth.render(ref_path, [synth.Cam(scale=z) for z in zoom], FPS)
    P = tmp_path / "proj"
    (P / "analysis").mkdir(parents=True)
    (P / "analysis" / "fingerprint.json").write_text(json.dumps(fingerprint.extract(ref_path, fps=FPS)))
    (P / "plan.json").write_text(json.dumps({"shots": [{"id": "S1", "start_s": 0, "end_s": 3, "ref_shot": 1}]}))
    wrong = {"version": 1, "fps": FPS, "bpm": 120, "offset": 0, "duration": 3, "cues": {}, "shots": [
        {"id": "S1", "start": "0", "end": "3", "ref_shot": 1, "camera": {"moves": [{"at": "S+0.4s", "dur": "1.1s", "by": {"zoom": 1.3}, "ease": "none"}]}}]}
    sdir = P / "build" / "score"
    os.makedirs(sdir / "shots")
    (sdir / "film.json").write_text(json.dumps({k: v for k, v in wrong.items() if k != "shots"}))
    (sdir / "shots" / "S1.json").write_text(json.dumps(wrong["shots"][0]))
    rep = optimize_project(str(P), str(sdir), budget=300, log=lambda *_: None)
    g = rep["groups"][0]
    assert g["kept"] and g["after"]["camera"]["S1"] < 0.35 * g["before"]["camera"]["S1"], g
    mv = rep["score"]["shots"][0]["camera"]["moves"][0]
    assert mv["by"] == {"zoom": 1.3}                        # framing intent untouched
    # the motion itself (5–95 % of the travel) now takes about as long as the reference's; the model's own duration may
    # stay longer with a curve that starts fast — that is the same motion
    from score import predict
    from score.runtime import Score
    r, d = model.resolve_score(rep["score"])
    ref_span = json.loads((P / "analysis" / "fingerprint.json").read_text())["shots"][0]["move"]["span90"]
    ours = predict.predicted_shots(Score(r))[0]["move"]
    assert ours["span90"] == pytest.approx(ref_span, rel=0.3), (ours["span90"], ref_span)
