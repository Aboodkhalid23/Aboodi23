import json

from editor.pipeline.plan import load_plan
from editor.pipeline.suite import _small, apply


def _episode(tmp_path):
    edit = tmp_path / "edit"
    edit.mkdir()
    plan = {"style": {"primary": "vox", "sections": []}, "style_reason": "", "teaser": [],
            "beats": [{"start": 0, "end": 2, "zone": "hook", "kind": "face"},
                      {"start": 2, "end": 4, "zone": "hook", "kind": "image", "query": "Dog"}]}
    (edit / "edit_plan.json").write_text(json.dumps(plan), encoding="utf-8")
    return tmp_path


def test_apply_brings_back_scenes_picks_and_reels(tmp_path):
    ep = _episode(tmp_path)
    pick = {"img": "cand/0.jpg", "provider": "Openverse", "title": "dog", "license": "CC0", "artist": "", "page": "p",
            "url": "https://x/dog.jpg", "width": 2000, "height": 1500}
    edits = {"edits": {"beats": [{"start": 0, "end": 2.5, "zone": "hook", "kind": "face", "uid": "b0", "thumb": "thumbs/0.jpg"},
                                 {"start": 2.5, "end": 4, "zone": "hook", "kind": "image", "query": "Dog", "uid": "b1",
                                  "transition": "shutter", "pick": pick}],
                       "reels": [{"from": 0, "to": 20, "title": "هوك"}]},
             "requests": [{"t": 3, "text": "حط صورة", "status": "queued"}, {"t": 1, "text": "خلص", "status": "done"}]}
    f = tmp_path / "edits.json"
    f.write_text(json.dumps(edits, ensure_ascii=False), encoding="utf-8")
    open_ = apply(ep, f)
    plan = load_plan(ep / "edit" / "edit_plan.json")
    assert [b.end for b in plan.beats] == [2.5, 4]
    assert plan.beats[1].transition == "shutter" and plan.beats[1].pick["url"] == "https://x/dog.jpg"
    assert plan.shorts == [{"from": 0, "to": 20, "title": "هوك"}]
    assert [r["text"] for r in open_] == ["حط صورة"]
    saved = json.loads((ep / "edit" / "edit_plan.json").read_text(encoding="utf-8"))
    assert "uid" not in saved["beats"][0] and "thumb" not in saved["beats"][0]


def test_small_asks_wikimedia_for_a_thumbnail():
    assert _small("https://upload.wikimedia.org/wikipedia/commons/a/ab/Dog%20a.jpg").endswith("Special:FilePath/Dog a.jpg?width=320")
    assert _small("https://example.org/a.jpg") == "https://example.org/a.jpg"
