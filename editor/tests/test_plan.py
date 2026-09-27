import json

from editor.pipeline.brief import write_brief
from editor.pipeline.paths import Episode
from editor.pipeline.plan import Beat, EditPlan, load_plan, save_plan, validate_plan
from editor.pipeline.transcribe import Word, save_words

HOOK = [(2.0, "face_zoom_in" if i % 2 == 0 else "graphic") for i in range(15)]
BODY = [(5.0, k) for k in ["face", "image", "face_zoom_in", "graphic", "face_zoom_out",
                           "image", "face_framed", "graphic", "image", "graphic"]]
TEASER = [(10.0, 12.0), (20.0, 22.0), (40.0, 42.0)]


def build(hook=HOOK, body=BODY):
    beats, t = [], 0.0
    for zone, items in (("hook", hook), ("body", body)):
        for dur, kind in items:
            b = Beat(start=round(t, 2), end=round(t + dur, 2), zone=zone, kind=kind)
            if kind == "image":
                b.query = "Evergrande headquarters"
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
    assert "35" in errors_for(plan, clean)


def test_ai_kind_rejected_in_part1():
    body = list(BODY)
    body[1] = (5.0, "ai_image")
    plan, clean = build(body=body)
    assert "الذكاء الاصطناعي مو مفعّل بعد (الجزء 2)" in errors_for(plan, clean)


def test_brief_has_no_json_and_one_line_per_phrase(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    ep.cuts.write_text(json.dumps([[0, 5.5]]))
    save_words([Word("شركة", 0.0, 0.5), Word("كبيرة", 0.5, 1.0),
                Word("انهارت", 3.0, 3.6), Word("فجأة", 3.6, 4.2)], ep.clean_words)
    text = write_brief(ep, "vox: ورق وملصقات").read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if ln.startswith("[")]
    assert lines == ["[00:00.0–00:01.0] شركة كبيرة", "[00:03.0–00:04.2] انهارت فجأة"]
    assert "{" not in text and "5.5" in text and "vox" in text
