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
