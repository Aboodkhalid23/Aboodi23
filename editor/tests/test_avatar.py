"""His face → a drawn character of him → story scenes with him inside, alive (owner's round 5)."""
import json

import pytest

from editor.pipeline import avatar
from editor.pipeline.paths import Episode
from editor.pipeline.plan import Beat, EditPlan, save_plan, validate_plan


@pytest.fixture
def chars(tmp_path, monkeypatch):
    monkeypatch.setattr(avatar, "CHARACTERS", tmp_path / "characters.json")
    return tmp_path / "characters.json"


def plan_with(*beats):
    return EditPlan({"primary": "retro-collage"}, "", [], list(beats), end_screen=0)


def test_avatar_beats_need_a_look_and_a_way_to_move():
    e = " ".join(validate_plan(plan_with(Beat(0, 5, "body", "avatar", prompt="in a factory", caption="مصنع"),
                                         Beat(5, 10, "body", "avatar", prompt="x", caption="ص", look="cartoon", animate="fly")), 10.0))
    assert "beat 0: avatar لازم look" in e and "beat 1: animate" in e
    ok = " ".join(validate_plan(plan_with(Beat(0, 5, "body", "avatar", prompt="in a factory", caption="مصنع", look="paper")), 5.0))
    assert "avatar" not in ok


def test_character_is_made_once_per_look_and_only_its_id_is_kept(chars, tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    (ep.assets / "face_ref_1.jpg").write_bytes(b"x")
    jobs = avatar.character_jobs(ep, ["cartoon", "cartoon", "anime"])
    assert [j["look"] for j in jobs] == ["cartoon", "anime"] and jobs[0]["face_refs"][0].endswith("face_ref_1.jpg")
    assert "beard" in jobs[0]["prompt"] and "cartoon" in jobs[0]["prompt"].lower()
    avatar.register("cartoon", "11111111-2222-3333-4444-555555555555")
    assert avatar.element("cartoon").startswith("1111") and "jpg" not in chars.read_text()
    assert [j["look"] for j in avatar.character_jobs(ep, ["cartoon", "anime"])] == ["anime"]


def test_scene_jobs_put_his_character_in_and_say_how_it_moves(chars, tmp_path):
    from editor.pipeline.ai import ai_jobs
    avatar.register("paper", "abcdef12-0000-4000-8000-000000000000")
    ep = Episode(tmp_path / "ep").ensure()
    save_plan(plan_with(Beat(0, 5, "body", "avatar", prompt="he tries to fix a smoking machine in a factory", caption="مصنع",
                             look="paper"),
                        Beat(5, 10, "body", "avatar", prompt="he runs out of a bank", caption="بنك", look="paper", animate="ai"),
                        Beat(10, 15, "body", "avatar", prompt="on a stage", caption="مسرح", look="anime")), ep.plan)
    jobs = ai_jobs(ep)
    kinds = [(j.beat, j.kind) for j in jobs]
    assert kinds == [(0, "avatar"), (0, "avatar_fg"), (1, "avatar"), (1, "avatar_video"), (2, "avatar"), (2, "avatar_fg")]
    assert "<<<abcdef12-0000-4000-8000-000000000000>>>" in jobs[0].prompt and "paper cut-out" in jobs[0].prompt
    assert jobs[3].model == avatar.VIDEO_MODEL and jobs[3].asset.endswith("ai_1.mp4")
    assert "مو مسوية" in jobs[4].note            # anime character not made yet


def test_a_cut_out_figure_is_saved_beside_the_scene(tmp_path):
    from editor.pipeline.ai import ai_fetch
    import cv2, numpy as np
    ep = Episode(tmp_path / "ep").ensure()
    png = cv2.imencode(".png", np.zeros((8, 8, 4), np.uint8))[1].tobytes()
    class S:
        def get(self, url, timeout=None):
            class R:
                content, headers = png, {"Content-Type": "image/png"}
                def raise_for_status(self): pass
            return R()
    out = ai_fetch(ep, 3, "https://x/fg.png", session=S(), part="fg")
    assert out.name == "ai_3_fg.png"
