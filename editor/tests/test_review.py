import json

from editor.pipeline.paths import Episode
from editor.pipeline.plan import Beat, save_plan
from editor.pipeline.review import dull_zones, review

from .test_plan import build


def test_long_face_and_still_scenes_are_dull():
    beats = [Beat(0, 5, "body", "face"), Beat(5, 10, "body", "face_punch"), Beat(10, 14, "body", "image"),
             Beat(14, 21, "body", "image")]
    zones = dull_zones(beats)
    assert (0, 10, "وجهك بس") in zones and (14, 21, "ما اكو شي جديد") in zones


def test_review_scores_and_points_at_missed_paper_moments(tmp_path, monkeypatch):
    import editor.pipeline.review as rv
    monkeypatch.setattr(rv, "HISTORY", tmp_path / "history.jsonl")
    plan, clean = build()
    ep = Episode(tmp_path / "ep").ensure()
    save_plan(plan, ep.plan)
    ep.cuts.write_text(json.dumps([[0, clean]]))
    face = next(b for b in plan.beats if b.kind == "face" and b.zone == "body")
    t = face.start + 0.5 - plan.teaser_total
    ep.plan_input.write_text(f"[{int(t // 60):02d}:{t % 60:04.1f}] face_paper newspaper: نشرت الجريدة خبر\n", encoding="utf-8")
    r = review(ep)
    assert r["score"] < 100 and any("ورقة يمّه" in i for i in r["issues"])
    assert json.loads((tmp_path / "history.jsonl").read_text(encoding="utf-8").splitlines()[0])["episode"] == "ep"
    assert (ep.work / "review.txt").read_text(encoding="utf-8").startswith("مراجعة المونتير الخبير")
