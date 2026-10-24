"""The Mac app's engine: a small local web server that the app window shows (owner, 2026-10-24: "تطبيق على
الماك بوك، خاص بيه وبحاسبتي").

It runs the same editor as the cloud sessions, on his own computer:
  prep     python -m editor.pipeline prep      (download/copy, transcribe, cut, names, pictures, brief)
  plan     Claude Code, headless (`claude -p`), follows the editor skill: writes the plan, previews, fixes
  render   python -m editor.pipeline render    (the full-quality episode)
  suite    python -m editor.pipeline.suite build, and the editing room is served here, with a local stand-in for
           the Artifact runtime (db, assets, user) so the same page works on the Mac
  requests his open requests from the room → Claude → render again

One job at a time (they all want the whole CPU). Episodes live outside the code folder (MONTIER_EPISODES,
default ~/Movies/المونتير), so updating the app never touches them.

  python -m editor.app.server [--port 47823]
"""
import argparse
import json
import mimetypes
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.parse
import uuid
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
UI = Path(__file__).resolve().parent / "ui"
MAC = sys.platform == "darwin"
HOME = Path(os.environ.get("MONTIER_HOME") or (Path.home() / ("Library/Application Support/Montier" if MAC else ".local/share/montier")))
EPISODES = Path(os.environ.get("MONTIER_EPISODES") or (Path.home() / ("Movies" if MAC else "") / "المونتير"))
UPDATE_EXIT = 75          # the app window restarts the server when it exits with this
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

STEPS = {"all": ["prep", "plan", "render", "suite"], "from-plan": ["plan", "render", "suite"],
         "from-render": ["render", "suite"], "prep": ["prep"], "plan": ["plan"], "render": ["render"],
         "suite": ["suite"], "requests": ["requests", "render", "suite"], "preview": ["preview"]}
STEP_NAMES = {"prep": "التجهيز", "plan": "خطة المونتير", "render": "النسخة الكاملة", "preview": "المعاينة",
              "suite": "غرفة المونتاج", "requests": "طلباتك"}
CLAUDE_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "WebSearch", "WebFetch", "TodoWrite",
                "Bash(python -m editor.pipeline:*)", "Bash(python3 -m editor.pipeline:*)",
                "Bash(ffprobe:*)", "Bash(ffmpeg:*)", "Bash(ls:*)"]


# ---------- episodes ----------

def _slug(name: str) -> str:
    s = re.sub(r"[^\w؀-ۿ]+", "-", name.strip()).strip("-")
    return s[:60] or "حلقة"


def episode_dir(ep_id: str) -> Path:
    d = (EPISODES / ep_id).resolve()
    if d.parent != EPISODES.resolve() or not d.is_dir():
        raise KeyError(ep_id)
    return d


def _meta(d: Path) -> dict:
    f = d / "edit" / "app.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"name": d.name, "created": datetime.fromtimestamp(d.stat().st_mtime).isoformat(timespec="minutes")}


def _save_meta(d: Path, meta: dict) -> None:
    (d / "edit").mkdir(parents=True, exist_ok=True)
    (d / "edit" / "app.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


def episode_state(d: Path) -> dict:
    e = d / "edit"
    review = e / "work" / "review.json"
    score = None
    try:
        score = json.loads(review.read_text(encoding="utf-8")).get("score")
    except (OSError, ValueError, AttributeError):
        pass
    db = _db_load(d)
    reqs = [v for k, v in db.items() if k.startswith("requests/") and isinstance(v, dict) and v.get("type") != "note"]
    names = e / "work" / "names_check.txt"
    return {
        "id": d.name, **_meta(d),
        "done": {"prep": (e / "work" / "plan_input.txt").exists(), "plan": (e / "edit_plan.json").exists(),
                 "preview": (e / "preview.mp4").exists(), "render": (e / "final.mp4").exists(),
                 "suite": (e / "work" / "suite" / "data.json").exists()},
        "score": score,
        "unsure_names": names.exists() and bool(names.read_text(encoding="utf-8").strip()),
        "requests": {"open": sum(r.get("status") not in ("done",) for r in reqs),
                     "queued": sum(r.get("status") == "queued" for r in reqs)},
        "running": JOB.ep == d.name and JOB.running,
    }


def list_episodes() -> list[dict]:
    if not EPISODES.exists():
        return []
    eps = [episode_state(d) for d in EPISODES.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))]
    return sorted(eps, key=lambda e: e.get("created", ""), reverse=True)


def create_episode(name: str, source: str, script: str = "") -> dict:
    if not name.strip():
        raise ValueError("اكتب اسم الحلقة")
    if not source.strip():
        raise ValueError("اختار الفيديو الخام أو حط رابط درايف")
    if not source.startswith(("http://", "https://")) and not Path(source).expanduser().exists():
        raise ValueError("ما لگيت الفيديو بهذا المكان")
    EPISODES.mkdir(parents=True, exist_ok=True)
    base = f"{date.today().isoformat()}-{_slug(name)}"
    d, n = EPISODES / base, 2
    while d.exists():
        d, n = EPISODES / f"{base}-{n}", n + 1
    d.mkdir(parents=True)
    _save_meta(d, {"name": name.strip(), "source": source.strip(), "created": datetime.now().isoformat(timespec="minutes")})
    if script.strip():
        (d / "04-script.md").write_text(script.strip() + "\n", encoding="utf-8")
    return episode_state(d)


# ---------- the editing room's storage (stand-in for the Artifact db / assets / user) ----------

_DB_LOCK = threading.Lock()


def _db_file(d: Path) -> Path:
    return d / "edit" / "work" / "suite_db.json"


def _db_load(d: Path) -> dict:
    try:
        return json.loads(_db_file(d).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _db_save(d: Path, data: dict) -> None:
    f = _db_file(d)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(f)


def _valid_path(p: str) -> bool:
    parts = p.split("/")
    return len(parts) % 2 == 0 and all(re.fullmatch(r"[\w\-]{1,80}", x) for x in parts)


def db_op(d: Path, op: str, path: str, body=None):
    with _DB_LOCK:
        data = _db_load(d)
        if op == "get":
            return data.get(path)
        if op == "set":
            data[path] = body
        elif op == "update":
            data[path] = {**(data.get(path) or {}), **(body or {})}
        elif op == "delete":
            data.pop(path, None)
        elif op == "add":
            path = f"{path}/{uuid.uuid4().hex[:12]}"
            data[path] = body
        elif op == "list":
            pre = path + "/"
            return [{"id": k[len(pre):], "data": v} for k, v in sorted(data.items())
                    if k.startswith(pre) and "/" not in k[len(pre):]]
        _db_save(d, data)
        return {"path": path}


# ---------- jobs ----------

class Job:
    def __init__(self):
        self.ep, self.step, self.steps, self.lines = None, None, [], []
        self.running, self.ok, self.proc, self.stop_asked, self.need_login = False, None, None, False, False
        self.claude_failed = False
        self.lock = threading.Lock()

    def say(self, line: str) -> None:
        line = ANSI.sub("", line).rstrip()
        if not line.strip():
            return
        with self.lock:
            self.lines.append(line)
            if len(self.lines) > 4000:
                del self.lines[:1000]
                self.lines.insert(0, "…")
        if self.ep:
            try:
                with open(EPISODES / self.ep / "edit" / "work" / "app_log.txt", "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except OSError:
                pass


JOB = Job()


def _env() -> dict:
    env = dict(os.environ, PYTHONUNBUFFERED="1", MONTIER_APP="1",
               ABOODI_HISTORY=str(HOME / "learning" / "history.jsonl"),
               BASH_DEFAULT_TIMEOUT_MS="3600000", BASH_MAX_TIMEOUT_MS="7200000")
    (HOME / "learning").mkdir(parents=True, exist_ok=True)
    py = Path(sys.executable).parent
    env["PATH"] = os.pathsep.join([str(py), str(Path.home() / ".local" / "bin"), env.get("PATH", "")])
    return env


def claude_bin() -> str | None:
    return shutil.which("claude") or next((str(p) for p in (Path.home() / ".local/bin/claude",
                                                             Path("/opt/homebrew/bin/claude")) if p.exists()), None)


def claude_logged_in() -> bool | None:
    """A hint only (no request is spent): Claude Code keeps the signed-in account in ~/.claude.json."""
    try:
        return bool(json.loads((Path.home() / ".claude.json").read_text(encoding="utf-8")).get("oauthAccount"))
    except (OSError, ValueError):
        return None


def _run(cmd: list[str], on_line=None) -> int:
    JOB.say("")
    p = subprocess.Popen(cmd, cwd=CODE, env=_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         start_new_session=True)
    JOB.proc = p
    buf = b""
    while True:
        chunk = p.stdout.read1(4096) if hasattr(p.stdout, "read1") else p.stdout.read(4096)
        if not chunk:
            break
        buf += chunk
        parts = re.split(rb"[\r\n]", buf)
        buf = parts.pop()
        for raw in parts:
            text = raw.decode("utf-8", "replace")
            (on_line or JOB.say)(text)
    if buf:
        (on_line or JOB.say)(buf.decode("utf-8", "replace"))
    code = p.wait()
    JOB.proc = None
    return code


def _claude_line(raw: str) -> None:
    """Claude's stream (one JSON event per line) → short Arabic lines for the log."""
    try:
        ev = json.loads(raw)
    except ValueError:
        JOB.say(raw)
        return
    if ev.get("type") == "assistant":
        for c in ev.get("message", {}).get("content", []):
            if c.get("type") == "text" and c.get("text", "").strip():
                JOB.say("💬 " + c["text"].strip())
            elif c.get("type") == "tool_use":
                name, inp = c.get("name"), c.get("input") or {}
                path = Path(str(inp.get("file_path") or inp.get("path") or "")).name
                JOB.say({"Read": f"📖 يقرا {path}", "Write": f"✍️ يكتب {path}", "Edit": f"✍️ يعدّل {path}",
                         "WebSearch": f"🔎 يدوّر: {inp.get('query', '')}", "WebFetch": "🌐 يفتح صفحة",
                         "Bash": "⚙️ " + (inp.get("description") or str(inp.get("command", ""))[:90]),
                         "Glob": "🗂️ يدوّر على ملفات", "Grep": "🗂️ يدوّر داخل الملفات"}.get(name, "🔧 " + str(name)))
    elif ev.get("type") == "result":
        text = str(ev.get("result") or "")
        if ev.get("is_error") or ev.get("subtype") != "success":
            if re.search(r"login|log in|api key|auth", text, re.I):
                JOB.need_login = True
                JOB.say("🔑 كلود يحتاج تسجيل دخول: دوس «سجّل دخول كلود» بالإعدادات")
            else:
                JOB.say("❌ كلود وگف: " + text[:300])
            JOB.claude_failed = True


def _claude(prompt: str) -> int:
    exe = claude_bin()
    if not exe:
        JOB.say("❌ كلود مو منصّب. دوس «حدّث المونتير» بالإعدادات حتى ينصبه")
        return 1
    JOB.claude_failed = False
    code = _run([exe, "-p", prompt, "--output-format", "stream-json", "--verbose",
                 "--permission-mode", "acceptEdits", "--allowedTools", *CLAUDE_TOOLS], on_line=_claude_line)
    return 1 if JOB.claude_failed else code


PLAN_PROMPT = """انت المونتير الآلي لقناة صاحب القناة، وشغّال من داخل تطبيق المونتير على حاسبته. ماكو أحد يجاوبك هسة، فلا تسأل، قرر بنفسك.
الحلقة بالمجلد: {ep}
التجهيز (prep) خلص: السحب والتفريغ والقص والأسماء والصور. صاحب القناة شاف الخام ووافق.
اتبع سكيل editor من الخطوة 5 لحد 11 (الفحص الذاتي)، ويه سكيل editor-mind:
- اقرا editor/LESSONS.md و"{ep}/edit/work/plan_input.txt".
- إذا "{ep}/edit/work/names_check.txt" بيه أسماء، اعرفها من القصة، اكتب "{ep}/edit/names.json"، وعيد names وبعدها entities وbrief بـ python -m editor.pipeline.
- اكتب "{ep}/edit/edit_plan.json"، وافحصه بـ python -m editor.pipeline validate "{ep}" لحد ما يطلع ✅.
- المعاينة: python -m editor.pipeline render "{ep}" --preview (تاخذ دقايق، انتظرها). اقرا لوحات qa_sheet بعينك وصلّح الخطة لحد ما الناقد يطلع 85 أو أكثر.
- لا تطلع النسخة الكاملة (التطبيق يطلعها بعدك).
- ممنوع تصرف فلوس أو رصيد: لا ذكاء اصطناعي مدفوع (هيگزفيلد، آرتلست). الحقيقي والمجاني بس.
- كل رسائلك عربي عراقي بس. وبالآخر سطرين: شنو سويت، وشگد الدرجة."""

REQ_PROMPT = """انت المونتير الآلي، وشغّال من داخل تطبيق المونتير على حاسبة صاحب القناة. ماكو أحد يجاوبك هسة، فلا تسأل.
الحلقة: {ep}
صاحب القناة ترك طلبات بغرفة المونتاج، وهاي هي (t = الثانية بالفيديو، text = الطلب، audio_text = رسالته الصوتية مفرّغة):
{reqs}
تعديلاته بالصفحة (المشاهد والصور والريلز) رجعت للخطة. نفّذ كل طلب بتعديل "{ep}/edit/edit_plan.json" (سكيل editor، قسم غرفة المونتاج)، وافحص بـ python -m editor.pipeline validate "{ep}" لحد ما يطلع ✅. لا تطلع النسخة الكاملة (التطبيق يطلعها بعدك). ممنوع صرف فلوس أو رصيد.
بالآخر اكتب "{ep}/edit/work/requests_done.json" بهالشكل: {{"<id الطلب>": "رد قصير بالعربي العراقي: شنو سويت"}}. كل رسائلك عربي بس."""


def _voice_text(d: Path, asset_id: str) -> str:
    f = next(iter(sorted((d / "edit" / "work" / "suite_assets").glob(f"{asset_id}.*"))), None)
    if not f:
        return ""
    code = ("import sys,json\nfrom faster_whisper import WhisperModel\nfrom editor.pipeline.transcribe import WHISPER_MODEL\n"
            "m=WhisperModel(WHISPER_MODEL,device='cpu',compute_type='int8')\n"
            "s,_=m.transcribe(sys.argv[1],language='ar')\nprint(' '.join(x.text.strip() for x in s))")
    out = subprocess.run([sys.executable, "-c", code, str(f)], cwd=CODE, env=_env(), capture_output=True, text=True)
    return out.stdout.strip()


def _requests_step(d: Path) -> int:
    db = _db_load(d)
    reqs = [{"id": k.split("/", 1)[1], **v} for k, v in db.items()
            if k.startswith("requests/") and isinstance(v, dict) and v.get("status") != "done"]
    edits_file = d / "edit" / "work" / "suite_edits.json"
    edits_file.write_text(json.dumps({"edits": db.get("edits/current") or {}, "requests": reqs}, ensure_ascii=False),
                          encoding="utf-8")
    JOB.say("↩️ أرجع تعديلاتك من الغرفة للخطة…")
    if _run([sys.executable, "-m", "editor.pipeline.suite", "apply", str(d), str(edits_file)]):
        return 1
    todo = [r for r in reqs if r.get("type") != "note"]
    if not todo:
        JOB.say("✅ ماكو طلبات مفتوحة، بس تعديلاتك رجعت للخطة")
        return 0
    for r in todo:
        if r.get("audio"):
            JOB.say("🎙️ أسمع رسالتك الصوتية…")
            r["audio_text"] = _voice_text(d, r["audio"])
    lines = json.dumps([{k: r.get(k) for k in ("id", "t", "to", "text", "audio_text", "beat") if r.get(k) is not None}
                        for r in todo], ensure_ascii=False, indent=1)
    done_file = d / "edit" / "work" / "requests_done.json"
    done_file.unlink(missing_ok=True)
    code = _claude(REQ_PROMPT.format(ep=d, reqs=lines))
    try:
        replies = json.loads(done_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        replies = {}
    for r in todo:
        if r["id"] in replies or (code == 0 and not replies):
            db_op(d, "update", f"requests/{r['id']}", {"status": "done", "reply": replies.get(r["id"], "انسوّى")})
    return code


def run_job(ep_id: str, what: str) -> None:
    d = episode_dir(ep_id)
    meta = _meta(d)
    JOB.steps = STEPS[what]
    ok = True
    for step in JOB.steps:
        if JOB.stop_asked:
            break
        JOB.step = step
        JOB.say(f"━━ {STEP_NAMES[step]} ━━")
        t0 = time.monotonic()
        if step == "prep":
            code = _run([sys.executable, "-m", "editor.pipeline", "prep", str(d), "--source", meta.get("source", "")])
        elif step == "plan":
            code = _claude(PLAN_PROMPT.format(ep=d))
            if code == 0 and not (d / "edit" / "edit_plan.json").exists():
                JOB.say("❌ كلود خلص بس ما كتب الخطة")
                code = 1
        elif step == "render":
            code = _run([sys.executable, "-m", "editor.pipeline", "render", str(d)])
        elif step == "preview":
            code = _run([sys.executable, "-m", "editor.pipeline", "render", str(d), "--preview"])
        elif step == "suite":
            code = _run([sys.executable, "-m", "editor.pipeline.suite", "build", str(d), "--name", meta.get("name", d.name)])
        elif step == "requests":
            code = _requests_step(d)
        else:
            code = 1
        mins = (time.monotonic() - t0) / 60
        if JOB.stop_asked:
            JOB.say("⏹️ وگّفته")
            ok = False
            break
        if code != 0:
            JOB.say(f"❌ {STEP_NAMES[step]} ما كمل. شوف آخر الأسطر فوگ")
            ok = False
            break
        JOB.say(f"✅ {STEP_NAMES[step]} خلص ({mins:.0f} دقيقة)" if mins >= 1 else f"✅ {STEP_NAMES[step]} خلص")
    JOB.ok, JOB.running = ok and not JOB.stop_asked, False


def start_job(ep_id: str, what: str) -> None:
    episode_dir(ep_id)
    if what not in STEPS:
        raise ValueError("خطوة مو معروفة")
    with JOB.lock:
        if JOB.running:
            raise RuntimeError("اكو شغل ماشي هسة. انتظره يخلص أو وگّفه")
        JOB.ep, JOB.step, JOB.lines, JOB.running, JOB.ok, JOB.stop_asked, JOB.need_login = ep_id, None, [], True, None, False, False
    threading.Thread(target=_guard, args=(ep_id, what), daemon=True).start()


def _guard(ep_id, what):
    try:
        run_job(ep_id, what)
    except Exception as exc:   # the log must say what happened, never a silent stop
        JOB.say(f"❌ خطأ غير متوقع: {exc}")
        JOB.ok, JOB.running = False, False


def stop_job() -> None:
    JOB.stop_asked = True
    p = JOB.proc
    if p and p.poll() is None:
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except OSError:
            p.terminate()


# ---------- app actions ----------

def open_terminal(cmd: str) -> None:
    if MAC:
        script = f'tell application "Terminal"\nactivate\ndo script "{cmd}"\nend tell'
        subprocess.Popen(["osascript", "-e", script])
    else:
        raise RuntimeError("هاي تشتغل على الماك بس")


def reveal(path: Path) -> None:
    if MAC:
        subprocess.Popen(["open", "-R", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path if path.is_dir() else path.parent)])


def update_app() -> None:
    """Fresh code (and anything new to install), then the server restarts on the new code."""
    with JOB.lock:
        if JOB.running:
            raise RuntimeError("اكو شغل ماشي هسة. انتظره يخلص")
        JOB.ep, JOB.step, JOB.lines, JOB.running, JOB.ok, JOB.stop_asked = None, "update", [], True, None, False

    def go():
        code = _run(["/bin/bash", str(CODE / "app" / "setup.sh"), "--update"])
        JOB.ok, JOB.running = code == 0, False
        if code == 0:
            JOB.say("✅ تحدّث. التطبيق يرجع يشتغل هسة…")
            time.sleep(1.5)
            os._exit(UPDATE_EXIT)
    threading.Thread(target=go, daemon=True).start()


def version() -> dict:
    try:
        return json.loads((HOME / "version.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# ---------- http ----------

SHIM = '<script src="/ui/room-shim.js" data-ep="{ep}"></script>'
BACK = ('<a href="/#{ep}" style="position:fixed;bottom:14px;left:14px;z-index:99999;background:#FF3B55;color:#fff;'
        'font:600 13px system-ui;padding:8px 14px;border-radius:20px;text-decoration:none;box-shadow:0 4px 14px #0006">'
        'رجوع للحلقة ←</a>')


class Handler(BaseHTTPRequestHandler):
    server_version = "Montier"

    def log_message(self, *a):
        pass

    def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8", extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _err(self, msg: str, code=400):
        self._json({"error": msg}, code)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        return json.loads(raw.decode("utf-8")) if raw else {}

    def _file(self, path: Path):
        if not path.is_file():
            return self._err("مو موجود", 404)
        size = path.stat().st_size
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        rng = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range") or "")
        start, end, code = 0, size - 1, 200
        if rng and size:
            a, b = rng.groups()
            start = int(a) if a else max(0, size - int(b or 0))
            end = min(size - 1, int(b)) if a and b else size - 1
            if start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return
            code = 206
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Cache-Control", "no-cache")
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if self.command == "HEAD":
            return
        with open(path, "rb") as f:
            f.seek(start)
            left = end - start + 1
            try:
                while left > 0:
                    chunk = f.read(min(1 << 20, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

    # --- routes ---
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path)
        path, q = urllib.parse.unquote(u.path), dict(urllib.parse.parse_qsl(u.query))
        try:
            if path in ("/", "/index.html"):
                return self._file(UI / "index.html")
            if path.startswith("/ui/"):
                f = (UI / path[4:]).resolve()
                return self._file(f) if f.is_relative_to(UI) else self._err("لا", 403)
            if path == "/api/ping":
                return self._json({"ok": True})
            if path == "/api/state":
                return self._json({"episodes": list_episodes(), "folder": str(EPISODES), "mac": MAC,
                                   "claude": {"installed": bool(claude_bin()), "logged_in": claude_logged_in()},
                                   "version": version(),
                                   "job": {"ep": JOB.ep, "running": JOB.running, "step": JOB.step}})
            if path == "/api/log":
                since = int(q.get("since") or 0)
                with JOB.lock:
                    lines, total = JOB.lines[since:], len(JOB.lines)
                return self._json({"ep": JOB.ep, "lines": lines, "next": total, "running": JOB.running, "ok": JOB.ok,
                                   "step": JOB.step, "steps": JOB.steps, "need_login": JOB.need_login})
            m = re.match(r"^/api/db/([^/]+)/(doc|list)$", path)
            if m:
                d = episode_dir(m.group(1))
                p = q.get("path", "")
                if m.group(2) == "doc":
                    return self._json(db_op(d, "get", p) if _valid_path(p) else None)
                return self._json(db_op(d, "list", p) if re.fullmatch(r"[\w\-]{1,80}", p) else [])
            m = re.match(r"^/files/([^/]+)/(.+)$", path)
            if m:
                d = episode_dir(m.group(1))
                f = (d / m.group(2)).resolve()
                return self._file(f) if f.is_relative_to(d) else self._err("لا", 403)
            m = re.match(r"^/room/([^/]+)/(.*)$", path)
            if m:
                d = episode_dir(m.group(1))
                root = d / "edit" / "work" / "suite"
                rel = m.group(2) or "index.html"
                if rel.startswith("_voice/"):
                    f = (d / "edit" / "work" / "suite_assets" / rel[7:]).resolve()
                    return self._file(f) if f.is_relative_to(d) else self._err("لا", 403)
                f = (root / rel).resolve()
                if not f.is_relative_to(root):
                    return self._err("لا", 403)
                if rel == "index.html" and f.exists():
                    ep = urllib.parse.quote(d.name)
                    html = f.read_text(encoding="utf-8")
                    html = re.sub(r"(<head[^>]*>)", lambda mm: mm.group(1) + SHIM.format(ep=ep), html, count=1)
                    html = html.replace("</body>", BACK.format(ep=ep) + "</body>") if "</body>" in html else html + BACK.format(ep=ep)
                    return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
                return self._file(f)
            if re.match(r"^/room/[^/]+$", path):
                self.send_response(302)
                self.send_header("Location", u.path + "/")
                self.end_headers()
                return
            return self._err("مو موجود", 404)
        except KeyError:
            return self._err("الحلقة مو موجودة", 404)

    def do_POST(self):
        path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))
        try:
            if path == "/api/episodes":
                b = self._body()
                return self._json(create_episode(b.get("name", ""), b.get("source", ""), b.get("script", "")))
            m = re.match(r"^/api/episodes/([^/]+)/(run|stop|reveal|rename)$", path)
            if m:
                ep, act = m.groups()
                d = episode_dir(ep)
                b = self._body()
                if act == "run":
                    start_job(ep, b.get("what", "all"))
                elif act == "stop":
                    stop_job()
                elif act == "reveal":
                    target = {"final": d / "edit" / "final.mp4", "preview": d / "edit" / "preview.mp4"}.get(b.get("what"), d)
                    reveal(target if target.exists() else d)
                elif act == "rename":
                    meta = _meta(d)
                    meta["name"] = (b.get("name") or meta["name"]).strip()
                    _save_meta(d, meta)
                return self._json({"ok": True})
            if path == "/api/claude-login":
                exe = claude_bin()
                if not exe:
                    raise RuntimeError("كلود مو منصّب بعد")
                open_terminal(exe)
                return self._json({"ok": True})
            if path == "/api/open-folder":
                EPISODES.mkdir(parents=True, exist_ok=True)
                reveal(EPISODES)
                return self._json({"ok": True})
            if path == "/api/update":
                update_app()
                return self._json({"ok": True})
            m = re.match(r"^/api/db/([^/]+)/add$", path)
            if m:
                d = episode_dir(m.group(1))
                col = q.get("col", "")
                if not re.fullmatch(r"[\w\-]{1,80}", col):
                    return self._err("لا")
                return self._json(db_op(d, "add", col, self._body()))
            return self._err("مو موجود", 404)
        except KeyError:
            return self._err("الحلقة مو موجودة", 404)
        except (ValueError, RuntimeError) as exc:
            return self._err(str(exc))

    def do_PUT(self):
        u = urllib.parse.urlsplit(self.path)
        path, q = urllib.parse.unquote(u.path), dict(urllib.parse.parse_qsl(u.query))
        try:
            m = re.match(r"^/api/db/([^/]+)/doc$", path)
            if m:
                d = episode_dir(m.group(1))
                p = q.get("path", "")
                if not _valid_path(p):
                    return self._err("لا")
                return self._json(db_op(d, "set", p, self._body()))
            m = re.match(r"^/api/db/([^/]+)/asset$", path)
            if m:   # a voice note from the room
                d = episode_dir(m.group(1))
                n = int(self.headers.get("Content-Length") or 0)
                if n > 50 * 1024 * 1024:
                    return self._err("الملف كبير", 413)
                ext = {"audio/webm": "webm", "audio/mp4": "m4a", "audio/ogg": "ogg", "audio/wav": "wav"}.get(
                    (q.get("type") or "").split(";")[0], "webm")
                aid = uuid.uuid4().hex
                out = d / "edit" / "work" / "suite_assets"
                out.mkdir(parents=True, exist_ok=True)
                (out / f"{aid}.{ext}").write_bytes(self.rfile.read(n))
                return self._json({"id": aid, "url": f"/room/{urllib.parse.quote(d.name)}/_voice/{aid}.{ext}",
                                   "sizeBytes": n, "contentType": q.get("type") or "audio/webm"})
            if path == "/api/upload":   # a video dropped on the window (copied next to the episodes)
                name = re.sub(r"[/\\]", "_", q.get("name") or "خام.mp4")
                dest = EPISODES / "_الخام" / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                left = int(self.headers.get("Content-Length") or 0)
                with open(dest, "wb") as f:
                    while left > 0:
                        chunk = self.rfile.read(min(1 << 20, left))
                        if not chunk:
                            break
                        f.write(chunk)
                        left -= len(chunk)
                return self._json({"path": str(dest)})
            return self._err("مو موجود", 404)
        except KeyError:
            return self._err("الحلقة مو موجودة", 404)

    def do_PATCH(self):
        u = urllib.parse.urlsplit(self.path)
        path, q = urllib.parse.unquote(u.path), dict(urllib.parse.parse_qsl(u.query))
        m = re.match(r"^/api/db/([^/]+)/doc$", path)
        try:
            if m and _valid_path(q.get("path", "")):
                return self._json(db_op(episode_dir(m.group(1)), "update", q["path"], self._body()))
        except KeyError:
            return self._err("الحلقة مو موجودة", 404)
        return self._err("لا")

    def do_DELETE(self):
        u = urllib.parse.urlsplit(self.path)
        path, q = urllib.parse.unquote(u.path), dict(urllib.parse.parse_qsl(u.query))
        m = re.match(r"^/api/db/([^/]+)/doc$", path)
        try:
            if m and _valid_path(q.get("path", "")):
                return self._json(db_op(episode_dir(m.group(1)), "delete", q["path"]))
        except KeyError:
            return self._err("الحلقة مو موجودة", 404)
        return self._err("لا")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m editor.app.server")
    ap.add_argument("--port", type=int, default=47823)
    a = ap.parse_args(argv)
    EPISODES.mkdir(parents=True, exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    srv.daemon_threads = True

    def bye(*_):
        stop_job()
        os._exit(0)
    signal.signal(signal.SIGTERM, bye)
    print(f"المونتير شغّال: http://127.0.0.1:{a.port}  (الحلقات: {EPISODES})", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
