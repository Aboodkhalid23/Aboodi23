import numpy as np

from editor.pipeline.composer import compose, pick_mood
from editor.pipeline.grade import grade_filter
from editor.pipeline.plan import Beat
from editor.pipeline.styles import load_style


def test_music_is_composed_for_the_mood_and_differs_per_episode():
    assert pick_mood("investigative documentary, suspense") == "tension"
    assert pick_mood("موسيقى حزن هادية") == "sad"
    a, b = compose(6, "wonder", 1), compose(6, "wonder", 2)
    assert a.shape == (6 * 48000, 2) and np.abs(a).max() <= 0.71 and not np.allclose(a, b)
    assert np.abs(a[: 4800]).max() < np.abs(a[48000:96000]).max()   # fades in


def test_cinema_look_is_soft_and_kept_light():
    g = grade_filter("eq=gamma=1.05", "cinema")
    assert g.startswith(",eq=gamma=1.05") and "noise=" in g and "vignette" in g and "hqdn3d" in g
    assert grade_filter("", "natural") != g


def test_noir_world_is_the_new_default_and_dark():
    s = load_style("noir")
    assert s.grade == "cinema" and s.palette["paper"].lower() == "#0f131c"


def test_search_subscribe_needs_time():
    from .test_plan import build
    from editor.pipeline.plan import validate_plan
    plan, clean = build()
    b = next(x for x in plan.beats if x.kind == "face" and x.zone == "body")
    b.kind, b.fx = "face_fx", "search"
    errs = validate_plan(plan, clean)
    assert (b.duration < 4.5) == any("search" in e for e in errs)
