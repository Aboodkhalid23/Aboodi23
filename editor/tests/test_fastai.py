"""The fast AI pass of the core steps: one quick question per piece, all pieces at once."""
import json
import subprocess
import threading
import time

import pytest

import editor.app.server as srv
from editor.app import fastai
from editor.pipeline.paths import Episode
from editor.pipeline.transcribe import Word, save_words


def test_parse_json_takes_the_object_out_of_any_wrapping():
    assert fastai.parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert fastai.parse_json('خلص: {"drop": [1, 2], "t": "a}b"} وبس') == {"drop": [1, 2], "t": "a}b"}
    with pytest.raises(ValueError):
        fastai.parse_json("ماكو")


def test_ask_sends_no_tools_and_retries_once():
    calls = []

    def runner(cmd, input=None, **kw):
        calls.append(cmd)
        out = "مو جواب" if len(calls) == 1 else '{"ok": true}'
        return subprocess.CompletedProcess(cmd, 0, out, "")
    assert fastai.ask("claude", "سؤال", "sonnet", runner=runner) == {"ok": True}
    cmd = calls[0]
    assert cmd[cmd.index("--tools") + 1] == "" and cmd[cmd.index("--model") + 1] == "sonnet" and len(calls) == 2


def test_long_videos_are_asked_in_pieces_at_the_same_time():
    pieces = fastai.chunks(list(range(500)), 160, 12)
    assert len(pieces) == 4 and pieces[1][0] == 148 and pieces[-1][-1] == 499
    seen = []

    def slow(p):
        seen.append(threading.get_ident())
        time.sleep(0.3)
        if p[0] == 148:
            raise RuntimeError("انقطع")
        return len(p)
    t0 = time.monotonic()
    out = fastai.run_parallel(slow, pieces)
    assert time.monotonic() - t0 < 0.9 and isinstance(out[1], RuntimeError) and out[0] == 160


def test_find_run_matches_spelling_variants():
    from editor.pipeline.clean import normalize_ar
    toks = "يوم من الأيام كان اكو يوم من الايام عاش".split()
    assert fastai.find_run(toks, "يوم من الايام كان اكو", normalize_ar) == (0, 5)
    assert fastai.find_run(toks, "شي ثاني", normalize_ar) is None


@pytest.fixture
def ep(tmp_path, monkeypatch):
    monkeypatch.setattr(srv, "EPISODES", tmp_path / "eps")
    monkeypatch.setattr(srv, "HOME", tmp_path / "home")
    monkeypatch.setattr(srv, "JOB", srv.Job())
    raw = tmp_path / "raw.mp4"
    raw.write_bytes(b"0123456789")
    d = srv.EPISODES / srv.create_episode("قصة رجل", str(raw))["id"]
    e = Episode(d).ensure()
    words, t = [], 0.0
    for sent in ("هلو شلونكم", "اليوم عندي قصة غريبة", "سمعتوا بيها قبل", "يوم من الايام كان اكو عاش رجل فقير"):
        for w in sent.split():
            words.append(Word(w, t, t + 0.4))
            t += 0.45
        t += 1.0
    save_words(words, e.transcript)
    return d, e


def test_sentences_review_drops_retakes_and_cuts_inside_a_sentence(ep, monkeypatch):
    from editor.app import studio
    d, e = ep
    asked = []

    def fake(prompt, tier="mid"):
        asked.append(prompt)
        return {"drop": [1], "cut": [{"i": 3, "text": "كان اكو"}], "why": {"1": "انعادت"}}
    monkeypatch.setattr(srv, "_fast_json", fake)
    assert srv._review_step(d, "sentences") == 0
    assert "قصة رجل" in asked[0] and "1|✓|اليوم عندي قصة غريبة" in asked[0]
    items = studio.sentences(e)["items"]
    assert [x["keep"] for x in items] == [True, False, True, True]
    assert "كان" in items[3]["cut_words"] and "عاش" not in items[3]["cut_words"]
    rev = json.loads((d / "edit/work/app/sentences_review.json").read_text(encoding="utf-8"))
    assert "حذفت 1" in rev["summary"] and rev["drop"] == [1]


def test_review_failure_inside_prepare_does_not_stop_the_job(ep, monkeypatch):
    d, _ = ep
    monkeypatch.setattr(srv, "_fast_json", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("ماكو نت")))
    assert srv._review_step(d, "sentences") == 1
    assert "sentences" in srv.STEPS["prepare"] and srv.STEPS["auto"].index("sentences") < srv.STEPS["auto"].index("cut")


def test_captions_review_reads_all_pieces(ep, monkeypatch):
    d, e = ep
    save_words([Word(f"كلمة{i}", i * 0.5, i * 0.5 + 0.4) for i in range(1000)], e.clean_words)
    e.cuts.write_text(json.dumps([[0, 600]]), encoding="utf-8")
    got = []

    def fake(prompt, tier="mid"):
        got.append(prompt)
        return {"fixes": [{"i": len(got), "old": "x", "new": "ستيف جوبز"}], "questions": []}
    monkeypatch.setattr(srv, "_fast_json", fake)
    assert srv._review_step(d, "captions") == 0
    rev = json.loads((d / "edit/work/app/captions_review.json").read_text(encoding="utf-8"))
    assert len(got) == 3 and len(rev["fixes"]) == 3


def test_hook_step_keeps_three_openings_and_his_pick_reaches_the_plan(ep, monkeypatch):
    d, e = ep
    save_words([Word(w, i * 0.5, i * 0.5 + 0.4) for i, w in enumerate("هواوي بدت بخمسة آلاف دولار بس".split())], e.clean_words)
    monkeypatch.setattr(srv, "_fast_json", lambda prompt, tier="mid": {"hooks": [
        {"title": "رقم", "from": 0, "to": 2.9, "text": "هواوي بدت بخمسة آلاف دولار بس", "why": "صادم"},
        {"title": "طويل كلش", "from": 0, "to": 90, "text": "x"}, {"title": "ناقص"}]})
    assert srv._hook_step(d) == 0
    rv = json.loads((d / "edit/work/app/hook_review.json").read_text(encoding="utf-8"))
    assert [h["title"] for h in rv["hooks"]] == ["رقم"]
    srv.save_hook(d, 0)
    extra = srv._plan_extra(d)
    assert "teaser: [[0.00, 2.90]]" in extra and "هواوي بدت" in extra


def test_viewer_step_scores_and_lists_moments(ep, monkeypatch):
    d, e = ep
    save_words([Word("كلمة", i, i + 0.5) for i in range(20)], e.clean_words)
    e.plan.write_text(json.dumps({"style": {"primary": "noir"}, "teaser": [], "beats": [
        {"start": 0, "end": 10, "kind": "face", "zone": "hook"}, {"start": 10, "end": 20, "kind": "image", "query": "x", "zone": "body"}]}), encoding="utf-8")
    asked = []
    monkeypatch.setattr(srv, "_fast_json", lambda prompt, tier="mid": asked.append(prompt) or {
        "score": 140, "summary": "زين", "notes": [{"t": 12, "issue": "ممل", "fix": "صورة", "level": "high"},
                                                  {"t": 3, "issue": "ضعيف", "fix": "قص", "level": "??"}, {"bad": 1}]})
    assert srv._viewer_step(d) == 0
    rv = json.loads((d / "edit/work/app/viewer_review.json").read_text(encoding="utf-8"))
    assert rv["score"] == 100 and [n["t"] for n in rv["notes"]] == [3, 12] and rv["notes"][0]["level"] == "mid"
    assert "يطلع: وجهه" in asked[0] or "[0.0–10.0]" in asked[0]
    assert srv.STEPS["hook"] == ["hook"] and srv.STEPS["viewer"] == ["viewer"]


def test_jobs_send_only_the_tools_they_use():
    from editor.app import fastai as fa
    fa._HELP["fake-new"] = "--tools <tools...>  --strict-mcp-config"
    fa._HELP["fake-old"] = "--model"
    assert fa.lean_flags("fake-new", ["Read", "Bash"], mcp=False) == ["--tools", "Read,Bash", "--strict-mcp-config"]
    assert fa.lean_flags("fake-new", ["Read"], mcp=True) == ["--tools", "Read"]     # the picture makers keep his connectors
    assert fa.lean_flags("fake-old", ["Read"], mcp=False) == []                      # an older Claude still starts


def test_planner_reads_only_steps_five_to_eight_of_the_editor_skill():
    """The plan prompt names exact lines (fewer tokens): if the skill moves, this must be updated with it."""
    from pathlib import Path
    lines = (Path(srv.CODE) / ".claude/skills/editor/SKILL.md").read_text(encoding="utf-8").splitlines()
    assert lines[59].startswith("5. **اقرا**") and lines[165].startswith("8. **افحص")
    assert "الأسطر 60 لحد 166" in srv.PLAN_PROMPT and (Path(srv.CODE) / "editor/PLAN_RULES.md").exists()


def test_free_media_keys_stay_private_and_reach_the_pipeline(tmp_path, monkeypatch):
    import os
    monkeypatch.setattr(srv, "HOME", tmp_path)
    assert srv.media_keys({"pexels": "abcdefghij1234567890", "pixabay": ""}) == {"pexels": "abcdefghij1234567890"}
    f = tmp_path / "media_keys.json"
    assert oct(os.stat(f).st_mode)[-3:] == "600"
    assert srv._env()["PEXELS_API_KEY"] == "abcdefghij1234567890"
    with pytest.raises(ValueError):
        srv.media_keys({"pixabay": "bad key!"})
    assert srv.media_keys({"pexels": "-"}) == {}


def test_a_video_sent_in_the_chat_becomes_the_episode_style(ep, monkeypatch):
    d, _ = ep
    seen = []

    def fake_ref(path):
        srv.JOB.new_style = "mine-test"
        return 0
    monkeypatch.setattr(srv, "style_from_reference", fake_ref)
    monkeypatch.setattr(srv, "_run", lambda *a, **k: seen.append(a[0]) or 0)
    monkeypatch.setattr(srv, "_council_step", lambda d: 0, raising=False)
    srv.JOB.message = "/tmp/ref.mp4"
    srv.run_job(d.name, "style-ref-apply")
    assert (d / "edit" / "style.txt").read_text(encoding="utf-8") == "mine-test"
    assert srv.STEPS["style-ref-apply"][:2] == ["style-ref", "plan"]


def test_plan_is_one_answer_and_only_real_mistakes_go_back(ep, monkeypatch):
    """Owner, 2026-10-28: a 2-minute test took an hour; the plan agent alone was 5 minutes and 27 turns."""
    d, e = ep
    (e.work / "plan_input.txt").write_text("[00:00.0] هلو شلونكم", encoding="utf-8")
    asked, checks = [], iter([["❌ beat 1: صورة ما تطابق"], []])
    answers = iter([{"plan": {"beats": [{"kind": "face"}]}, "idea": "فكرة"},
                    {"plan": {"beats": [{"kind": "face"}, {"kind": "image"}]}}])
    monkeypatch.setattr(srv, "_fast_json", lambda prompt, tier="mid": asked.append(prompt) or next(answers))
    monkeypatch.setattr(srv, "_plan_errors", lambda d: next(checks))
    assert srv._fast_plan(d) == 0
    assert "PLAN_RULES" not in asked[0] and "هلو شلونكم" in asked[0] and "صورة ما تطابق" in asked[1]
    assert len(json.loads((e.edit / "edit_plan.json").read_text(encoding="utf-8"))["beats"]) == 2
    assert srv.prefs()["council"] is False     # ChatGPT and Gemini only when he turns them on


def test_plan_falls_back_to_the_agent_when_the_answer_is_no_plan(ep, monkeypatch):
    d, e = ep
    (e.work / "plan_input.txt").write_text("x", encoding="utf-8")
    monkeypatch.setattr(srv, "_fast_json", lambda prompt, tier="mid": {"oops": 1})
    assert srv._fast_plan(d) == -1 and not (e.edit / "edit_plan.json").exists()
