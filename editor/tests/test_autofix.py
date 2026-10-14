import copy
import json

from editor.pipeline.autofix import repair
from editor.pipeline.plan import validate_plan

from .test_plan import build


def test_a_clean_plan_is_left_alone():
    plan, clean = build()
    before = copy.deepcopy(plan.beats)
    assert repair(plan, clean) == []
    assert plan.beats == before


def test_mechanical_mistakes_are_repaired_until_the_plan_validates():
    plan, clean = build()
    b = plan.beats
    b[3].start += 0.4                      # a gap
    b[6].start -= 0.3                      # an overlap
    b[-1].end -= 2.0                       # stops before the video ends
    k = next(i for i, x in enumerate(b) if x.zone == "body" and x.kind == "image")
    b[k].end = b[k + 1].end                # one long body beat swallowing the next…
    del b[k + 1]
    fixes = repair(plan, clean)
    assert fixes
    assert validate_plan(plan, clean) == [], validate_plan(plan, clean)


def test_a_long_beat_is_split_on_a_pause_between_words(tmp_path):
    plan, clean = build()
    b = plan.beats
    k = next(i for i, x in enumerate(b) if x.zone == "body" and x.kind == "image")
    start = b[k].start
    b[k].end = b[k + 1].end
    del b[k + 1]
    t0 = start - plan.teaser_total
    words = [{"t": "كلمة", "s": t0 + 0.1, "e": t0 + 5.0}, {"t": "ثانية", "s": t0 + 5.6, "e": t0 + 8.0}]
    f = tmp_path / "words.json"
    f.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    repair(plan, clean, f)
    assert abs(plan.beats[k].end - (start + 5.3)) < 0.01   # between the two words, not the middle


def test_two_same_face_moves_in_a_row_become_different():
    plan, clean = build()
    b = plan.beats
    i = next(i for i in range(1, len(b)) if b[i].kind.startswith("face") and b[i - 1].kind != b[i].kind
             and b[i - 1].kind.startswith("face") is False)
    b[i - 1].kind = b[i].kind = "face"
    b[i - 1].query = b[i - 1].caption = b[i - 1].graphic = None
    repair(plan, clean)
    assert b[i - 1].kind != b[i].kind
