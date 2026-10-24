"""URU's engine (the Mac app, first named المونتير): a small local web server that the app window shows (owner, 2026-10-24: "تطبيق على
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
         "from-render": ["render", "suite"], "prep": ["prep"], "plan": ["plan", "images"], "render": ["render"],
         "suite": ["suite"], "requests": ["requests", "render"], "preview": ["preview"],
         # the studio's steps (one screen each)
         "prepare": ["fetch", "transcribe"], "cut": ["cut"], "sentences": ["sentences"], "captions": ["captions"],
         "images": ["images"], "build": ["preview"], "final": ["render"], "assist": ["assist"],
         "auto": ["fetch", "transcribe", "cut", "plan", "images", "render"], "chat": ["chat"],
         "shorts": ["shorts"], "export": ["export"]}
STEP_NAMES = {"prep": "التجهيز", "plan": "خطة المونتير", "render": "النسخة الكاملة", "preview": "المعاينة",
              "suite": "غرفة المونتاج", "requests": "ملاحظاتك", "fetch": "تجهيز الفيديو", "transcribe": "تفريغ الكلام",
              "cut": "قص المقطع", "sentences": "المساعد يراجع الجمل", "captions": "المساعد يراجع الكابشن",
              "images": "الصور", "assist": "المساعد", "chat": "المساعد", "shorts": "الريلز", "export": "التصدير"}
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
        "done": {"fetch": (e / "work" / "source.mp4").exists(), "transcribe": (e / "transcript.json").exists(),
                 "proxy_source": (e / "work" / "app" / "proxy_source.mp4").exists(),
                 "proxy_clean": (e / "work" / "app" / "proxy_clean.mp4").exists(),
                 "cut": (e / "work" / "clean.mp4").exists() and (e / "work" / "plan_input.txt").exists(),
                 "prep": (e / "work" / "plan_input.txt").exists(), "plan": (e / "edit_plan.json").exists(),
                 "preview": (e / "preview.mp4").exists(), "render": (e / "final.mp4").exists(),
                 "suite": (e / "work" / "suite" / "data.json").exists()},
        "score": score,
        "unsure_names": names.exists() and bool(names.read_text(encoding="utf-8").strip()),
        "requests": {"open": sum(r.get("status") not in ("done",) for r in reqs),
                     "queued": sum(r.get("status") == "queued" for r in reqs)},
        "running": JOB.ep == d.name and JOB.running,
    }


def trash_episode(ep_id: str) -> None:
    """Delete from the app = move to the Mac's Trash (it can still be brought back from there)."""
    d = episode_dir(ep_id)
    if JOB.running and JOB.ep == ep_id:
        raise RuntimeError("هالحلقة دا تشتغل هسة. وگّفها أول")
    if MAC:
        target = Path.home() / ".Trash" / d.name
        n = 2
        while target.exists():
            target, n = Path.home() / ".Trash" / f"{d.name} {n}", n + 1
    else:
        target = EPISODES / ".trash" / d.name
        target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(d), str(target))


def list_episodes() -> list[dict]:
    if not EPISODES.exists():
        return []
    eps = [episode_state(d) for d in EPISODES.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))]
    return sorted(eps, key=lambda e: e.get("created", ""), reverse=True)


def create_episode(name: str, source: str, script: str = "", look: dict | None = None, lut_key: str = "") -> dict:
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
    if look:
        from editor.pipeline.paths import Episode
        from .studio import save_look
        lut = HOME / "cache" / re.sub(r"[^0-9a-f]", "", lut_key) / "look.cube" if lut_key else None
        if lut and lut.exists():
            (d / "edit").mkdir(parents=True, exist_ok=True)
            shutil.copyfile(lut, d / "edit" / "look.cube")
            look = {**look, "lut": True}
        save_look(Episode(d), look)
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
        self.progress, self.message, self.started, self.last_reply = None, "", 0.0, ""
        self.lock = threading.Lock()

    def say(self, line: str) -> None:
        line = ANSI.sub("", line).rstrip()
        if not line.strip():
            return
        m = re.fullmatch(r"@@ (\d+)", line.strip())
        if m:   # a stage telling how far it is (transcription: "@@ 41")
            self.progress = int(m.group(1))
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
    tok = HOME / "claude_token"
    if tok.exists() and tok.read_text(encoding="utf-8").strip():   # linked from the app (ClaudeLink)
        env["CLAUDE_CODE_OAUTH_TOKEN"] = tok.read_text(encoding="utf-8").strip()
    py = Path(sys.executable).parent
    env["PATH"] = os.pathsep.join([str(py), str(Path.home() / ".local" / "bin"), env.get("PATH", "")])
    return env


def claude_bin() -> str | None:
    return shutil.which("claude") or next((str(p) for p in (Path.home() / ".local/bin/claude",
                                                             Path("/opt/homebrew/bin/claude")) if p.exists()), None)


def _token_file() -> Path:
    return HOME / "claude_token"


def claude_logged_in() -> bool | None:
    """A hint only (no request is spent): the app's own link (a long-lived token from `claude setup-token`), or
    Claude Code's signed-in account in ~/.claude.json."""
    if _token_file().exists() and _token_file().read_text(encoding="utf-8").strip():
        return True
    try:
        return bool(json.loads((Path.home() / ".claude.json").read_text(encoding="utf-8")).get("oauthAccount"))
    except (OSError, ValueError):
        return None


class ClaudeLink:
    """Linking his Claude account from inside the app, in Arabic, without the terminal (owner, 2026-10-24: "ما
    گدرت أربطه"). Runs `claude setup-token` in a pseudo-terminal: it opens the browser on the sign-in page; after
    he approves, the page shows a code that he pastes in the app; the long-lived token it prints is kept in
    HOME/claude_token (only his user can read it) and given to every Claude run as CLAUDE_CODE_OAUTH_TOKEN."""

    def __init__(self):
        self.status, self.url, self.error, self.pid, self.fd, self.out = "idle", "", "", None, None, ""
        self.lock = threading.Lock()

    def start(self) -> dict:
        import fcntl
        import pty
        import struct
        import termios
        exe = claude_bin()
        if not exe:
            raise RuntimeError("كلود مو منصّب بعد. دوس «حدّث» بالإعدادات")
        self.cancel()
        env = {k: v for k, v in _env().items() if k not in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY")}
        env["TERM"] = "xterm-256color"
        pid, fd = pty.fork()
        if pid == 0:   # the child: claude itself
            try:
                os.execvpe(exe, [exe, "setup-token"], env)
            finally:
                os._exit(127)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 50, 1000, 0, 0))   # the link stays on one line
        with self.lock:
            self.status, self.url, self.error, self.pid, self.fd, self.out = "starting", "", "", pid, fd, ""
        threading.Thread(target=self._read, daemon=True).start()
        return self.state()

    def _read(self) -> None:
        import select
        fd = self.fd
        while True:
            try:
                r, _, _ = select.select([fd], [], [], 1.0)
                if not r:
                    if self.status in ("done", "error", "idle"):
                        break
                    continue
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            text = ANSI.sub(" ", chunk.decode("utf-8", "replace")).replace("\x1b", "")   # cursor moves stand for spaces
            with self.lock:
                self.out = (self.out + text)[-20000:]
                flat = re.sub(r"\s+", "", self.out)
                m = re.search(r"https://\S*oauth/authorize\?\S*state=[\w\-]+", self.out)   # one line (1000 columns)
                if m and not self.url:
                    self.url, self.status = m.group(0), "waiting"
                    if MAC:   # claude opens the browser itself too; this is the fallback
                        subprocess.Popen(["open", self.url])
                tok = re.search(r"(sk-ant-oat[\w\-]{20,})", self.out)
                if tok:
                    _token_file().parent.mkdir(parents=True, exist_ok=True)
                    _token_file().write_text(tok.group(1), encoding="utf-8")
                    os.chmod(_token_file(), 0o600)
                    self.status = "done"
                elif re.search(r"(?i)invalid|error|failed|expired", flat[-400:]) and self.status == "checking":
                    self.status, self.error = "error", "الرمز ما زبط. جرّب مرة ثانية من الأول"
        with self.lock:
            if self.status not in ("done", "error"):
                self.status, self.error = "error", "انسكر قبل ما يخلص. جرّب مرة ثانية"
        self._reap()

    def submit(self, code: str) -> dict:
        code = re.sub(r"\s+", "", code or "")
        if not code:
            raise ValueError("الصق الرمز أول")
        with self.lock:
            if self.fd is None or self.status != "waiting":
                raise RuntimeError("ابدأ الربط من جديد")
            os.write(self.fd, code.encode() + b"\r")
            self.status = "checking"
        return self.state()

    def cancel(self) -> None:
        with self.lock:
            if self.pid:
                try:
                    os.kill(self.pid, signal.SIGTERM)
                except OSError:
                    pass
            self.status = "idle" if self.status != "done" else "done"
        self._reap()

    def _reap(self) -> None:
        if self.pid:
            try:
                os.waitpid(self.pid, os.WNOHANG)
            except OSError:
                pass

    def state(self) -> dict:
        return {"status": self.status, "url": self.url, "error": self.error, "linked": bool(claude_logged_in())}


LINK = ClaudeLink()


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
        JOB.last_reply = text.strip()
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
القص والتفريغ والأسماء خلصت (صاحب القناة راجع الجمل والكابشن بنفسه).
اتبع سكيل editor من الخطوة 5 لحد 8، ويه سكيل editor-mind:
- اقرا editor/LESSONS.md و"{ep}/edit/work/plan_input.txt".
- إذا "{ep}/edit/work/names_check.txt" بيه أسماء، اعرفها من القصة، اكتب "{ep}/edit/names.json"، وعيد names وبعدها entities وbrief بـ python -m editor.pipeline.
- اكتب "{ep}/edit/edit_plan.json"، وافحصه بـ python -m editor.pipeline validate "{ep}" لحد ما يطلع ✅.
{extra}
- لا تطلع معاينة ولا النسخة الكاملة (التطبيق يجيب الصور ويطلعها بعدك).
- ممنوع تصرف فلوس أو رصيد: لا ذكاء اصطناعي مدفوع (هيگزفيلد، آرتلست). الحقيقي والمجاني بس.
- كل رسائلك عربي عراقي بس. وبالآخر سطر: شنو الفكرة البصرية للحلقة."""

SENT_PROMPT = """انت مساعد المونتاج بتطبيق المونتير على حاسبة صاحب القناة. ماكو أحد يجاوبك هسة، فلا تسأل.
بالملف "{file}" جمل الحلقة كلها: i رقم الجملة، s ثانيتها بالخام، text الكلام، keep هل القص الآلي يخليها، why ليش انحذفت.
راجع اختيار القص الآلي: الإعادات والبدايات المتعثرة والجمل الناقصة تنحذف، وإذا جملة انعادت أكثر من مرة تبقى أحسن نسخة (عادة الأخيرة).
المزحة والسالفة الجانبية والمعلومة الإضافية تبقى (قاعدة صاحب القناة). لا تحذف كلام مفيد.
{message}
اكتب "{out}" بهالشكل بس: {{"summary": "سطر عربي عراقي: شگد جملة اقترحت تنحذف وليش", "drop": [أرقام الجمل], "keep": [أرقام الجمل], "why": {{"رقم": "سبب قصير"}}}}.
لا تعدّل أي ملف ثاني."""

CAP_PROMPT = """انت مساعد المونتاج بتطبيق المونتير. ماكو أحد يجاوبك هسة، فلا تسأل.
بالملف "{file}" كلام الحلقة بعد القص كلمة كلمة: i رقم الكلمة، t الكلمة، doubt إذا التفريغ مو متأكد منها. الكلام عراقي، والحلقة عن: {topic}.
{context}
صحّح بس الغلط الواضح: أسماء أشخاص وشركات وبلدان انكتبت غلط، وكلمة عراقية انكتبت فصحى (اكتبها مثل ما انگالت)، وكلمة ما إلها معنى بمكانها. لا تغيّر أسلوب كلامه.
والكلمات الي مو متأكد منها، اسأله عنها بخيارات (لا تخمّن).
{message}
اكتب "{out}" بهالشكل بس: {{"summary": "سطر عربي: صححت كذا كلمة، وعندي كذا سؤال", "fixes": [{{"i": رقم, "old": "الكلمة", "new": "الصح", "why": "سبب قصير"}}], "questions": [{{"i": رقم, "q": "السؤال", "options": ["خيار", "خيار"]}}]}}.
للتصحيح الي يشمل أكثر من كلمة، حط i أول كلمة وnew كل الكلام. لا تعدّل أي ملف ثاني."""

ASSIST_PROMPT = """انت مساعد المونتاج بتطبيق المونتير على حاسبة صاحب القناة. ماكو أحد يجاوبك هسة غير هالرسالة، فلا تسأل.
الحلقة: {ep}
صاحب القناة يگول: «{message}»
نفّذ طلبه بأحسن طريقة حسب سكيل editor (الخطة "{ep}/edit/edit_plan.json"، والفحص بـ python -m editor.pipeline validate). لا تطلع معاينة ولا نسخة كاملة. ممنوع صرف فلوس.
بالآخر اكتب سطر أو سطرين بالعربي العراقي: شنو سويت."""

REQ_PROMPT = """انت المونتير الآلي، وشغّال من داخل تطبيق المونتير على حاسبة صاحب القناة. ماكو أحد يجاوبك هسة، فلا تسأل.
الحلقة: {ep}
صاحب القناة ترك طلبات بغرفة المونتاج، وهاي هي (t = الثانية بالفيديو، text = الطلب، audio_text = رسالته الصوتية مفرّغة):
{reqs}
تعديلاته بالصفحة (المشاهد والصور والريلز) رجعت للخطة. نفّذ كل طلب بتعديل "{ep}/edit/edit_plan.json" (سكيل editor، قسم غرفة المونتاج)، وافحص بـ python -m editor.pipeline validate "{ep}" لحد ما يطلع ✅. لا تطلع النسخة الكاملة (التطبيق يطلعها بعدك). ممنوع صرف فلوس أو رصيد.
بالآخر اكتب "{ep}/edit/work/requests_done.json" بهالشكل: {{"<id الطلب>": "رد قصير بالعربي العراقي: شنو سويت"}}. كل رسائلك عربي بس."""


CHAT_PROMPT = """انت مساعد المونتاج بتطبيق URU على حاسبة صاحب القناة، وتحچي وياه مثل مونتير صاحبه. هو يشوف الحلقة ويحچي وياك.
الحلقة: {ep}
المحادثة لحد هسة:
{history}
صاحب القناة يگول هسة: «{message}»
{context}
الملفات الي تگدر تغيّرها:
- الخطة "{ep}/edit/edit_plan.json": المشاهد (beats) بأوقات الفيديو النهائي، حسب سكيل editor. صورة ما عجبته: غيّر query (كلمات بحث إنگليزية أدق) أو النوع، وامسح pick. موشن جرافك: graphic أو kinetic أو face_paper. صوت بمكان معيّن: sfx بالمشهد.
- الألوان "{ep}/edit/look.json": look من ({looks})، source (rec709 أو slog3 لسوني لوگ ٣)، strength من 0 لـ 1، temp وtint من -100 لـ 100، exposure من -2 لـ 2.
- الصوت "{ep}/edit/sound.json": clean من 0 لـ 3 (تنظيف الصوت)، music (auto أو tension أو wonder أو sad أو drive أو dark أو calm أو off)، level من -32 لـ -16 (علو الموسيقى)، sfx (true/false).
- الجمل: "{ep}/edit/cuts_override.json" (drop/keep بثواني الخام) إذا يريد يشيل أو يرجّع كلام.
نفّذ طلبه، وإذا غيّرت الخطة افحصها بـ python -m editor.pipeline validate "{ep}" لحد ما يطلع ✅. إذا طلبه مو واضح، اسأله سؤال واحد قصير بدال ما تخمّن.
لا تطلع معاينة ولا نسخة كاملة (التطبيق يطلعها لما يريد). ممنوع صرف فلوس أو رصيد.
آخر شي تكتبه: سطر أو سطرين بالعربي العراقي تخاطبه بيهم: شنو سويت (أو سؤالك). بلا ولا كلمة إنگليزي."""


def _chat_file(d: Path) -> Path:
    return d / "edit" / "work" / "app" / "chat.json"


def chat_load(d: Path) -> list[dict]:
    try:
        return json.loads(_chat_file(d).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def chat_add(d: Path, msg: dict) -> list[dict]:
    msgs = chat_load(d) + [{**msg, "at": datetime.now().isoformat(timespec="seconds")}]
    _chat_file(d).parent.mkdir(parents=True, exist_ok=True)
    _chat_file(d).write_text(json.dumps(msgs[-200:], ensure_ascii=False, indent=1), encoding="utf-8")
    return msgs


def _chat_context(d: Path, ctx: dict) -> str:
    """Where he is when he talks: the moment and the scene under the playhead."""
    if not ctx or ctx.get("t") is None:
        return ""
    t = float(ctx["t"])
    out = [f"هو واگف عند الثانية {t:.1f} من {'الفيديو النهائي' if ctx.get('timeline') == 'final' else 'الفيديو بعد القص'}."]
    try:
        plan = json.loads((d / "edit" / "edit_plan.json").read_text(encoding="utf-8"))
        off = 0.0 if ctx.get("timeline") == "final" else sum(e - s for s, e in plan.get("teaser", []))
        i = next((k for k, b in enumerate(plan["beats"]) if b["start"] <= t + off < b["end"]), None)
        if ctx.get("scene") is not None:
            i = int(ctx["scene"])
        if i is not None:
            b = plan["beats"][i]
            out.append(f"المشهد {i} ({b['start']:.1f}–{b['end']:.1f} ث) نوعه {b['kind']}: " +
                       json.dumps({k: v for k, v in b.items() if k not in ("start", "end", "zone")}, ensure_ascii=False))
    except (OSError, ValueError, KeyError, StopIteration):
        pass
    return "\n".join(out)


def _changed_beats(before: dict, after: dict) -> list[int]:
    """Scenes whose picture must be fetched again (search words, chosen picture or kind changed)."""
    out = []
    for i, b in enumerate(after.get("beats", [])):
        old = before.get("beats", [])[i] if i < len(before.get("beats", [])) else {}
        if any(b.get(k) != old.get(k) for k in ("query", "pick", "kind", "entity", "source")):
            out.append(i)
    return out


def _chat_step(d: Path) -> int:
    from editor.pipeline.grade import LOOK_NAMES
    msgs = chat_load(d)
    history = "\n".join(f"{'هو' if m['role'] == 'owner' else 'انت'}: {m['text']}" for m in msgs[-12:-1]) or "(أول رسالة)"
    last = msgs[-1] if msgs else {"text": JOB.message, "ctx": {}}
    plan_f = d / "edit" / "edit_plan.json"
    before = json.loads(plan_f.read_text(encoding="utf-8")) if plan_f.exists() else {}
    from editor.pipeline.paths import Episode
    from .studio import snapshot
    snapshot(Episode(d))   # what the assistant changes can be undone too
    JOB.last_reply = ""
    code = _claude(CHAT_PROMPT.format(ep=d, history=history, message=last["text"], context=_chat_context(d, last.get("ctx") or {}),
                                      looks="، ".join(LOOK_NAMES)))
    after = json.loads(plan_f.read_text(encoding="utf-8")) if plan_f.exists() else {}
    changed = before != after
    redo = _changed_beats(before, after) if changed else []
    for i in redo:   # its old picture goes, so the new search brings a new one
        for f in (d / "edit" / "assets").glob(f"img_{i}.*"):
            f.unlink(missing_ok=True)
    reply = JOB.last_reply or ("سويتها." if code == 0 else "ما گدرت أكمل، جرّب مرة ثانية.")
    chat_add(d, {"role": "assistant", "text": reply, "changed": changed, "ok": code == 0})
    if code == 0 and redo:
        JOB.say("🖼️ أجيب الصور الجديدة…")
        _pipe("images", d)
    return code


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


def _pipe(stage: str, d: Path, *extra: str) -> int:
    return _run([sys.executable, "-m", "editor.pipeline", stage, str(d), *extra])


def _plan_extra(d: Path) -> str:
    """The owner's idea, his chosen look and sound, and his notes on the old plan's cards, for the plan prompt."""
    lines = []
    idea = d / "edit" / "idea.txt"
    if idea.exists() and idea.read_text(encoding="utf-8").strip():
        lines.append("- فكرة صاحب القناة للحلقة (التزم بيها): «" + idea.read_text(encoding="utf-8").strip() + "»")
    try:
        opts = json.loads((d / "edit" / "options.json").read_text(encoding="utf-8"))
        pace = {"calm": "هادئ (مشاهد أطول، وقفات أكثر)", "normal": "عادي", "fast": "سريع (مشاهد قصيرة، تغيير كل ٢–٤ ثواني، هوك سريع جداً)"}.get(opts.get("pace"))
        if pace:
            lines.append(f"- الرتم: صاحب القناة خلّاه عليك، وريده {pace}. اضبط طول المشاهد والانتقالات على هذا.")
    except (OSError, ValueError):
        pass
    sf = d / "edit" / "style.txt"
    if sf.exists() and sf.read_text(encoding="utf-8").strip():
        lines.append(f"- الستايل: صاحب القناة اختار «{sf.read_text(encoding='utf-8').strip()}» (style.primary).")
    if (d / "edit" / "look.json").exists():
        lines.append('- الألوان اختارها صاحب القناة (edit/look.json): لا تحط "grade" بالخطة.')
    try:
        snd = json.loads((d / "edit" / "sound.json").read_text(encoding="utf-8"))
        if snd.get("music") not in (None, "auto"):
            lines.append(f"- الموسيقى: صاحب القناة اختار «{snd['music']}» (off = بلا موسيقى).")
    except (OSError, ValueError):
        pass
    try:
        old = json.loads((d / "edit" / "edit_plan.json").read_text(encoding="utf-8"))
        notes = [f"  مشهد {i} ({b['start']:.1f}–{b['end']:.1f} ث): {b['note']}" for i, b in enumerate(old.get("beats", []))
                 if b.get("note")]
        if notes:
            lines.append("- اكو خطة قديمة، وصاحب القناة كتب ملاحظات على مشاهدها؛ طبقها بالخطة الجديدة وامسح note:\n" + "\n".join(notes))
    except (OSError, ValueError):
        pass
    if JOB.message:
        lines.append(f"- وطلب هسة: «{JOB.message}»")
    return "\n".join(lines)


def _review_step(d: Path, kind: str) -> int:
    """The assistant reads the sentences or the captions and writes its suggestions (the screen shows them)."""
    from editor.pipeline.paths import Episode
    from . import studio
    ep = Episode(d)
    app = d / "edit" / "work" / "app"
    app.mkdir(parents=True, exist_ok=True)
    out = app / f"{kind}_review.json"
    out.unlink(missing_ok=True)
    msg = f"وصاحب القناة يگول: «{JOB.message}»" if JOB.message else ""
    if kind == "sentences":
        data = studio.sentences(ep)
        f = app / "sentences_in.json"
        f.write_text(json.dumps([{k: x[k] for k in ("i", "s", "text", "keep", "why")} for x in data["items"]],
                                ensure_ascii=False), encoding="utf-8")
        code = _claude(SENT_PROMPT.format(file=f, out=out, message=msg))
    else:
        caps = studio.captions(ep)
        f = app / "captions_in.json"
        f.write_text(json.dumps([{"i": w["i"], "t": w["t"], **({"doubt": True} if w["doubt"] else {})}
                                 for line in caps["lines"] for w in line], ensure_ascii=False), encoding="utf-8")
        ctx = []
        for name in ("04-script.md", "02-draft.md"):
            if (d / name).exists():
                ctx.append(f'سكربت الحلقة الي قراه: "{d / name}".')
                break
        if (d / "edit" / "entities.json").exists():
            ctx.append(f'الأسماء المعروفة بالحلقة: "{d / "edit" / "entities.json"}".')
        code = _claude(CAP_PROMPT.format(file=f, out=out, message=msg, topic=_meta(d).get("name", ""),
                                         context="\n".join(ctx)))
    if code == 0 and not out.exists():
        JOB.say("❌ المساعد خلص بس ما كتب اقتراحاته")
        return 1
    if code == 0 and kind == "sentences":   # its choices go straight onto the list; he can still change any
        rev = json.loads(out.read_text(encoding="utf-8"))
        cur = {x["i"]: x["keep"] for x in studio.sentences(ep)["items"]}
        cur.update({int(i): False for i in rev.get("drop", [])})
        cur.update({int(i): True for i in rev.get("keep", [])})
        studio.set_sentences(ep, cur)
    if code == 0:
        JOB.say("💡 " + json.loads(out.read_text(encoding="utf-8")).get("summary", "خلص"))
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
        JOB.progress = None
        if step == "prep":
            code = _run([sys.executable, "-m", "editor.pipeline", "prep", str(d), "--source", meta.get("source", "")])
        elif step == "fetch":
            os.environ["ABOODI_PROGRESS"] = "1"
            code = _pipe("fetch", d, "--source", meta.get("source", ""))
        elif step == "transcribe":
            os.environ["ABOODI_PROGRESS"] = "1"
            code = _pipe("transcribe", d)
        elif step == "cut":
            code = 0
            for stage in ("clean", "names", "entities", "brief"):
                code = code or _pipe(stage, d)
        elif step in ("sentences", "captions"):
            code = _review_step(d, step)
        elif step == "images":
            code = _pipe("images", d)
            if code:   # pictures are a nicety for the storyboard: a failed download never stops the episode
                JOB.say("⚠️ بعض الصور ما نزلت، تنجاب وقت النسخة الكاملة")
                code = 0
        elif step == "shorts":
            code = _pipe("shorts", d)
        elif step == "export":   # a smaller copy for sending (the full file stays as it is)
            mb = re.sub(r"[^0-9.]", "", JOB.message or "") or "200"
            code = _pipe("deliver", d, "--max-mb", mb)
        elif step == "chat":
            code = _chat_step(d)
        elif step == "assist":
            code = _claude(ASSIST_PROMPT.format(ep=d, message=JOB.message or "راجع الخطة وحسّنها"))
        elif step == "plan":
            code = _claude(PLAN_PROMPT.format(ep=d, extra=_plan_extra(d)))
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


def start_job(ep_id: str, what: str, message: str = "") -> None:
    episode_dir(ep_id)
    if what not in STEPS:
        raise ValueError("خطوة مو معروفة")
    with JOB.lock:
        if JOB.running:
            raise RuntimeError("اكو شغل ماشي هسة. انتظره يخلص أو وگّفه")
        JOB.ep, JOB.step, JOB.lines, JOB.running, JOB.ok, JOB.stop_asked, JOB.need_login = ep_id, None, [], True, None, False, False
        JOB.what, JOB.message, JOB.progress, JOB.started = what, message.strip(), None, time.time()
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
            (HOME / "after_update").write_text("1", encoding="utf-8")   # the next start also brings the newest app
            JOB.say("✅ تحدّث. التطبيق يرجع يشتغل هسة…")
            time.sleep(1.5)
            os._exit(UPDATE_EXIT)
    threading.Thread(target=go, daemon=True).start()


APP_RELEASE = "https://github.com/aboodkhalid23/aboodi23/releases/download/mac-app/app-version.txt"
APP_STATE = {"update": None}   # None | "available" | "running"


def _parent_app() -> str:
    """The app window that started this server (its bundle path), on the Mac."""
    if os.environ.get("URU_APP_PATH"):
        return os.environ["URU_APP_PATH"]
    if not MAC:
        return ""
    out = subprocess.run(["ps", "-o", "comm=", "-p", str(os.getppid())], capture_output=True, text=True).stdout.strip()
    return out.split("/Contents/MacOS/")[0] if "/Contents/MacOS/" in out else ""


def upgrade_app() -> None:
    """Swap the app itself (name, logo, window) for the newest one on the release page, then reopen it."""
    with JOB.lock:
        if JOB.running:
            raise RuntimeError("اكو شغل ماشي هسة. انتظره يخلص")
        JOB.ep, JOB.step, JOB.lines, JOB.running, JOB.ok, JOB.stop_asked = None, "app", [], True, None, False
    APP_STATE["update"] = "running"

    def go():
        code = _run(["/bin/bash", str(CODE / "app" / "setup.sh"), "--app", str(os.getppid()), str(os.getpid()), _parent_app()])
        JOB.ok, JOB.running = code == 0, False
        APP_STATE["update"] = None if code == 0 else "available"
    threading.Thread(target=go, daemon=True).start()


def check_app() -> None:
    """At start: an app still under its old name is replaced at once; a newer app after a code update ("حدّث")
    is installed too; otherwise a newer app is only offered in the settings."""
    if not MAC or not os.environ.get("MONTIER_APP") or ".app" not in _parent_app():
        return    # only when the app window started this server (never from a terminal or a test)
    marker = HOME / "after_update"
    after = marker.exists()
    marker.unlink(missing_ok=True)
    if not os.environ.get("URU_APP_PATH"):    # the first app (المونتير) does not say its version: always old
        installed = next((p for p in (Path("/Applications/URU.app"), Path.home() / "Applications" / "URU.app")
                          if (p / "Contents" / "MacOS" / "URU").exists()), None)
        tries = HOME / "app_swap_tries"
        n = int(tries.read_text() or 0) if tries.exists() else 0
        tries.write_text(str(n + 1))
        if installed and n >= 3:
            APP_STATE["update"] = "stuck"     # it keeps coming back: say where the new app is, stop trying
            return
        if installed:   # already there (an earlier swap could not reopen it): just open it and close this one
            APP_STATE["update"] = "running"
            subprocess.Popen(["/bin/bash", "-c", f"sleep 1.5; kill {os.getppid()}; kill {os.getpid()}; sleep 1; open '{installed}'"],
                             start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        upgrade_app()
        return
    (HOME / "app_swap_tries").unlink(missing_ok=True)
    try:
        import urllib.request
        latest = urllib.request.urlopen(APP_RELEASE, timeout=8).read().decode().strip()
    except Exception:
        return
    if latest and latest != os.environ.get("URU_APP_VERSION", ""):
        if after:
            upgrade_app()
        else:
            APP_STATE["update"] = "available"


def version() -> dict:
    try:
        return json.loads((HOME / "version.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


SFX_AR = {"whoosh": "ووش", "swoosh": "سحبة", "boom": "بووم", "pop": "طگة", "click": "كليك", "ding": "دينگ", "hit": "ضربة",
          "riser": "صعود", "paper": "ورق", "glitch": "تشويش", "tick": "تك تك", "switch": "مفتاح", "factory_machine": "مكينة مصنع",
          "old_factory": "مصنع قديم", "robot_arm": "ذراع روبوت", "camera": "كاميرا", "typing": "طباعة", "heartbeat": "نبض قلب"}
STYLE_NAMES = {"investigation": "لوحة تحقيق", "noir": "سينما الليل", "retro-collage": "كولاج ريترو", "vox": "ورق وقص ولزق"}


def styles_list() -> list[dict]:
    """The style library with Arabic names (the part of the summary before the dash)."""
    from editor.pipeline.styles import _style_files, load_style
    out = []
    for f in _style_files():
        st = load_style(f.stem)
        name = STYLE_NAMES.get(f.stem) or re.split(r"\s+—\s+|\.|،", st.summary, maxsplit=1)[0].strip()[:30]
        out.append({"id": f.stem, "name": name, "summary": st.summary})
    return out


# ---------- samples for the studio's colour and sound steps ----------

def frame_with_look(ep, t: float, raw: bool = False) -> Path:
    """One frame of his video at `t` through the chosen look and sliders (what the render will do)."""
    from editor.pipeline.grade import app_chain
    video = ep.clean_video if ep.clean_video.exists() else ep.source
    chain = "scale=-2:540" + ("" if raw else app_chain(ep, ""))
    out = ep.work / "app" / f"frame_{'raw' if raw else 'look'}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0.0, t):.2f}", "-i", str(video), "-frames:v", "1",
                    "-vf", chain, "-q:v", "3", str(out)], capture_output=True)
    return out


def voice_sample(ep, t: float, clean: int) -> Path:
    """Eight seconds of his voice from `t`, cleaned at the chosen level (before/after in the sound step)."""
    from editor.pipeline.compose import voice_chain
    video = ep.clean_video if ep.clean_video.exists() else ep.source
    out = ep.work / "app" / f"voice_{clean}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    chain = voice_chain(clean) if clean >= 0 else "anull"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0.0, t):.2f}", "-t", "8", "-i", str(video), "-vn",
                    "-af", chain, str(out)], capture_output=True)
    return out


def music_sample(mood: str) -> Path:
    """Fifteen seconds of the code-made music in a mood (cached)."""
    from editor.pipeline.composer import PROGRESSIONS, compose, write_wav
    mood = mood if mood in PROGRESSIONS else "tension"
    out = HOME / "cache" / "music" / f"{mood}.wav"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        write_wav(compose(15.0, mood, 7), out)
    return out


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
                                   "version": version(), "app_update": APP_STATE["update"],
                                   "job": {"ep": JOB.ep, "running": JOB.running, "step": JOB.step}})
            if path == "/api/log":
                since = int(q.get("since") or 0)
                with JOB.lock:
                    lines, total = JOB.lines[since:], len(JOB.lines)
                return self._json({"ep": JOB.ep, "lines": lines, "next": total, "running": JOB.running, "ok": JOB.ok,
                                   "step": JOB.step, "steps": JOB.steps, "need_login": JOB.need_login,
                                   "progress": JOB.progress, "what": getattr(JOB, "what", None),
                                   "elapsed": round(time.time() - JOB.started) if JOB.started else 0})
            if path.startswith("/cache/"):
                root = (HOME / "cache").resolve()
                f = (root / path[7:]).resolve()
                return self._file(f) if f.is_relative_to(root) else self._err("لا", 403)
            if path == "/api/claude-link":
                return self._json(LINK.state())
            if path == "/api/styles":
                return self._json(styles_list())
            if path == "/api/music-sample":
                return self._file(music_sample(q.get("mood", "tension")))
            m = re.match(r"^/api/episodes/([^/]+)/chat$", path)
            if m:
                return self._json(chat_load(episode_dir(m.group(1))))
            if path == "/api/sfx":
                from editor.pipeline.sfx import names
                return self._json([{"id": n, "name": SFX_AR.get(n, n)} for n in names()])
            if path == "/api/sfx-sample":
                from editor.pipeline.sfx import sfx_path
                return self._file(sfx_path(q.get("name", "whoosh")))
            m = re.match(r"^/api/episodes/([^/]+)/(sentences|captions|plan|timeline|look|sound|idea|review|frame|voice-sample|media|effects|export-info|options|suggest)$", path)
            if m:
                return self._studio_get(episode_dir(m.group(1)), m.group(2), q)
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
        except (ValueError, RuntimeError) as exc:
            return self._err(str(exc), 400)

    def _qs(self) -> dict:
        return dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))

    def _studio_get(self, d: Path, what: str, q: dict):
        from editor.pipeline.paths import Episode
        from . import studio
        ep = Episode(d)
        if what == "sentences":
            return self._json(studio.sentences(ep))
        if what == "captions":
            return self._json(studio.captions(ep))
        if what == "plan":
            return self._json(studio.storyboard(ep))
        if what == "timeline":
            return self._json(studio.timeline(ep))
        if what == "look":
            from editor.pipeline.grade import LOOK_NAMES, look_settings
            return self._json({"settings": look_settings(ep), "names": LOOK_NAMES})
        if what == "sound":
            from editor.pipeline.compose import sound_settings
            return self._json(sound_settings(ep))
        if what == "idea":
            f, sf = d / "edit" / "idea.txt", d / "edit" / "style.txt"
            style = sf.read_text(encoding="utf-8").strip() if sf.exists() else ""
            name = next((x["name"] for x in styles_list() if x["id"] == style), "")
            return self._json({"text": f.read_text(encoding="utf-8") if f.exists() else "", "style": style, "style_name": name})
        if what == "review":
            f = d / "edit" / "work" / "app" / f"{q.get('kind', 'captions')}_review.json"
            return self._json(json.loads(f.read_text(encoding="utf-8")) if f.exists() else None)
        if what == "frame":
            return self._file(frame_with_look(ep, float(q.get("t") or 0), q.get("raw") == "1"))
        if what == "media":
            return self._json(studio.media_list(ep))
        if what == "effects":
            return self._json(studio.effect_thumbs(ep))
        if what == "export-info":
            final = d / "edit" / "final.mp4"
            plan = json.loads(ep.plan.read_text(encoding="utf-8")) if ep.plan.exists() else {}
            ch = d / "edit" / "chapters.txt"
            cr = d / "edit" / "credits.txt"
            shorts = sorted((d / "edit").glob("short_*.mp4")) + sorted((d / "edit" / "shorts").glob("*.mp4") if (d / "edit" / "shorts").exists() else [])
            return self._json({"final": final.exists(), "size": final.stat().st_size if final.exists() else 0,
                               "chapters": ch.read_text(encoding="utf-8") if ch.exists() else "",
                               "credits": cr.read_text(encoding="utf-8") if cr.exists() else "",
                               "shorts_plan": plan.get("shorts", []), "shorts": [str(f.relative_to(d)) for f in shorts]})
        if what == "options":
            from editor.pipeline.options import load_options
            return self._json(load_options(ep))
        if what == "suggest":
            text = (q.get("q") or "").strip()
            if not text:
                raise ValueError("اكتب شنو تريد")
            kind = q.get("kind") if q.get("kind") in ("image", "video") else "image"
            return self._json(studio.suggest(text, kind))
        if what == "voice-sample":
            return self._file(voice_sample(ep, float(q.get("t") or 0), int(q.get("clean") or 1)))
        return self._err("مو موجود", 404)

    def _studio_post(self, d: Path, what: str, b: dict):
        from editor.pipeline.paths import Episode
        from . import studio
        ep = Episode(d)
        if what == "options":
            from editor.pipeline.options import save_options
            studio.snapshot(ep)
            return self._json(save_options(ep, b))
        if what == "choose":
            studio.snapshot(ep)
            return self._json(studio.suggest_choose(ep, int(b.get("i", -1)), b.get("cand") or {}))
        if what in ("beat", "look", "sound", "sentences", "captions"):
            studio.snapshot(ep)   # every change can be undone
        if what in ("undo", "redo"):
            ok = (studio.undo if what == "undo" else studio.redo)(ep)
            return self._json({"ok": ok, "plan": studio.storyboard(ep)})
        if what == "media":
            return self._json(studio.media_add(ep, str(b.get("path", ""))))
        if what == "short":
            plan = json.loads(ep.plan.read_text(encoding="utf-8"))
            fr, to = float(b.get("from", 0)), float(b.get("to", 30))
            if not 10 <= to - fr <= 90:
                raise ValueError("الريل لازم بين ١٠ و٩٠ ثانية")
            plan["shorts"] = (plan.get("shorts") or []) + [{"from": round(fr, 2), "to": round(to, 2), "title": str(b.get("title", ""))}]
            ep.plan.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
            return self._json({"shorts": plan["shorts"]})
        if what == "sentences":
            return self._json(studio.set_sentences(ep, b.get("keep") or {}))
        if what == "captions":
            return self._json(studio.edit_words(ep, b.get("fixes") or {}, b.get("delete") or []))
        if what == "look":
            return self._json(studio.save_look(ep, b))
        if what == "sound":
            keep = {"clean": max(0, min(3, int(b.get("clean", 1)))), "music": str(b.get("music", "auto")),
                    "level": max(-32.0, min(-16.0, float(b.get("level", -24)))), "sfx": bool(b.get("sfx", True))}
            (d / "edit" / "sound.json").write_text(json.dumps(keep, ensure_ascii=False, indent=1), encoding="utf-8")
            return self._json(keep)
        if what == "idea":
            (d / "edit").mkdir(parents=True, exist_ok=True)
            if "text" in b:
                (d / "edit" / "idea.txt").write_text(str(b.get("text", "")).strip() + "\n", encoding="utf-8")
            if "style" in b:
                ok = {x["id"] for x in styles_list()}
                (d / "edit" / "style.txt").write_text(b["style"] if b["style"] in ok else "", encoding="utf-8")
            return self._json({"ok": True})
        if what == "beat":
            return self._json(studio.edit_beat(ep, int(b.get("i", -1)), b.get("change") or {}))
        return self._err("مو موجود", 404)

    def do_POST(self):
        path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))
        try:
            if path == "/api/episodes":
                b = self._body()
                return self._json(create_episode(b.get("name", ""), b.get("source", ""), b.get("script", ""),
                                                 b.get("look"), b.get("lut_key", "")))
            if path == "/api/probe":
                from .studio import probe_source
                b = self._body()
                src = Path(str(b.get("path", ""))).expanduser()
                if not src.is_file():
                    raise ValueError("ما لگيت الفيديو بهذا المكان")
                return self._json(probe_source(src, HOME / "cache", b.get("source")))
            if path == "/api/lut":
                from .studio import lut_preview
                b = self._body()
                key = re.sub(r"[^0-9a-f]", "", str(b.get("key", "")))
                src = Path(str(b.get("path", ""))).expanduser()
                if not key or src.suffix.lower() != ".cube" or not src.is_file():
                    raise ValueError("اختار ملف ألوان بصيغة كيوب")
                folder = HOME / "cache" / key
                shutil.copyfile(src, folder / "look.cube")
                return self._json({"img": f"{key}/" + lut_preview(folder, folder / "look.cube"), "name": src.stem})
            m = re.match(r"^/api/episodes/([^/]+)/chat$", path)
            if m:
                d = episode_dir(m.group(1))
                b = self._body()
                text = str(b.get("text", "")).strip()
                if not text:
                    raise ValueError("اكتب شنو تريد")
                if JOB.running:
                    raise RuntimeError("المساعد مشغول هسة. انتظره يخلص")
                chat_add(d, {"role": "owner", "text": text, "ctx": b.get("ctx") or {}})
                start_job(m.group(1), "chat", text)
                return self._json({"ok": True, "messages": chat_load(d)})
            m = re.match(r"^/api/episodes/([^/]+)/(sentences|captions|look|sound|idea|beat|undo|redo|media|short|options|choose)$", path)
            if m:
                return self._studio_post(episode_dir(m.group(1)), m.group(2), self._body())
            m = re.match(r"^/api/episodes/([^/]+)/(delete|media-delete)$", path)
            if m:
                if m.group(2) == "delete":
                    trash_episode(m.group(1))
                    return self._json({"ok": True})
                d = episode_dir(m.group(1))
                name = Path(str(self._body().get("name", ""))).name
                f = d / "edit" / "media" / name
                if name and f.exists():
                    f.unlink()
                from editor.pipeline.paths import Episode
                from .studio import media_list
                return self._json(media_list(Episode(d)))
            m = re.match(r"^/api/episodes/([^/]+)/(run|stop|reveal|rename)$", path)
            if m:
                ep, act = m.groups()
                d = episode_dir(ep)
                b = self._body()
                if act == "run":
                    start_job(ep, b.get("what", "all"), str(b.get("message", "")))
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
            if path == "/api/claude-link/start":
                return self._json(LINK.start())
            if path == "/api/claude-link/code":
                return self._json(LINK.submit(str(self._body().get("code", ""))))
            if path == "/api/claude-link/cancel":
                LINK.cancel()
                return self._json(LINK.state())
            if path == "/api/claude-link/unlink":
                _token_file().unlink(missing_ok=True)
                return self._json(LINK.state())
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
            if path == "/api/show-new-app":
                target = next((p for p in (Path("/Applications/URU.app"), Path.home() / "Applications" / "URU.app") if p.exists()), None)
                if target:
                    reveal(target)
                return self._json({"ok": bool(target)})
            if path == "/api/update-app":
                upgrade_app()
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


def _safe(fn):
    try:
        fn()
    except Exception as exc:   # an update check must never stop the app
        print("app check:", exc, flush=True)


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
    print(f"URU شغّال: http://127.0.0.1:{a.port}  (الحلقات: {EPISODES})", flush=True)
    threading.Timer(2.0, lambda: _safe(check_app)).start()
    srv.serve_forever()


if __name__ == "__main__":
    main()
