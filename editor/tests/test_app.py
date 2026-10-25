"""The Mac app's engine (editor/app/server.py), with a stand-in for Claude so nothing is spent."""
import json
import os
import stat
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

import editor.app.server as srv

FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, pathlib, re, sys
prompt = sys.argv[sys.argv.index("-p") + 1]
ev = lambda o: print(json.dumps(o, ensure_ascii=False), flush=True)
if os.environ.get("FAKE_CLAUDE") == "login":
    ev({"type": "result", "subtype": "success", "is_error": True, "result": "Invalid API key · Please run /login"})
    sys.exit(1)
t = re.search(r"ملف الذوق الحالي: (.+)", prompt)
if t:   # the learning step: the taste file is rewritten from what he changed
    seen = "كابشن أصفر" if "yellow" in prompt else "شي"
    pathlib.Path(t.group(1).strip()).write_text("## الكابشن والخط\n- يحب " + seen + " (مرة وحدة)\n", encoding="utf-8")
    ev({"type": "result", "subtype": "success", "is_error": False, "result": "تعلمت"})
    sys.exit(0)
m = re.search(r"الحلقة بالمجلد: (.+)", prompt)
if m:
    ep = pathlib.Path(m.group(1).strip())
    (ep / "edit" / "edit_plan.json").write_text(json.dumps({"style": {"primary": "noir", "sections": []}, "beats": []}))
    ev({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Write", "input": {"file_path": str(ep / "edit" / "edit_plan.json")}},
        {"type": "text", "text": "خلصت الخطة"}]}})
else:
    ep = pathlib.Path(re.search(r"الحلقة: (.+)", prompt).group(1).strip())
    ids = re.findall(r'"id": "(\w+)"', prompt)
    (ep / "edit" / "work" / "requests_done.json").write_text(json.dumps({i: "حطيت الصورة" for i in ids}, ensure_ascii=False))
ev({"type": "result", "subtype": "success", "is_error": False, "result": "تم"})
'''


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(srv, "EPISODES", tmp_path / "eps")
    monkeypatch.setattr(srv, "HOME", tmp_path / "home")
    monkeypatch.setattr(srv, "JOB", srv.Job())
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "claude"
    fake.write_text(FAKE_CLAUDE, encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    raw = tmp_path / "raw.mp4"
    raw.write_bytes(b"0123456789")
    return raw


def _wait():
    for _ in range(200):
        if not srv.JOB.running:
            return
        time.sleep(0.05)
    raise AssertionError("the job never finished")


def test_create_episode_names_the_folder_and_keeps_the_script(app):
    e = srv.create_episode("قصة نوكيا: الصعود!", str(app), "هلا بيكم")
    assert e["id"].endswith("-قصة-نوكيا-الصعود") and e["name"] == "قصة نوكيا: الصعود!"
    d = srv.EPISODES / e["id"]
    assert (d / "04-script.md").read_text(encoding="utf-8").startswith("هلا بيكم")
    assert not any(e["done"].values())
    again = srv.create_episode("قصة نوكيا: الصعود!", str(app))
    assert again["id"] == e["id"] + "-2"
    with pytest.raises(ValueError):
        srv.create_episode("", str(app))
    with pytest.raises(ValueError):
        srv.create_episode("حلقة", str(app.parent / "missing.mp4"))
    with pytest.raises(KeyError):
        srv.episode_dir("../eps")


def test_room_storage_works_like_the_artifact_db(app):
    d = srv.EPISODES / srv.create_episode("حلقة", str(app))["id"]
    srv.db_op(d, "set", "edits/current", {"reels": [1]})
    srv.db_op(d, "update", "edits/current", {"beats": []})
    assert srv.db_op(d, "get", "edits/current") == {"reels": [1], "beats": []}
    path = srv.db_op(d, "add", "requests", {"t": 3, "text": "طلب"})["path"]
    assert [r["data"]["text"] for r in srv.db_op(d, "list", "requests")] == ["طلب"]
    srv.db_op(d, "delete", path)
    assert srv.db_op(d, "list", "requests") == []
    assert not srv._valid_path("../x") and not srv._valid_path("requests") and srv._valid_path("requests/ab12")


def test_plan_step_runs_claude_and_shows_what_it_does(app):
    e = srv.create_episode("حلقة", str(app))
    srv.start_job(e["id"], "plan")
    _wait()
    assert srv.JOB.ok, srv.JOB.lines
    assert (srv.EPISODES / e["id"] / "edit" / "edit_plan.json").exists()
    assert "✍️ يكتب edit_plan.json" in srv.JOB.lines and "💬 خلصت الخطة" in srv.JOB.lines
    assert srv.episode_state(srv.EPISODES / e["id"])["done"]["plan"]
    with pytest.raises(ValueError):
        srv.start_job(e["id"], "nothing")


def test_claude_not_signed_in_is_said_plainly(app, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE", "login")
    e = srv.create_episode("حلقة", str(app))
    srv.start_job(e["id"], "plan")
    _wait()
    assert srv.JOB.ok is False and srv.JOB.need_login
    assert any("تسجيل دخول" in line for line in srv.JOB.lines)


def test_requests_come_back_answered(app):
    d = srv.EPISODES / srv.create_episode("حلقة", str(app))["id"]
    plan = {"style": {"primary": "noir", "sections": []}, "teaser": [],
            "beats": [{"start": 0, "end": 2, "zone": "hook", "kind": "face"}]}
    (d / "edit" / "edit_plan.json").write_text(json.dumps(plan), encoding="utf-8")
    req = srv.db_op(d, "add", "requests", {"t": 1.5, "text": "حط صورة جوبز", "status": "queued"})["path"]
    note = srv.db_op(d, "add", "requests", {"t": 0, "text": "للفريق", "type": "note", "status": "new"})["path"]
    srv.db_op(d, "set", "edits/current", {"reels": [{"from": 0, "to": 20, "title": "هوك"}]})
    srv.JOB.ep = d.name
    assert srv._requests_step(d) == 0
    assert srv.db_op(d, "get", req) == {"t": 1.5, "text": "حط صورة جوبز", "status": "done", "reply": "حطيت الصورة"}
    assert srv.db_op(d, "get", note)["status"] == "new"
    assert json.loads((d / "edit" / "edit_plan.json").read_text(encoding="utf-8"))["shorts"][0]["title"] == "هوك"


def test_http_serves_the_room_with_its_stand_in_and_video_ranges(app):
    e = srv.create_episode("حلقة", str(app))
    d = srv.EPISODES / e["id"]
    room = d / "edit" / "work" / "suite"
    room.mkdir(parents=True)
    (room / "index.html").write_text("<html><head><title>غرفة</title></head><body>x</body></html>", encoding="utf-8")
    (d / "edit" / "final.mp4").write_bytes(bytes(range(100)))
    server = ThreadingHTTPServer(("127.0.0.1", 0), srv.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    ep = urllib.parse.quote(e["id"])
    try:
        html = urllib.request.urlopen(f"{base}/room/{ep}/").read().decode("utf-8")
        assert 'src="/ui/room-shim.js"' in html and html.index("room-shim") < html.index("<title>") and "رجوع للحلقة" in html
        r = urllib.request.urlopen(urllib.request.Request(f"{base}/files/{ep}/edit/final.mp4", headers={"Range": "bytes=10-19"}))
        assert r.status == 206 and r.read() == bytes(range(10, 20))
        state = json.loads(urllib.request.urlopen(f"{base}/api/state").read())
        assert state["episodes"][0]["done"]["render"] is True
        assert b"window.claude" in urllib.request.urlopen(f"{base}/ui/room-shim.js").read()
        with pytest.raises(urllib.error.HTTPError) as err:
            urllib.request.urlopen(f"{base}/files/{ep}/..%2F..%2F..%2Fraw.mp4")
        assert err.value.code in (403, 404)
    finally:
        server.shutdown()


FAKE_SETUP = r'''#!/usr/bin/env python3
import sys
print("Welcome to Claude Code\nBrowser didn't open? Use the url below to sign in\n")
print("https://claude.com/cai/oauth/authorize?code=true&client_id=abc&redirect_uri=x&state=st-ate_1\n")
sys.stdout.write("Paste code here if prompted > "); sys.stdout.flush()
code = sys.stdin.readline().strip()
if code == "good-code":
    print("\nYour OAuth token (valid for 1 year):\n\nsk-ant-oat01-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n")
else:
    print("\nError: invalid code")
'''


def test_linking_claude_inside_the_app(tmp_path, monkeypatch):
    monkeypatch.setattr(srv, "HOME", tmp_path / "home")
    monkeypatch.setattr(srv, "MAC", False)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "claude"
    fake.write_text(FAKE_SETUP, encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("HOME", str(tmp_path))      # no real ~/.claude.json
    link = srv.ClaudeLink()
    link.start()
    for _ in range(100):
        if link.status == "waiting":
            break
        time.sleep(0.05)
    assert link.status == "waiting" and link.url.endswith("state=st-ate_1")
    link.submit(" good-code \n")
    for _ in range(100):
        if link.status == "done":
            break
        time.sleep(0.05)
    assert link.status == "done", link.out[-300:]
    tok = srv._token_file()
    assert tok.read_text() == "sk-ant-oat01-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    assert oct(tok.stat().st_mode)[-3:] == "600"
    assert srv._env()["CLAUDE_CODE_OAUTH_TOKEN"].startswith("sk-ant-oat01-")
    assert srv.claude_logged_in() is True


def test_chat_with_the_assistant_keeps_the_conversation(app):
    d = srv.EPISODES / srv.create_episode("حلقة", str(app))["id"]
    plan = {"style": {"primary": "noir", "sections": []}, "teaser": [],
            "beats": [{"start": 0, "end": 4, "zone": "hook", "kind": "face"},
                      {"start": 4, "end": 9, "zone": "hook", "kind": "image", "query": "old factory", "caption": "مصنع"}]}
    (d / "edit" / "edit_plan.json").write_text(json.dumps(plan), encoding="utf-8")
    srv.chat_add(d, {"role": "owner", "text": "ما عجبتني الصورة", "ctx": {"t": 5.0, "timeline": "final"}})
    ctx = srv._chat_context(d, {"t": 5.0, "timeline": "final"})
    assert "المشهد 1" in ctx and "old factory" in ctx
    srv.JOB.ep = d.name
    assert srv._chat_step(d) == 0
    msgs = srv.chat_load(d)
    assert [m["role"] for m in msgs] == ["owner", "assistant"] and msgs[-1]["text"] == "تم"
    assert srv._changed_beats(plan, {**plan, "beats": [plan["beats"][0], {**plan["beats"][1], "query": "steel mill"}]}) == [1]


def test_sony_log_becomes_normal_colour():
    import numpy as np
    from editor.pipeline.luts import slog3_to_display, split_chain
    grey = (420 - 64) / 876      # Sony's 18% grey in S-Log3, as ffmpeg reads legal-range video
    out = slog3_to_display(np.array([[grey] * 3]))
    assert 0.45 < out[0][0] < 0.6
    assert slog3_to_display(np.array([[0.0] * 3]))[0][0] == 0
    pix, spatial = split_chain("curves=master='0/0 0.5/0.6 1/1',eq=saturation=1.2,noise=alls=3:allf=t")
    assert pix == "curves=master='0/0 0.5/0.6 1/1',eq=saturation=1.2" and spatial == "noise=alls=3:allf=t"


def test_scene_tools_and_undo(app, tmp_path):
    from editor.app import studio
    from editor.pipeline.paths import Episode
    d = srv.EPISODES / srv.create_episode("حلقة", str(app))["id"]
    ep = Episode(d).ensure()
    plan = {"style": {"primary": "noir", "sections": []}, "teaser": [],
            "beats": [{"start": 0, "end": 10, "zone": "hook", "kind": "face"}]}
    ep.plan.write_text(json.dumps(plan), encoding="utf-8")
    studio.snapshot(ep)
    studio.edit_beat(ep, 0, {"insert": {"t": 3, "dur": 3, "style": "title", "text": "نوكيا"}})
    beats = json.loads(ep.plan.read_text())["beats"]
    assert [b["kind"] for b in beats] == ["face", "cinematic_title", "face"] and beats[1]["title"] == "نوكيا"
    assert [(b["start"], b["end"]) for b in beats] == [(0, 3), (3, 6), (6, 10)]
    studio.edit_beat(ep, 0, {"sticker": {"type": "stamp", "text": "سري", "at": 1}})
    b0 = json.loads(ep.plan.read_text())["beats"][0]
    assert b0["kind"] == "face_fx" and b0["stickers"][0] == {"type": "stamp", "at": 1.0, "text": "سري"}
    studio.edit_beat(ep, 2, {"effect": "vhs"})
    assert json.loads(ep.plan.read_text())["beats"][2]["effect"] == "vhs"
    pic = tmp_path / "صورتي.png"
    pic.write_bytes(b"\x89PNG fake")
    studio.media_add(ep, str(pic))
    studio.edit_beat(ep, 2, {"media": "صورتي.png"})
    b2 = json.loads(ep.plan.read_text())["beats"][2]
    assert b2["kind"] == "image" and b2["pick"] == {"local": True} and (ep.assets / "img_2.png").exists()
    assert studio.undo(ep)            # back to the first snapshot: one face scene
    assert len(json.loads(ep.plan.read_text())["beats"]) == 1
    assert studio.redo(ep) and len(json.loads(ep.plan.read_text())["beats"]) == 3


def test_versions_keep_every_build_and_go_back(app):
    from editor.app import studio
    from editor.pipeline.paths import Episode
    d = srv.EPISODES / srv.create_episode("نسخ", str(app))["id"]
    ep = Episode(d).ensure()
    ep.plan.write_text('{"beats": [1]}', encoding="utf-8")
    (ep.edit / "style.txt").write_text("noir", encoding="utf-8")
    (ep.edit / "preview.mp4").write_bytes(b"first")
    assert studio.save_version(ep, auto=True)["style"] == "noir"
    ep.plan.write_text('{"beats": [1, 2]}', encoding="utf-8")
    (ep.edit / "style.txt").write_text("retro-collage", encoding="utf-8")
    (ep.edit / "preview.mp4").write_bytes(b"second")
    studio.save_version(ep, "الثانية")
    assert [(v["n"], v["style"]) for v in studio.list_versions(ep)] == [(2, "retro-collage"), (1, "noir")]
    studio.use_version(ep, 1)                        # back to the first; the current work is kept as a version first
    assert ep.plan.read_text() == '{"beats": [1]}' and (ep.edit / "preview.mp4").read_bytes() == b"first"
    vs = studio.list_versions(ep)
    assert vs[0]["n"] == 3 and (d / vs[0]["preview"]).read_bytes() == b"second"
    (ep.edit / "preview.mp4").write_bytes(b"rebuilt")   # a new build never touches a kept version
    assert (d / vs[-1]["preview"]).read_bytes() == b"first"
    studio.rename_version(ep, 3, "قبل")
    assert [v["name"] for v in studio.delete_version(ep, 2)] == ["قبل", "النسخة 1"]
    for _ in range(studio.KEEP_AUTO + 3):            # old automatic versions are cleaned, named ones stay
        studio.save_version(ep, auto=True)
    vs = studio.list_versions(ep)
    assert sum(v["auto"] for v in vs) == studio.KEEP_AUTO and "قبل" in [v["name"] for v in vs]
    with pytest.raises(ValueError):
        studio.use_version(ep, 99)


def test_the_assistant_learns_his_taste_and_uses_it_next_time(app):
    from editor.app import learning
    e = srv.create_episode("ذوق", str(app))
    d = srv.EPISODES / e["id"]
    learning.note(srv.HOME, e["id"], "options", {"captions": {"color": "yellow"}, "words": ["كبير"] * 500})
    assert "words" not in learning.events(srv.HOME)[0]["detail"]          # bulky parts are never logged
    assert learning.status(srv.HOME)["pending"] == 1 and srv.learning.prompt_block(srv.HOME) == ""
    srv.start_job(e["id"], "learn")
    _wait()
    assert srv.JOB.ok, srv.JOB.lines
    st = learning.status(srv.HOME)
    assert "كابشن أصفر" in st["taste"] and st["pending"] == 0 and st["lessons"] == 1
    assert "كابشن أصفر" in srv._plan_extra(d)                              # the next plan starts from his taste
    srv.start_job(e["id"], "learn")                                        # nothing new: no Claude call, still fine
    _wait()
    assert srv.JOB.ok and learning.status(srv.HOME)["lessons"] == 1
    learning.set_taste(srv.HOME, "")
    assert learning.taste(srv.HOME) == "" and srv.STEPS["final"][-1] == "learn"


def test_self_check_and_a_stuck_step_is_stopped(app, monkeypatch, tmp_path):
    (srv.HOME).mkdir(parents=True, exist_ok=True)
    (srv.HOME / "prefs.json").write_text("{broken", encoding="utf-8")
    rows = srv.selfcheck()
    assert any("خربان" in r["text"] for r in rows) and not (srv.HOME / "prefs.json").exists()
    assert any("المساحة" in r["text"] for r in rows)
    monkeypatch.setattr(srv, "STALL_MIN", 0.02)                           # ~1 second of silence = stuck
    real_sleep = time.sleep
    monkeypatch.setattr(srv.time, "sleep", lambda s: real_sleep(0.2 if s == 15 else s))
    t0 = time.monotonic()
    code = srv._run([sys.executable, "-c", "import time; print('hi', flush=True); time.sleep(30)"])
    assert time.monotonic() - t0 < 10 and code != 0 and any("علگت" in x for x in srv.JOB.lines)


def test_big_colour_library_has_groups_and_every_look_renders(tmp_path):
    import subprocess
    from editor.app import studio
    from editor.pipeline.grade import LOOK_GROUPS, LOOK_NAMES, LOOKS, PACK_CATS
    assert len(PACK_CATS) >= 100 and set(PACK_CATS.values()) == set(LOOK_GROUPS)
    assert all(k in LOOKS and k in LOOK_NAMES for k in PACK_CATS)
    src = tmp_path / "clip.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x180:d=2", str(src)], check=True)
    group = [k for k, g in PACK_CATS.items() if g == "night"]
    pics = studio.group_thumbs(src, tmp_path / "cache", "rec709", group + ["no-such-look"])
    assert set(pics) == set(group) and all((tmp_path / "cache" / p["img"]).exists() for p in pics.values())


def test_chatgpt_and_gemini_give_a_second_opinion_read_only(app, tmp_path):
    from editor.app import brains
    tools = srv.HOME / "tools" / "brains" / "bin"
    tools.mkdir(parents=True)
    log = tmp_path / "calls.txt"
    (tools / "codex").write_text(f"""#!/bin/sh
echo "$@" >> {log}
[ "$1" = exec ] || exit 1
while [ "$1" != "-o" ]; do shift; done
printf '1. 0:05 قوّي الهوك بخريطة' > "$2"
""")
    (tools / "agy").write_text(f"""#!/bin/sh
echo "$@" >> {log}
echo '1. 0:40 هنا ممل، حط صورة أرشيف'
""")
    for f in tools.iterdir():
        f.chmod(0o755)
    st = brains.status(srv.HOME, srv.HOME / "tools")
    assert st["chatgpt"]["installed"] and not st["chatgpt"]["linked"]
    assert brains.test("chatgpt", srv.HOME, srv.HOME / "tools")["ok"] and brains.test("gemini", srv.HOME, srv.HOME / "tools")["ok"]
    assert brains.active(srv.HOME, srv.HOME / "tools") == ["chatgpt", "gemini"]
    e = srv.create_episode("رأي", str(app))
    d = srv.EPISODES / e["id"]
    (d / "edit").mkdir(parents=True, exist_ok=True)
    (d / "edit" / "edit_plan.json").write_text(json.dumps({"beats": [{"start": 0, "end": 5, "kind": "face", "title": "نوكيا"}]}))
    srv.start_job(e["id"], "opinion")
    _wait()
    assert srv.JOB.ok, srv.JOB.lines
    assert "الهوك" in (d / "edit" / "opinions" / "chatgpt.md").read_text() and "أرشيف" in (d / "edit" / "opinions" / "gemini.md").read_text()
    calls = log.read_text()
    assert "--sandbox read-only" in calls and "workspace-write" not in calls
    brains.set_on("gemini", False, srv.HOME)
    assert brains.active(srv.HOME, srv.HOME / "tools") == ["chatgpt"]


def test_youtube_subtitles_and_titles_in_other_languages(tmp_path):
    from editor.app import youtube

    class R:
        def __init__(self, code, js=None, text=""):
            self.status_code, self._js, self.text = code, js or {}, text
        def json(self):
            return self._js

    class S:
        def __init__(self):
            self.caps, self.put_body = [], None
        def post(self, url, data=None, params=None, headers=None, timeout=None, json=None):
            self.caps.append((params, headers["Content-Type"], data))
            return R(200, {"id": "CAP"})
        def get(self, url, params=None, headers=None, timeout=None):
            return R(200, {"items": [{"snippet": {"title": "نوكيا", "description": "د", "categoryId": "27"},
                                      "localizations": {"en": {"title": "Nokia", "description": ""}}}]})
        def put(self, url, json=None, params=None, headers=None, timeout=None):
            self.put_body = json
            return R(200, {})

    (tmp_path / "youtube.json").write_text('{"refresh_token": "RT", "access_token": "AT", "expires": 9999999999}')
    srt = tmp_path / "subtitles-es.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:02,000\nHola\n", encoding="utf-8")
    s = S()
    assert youtube.upload_caption(tmp_path, "VID", "es", srt, "Español", session=s) == "CAP"
    params, ctype, body = s.caps[0]
    assert params["uploadType"] == "multipart" and ctype.startswith("multipart/related") and b"Hola" in body and b'"language": "es"' in body
    youtube.set_languages(tmp_path, "VID", {"es": {"title": "Nokia en español", "description": "x"}}, session=s)
    assert s.put_body["localizations"]["es"]["title"] == "Nokia en español" and "en" in s.put_body["localizations"]
    assert s.put_body["snippet"]["defaultLanguage"] == "ar" and s.put_body["snippet"]["title"] == "نوكيا"


def test_one_button_link_opens_the_page_and_takes_the_code(app, tmp_path):
    from editor.app import brains
    tools = srv.HOME / "tools" / "brains" / "bin"
    tools.mkdir(parents=True)
    (tools / "codex").write_text("#!/bin/sh\necho 'Open https://auth.openai.com/oauth/authorize?x=1 to sign in'\nsleep 1\necho 'Successfully logged in'\n")
    (tools / "agy").write_text("#!/bin/sh\necho 'Visit https://accounts.google.com/o/oauth2/auth?y=2'\necho 'Paste the code:'\nread c\n[ \"$c\" = 4/abc ] && echo ready\n")
    for f in tools.iterdir():
        f.chmod(0o755)
    opened = []
    for k in ("chatgpt", "gemini"):
        brains.LINKS[k].start(srv.HOME, srv.HOME / "tools", opener=opened.append)
    for _ in range(100):
        if brains.LINKS["gemini"].state()["status"] == "waiting":
            break
        time.sleep(0.05)
    brains.LINKS["gemini"].submit(" 4/abc ")
    for _ in range(100):
        if all(brains.LINKS[k].state()["status"] == "done" for k in brains.BRAINS):
            break
        time.sleep(0.05)
    assert [brains.LINKS[k].state()["status"] for k in brains.BRAINS] == ["done", "done"]
    assert any("auth.openai.com" in u for u in opened) and any("accounts.google.com" in u for u in opened)
    assert brains.active(srv.HOME, srv.HOME / "tools") == ["chatgpt", "gemini"]


def test_optional_extras_and_suggestions(app, monkeypatch):
    from editor.app import studio
    from editor.pipeline import options
    from editor.pipeline.paths import Episode
    d = srv.EPISODES / srv.create_episode("حلقة", str(app))["id"]
    ep = Episode(d).ensure()
    plan = {"style": {"primary": "noir", "sections": []}, "teaser": [], "end_screen": 20.0,
            "beats": [{"start": 0, "end": 10, "zone": "hook", "kind": "face"}]}
    ep.plan.write_text(json.dumps(plan), encoding="utf-8")
    o = options.load_options(ep)
    assert o["captions"]["on"] is False and o["pace"] == "off" and o["intro"] is False and o["outro"] is True
    assert options.pace_gaps(ep) is None
    o = options.save_options(ep, {"captions": {"on": True, "words": 9, "style": "weird"}, "pace": "fast", "outro": False})
    assert {k: o["captions"][k] for k in ("on", "style", "words", "lang")} == {"on": True, "style": "pop", "words": 6, "lang": "ar"}
    assert options.pace_gaps(ep) == options.PACE["fast"]
    assert json.loads(ep.plan.read_text())["end_screen"] == 0
    ass = options.captions_ass([("هلو", 0.0, 0.4), ("شلونكم", 0.4, 1.0), ("اليوم", 1.0, 1.5)], 2.0, 1920, 1080, "pop", 2)
    assert "Vazirmatn" in ass and "شلونكم" in ass and "0:00:02.00" in ass
    studio.edit_beat(ep, 0, {"cutout": "title", "title": "نوكيا"})
    b = json.loads(ep.plan.read_text())["beats"][0]
    assert b["kind"] == "face_cutout" and b["treatment"] == "title" and b["title"] == "نوكيا"
    studio.edit_beat(ep, 0, {"cutout": "none"})
    assert json.loads(ep.plan.read_text())["beats"][0]["kind"] == "face"
    studio.edit_beat(ep, 0, {"sfx": "whoosh"})
    assert studio.storyboard(ep)["cards"][0]["sfx"] == "whoosh"
    import editor.pipeline.sources as sources
    monkeypatch.setattr(sources, "download", lambda f, s: b"\x89PNG picked")
    studio.suggest_choose(ep, 0, {"kind": "image", "url": "https://x/a.png", "provider": "wikimedia", "title": "t",
                                  "query": "old factory", "credit": "t — a — cc"})
    b = json.loads(ep.plan.read_text())["beats"][0]
    assert b["kind"] == "image" and b["pick"]["local"] and (ep.assets / "img_0.png").read_bytes() == b"\x89PNG picked"


def test_style_library_and_plan_prompt_follow_the_chosen_style(app):
    import re
    lst = srv.styles_list()
    assert len(lst) >= 60 and len({x["category"] for x in lst}) >= 6
    assert all(x["palette"]["paper"].startswith("#") and x["name"] and not re.search("[A-Za-z]", x["name"]) for x in lst)
    d = srv.EPISODES / srv.create_episode("حلقة", str(app))["id"]
    (d / "edit").mkdir(parents=True, exist_ok=True)
    (d / "edit" / "style.txt").write_text("cyberpunk", encoding="utf-8")
    extra = srv._plan_extra(d)
    assert 'style.primary = "cyberpunk"' in extra and "face_cutout" in extra


def test_my_files_notes_own_music_and_placement(app, tmp_path):
    from editor.app import studio
    from editor.pipeline.paths import Episode
    d = srv.EPISODES / srv.create_episode("حلقة", str(app))["id"]
    ep = Episode(d).ensure()
    pic, song = tmp_path / "مصنع.png", tmp_path / "اغنية.mp3"
    pic.write_bytes(b"\x89PNG fake"); song.write_bytes(b"ID3 fake")
    studio.media_add(ep, str(pic)); studio.media_add(ep, str(song))
    studio.media_note(ep, "مصنع.png", "حطها لما أحچي عن المصنع", "auto")
    lst = studio.media_note(ep, "اغنية.mp3", "", "music")
    assert {m["name"]: m["use"] for m in lst} == {"مصنع.png": "auto", "اغنية.mp3": "music"}
    assert json.loads((ep.edit / "sound.json").read_text())["music"] == "own:اغنية.mp3"
    note = srv._files_note(d)
    assert "مصنع.png" in note and "حطها لما أحچي عن المصنع" in note and "موسيقى الحلقة" in note
    plan = {"style": {"primary": "noir", "sections": []}, "teaser": [],
            "beats": [{"start": 0, "end": 5, "zone": "hook", "kind": "image", "query": "factory",
                       "pick": {"local": True, "file": "مصنع.png"}}]}
    ep.plan.write_text(json.dumps(plan), encoding="utf-8")
    assert studio.apply_own_media(ep) == 1 and (ep.assets / "img_0.png").read_bytes() == b"\x89PNG fake"
    studio.media_note(ep, "اغنية.mp3", None, "")
    assert json.loads((ep.edit / "sound.json").read_text())["music"] == "auto"


def test_reels_pack_is_picked_main_first_and_trimmed(app, monkeypatch):
    from editor.pipeline.paths import Episode
    from editor.pipeline.shorts import transcript_lines
    d = srv.EPISODES / srv.create_episode("حلقة", str(app))["id"]
    ep = Episode(d).ensure()
    plan = {"style": {"primary": "noir", "sections": []}, "teaser": [],
            "beats": [{"start": 0, "end": 300, "zone": "body", "kind": "face"}]}
    ep.plan.write_text(json.dumps(plan), encoding="utf-8")
    ep.clean_words.write_text(json.dumps([{"t": "هلو", "s": 1.0, "e": 1.4}, {"t": "شلونكم", "s": 1.5, "e": 2.0},
                                          {"t": "اليوم", "s": 4.0, "e": 4.5}]), encoding="utf-8")
    assert transcript_lines(ep) == ["[1.0–2.0] هلو شلونكم", "[4.0–4.5] اليوم"]

    def fake(prompt):
        out = re.search(r'اكتب "([^"]+)"', prompt).group(1)
        reels = [{"from": 10, "to": 95, "main": True, "title": "الرئيسي"}, {"from": 100, "to": 180, "title": "ثاني"},
                 {"from": 200, "to": 203, "title": "قصير"}]
        open(out, "w", encoding="utf-8").write(json.dumps({"reels": reels}, ensure_ascii=False))
        return 0
    import re
    monkeypatch.setattr(srv, "_claude", fake)
    assert srv._reels_pick(d) == 0
    shorts = json.loads(ep.plan.read_text())["shorts"]
    assert [(s["from"], s["to"], s["main"]) for s in shorts] == [(10, 69, True), (100, 180, False)]
    assert "يوتيوب شورتس" in (d / "edit" / "shorts" / "posts.txt").read_text(encoding="utf-8")


def test_youtube_link_and_private_resumable_upload(tmp_path):
    from editor.app import youtube
    import urllib.parse as up

    class R:
        def __init__(self, code, js=None, headers=None, text=""):
            self.status_code, self._js, self.headers, self.text = code, js or {}, headers or {}, text
        def json(self):
            return self._js

    class S:
        def __init__(self):
            self.calls, self.meta, self.got = [], None, b""
        def post(self, url, data=None, json=None, params=None, headers=None, timeout=None):
            self.calls.append(url)
            if url == youtube.TOKEN:
                return R(200, {"access_token": "AT", "refresh_token": "RT", "expires_in": 3600})
            self.meta = json
            return R(200, headers={"Location": "https://up/1"})
        def get(self, url, params=None, headers=None, timeout=None):
            return R(200, {"items": [{"snippet": {"title": "قناتي"}}]})
        def put(self, url, data=None, headers=None, timeout=None):
            self.got += data
            a, b = headers["Content-Range"].split(" ")[1].split("/")[0].split("-")
            if int(b) + 1 < int(headers["Content-Range"].split("/")[1]):
                return R(308, headers={"Range": f"bytes=0-{b}"})
            return R(200, {"id": "VID1"})

    with pytest.raises(ValueError):
        youtube.set_client(tmp_path, "nope", "short")
    youtube.set_client(tmp_path, "123-abc.apps.googleusercontent.com", "GOCSPX-secret-value")
    url = youtube.auth_url(tmp_path, "http://127.0.0.1:1/oauth/youtube")
    q = dict(up.parse_qsl(up.urlsplit(url).query))
    assert q["code_challenge_method"] == "S256" and "youtube.upload" in q["scope"]
    s = S()
    st = youtube.finish(tmp_path, "CODE", q["state"], "http://127.0.0.1:1/oauth/youtube", session=s)
    assert st == {"client": True, "linked": True, "channel": "قناتي", "langs": True}
    assert oct((tmp_path / "youtube.json").stat().st_mode & 0o777) == "0o600"
    video = tmp_path / "v.mp4"
    video.write_bytes(b"x" * (youtube.CHUNK + 10))
    youtube.CHUNK = 1024 * 1024
    seen = []
    assert youtube.upload(tmp_path, video, "حلقة", progress=seen.append, session=s) == "VID1"
    assert s.got == video.read_bytes() and s.meta["status"]["privacyStatus"] == "private" and seen[-1] == 100


def test_script_word_file_translation_and_subtitles(app, monkeypatch):
    import io, re, zipfile
    from editor.pipeline import options
    from editor.pipeline.paths import Episode
    b = io.BytesIO(); z = zipfile.ZipFile(b, "w")
    z.writestr("word/document.xml", "<w:p><w:r><w:t>ستيف جوبز</w:t></w:r></w:p>"); z.close()
    assert srv.extract_text("s.docx", b.getvalue()) == "ستيف جوبز"
    d = srv.EPISODES / srv.create_episode("حلقة", str(app))["id"]
    ep = Episode(d).ensure()
    ep.plan.write_text(json.dumps({"style": {"primary": "noir", "sections": []}, "teaser": [],
                                   "beats": [{"start": 0, "end": 9, "zone": "hook", "kind": "face"}]}), encoding="utf-8")
    ep.clean_words.write_text(json.dumps([{"t": "هلو", "s": 1.0, "e": 1.4}, {"t": "شلونكم.", "s": 1.5, "e": 2.0},
                                          {"t": "اليوم", "s": 4.0, "e": 4.5}]), encoding="utf-8")

    def fake(prompt):
        out = re.search(r'اكتب "([^"]+)"', prompt).group(1)
        open(out, "w").write(json.dumps({"lines": [{"i": 0, "en": "Hi, how are you?"}, {"i": 1, "en": "Today"}]}))
        return 0
    monkeypatch.setattr(srv, "_claude", fake)
    assert srv._translate(d) == 0
    options.save_options(ep, {"captions": {"on": True, "lang": "en"}, "hook": 10})
    o = options.load_options(ep)
    assert o["captions"]["lang"] == "en" and o["hook"] == 10
    srt = options.subtitles_srt(ep, "en")
    assert "00:00:01,000 --> 00:00:02,150\nHi, how are you?" in srt and "Today" in srt
    assert "هلو شلونكم." in options.subtitles_srt(ep, "ar")
    assert "أول 10 ثانية" in srv._plan_extra(d)


def test_paid_ai_is_off_until_he_turns_it_on_and_versions_swap(app, tmp_path, monkeypatch):
    from editor.app import studio
    from editor.pipeline.paths import Episode
    monkeypatch.setattr(srv, "HOME", tmp_path)
    assert "ممنوع تصرف فلوس" in srv._money_rule()
    p = srv.prefs({"ai_on": True, "ai_budget": 40, "ai_variants": 9, "theme": "nope"})
    assert p["ai_on"] and p["ai_budget"] == 40 and p["ai_variants"] == 4 and p["theme"] == "forest"
    srv.face_files("add", "وجهي.jpg", b"\xff\xd8 fake")
    assert "40 دولار" in srv._money_rule() and "وجهي.jpg" in srv._money_rule()
    with pytest.raises(ValueError):
        srv.face_files("add", "x.exe", b"")
    d = srv.EPISODES / srv.create_episode("حلقة", str(app))["id"]
    ep = Episode(d).ensure()
    (ep.assets / "ai_2.png").write_bytes(b"one"); (ep.assets / "ai_2_v2.png").write_bytes(b"two")
    assert [v["used"] for v in studio.ai_variants(ep, 2)] == [True, False]
    studio.ai_choose(ep, 2, "ai_2_v2.png")
    assert (ep.assets / "ai_2.png").read_bytes() == b"two" and (ep.assets / "ai_2_v2.png").read_bytes() == b"one"
    calls = []
    monkeypatch.setattr(srv, "_claude", lambda prompt, tools=None: calls.append(tools) or 0)
    ep.plan.write_text(json.dumps({"beats": [{"kind": "ai_video"}]}), encoding="utf-8")
    assert srv._ai_step(d) == 0 and calls and "mcp__claude_ai_Higgsfield" in calls[0]


def test_style_from_a_video_he_likes(tmp_path, monkeypatch):
    import re, subprocess
    monkeypatch.setattr(srv, "HOME", tmp_path)
    monkeypatch.setenv("MONTIER_HOME", str(tmp_path))
    v = tmp_path / "مرجع.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x568:d=3", str(v)], check=True)
    seen = {}

    def fake(prompt, tools=None):
        seen["p"] = prompt
        out = re.search(r'بـ "([^"]+\.md)"', prompt).group(1)
        sid = re.search(r"name: (mine-[^،]+)،", prompt).group(1)
        noir = (srv.CODE / "editor" / "styles" / "noir.md").read_text(encoding="utf-8")
        open(out, "w", encoding="utf-8").write(noir.replace("name: noir", f"name: {sid}", 1)
                                               .replace("grade: cinema", 'grade: cinema\ntitle_ar: "ستايل مرجعي"\ncategory: "ستايلاتي"', 1))
        return 0
    monkeypatch.setattr(srv, "_claude", fake)
    srv.JOB.ep = None
    assert srv.style_from_reference(v) == 0
    assert seen["p"].count("sheet_") == 3
    mine = [x for x in srv.styles_list() if x["category"] == "ستايلاتي"]
    assert mine and mine[0]["name"] == "ستايل مرجعي"


def test_dubbing_in_his_voice_with_a_mocked_service(tmp_path):
    import subprocess
    from editor.app import dubbing
    with pytest.raises(ValueError):
        dubbing.set_key(tmp_path, "short")
    dubbing.set_key(tmp_path, "sk_" + "x" * 30)
    assert dubbing.status(tmp_path)["linked"] and oct((tmp_path / "elevenlabs.json").stat().st_mode & 0o777) == "0o600"
    v = tmp_path / "final.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x180:d=2", "-f", "lavfi", "-i",
                    "sine=d=2", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(v)], check=True)
    dubbed = tmp_path / "dub.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=600:d=2", str(dubbed)], check=True)

    class R:
        def __init__(self, code=200, js=None, content=b""):
            self.status_code, self._js, self.content, self.text = code, js or {}, content, ""
        def json(self):
            return self._js

    class S:
        polls = 0
        def post(self, url, headers=None, files=None, data=None, timeout=None):
            assert headers["xi-api-key"].startswith("sk_") and data["target_lang"] == "es" and data["source_lang"] == "ar"
            return R(js={"dubbing_id": "D1"})
        def get(self, url, headers=None, timeout=None):
            if url.endswith("/audio/es"):
                return R(content=dubbed.read_bytes())
            S.polls += 1
            return R(js={"status": "dubbed" if S.polls > 1 else "dubbing"})
    out = dubbing.dub(tmp_path, v, "es", tmp_path / "dubs", say=lambda *_: None, session=S(), poll=0)
    assert out.exists() and (tmp_path / "dubs" / "es.mp3").exists()
