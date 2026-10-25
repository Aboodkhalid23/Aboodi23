"""End to end on rendered video: a known push-in, a cut, a known pan — perception must measure what was filmed."""
import json
import math

import numpy as np
import pytest

import synth
from perception import curves, distance, fingerprint

FPS = 24


def canonical(name):
    """The ease's own curve in the same 5–95 % travel window perception compares moves on."""
    u = np.linspace(0, 1, 2001)
    return curves.canonical_progress(u, curves.NAMED[name](u))[2]
N = 48   # frames per shot


@pytest.fixture(scope="module")
def film(tmp_path_factory):
    """Shot 1: push in 1.0 → 1.3 with power3.out over frames 6–30. Shot 2 (another plate): pan right 0.25 frame widths
    with power2.inOut over frames 6–30."""
    p3, p2 = curves.NAMED["power3.out"], curves.NAMED["power2.inOut"]
    zoom = synth.move(N, 6, 24, p3, 1.0, 1.3)
    pan = synth.move(N, 6, 24, p2, 0.0, 0.25)
    cams = [synth.Cam(scale=z, plate=0) for z in zoom] + [synth.Cam(x=x, plate=1) for x in pan]
    path = str(tmp_path_factory.mktemp("synth") / "film.mp4")
    synth.render(path, cams, FPS)
    return path


@pytest.fixture(scope="module")
def fp(film):
    return fingerprint.extract(film, fps=FPS)


def test_cut_is_detected(fp):
    assert fp["cuts"] == [pytest.approx(2.0, abs=1 / FPS)]
    assert len(fp["shots"]) == 2


def test_push_in_is_measured(fp):
    m = fp["shots"][0]["move"]
    assert m["kind"] == ["push_in"]
    assert m["amount"]["z"] == pytest.approx(math.log(1.3), rel=0.05)
    assert m["start"] == pytest.approx(6 / FPS, abs=0.06)
    assert m["duration"] == pytest.approx(1.0, rel=0.12)
    truth = canonical("power3.out")
    assert np.sqrt(np.mean((np.asarray(m["progress"]) - truth) ** 2)) < 0.05


def test_pan_is_measured(fp):
    m = fp["shots"][1]["move"]
    assert m["kind"] == ["move_right"]
    assert m["amount"]["x"] == pytest.approx(0.25, rel=0.06)
    truth = canonical("power2.inOut")
    assert np.sqrt(np.mean((np.asarray(m["progress"]) - truth) ** 2)) < 0.05


def test_given_shots_keep_their_ids(film):
    fp = fingerprint.extract(film, fps=FPS, shots=[{"id": "s1", "start_s": 0, "end_s": 2}, {"id": "s2", "start_s": 2, "end_s": 4}])
    assert [s["id"] for s in fp["shots"]] == ["s1", "s2"]


def test_roll_sign(tmp_path):
    path = str(tmp_path / "roll.mp4")
    synth.render(path, [synth.Cam(roll=r) for r in synth.move(36, 4, 24, curves.NAMED["sine.inOut"], 0.0, 0.2)], FPS)
    m = fingerprint.extract(path, fps=FPS)["shots"][0]["move"]
    assert m["kind"] == ["roll_cw"] and m["amount"]["r"] == pytest.approx(0.2, rel=0.08)


def test_same_film_scores_high_and_slower_move_is_flagged(film, fp, tmp_path):
    same = distance.style_distance(fp, fp, pairs=[{"id": 1, "ref_shot": 1}, {"id": 2, "ref_shot": 2}])
    assert same["components"]["camera"]["score"] > 95 and not [f for f in same["findings"] if f["component"] == "camera"]
    # the same push, twice as slow and with a linear ease
    slow = synth.move(N, 6, 40, curves.NAMED["none"], 1.0, 1.3)
    path = str(tmp_path / "slow.mp4")
    synth.render(path, [synth.Cam(scale=z) for z in slow], FPS)
    ours = fingerprint.extract(path, fps=FPS)
    sd = distance.style_distance(fp, ours, pairs=[{"id": 1, "ref_shot": 1}], ref_window=(0, 2))
    text = " ".join(f["text"] for f in sd["findings"] if f["component"] == "camera")
    assert "slower" in text and "easing differs" in text
    assert sd["shots"][0]["camera"]["score"] < 60


def test_cadence_on_twos_vs_ones(tmp_path):
    """The same pan, once drawn every frame and once with every drawing held for two frames."""
    pan = synth.move(48, 4, 40, curves.NAMED["none"], 0.0, 0.3)
    ones, twos = str(tmp_path / "ones.mp4"), str(tmp_path / "twos.mp4")
    synth.render(ones, [synth.Cam(x=x) for x in pan], FPS)
    synth.render(twos, [synth.Cam(x=pan[f - f % 2]) for f in range(48)], FPS)
    c1, c2 = fingerprint.extract(ones, fps=FPS)["cadence"], fingerprint.extract(twos, fps=FPS)["cadence"]
    assert c1["label"] == "on ones" and c2["label"] == "on twos"
    assert c2["drawings_per_second"] == pytest.approx(12, abs=1.5)
    # holds share out the motion: the trajectory is the same, the speed has no comb
    m = fingerprint.extract(twos, fps=FPS)["shots"][0]["move"]
    assert m["amount"]["x"] == pytest.approx(0.3, rel=0.06)


def test_shot_list_one_frame_off_the_cut(film):
    """A plan whose cut is a frame late must not turn the cut into a huge camera move."""
    fp = fingerprint.extract(film, fps=FPS, shots=[{"id": "a", "start_s": 0, "end_s": 2 + 1 / FPS}, {"id": "b", "start_s": 2 + 1 / FPS, "end_s": 4}])
    assert fp["cuts"] == [pytest.approx(2.0, abs=0.01)]                  # snapped to the real cut
    assert fp["shots"][1]["move"]["kind"] == ["move_right"]
    assert fp["shots"][1]["move"]["amount"]["x"] == pytest.approx(0.25, rel=0.06)


def test_unrelated_frames_are_not_a_camera_move():
    a, b = synth.plate(1)[:360, :640], synth.plate(2)[:360, :640]
    import cv2
    from perception import camera
    step = camera.estimate(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY))
    assert not step.ok


def test_two_moves_in_one_shot(tmp_path):
    """Push in, rest, then pan: two moves, each with its own timing."""
    n = 72
    zoom = synth.move(n, 4, 18, curves.NAMED["power2.out"], 1.0, 1.25)
    pan = synth.move(n, 40, 24, curves.NAMED["sine.inOut"], 0.0, 0.3)
    path = str(tmp_path / "two.mp4")
    synth.render(path, [synth.Cam(scale=z, x=x) for z, x in zip(zoom, pan)], FPS)
    m = fingerprint.extract(path, fps=FPS)["shots"][0]["move"]
    assert m["moves"] == 2 and set(m["kind"]) == {"push_in", "move_right"}
    other = m["other_moves"][0]
    starts = sorted([m["start"], other["start"]])
    assert starts[0] == pytest.approx(4 / FPS, abs=0.08) and starts[1] == pytest.approx(40 / FPS, abs=0.08)


def test_static_overlay_does_not_hold_the_camera(tmp_path):
    """A screen recording: the pan happens under a UI strip that never moves. The strip must not vote "no motion"."""
    import cv2
    pan = synth.move(48, 4, 36, curves.NAMED["sine.inOut"], 0.0, 0.25)
    raw, rec = str(tmp_path / "raw.mp4"), str(tmp_path / "rec.mp4")
    synth.render(raw, [synth.Cam(x=x) for x in pan], FPS)
    ui = synth.plate(9)[:360, :200]
    cap, vw = cv2.VideoCapture(raw), cv2.VideoWriter(rec, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (640, 360))
    while True:
        ok, f = cap.read()
        if not ok:
            break
        f[:, 440:] = ui   # a textured, rich, perfectly still overlay over the right third
        vw.write(f)
    vw.release()
    fp = fingerprint.extract(rec, fps=FPS)
    assert fp["static_overlay"] > 0.2
    assert fp["shots"][0]["move"]["amount"]["x"] == pytest.approx(0.25, rel=0.1)


def test_a_rest_before_a_move_is_not_a_held_drawing():
    """Three still frames at the start, then a push: the push must start where it starts (found by rendering through
    the real engine — the rest was taken for limited animation and the first step spread back over it)."""
    diff = np.r_[0.0, 0.0, 0.0, 0.0, 0.05, 0.04, 0.0, 0.03, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, 0.03]
    hold = fingerprint.held_frames(diff, [])
    assert not hold[1:4].any()               # the opening rest
    assert hold[6]                           # a single still frame inside motion: a held drawing
    assert not hold[9:14].any()              # five still frames: the scene resting, not a hold
    assert not fingerprint.held_frames(np.r_[0.0, 0.03, 0.2, 0.0, 0.03], [2])[3]   # a still frame right after a cut


def _flat_scene(path, frames, fps=FPS, size=(640, 360), sparkles=0):
    """A soft vertical gradient (optionally with small sparkles) and a textured character disc; frames: list of
    (camera_dx_px, char_dx_px, char_rot_deg)."""
    import cv2
    W, H = size
    big_w = W + 400
    bg = np.zeros((H, big_w, 3), np.uint8)
    for y in range(H):
        bg[y] = (200 - y // 8, 190 - y // 10, 235 - y // 12)
    rng = np.random.default_rng(3)
    for _ in range(sparkles):
        cv2.circle(bg, (int(rng.integers(0, big_w)), int(rng.integers(0, H))), 2, (255, 255, 255), -1)
    char = synth.plate(5, 220, 220)
    mask = np.zeros((220, 220), np.uint8)
    cv2.circle(mask, (110, 110), 105, 255, -1)
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    for cam_dx, char_dx, rot in frames:
        f = bg[:, 200 + int(round(cam_dx)):200 + int(round(cam_dx)) + W].copy()
        R = cv2.getRotationMatrix2D((110, 110), rot, 1.0)
        c = cv2.warpAffine(char, R, (220, 220), borderMode=cv2.BORDER_REFLECT)
        x0, y0 = int(W / 2 - 110 + char_dx - cam_dx), 70
        roi = f[y0:y0 + 220, x0:x0 + 220]
        roi[mask > 0] = c[mask > 0]
        vw.write(f)
    vw.release()


def test_a_character_moving_over_a_plain_background_is_not_a_camera_move(tmp_path):
    """Real film: a character's head tilt over a flat gradient was read as a 2.5° camera roll."""
    path = str(tmp_path / "flat.mp4")
    tilt = synth.move(48, 6, 30, curves.NAMED["sine.inOut"], 0.0, 9.0)
    _flat_scene(path, [(0, 25 * k / 47, r) for k, r in enumerate(tilt)])
    fp = fingerprint.extract(path, fps=FPS)
    m = fp["shots"][0]["move"]
    assert m["kind"] == ["static"], m
    assert fp["shots"][0]["local_motion"] > 0.0005


def test_a_pan_over_a_plain_background_with_some_detail_is_still_found(tmp_path):
    """The other side: the camera really pans; a few sparkles in the background are the evidence."""
    path = str(tmp_path / "pan.mp4")
    pan = synth.move(48, 4, 36, curves.NAMED["sine.inOut"], 0.0, 160.0)
    _flat_scene(path, [(p, p, 0.0) for p in pan], sparkles=60)
    m = fingerprint.extract(path, fps=FPS)["shots"][0]["move"]
    assert m["kind"] == ["move_right"], m
    assert m["amount"]["x"] == pytest.approx(160 / 640, rel=0.15)


def test_a_push_on_a_frame_filling_subject_is_not_overruled_by_a_caption(tmp_path):
    """Real film: a bowl and two arms filling the frame, pushed in 26 %, with a burned-in caption that never moves.
    The caption's corners must not turn the push into a still camera."""
    import cv2
    zoom = synth.move(48, 4, 40, curves.NAMED["sine.inOut"], 1.0, 1.3)
    raw, out = str(tmp_path / "raw.mp4"), str(tmp_path / "cap.mp4")
    synth.render(raw, [synth.Cam(scale=z) for z in zoom], FPS)
    cap, vw = cv2.VideoCapture(raw), cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (640, 360))
    while True:
        ok, f = cap.read()
        if not ok:
            break
        cv2.rectangle(f, (150, 312), (490, 344), (250, 250, 250), -1)
        cv2.putText(f, "EGGS ARE EASY. SHELLS: MORE", (160, 336), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 20, 20), 2, cv2.LINE_AA)
        vw.write(f)
    vw.release()
    m = fingerprint.extract(out, fps=FPS)["shots"][0]["move"]
    assert "push_in" in m["kind"], m
    assert m["amount"]["z"] == pytest.approx(np.log(1.3), rel=0.15)


def test_plan_check_flags_slow_plans_and_reports_squeezed_shots(tmp_path, monkeypatch):
    from perception import cli
    ref = {"start": 0.0, "end": 20.0, "frames": 480, "fps": 24, "cuts": [5.0, 10.0, 15.0],
           "shots": [{"id": i + 1, "start": 5.0 * i, "end": 5.0 * (i + 1), "move": {"kind": ["push_in"], "amount": {"x": 0, "y": 0, "z": 0.1, "r": 0},
                      "duration": 4.0}} for i in range(4)],
           "series": {"camera": {k: [0.0] * 480 for k in ("dx", "dy", "dz", "dr")}, "tracked": [1] * 480, "local": [0.0] * 480,
                      "diff": [0.0] * 480, "lab": [[0.5] * 480] * 3, "tension": [0.0] * 480},
           "beats": [], "peaks": [], "descriptors": {"fps": 2, "grid": [8, 4], "data": []}}
    monkeypatch.setattr(cli, "ensure_reference", lambda P: ref)
    (tmp_path / "plan.json").write_text(json.dumps({"shots": [{"id": f"S{i}", "start_s": 1.0 * i, "end_s": 1.0 * (i + 1), "ref_shot": i % 4 + 1} for i in range(20)]}))
    r = cli.plan_check(str(tmp_path))
    assert r["ok"] and r["ratio"] > 3                         # 19 cuts in 20 s against 3: faster is the brief's call …
    assert r["squeezed"] and r["squeezed"][0]["ref_moving_s"] == 4.0   # … but 1 s shots for 4 s pushes are reported
    (tmp_path / "plan.json").write_text(json.dumps({"shots": [{"id": "S1", "start_s": 0.0, "end_s": 20.0, "ref_shot": 1}]}))
    assert not cli.plan_check(str(tmp_path))["ok"]            # one shot for a take the reference cuts three times: too slow
