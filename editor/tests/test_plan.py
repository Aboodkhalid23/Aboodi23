import json

from editor.pipeline.brief import write_brief
from editor.pipeline.paths import Episode
from editor.pipeline.plan import Beat, EditPlan, load_plan, save_plan, validate_plan
from editor.pipeline.transcribe import Word, save_words

HOOK = [(2.0, "face_zoom_in" if i % 2 == 0 else "graphic") for i in range(15)]
BODY = [(5.0, k) for k in ["face", "image", "face_zoom_in", "graphic", "face_zoom_out",
                           "image", "face_framed", "graphic", "face_punch", "graphic"]]
TEASER = [(10.0, 12.0), (20.0, 22.0), (40.0, 42.0)]


def build(hook=HOOK, body=BODY):
    beats, t = [], 0.0
    for zone, items in (("hook", hook), ("body", body)):
        for dur, kind in items:
            b = Beat(start=round(t, 2), end=round(t + dur, 2), zone=zone, kind=kind)
            if kind == "image":
                b.query, b.caption = "Evergrande headquarters", "مقر إيفرغراند"
            if kind == "graphic":
                b.graphic = {"type": "text", "text": "شركة"}
            beats.append(b)
            t += dur
    plan = EditPlan(style={"primary": "vox", "sections": []}, style_reason="قصة شركة",
                    teaser=list(TEASER), beats=beats, shorts=[])
    return plan, round(t - 6.0, 2)  # clean duration = total - teaser


def errors_for(plan, clean):
    errs = validate_plan(plan, clean)
    assert len(errs) == 1, errs
    return errs[0]


def test_valid_plan_passes():
    plan, clean = build()
    assert validate_plan(plan, clean) == []


def test_plan_round_trip(tmp_path):
    plan, _ = build()
    save_plan(plan, tmp_path / "p.json")
    assert load_plan(tmp_path / "p.json") == plan


def test_body_beat_too_long():
    body = list(BODY)
    body[2] = (7.0, "face_zoom_in")
    plan, clean = build(body=body)
    err = errors_for(plan, clean)
    assert err.startswith("beat 17:") and "6" in err


def test_gap_detected():
    plan, clean = build()
    plan.beats[20].start += 0.5
    plan.beats[20].end += 0.0
    assert errors_for(plan, clean).startswith("beat 20:")


def test_overlap_detected():
    plan, clean = build()
    plan.beats[20].start -= 0.5
    assert errors_for(plan, clean).startswith("beat 20:")


def test_past_duration_detected():
    plan, clean = build()
    assert errors_for(plan, clean - 1.0).startswith("beat 24:")


def test_same_kind_twice():
    body = list(BODY)
    body[1] = (5.0, "face")
    body[2] = (5.0, "image")  # keep face share inside the band
    plan, clean = build(body=body)
    assert errors_for(plan, clean).startswith("beat 16:")


def test_face_share_too_low():
    body = [(5.0, k) for k in ["face", "image", "graphic", "image", "graphic",
                               "image", "graphic", "image", "graphic", "image"]]
    plan, clean = build(body=body)
    assert "40%" in errors_for(plan, clean)


def test_ai_beat_needs_prompt_and_caption():
    body = list(BODY)
    body[1] = (5.0, "ai_image")
    plan, clean = build(body=body)
    assert "prompt" in errors_for(plan, clean)
    plan.beats[16].prompt, plan.beats[16].caption = "1970s boardroom", "اجتماع الشركة"
    assert validate_plan(plan, clean) == []


def test_ai_budget_enforced():
    plan, clean = build()
    plan.ai_budget = 10
    assert validate_plan(plan, clean, ai_spent=9.5) == []
    assert errors_for_spent(plan, clean, 12).startswith("ai:")


def errors_for_spent(plan, clean, spent):
    errs = validate_plan(plan, clean, ai_spent=spent)
    assert len(errs) == 1, errs
    return errs[0]


def test_entity_beat_must_exist_in_entities():
    body = list(BODY)
    body[1] = (5.0, "entity")
    plan, clean = build(body=body)
    assert "entity" in errors_for(plan, clean)
    plan.beats[16].entity = "musk"
    assert validate_plan(plan, clean, entities={"musk"}) == []
    assert "entities.json" in validate_plan(plan, clean, entities={"jobs"})[0]


def test_face_fx_counts_as_face_and_needs_fx():
    body = list(BODY)
    body[0] = (5.0, "face_fx")
    plan, clean = build(body=body)
    assert "fx" in errors_for(plan, clean)
    plan.beats[15].fx = "subscribe"
    plan.beats[15].stickers = [{"type": "stamp", "text": "حقيقي", "at": 1.0}]
    assert validate_plan(plan, clean) == []
    plan.beats[15].stickers = [{"type": "emoji"}]
    assert "الملصقات" in errors_for(plan, clean)


def test_stickers_only_on_face_fx_and_known_transitions():
    plan, clean = build()
    plan.beats[16].stickers = [{"type": "stamp", "text": "x"}]
    assert "الملصقات" in errors_for(plan, clean)
    plan.beats[16].stickers = None
    plan.beats[16].transition = "spin"
    assert "transition" in errors_for(plan, clean)
    plan.beats[16].transition = "whip"
    assert validate_plan(plan, clean) == []


def test_old_plans_still_load(tmp_path):
    plan, _ = build()
    save_plan(plan, tmp_path / "p.json")
    d = json.loads((tmp_path / "p.json").read_text())
    d.pop("ai_budget")
    (tmp_path / "p.json").write_text(json.dumps(d))
    assert load_plan(tmp_path / "p.json").ai_budget == 0.0


def test_brief_suggests_subscribe_and_greeting_moments(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    ep.cuts.write_text(json.dumps([[0, 9]]))
    save_words([Word("هلا", 0.0, 0.4), Word("بيكم", 0.4, 0.9), Word("شلونكم", 0.9, 1.5),
                Word("لا", 4.0, 4.2), Word("تنسون", 4.2, 4.7), Word("تشتركون", 4.7, 5.3),
                Word("اشتركوا", 7.0, 7.6), Word("بالقناة", 7.6, 8.3)], ep.clean_words)
    (ep.edit / "entities.json").write_text(json.dumps(
        [{"id": "musk", "name": "إيلون ماسك", "en": "Elon Musk", "kind": "person", "role": "مؤسس تسلا"}]))
    text = write_brief(ep, "vox: ورق").read_text(encoding="utf-8")
    assert "face_fx tv: هلا بيكم" in text
    assert "face_fx subscribe: اشتركوا بالقناة" in text
    assert "musk: إيلون ماسك (مؤسس تسلا)" in text


def test_brief_has_no_json_and_one_line_per_phrase(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    ep.cuts.write_text(json.dumps([[0, 5.5]]))
    save_words([Word("شركة", 0.0, 0.5), Word("كبيرة", 0.5, 1.0),
                Word("انهارت", 3.0, 3.6), Word("فجأة", 3.6, 4.2)], ep.clean_words)
    text = write_brief(ep, "vox: ورق وملصقات").read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if ln.startswith("[")]
    assert lines == ["[00:00.0–00:01.0] شركة كبيرة", "[00:03.0–00:04.2] انهارت فجأة"]
    assert "{" not in text and "5.5" in text and "vox" in text


def test_image_needs_arabic_caption():
    plan, clean = build()
    plan.beats[16].caption = None
    assert errors_for(plan, clean).startswith("beat 16:")


def test_brief_splits_long_phrases_into_short_lines(tmp_path):
    """A 20 s breathless phrase becomes ~5 s lines so beats can be timed to the words."""
    ep = Episode(tmp_path / "ep").ensure()
    ep.cuts.write_text(json.dumps([[0, 20]]))
    save_words([Word(f"ك{i}", i * 0.5, i * 0.5 + 0.45) for i in range(40)], ep.clean_words)
    lines = [ln for ln in write_brief(ep, "vox: x").read_text(encoding="utf-8").splitlines() if ln.startswith("[")]
    assert len(lines) == 4
    assert lines[0].startswith("[00:00.0–00:05.0]")  # 4.95 s shown at 1 decimal
