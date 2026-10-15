import json

from editor.pipeline.names import candidates, resolve, similarity
from editor.pipeline.paths import Episode
from editor.pipeline.transcribe import Word, load_words, save_words


def _words(text, low=()):
    return [Word(w, i * 0.5, i * 0.5 + 0.4, 0.3 if i in low else 0.98) for i, w in enumerate(text.split())]


def test_names_that_sound_alike_match():
    assert similarity("ايلون موسك", "إيلون ماسك") > 0.9
    assert similarity("جيف بيزوز", "جيف بيزوس") > 0.8
    assert similarity("ايدن استي", "إيدان سيغيف") >= 0.62
    assert similarity("جاك ما", "جيف بيزوس") < 0.4


def test_name_spans_come_after_titles_and_from_unsure_words():
    ws = _words("بس البروفيسور ايدن استي وفريقه سووا تجربة وبعدين زوكربرگ گال", low=(8,))
    spans = [" ".join(w.text for w in ws[a:z]) for a, z in candidates(ws)]
    assert "ايدن استي" in spans and "زوكربرگ" in spans
    assert not any("العالم" in s for s in spans)


def test_known_names_are_corrected_and_unknown_ones_are_asked(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    save_words(_words("هلا بيكم الملياردير ايلون موسك اشترى تويتر وبعدها البروفيسور ايدن استي وفريقه"), ep.clean_words)
    (ep.edit / "entities.json").write_text(json.dumps([{"id": "musk", "name": "إيلون ماسك", "en": "Elon Musk",
                                                         "kind": "person"}], ensure_ascii=False), encoding="utf-8")
    r = resolve(ep)
    assert [f["name"] for f in r["fixed"]] == ["إيلون ماسك"]
    assert [u["heard"] for u in r["unsure"]] == ["ايدن استي"]
    assert "إيلون ماسك" in " ".join(w.text for w in load_words(ep.clean_words))
    # Claude identifies him from the story; the next run writes his name and makes him an entity (real photo)
    (ep.edit / "names.json").write_text(json.dumps({"ايدن استي": {"name": "إيدان سيغيف", "en": "Idan Segev",
                                                                "kind": "person"}}, ensure_ascii=False), encoding="utf-8")
    r = resolve(ep)
    assert r["unsure"] == [] and "إيدان سيغيف" in " ".join(w.text for w in load_words(ep.clean_words))
    ids = [e["id"] for e in json.loads((ep.edit / "entities.json").read_text(encoding="utf-8"))]
    assert ids == ["musk", "idan_segev"]


def test_subscribe_and_aside_moments_get_their_look(tmp_path):
    from editor.pipeline.autofix import moments
    from editor.pipeline.plan import Beat, EditPlan
    f = tmp_path / "w.json"
    words = [Word(t, 10 + i * 0.4, 10 + i * 0.4 + 0.3) for i, t in enumerate("لا تنسون تشتركون بالقناة".split())]
    words += [Word(t, 30 + i * 0.4, 30 + i * 0.4 + 0.3) for i, t in enumerate("على الطاري هاي مزحة صغيرة".split())]
    save_words(words, f)
    plan = EditPlan({"primary": "vox"}, "", [], [Beat(0, 8, "body", "image"), Beat(8, 13, "body", "face"),
                                                 Beat(13, 28, "body", "graphic"), Beat(28, 33, "body", "face_zoom_in"),
                                                 Beat(33, 40, "body", "image")])
    fixes = moments(plan, f)
    assert plan.beats[1].kind == "face_fx" and plan.beats[1].fx == "subscribe"
    assert plan.beats[3].fx == "none" and plan.beats[3].stickers[0]["text"] == "على الهامش"
    assert len(fixes) == 2
