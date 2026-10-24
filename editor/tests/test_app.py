"""The Mac app's engine (editor/app/server.py), with a stand-in for Claude so nothing is spent."""
import json
import os
import stat
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
