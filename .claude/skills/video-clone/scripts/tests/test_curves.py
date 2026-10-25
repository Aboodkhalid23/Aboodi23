"""Easing recovery on analytic trajectories: the timed fit must find start, duration, amount and shape."""
import numpy as np
import pytest

from perception import curves

FPS = 24


def canonical(name):
    """The ease's own curve in the same 5–95 % travel window perception compares moves on."""
    u = np.linspace(0, 1, 2001)
    return curves.canonical_progress(u, curves.NAMED[name](u))[2]


def trajectory(ease, t0=0.5, dur=1.0, amount=0.3, total=3.0, noise=0.0, seed=0):
    t = np.arange(int(total * FPS)) / FPS
    x = amount * ease(np.clip((t - t0) / dur, 0, 1))
    if noise:
        x = x + np.random.default_rng(seed).normal(0, noise, len(x))
    return t, {"x": x - x[0], "y": np.zeros_like(t), "z": np.zeros_like(t), "r": np.zeros_like(t)}


@pytest.mark.parametrize("name", ["power3.out", "power2.inOut", "expo.out", "sine.inOut", "back.out", "none"])
def test_named_ease_is_recovered(name):
    t, traj = trajectory(curves.NAMED[name])
    m = curves.describe_move(t, traj)
    assert m["kind"] == ["move_right"]
    assert m["ease"]["named"] == name or m["ease"]["named_rmse"] < 0.01
    assert m["start"] == pytest.approx(0.5, abs=0.05)
    assert m["duration"] == pytest.approx(1.0, rel=0.08)


def test_long_tail_ease_keeps_its_tail():
    """power3.out spends its last quarter almost still; a speed-threshold window would cut it off and call it shorter."""
    t, traj = trajectory(curves.NAMED["power3.out"], dur=1.2)
    m = curves.describe_move(t, traj)
    assert m["duration"] == pytest.approx(1.2, rel=0.08)
    truth = canonical("power3.out")
    assert np.sqrt(np.mean((np.asarray(m["progress"]) - truth) ** 2)) < 0.03


def test_bezier_matches_a_css_curve():
    ease = lambda u: curves.bezier(u, 0.16, 1.0, 0.3, 1.0)   # "easeOutExpo"-like CSS curve
    t, traj = trajectory(ease, noise=0.001)
    m = curves.describe_move(t, traj)
    u = np.linspace(0, 1, 50)
    assert np.max(np.abs(curves.bezier(u, *m["ease"]["bezier"]) - ease(u))) < 0.06


def test_overshoot_is_measured():
    t, traj = trajectory(curves.NAMED["back.out"])
    m = curves.describe_move(t, traj)
    assert m["ease"]["overshoot"] == pytest.approx(0.1, abs=0.03)   # back.out(1.7) overshoots by ≈ 10 %


def test_noise_does_not_change_the_answer():
    t, traj = trajectory(curves.NAMED["power2.inOut"], noise=0.002)
    m = curves.describe_move(t, traj)
    assert m["ease"]["named"] in ("power2.inOut", "sine.inOut", "power1.inOut")
    assert m["duration"] == pytest.approx(1.0, rel=0.12)


def test_static_and_shake():
    t = np.arange(48) / FPS
    flat = {a: np.zeros_like(t) for a in curves.AXES}
    assert curves.describe_move(t, flat)["kind"] == ["static"]
    shake = dict(flat, x=0.03 * np.sin(2 * np.pi * 4 * t))
    assert "shake" in curves.describe_move(t, shake)["kind"]


def test_slow_there_and_back_is_moves_not_a_shake():
    """A real reference: over twelve seconds the camera drifts down and back up a few times — several moves."""
    t = np.arange(10 * FPS) / FPS
    x = 0.12 * curves.NAMED["sine.inOut"](np.clip(t / 3, 0, 1)) - 0.09 * curves.NAMED["sine.inOut"](np.clip((t - 5) / 3, 0, 1))
    traj = {"x": x, "y": np.zeros_like(t), "z": np.zeros_like(t), "r": np.zeros_like(t)}
    m = curves.describe_shot(t, traj)
    assert "shake" not in m["kind"] and m.get("moves") == 2, m["kind"]
    fast = {**traj, "x": 0.03 * np.sin(2 * np.pi * 3 * t)}             # 3 Hz: a shake
    assert "shake" in curves.describe_shot(t, fast)["kind"]
