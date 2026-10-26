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
import secrets
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

from . import brains, comfort, fastai, learning

CODE = Path(__file__).resolve().parents[2]
UI = Path(__file__).resolve().parent / "ui"
MAC = sys.platform == "darwin"
HOME = Path(os.environ.get("MONTIER_HOME") or (Path.home() / ("Library/Application Support/Montier" if MAC else ".local/share/montier")))
EPISODES = Path(os.environ.get("MONTIER_EPISODES") or (Path.home() / ("Movies" if MAC else "") / "المونتير"))
UPDATE_EXIT = 75          # the app window restarts the server when it exits with this
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

STEPS = {"all": ["prep", "plan", "render", "suite"], "from-plan": ["plan", "render", "suite"],
         "from-render": ["render", "suite"], "prep": ["prep"], "plan": ["plan", "council", "ai", "images"], "render": ["render"],
         "suite": ["suite"], "requests": ["requests", "render"], "preview": ["preview"],
         # the studio's steps (one screen each)
         "prepare": ["fetch", "script-names", "transcribe", "sentences"], "cut": ["cut", "captions"], "sentences": ["sentences"], "captions": ["captions"], "hook": ["hook"], "viewer": ["viewer"],
         "images": ["images"], "build": ["preview"], "final": ["render", "learn"], "assist": ["assist"],
         "auto": ["fetch", "script-names", "transcribe", "sentences", "cut", "captions", "hook", "plan", "council", "ai", "images", "render", "learn"], "chat": ["chat"],
         # the assistant learns his taste from what he changed (also after every final build), and the app checks itself
         "learn": ["learn"], "selfcheck": ["selfcheck"],
         # ChatGPT and Gemini (his own subscriptions) read the plan and give a second opinion; ideas for the app
         "opinion": ["opinion"], "app-ideas": ["app-ideas"],
         # after the upload: subtitles in every language he translated, and the title/description in those languages
         "youtube-langs": ["youtube-langs"],
         # the smart tools panel (owner, 2026-10-25): one report or one careful change each; JOB.message = which
         "smart": ["smart"],
         "shorts": ["shorts"], "export": ["export"],
         # a style from the Styles panel on the whole video: the assistant re-plans in it, then a new preview
         "restyle": ["plan", "council", "ai", "images", "preview"],
         # the reels pack: the assistant picks 1 main short (< 1 min) + 5 clips, then they are cut tall
         "reels": ["reels-pick", "shorts"], "dub": ["dub"], "thumbs": ["thumbs"], "style-ref": ["style-ref"], "translate": ["translate"], "youtube": ["youtube"]}
STEP_NAMES = {"prep": "التجهيز", "plan": "خطة المونتير", "render": "النسخة الكاملة", "preview": "المعاينة",
              "suite": "غرفة المونتاج", "requests": "ملاحظاتك", "fetch": "تجهيز الفيديو", "transcribe": "تفريغ الكلام",
              "cut": "قص المقطع", "sentences": "المساعد يراجع الجمل", "captions": "المساعد يراجع الكابشن", "hook": "المساعد يدوّر الهوك", "viewer": "عين المشاهد",
              "images": "الصور", "assist": "المساعد", "chat": "المساعد", "shorts": "الريلز", "export": "التصدير", "reels-pick": "اختيار الريلز", "dub": "الدبلجة", "thumbs": "الصور المصغرة", "style-ref": "ستايل من فيديو", "script-names": "أسماء السكربت", "translate": "الترجمة", "ai": "مشاهد الذكاء الاصطناعي", "youtube": "الرفع على يوتيوب", "learn": "المساعد يتعلم ذوقك", "selfcheck": "فحص التطبيق والحلقة", "opinion": "رأي شات جي بي تي وجيميناي", "council": "لمسات شات جي بي تي وجيميناي", "youtube-langs": "اللغات على يوتيوب", "smart": "الأدوات الذكية", "app-ideas": "أفكار للتطبيق"}
CLAUDE_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "WebSearch", "WebFetch", "TodoWrite",
                "Bash(python -m editor.pipeline:*)", "Bash(python3 -m editor.pipeline:*)",
                "Bash(ffprobe:*)", "Bash(ffmpeg:*)", "Bash(ls:*)"]
# the AI generators he connected to his Claude account (claude.ai connectors), allowed only in the AI step
GEN_TOOLS = ["mcp__claude_ai_Higgsfield", "mcp__claude_ai_higgsfield", "mcp__Higgsfield", "mcp__higgsfield",
             "mcp__claude_ai_artlist", "mcp__claude_ai_Artlist", "mcp__artlist", "mcp__Artlist"]


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


def episode_cover(d: Path) -> Path:
    """A small picture of the episode for its card on the home page (made once, from the lightest video there)."""
    out = d / "work" / "app" / "cover.jpg"
    if out.exists():
        return out
    for v in (d / "edit" / "final.mp4", d / "work" / "app" / "proxy_clean.mp4", d / "work" / "app" / "proxy_source.mp4",
              d / "work" / "source.mp4"):
        if v.exists() and v.stat().st_size > 0:
            out.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "8", "-i", str(v), "-frames:v", "1", "-vf", "scale=480:-2",
                            "-q:v", "4", str(out)], timeout=30, check=False)
            if not out.exists():   # a clip shorter than 8 s
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-frames:v", "1", "-vf", "scale=480:-2",
                                "-q:v", "4", str(out)], timeout=30, check=False)
            break
    return out


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
        self.claude_failed, self.stalled, self.last_out = False, False, 0.0
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
               BASH_DEFAULT_TIMEOUT_MS="3600000", BASH_MAX_TIMEOUT_MS="7200000",
               # skills that ship usage counters (HyperFrames media-use): off, nothing about his work leaves the Mac
               HYPERFRAMES_NO_TELEMETRY="1", DO_NOT_TRACK="1", MONTIER_HOME=str(HOME))
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


STALL_MIN = 25   # minutes without one line of output before a step counts as stuck


def _run(cmd: list[str], on_line=None) -> int:
    JOB.say("")
    p = subprocess.Popen(cmd, cwd=CODE, env=_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         start_new_session=True)
    JOB.proc = p
    JOB.last_out = time.monotonic()

    def watchdog():   # a step silent for STALL_MIN minutes is stuck: stop it so the app never hangs
        while p.poll() is None:
            time.sleep(15)
            if time.monotonic() - JOB.last_out > STALL_MIN * 60 and p.poll() is None:
                JOB.stalled = True
                try:
                    os.killpg(p.pid, signal.SIGTERM)
                except OSError:
                    pass
                return
    JOB.stalled = False
    threading.Thread(target=watchdog, daemon=True).start()
    buf = b""
    while True:
        chunk = p.stdout.read1(4096) if hasattr(p.stdout, "read1") else p.stdout.read(4096)
        if not chunk:
            break
        buf += chunk
        JOB.last_out = time.monotonic()
        parts = re.split(rb"[\r\n]", buf)
        buf = parts.pop()
        for raw in parts:
            text = raw.decode("utf-8", "replace")
            (on_line or JOB.say)(text)
    if buf:
        (on_line or JOB.say)(buf.decode("utf-8", "replace"))
    code = p.wait()
    JOB.proc = None
    if JOB.stalled:
        JOB.say(f"⏱️ هاي الخطوة علگت ({STALL_MIN} دقيقة بلا ولا حركة)، فوگفتها. دوسها مرة ثانية، وإذا رجعت تعلگ دز لنا من «اقترح ميزة»")
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


# Speed (owner, 2026-10-26: "فيديو دقيقتين طوّل ٢٥ دقيقة… أريد سرعة"): every Claude task gets the model it needs.
# Quick checks (sentences, names, learning) use the fastest model; careful ones (captions, plan, chat) a strong and
# quick one; his "speed" setting can move everything up (quality) or down (fastest).
TIERS = {"fast": "haiku", "mid": "sonnet", "best": None}   # None: Claude Code's own default (the strongest)
SPEED_MAP = {"fastest": {"fast": "fast", "mid": "fast", "best": "mid"},
             "balanced": {"fast": "fast", "mid": "mid", "best": "mid"},
             "quality": {"fast": "mid", "mid": "best", "best": "best"}}


def _model_for(tier: str) -> str | None:
    speed = prefs().get("speed", "balanced")
    return TIERS[SPEED_MAP.get(speed, SPEED_MAP["balanced"]).get(tier, tier)]


def _claude(prompt: str, tools: list[str] | None = None, tier: str = "best") -> int:
    exe = claude_bin()
    if not exe:
        JOB.say("❌ كلود مو منصّب. دوس «حدّث المونتير» بالإعدادات حتى ينصبه")
        return 1
    JOB.claude_failed = False
    model = _model_for(tier)
    code = _run([exe, "-p", prompt, "--output-format", "stream-json", "--verbose", *(["--model", model] if model else []),
                 "--permission-mode", "acceptEdits", "--allowedTools", *CLAUDE_TOOLS, *(tools or [])], on_line=_claude_line)
    return 1 if JOB.claude_failed else code


PLAN_PROMPT = """انت المونتير الآلي لقناة صاحب القناة، وشغّال من داخل تطبيق المونتير على حاسبته. ماكو أحد يجاوبك هسة، فلا تسأل، قرر بنفسك.
الحلقة بالمجلد: {ep}
القص والتفريغ والأسماء خلصت (صاحب القناة راجع الجمل والكابشن بنفسه).
اتبع سكيل editor من الخطوة 5 لحد 8، ويه سكيل editor-mind:
- اقرا editor/LESSONS.md و"{ep}/edit/work/plan_input.txt".
- إذا "{ep}/edit/work/names_check.txt" بيه أسماء، اعرفها من القصة، اكتب "{ep}/edit/names.json"، وعيد names وبعدها entities وbrief بـ python -m editor.pipeline.
- اكتب "{ep}/edit/edit_plan.json"، وافحصه بـ python -m editor.pipeline validate "{ep}" لحد ما يطلع ✅.
- السكيلزات الي تقويك هنا: storytelling-hooks وviral-hooks (أول ٣٠ ثانية)، retention-pass (كل كم ثانية يتغير شي، ولا مشهد ممل)، media-sources (صور ومقاطع حقيقية بجودة عالية تطابق الكلام بالضبط)، shot-composition (وين يوگف كل شي بالكادر)، beat-sync-editing (القطع على الإيقاع).
- كل صورة لازم تطابق الكلام الي ينگال وياها بالضبط: إذا يحچي عن شخص، صورته هو؛ عن رقم، الرقم ينكتب كبير؛ عن مكان، المكان نفسه. لا صور عامة.
- الموسيقى (music بالخطة): مقسّمة على أقسام القصة، كل قسم مزاجه من الي ينحچى وينعرض بيه (غموض، توتر، دهشة، حزن، انتصار)، وتتبدل لما تتغير القصة، مو موسيقى وحدة للحلقة كلها. هادئة وبلا غناء، تحت صوته دائماً.
- قبل ما تسلّم، فكّر مثل مونتير كبير (سكيلات thinking-pre-mortem وthinking-second-order وsw-story-structure): تخيل المشاهد طلع بالدقيقة ٢، ليش؟ صلّح السبب. والهوك يفتح سؤال والقصة تتصاعد لحد الجواب. ولا تغيّر شي يعارض فكرة صاحب القناة.
{extra}
- لا تطلع معاينة ولا النسخة الكاملة (التطبيق يجيب الصور ويطلعها بعدك).
{money}
- كل رسائلك عربي عراقي بس. وبالآخر سطر: شنو الفكرة البصرية للحلقة."""

TRANSLATE_PROMPT = """انت مترجم ترجمة أفلام. ماكو أحد يجاوبك هسة، فلا تسأل.
بالملف "{file}" كلام حلقة يوتيوب (عراقي محكي) سطر سطر: i رقم السطر، text الكلام.
ترجم كل سطر للغة «{lang}» ({code}): ترجمة حقيقية دقيقة بالمعنى (مو حرفية)، طبيعية وقصيرة تنقرا بسرعة على الشاشة، والأسماء بتهجئتها الصحيحة بهاي اللغة. {names}
اكتب "{out}" بهالشكل بس (JSON): {{"lines": [{{"i": 0, "t": "..."}}]}} بنفس عدد الأسطر.
لا تعدّل أي ملف ثاني."""

NAMES_PROMPT = """انت مساعد المونتاج. ماكو أحد يجاوبك هسة، فلا تسأل.
بالملف "{script}" سكربت الحلقة الي صاحب القناة راح يقراه (عراقي). طلّع منه كل اسم علم: أشخاص، شركات، أماكن، منتجات، أحداث.
اكتب "{out}" بهالشكل بس (JSON): {{"names": [{{"ar": "الاسم مثل ما مكتوب بالسكربت", "en": "الاسم الصحيح بالإنگليزي", "kind": "person|company|place|thing|event", "who": "سطر عربي قصير: منو أو شنو"}}]}}
لا تعدّل أي ملف ثاني."""

STYLE_REF_PROMPT = """انت مدير فني لمونتاج يوتيوب. صاحب القناة دزلك فيديو يعجبه ستايله، وتريد تسوي منه ستايل جديد لتطبيقه. ماكو أحد يجاوبك هسة، فلا تسأل.
- صور من الفيديو (كل صورة شبكة لقطات بالترتيب): {sheets}
- قياسات: المدة {dur:.0f} ث، قطع كل {cut:.1f} ث تقريباً، المقاس {size}.
- اقرا الطريقة بسكيلات reference-to-motion وmx-steal-style (قِس، لا تخمّن).
- شوف مثال ستايل جاهز: "{example}" (نفس الحقول بالضبط).
اكتب ستايل جديد بـ "{out}" (ملف md: front matter بين --- ثم ملاحظات عربية):
  name: {sid}، title_ar: اسم عربي قصير يوصف الشكل، category: ستايلاتي، summary: سطر يوصفه (يبدي بالاسم العربي ثم —)
  palette: paper/ink/accent/red/maroon/teal/grid (ألوان hex من الفيديو نفسه)، fonts: title/body من: {fonts}
  texture: clean|grain|paper، image_treatment و image_treatments من: {treatments}، text_variants من: highlight, marker, typewriter, ransom
  transition من: cut, {transitions}، beat_seconds رقم (من قياس القطع)، music_mood إنگليزي، sfx من: whoosh, pop, click, ding, hit, riser, paper, glitch, boom
  ai_suffix إنگليزي يوصف شكل الصور، grade من: {grades}، layouts من: {kinds}، fits: مواضيع تناسبه.
  وبالملاحظات: «## شلون ينبني» وأول سطر بيه يبدي بـ "- " ويوصف شنو يسوي بالفيديو بالعربي بلا حروف إنگليزية.
لا تعدّل أي ملف ثاني. بالآخر سطر عربي: شنو الي يميّز هالستايل."""

THUMBS_PROMPT = """انت مصمم صور مصغرة يوتيوب. ماكو أحد يجاوبك هسة، فلا تسأل.
الحلقة: {ep} (العنوان: «{title}»). اقرا خطتها "{ep}/edit/edit_plan.json" والسكربت إذا موجود حتى تعرف الموضوع الحقيقي.
اقرا سكيل higgsfield-youtube-thumbnail واتبع طريقته (فجوة معلومة صادقة، وجه واضح، ٣ كلمات بالكثير)، بس ولّد بأدوات هيگزفيلد المربوطة (لا تنصّب شي).
{faces}
سوّ 3 أفكار مختلفة، كل وحدة صورة 1280×720. لا تنزّلها بنفسك: اكتب روابطها بـ "{out}" بهالشكل: {{"thumbs": [{{"url": "...", "idea": "سطر عربي"}}]}}.
الحد الأعلى للصرف {budget} دولار. كل رسائلك عربي عراقي."""

REELS_PROMPT = """انت مونتير ريلز وتيك توك لقناة صاحب القناة. ماكو أحد يجاوبك هسة، فلا تسأل.
بالملف "{file}" كلام الحلقة الجاهزة سطر سطر، وكل سطر وقته [من–لحد] بالثواني على الحلقة النهائية.
اختار {n} مقاطع تنفع ريلز (كل وحدة تنفهم لحالها بلا الحلقة):
- الأولى "main": أقوى لحظة بالحلقة كلها، طولها بين 30 و59 ثانية (يوتيوب شورتس).
- الباقي {rest}: كل وحدة بين 20 و90 ثانية، ما تتداخل ويه بعض، ومن أماكن مختلفة بالحلقة.
- كل مقطع يبدي بجملة تمسك (سؤال، رقم صادم، كشف) ويخلص بنهاية جملة مو بنصها. ابدأ وخلّص على أوقات الأسطر بالضبط.
اكتب "{out}" بهالشكل بس (JSON):
{{"reels": [{{"from": 12.3, "to": 58.0, "main": true, "title": "عنوان قصير يطلع فوق الريل", "caption": "كابشن للنشر بالعراقي ويه سؤال للتعليقات", "hashtags": "#وسم #وسم"}}]}}
لا تعدّل أي ملف ثاني. كل الكلام عربي عراقي."""

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


LEARN_PROMPT = """انت مساعد المونتاج بتطبيق URU على حاسبة صاحب القناة. شغلك هسة: تتعلم ذوقه من الي غيّره هو بيده، حتى الحلقات الجاية تطلع من أول مرة مثل ما يريد. ماكو أحد يجاوبك، فلا تسأل.

هاي التعديلات الي سواها من آخر مرة تعلمت (كل سطر: الحلقة، نوع التعديل، التفاصيل):
{events}

الحلقة الأخيرة: {ep}
- خطتها النهائية: {ep}/edit/edit_plan.json، ونسخها القديمة (الي بناها المساعد قبل تعديلاته) بـ {ep}/edit/versions/*/edit_plan.json. قارن أول نسخة بالأخيرة: شنو شال، شنو ضاف، شنو بدّل (مشاهد، صور، مؤثرات، انتقالات، ستايل، كابشن، ألوان، موسيقى، أصوات، رتم).
- ملاحظاته ومحادثته ويه المساعد بـ {ep}/edit/ (إذا موجودة).

ملف الذوق الحالي: {taste_file}
{taste}

اكتب ملف الذوق من جديد بـ Write على نفس المسار ({taste_file}):
- قواعد قصيرة وواضحة بالعربي، كل وحدة سطر يبدي بـ «- »، مجمّعة تحت عناوين: الستايل والشكل، الكابشن والخط، الصور والمشاهد، المؤثرات والانتقالات، الصوت والموسيقى، الرتم والقص، أشياء يكرهها.
- كل قاعدة لازم تجي من شي سواه هو فعلاً (تعديل تكرر، أو طلب صريح). لا تخمّن. إذا شي سواه مرة وحدة اكتب «(مرة وحدة)» بآخره، وإذا تكرر بأكثر من حلقة اكتب «(ثابت)».
- إذا تعديل جديد يناقض قاعدة قديمة، الجديد يغلب: بدّل القديمة.
- خلي الملف أقل من ٦٠ سطر: ادمج المتشابه، واحذف الي ما يفيد.
- لا تغيّر أي ملف ثاني.
بالآخر اكتب سطرين: شنو تعلمت جديد.
"""

CHAT_PROMPT = """انت مساعد المونتاج بتطبيق URU على حاسبة صاحب القناة، وتحچي وياه مثل مونتير صاحبه. هو يشوف الحلقة ويحچي وياك.
الحلقة: {ep}
المحادثة لحد هسة:
{history}
صاحب القناة يگول هسة: «{message}»
{context}
الملفات الي تگدر تغيّرها:
- الخطة "{ep}/edit/edit_plan.json": المشاهد (beats) بأوقات الفيديو النهائي، حسب سكيل editor. صورة ما عجبته: غيّر query (كلمات بحث إنگليزية أدق) أو النوع، وامسح pick. موشن جرافك: graphic أو kinetic أو face_paper. صوت بمكان معيّن: sfx بالمشهد.
- الألوان "{ep}/edit/look.json": look من ({looks})، source (rec709 أو slog3 لسوني لوگ ٣)، strength من 0 لـ 1، temp وtint من -100 لـ 100، exposure من -2 لـ 2.
- الصوت "{ep}/edit/sound.json": clean من 0 لـ 3 (تنظيف الصوت)، music (auto أو tension أو wonder أو sad أو drive أو dark أو calm أو off)، level من -38 لـ -18 (علو الموسيقى، الطبيعي -28: تحت صوته بوضوح)، sfx (true/false).
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


PREF_KEYS = {"theme": ("calm", "forest", "mint", "night", "ocean", "rose", "black", "violet", "carbon", "sand", "sky"), "lang": ("ar", "en"),
             "ai_on": (True, False), "council": (True, False), "speed": ("fastest", "balanced", "quality"), "uifont": ("alexandria", "plex", "cairo", "vazir")}
PREF_NUMS = {"ai_budget": (0, 300), "ai_variants": (1, 4)}   # dollars per episode, versions per AI scene


def prefs(change: dict | None = None) -> dict:
    """His app choices (theme, language), kept beside the tools so they survive anything the window forgets."""
    f = HOME / "prefs.json"
    try:
        cur = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cur = {}
    if change:
        for k, ok in PREF_KEYS.items():
            if k in change and change[k] in ok:
                cur[k] = change[k]
        for k, (lo, hi) in PREF_NUMS.items():
            if isinstance(change.get(k), (int, float)):
                cur[k] = int(max(lo, min(hi, change[k])))
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(cur), encoding="utf-8")
    return {"theme": cur.get("theme", "calm"), "lang": cur.get("lang", "ar"), "ai_on": bool(cur.get("ai_on", False)),
            "ai_budget": int(cur.get("ai_budget", 30)), "council": bool(cur.get("council", True)), "speed": cur.get("speed", "balanced"), "ai_variants": int(cur.get("ai_variants", 2)),
            "faces": [f.name for f in sorted((HOME / "face").glob("*")) if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".mp4", ".mov")]
            if (HOME / "face").exists() else []}


def ai_check() -> dict:
    """Which AI generators his Claude can reach (the connectors on his claude.ai account)."""
    exe = claude_bin()
    if not exe:
        return {"ok": False, "found": [], "error": "كلود مو منصّب"}
    try:
        out = subprocess.run([exe, "mcp", "list"], capture_output=True, text=True, timeout=90, env=_env()).stdout
    except (OSError, subprocess.TimeoutExpired):
        return {"ok": False, "found": [], "error": "ما گدرت أفحص"}
    found = []
    for line in out.splitlines():
        low = line.lower()
        for name, ar in (("higgsfield", "هيگزفيلد"), ("artlist", "آرتلست")):
            if name in low:
                found.append({"name": ar, "connected": "connected" in low or "✓" in line})
    return {"ok": True, "found": found}


def face_files(action: str, name: str = "", data: bytes = b"") -> dict:
    """His face photos / short face clips: the reference when an AI scene shows him."""
    f = HOME / "face"
    f.mkdir(parents=True, exist_ok=True)
    name = Path(name).name
    if action == "add":
        if Path(name).suffix.lower() not in (".jpg", ".jpeg", ".png", ".mp4", ".mov") or name.startswith("."):
            raise ValueError("صورة أو مقطع قصير بس")
        (f / name).write_bytes(data)
    elif action == "remove" and name:
        (f / name).unlink(missing_ok=True)
    return prefs()


def preload_libraries() -> None:
    """Owner, 2026-10-25: "ألقاها كلها محملة": every sound effect made and levelled, every free font downloaded,
    once, in the background (a missing one just tries again next start)."""
    try:   # the fast speech model for Apple Silicon (1.6 GB once), so the first episode does not wait for it
        from editor.pipeline.transcribe import MLX_MODEL, mlx_ready
        if mlx_ready():
            from huggingface_hub import snapshot_download
            snapshot_download(MLX_MODEL)
            snapshot_download("mlx-community/whisper-large-v3")   # the sharper one, for talks up to 20 minutes
    except Exception as exc:
        print("mlx model:", exc, flush=True)
    from editor.pipeline.sfx import names, sfx_path
    for n in names():
        try:
            sfx_path(n)
        except Exception:
            pass
    from . import fonts
    have = fonts.installed(HOME)
    for fam in fonts.ARABIC + fonts.LATIN:
        if fam not in have:
            try:
                fonts.download(HOME, fam)
            except Exception:
                pass


def _money_rule() -> str:
    """Paid AI only when he turned it on, within his budget (owner, 2026-10-25: "٣٠ لـ٤٠ دولار للحلقة ما عندي مشكلة")."""
    p = prefs()
    if not p["ai_on"] or p["ai_budget"] <= 0:
        return "- ممنوع تصرف فلوس أو رصيد: لا ذكاء اصطناعي مدفوع (هيگزفيلد، آرتلست). الحقيقي والمجاني بس."
    faces = [str(HOME / "face" / f) for f in p["faces"]]
    return (f"- الذكاء الاصطناعي المدفوع مسموح: ميزانية الحلقة {p['ai_budget']} دولار كحد أعلى. استعمله بس وين يفرق: الهوك، "
            "اللحظات الكبيرة، الي ما إله صورة حقيقية (تاريخ ما مصوّر، تخيّل، شخصية بمشهد). الحقيقي أول دائماً. "
            "حط بالخطة ai_image أو ai_video ويه prompt إنگليزي قوي، وai_budget بالرصيد."
            + (f" صور وجه صاحب القناة (مرجع لما يطلع هو بمشهد مولّد): {', '.join(faces)}." if faces else ""))


AI_PROMPT = """انت مولّد مشاهد الذكاء الاصطناعي لحلقة بالمجلد {ep}. ماكو أحد يجاوبك هسة، فلا تسأل.
0. اقرا سكيل higgsfield-generate (شلون تكتب البرومبت لكل موديل)، وإذا المشهد بيه صاحب القناة اقرا higgsfield-soul-id. لا تنصّب أي شي: استعمل الأدوات المربوطة بس.
1. شغّل: python -m editor.pipeline ai-jobs "{ep}" واقرا "{ep}/edit/work/ai_jobs.json" (المشاهد الناقصة).
2. لكل مشهد ناقص: ولّده بأدوات التوليد المربوطة بحسابك (هيگزفيلد أولاً، وآرتلست إذا أنسب). {variants} نسخة لكل مشهد،
   الأولى تنزل بـ: python -m editor.pipeline ai-fetch "{ep}" --beat <رقم> --url <الرابط>
   والباقي بـ --part v2 ثم v3… (صاحب القناة يختار بينهم بالتطبيق).
3. سجّل الصرف بعد كل توليد بـ python -m editor.pipeline ai-log إذا موجود، وشيك الرصيد. الحد الأعلى للحلقة كلها {budget} دولار: إذا قربت توگف.
4. {faces}
إذا ماكو أدوات توليد مربوطة، اكتب سطر واحد: «أدوات التوليد مو مربوطة بحسابك» وخلّص.
كل رسائلك عربي عراقي بس."""


def _ai_step(d: Path) -> int:
    p = prefs()
    if not p["ai_on"] or p["ai_budget"] <= 0:
        return 0
    plan_f = d / "edit" / "edit_plan.json"
    try:
        kinds = [b.get("kind") for b in json.loads(plan_f.read_text(encoding="utf-8"))["beats"]]
    except (OSError, ValueError, KeyError):
        return 0
    if not any(k in ("ai_image", "ai_video", "avatar") for k in kinds):
        JOB.say("🤖 الخطة ما بيها مشاهد ذكاء اصطناعي")
        return 0
    faces = [str(HOME / "face" / f) for f in p["faces"]]
    code = _claude(AI_PROMPT.format(ep=d, variants=p["ai_variants"], budget=p["ai_budget"],
                                    faces=("صور وجه صاحب القناة للمرجع: " + "، ".join(faces)) if faces else ""), tools=GEN_TOOLS)
    if code:   # generated scenes are a bonus: the episode builds anyway (missing ones become text)
        JOB.say("⚠️ بعض مشاهد الذكاء ما تولدت، تنبني الحلقة بدونها")
    return 0


def extract_text(name: str, data: bytes) -> str:
    """Plain text of a script file: .docx (Word), .rtf, or plain text."""
    import io
    import zipfile
    low = name.lower()
    if low.endswith(".docx"):
        try:
            xml = zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml").decode("utf-8")
        except (zipfile.BadZipFile, KeyError):
            raise ValueError("ملف الوورد هذا ما ينقرا")
        paras = re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)
        return "\n".join("".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, re.S)) for p in paras).strip()
    text = data.decode("utf-8", errors="replace")
    if low.endswith(".rtf"):
        text = re.sub(r"\\[a-z]+-?\d* ?|[{}]", "", text)
    return text.strip()


def _duration_min(f: Path) -> float:
    try:
        from editor.pipeline.media import probe
        return probe(f).duration / 60 if f.exists() else 0.0
    except Exception:
        return 0.0


def _canvas(d: Path):
    try:
        f = json.loads((d / "edit" / "work" / "format.json").read_text(encoding="utf-8"))
        return [f["width"], f["height"]]
    except (OSError, ValueError, KeyError):
        return None


def _yt_redirect() -> str:
    return f"http://127.0.0.1:{PORT[0]}/oauth/youtube"


def _youtube_step(d: Path) -> int:
    """Up to his channel, private, at the best quality there is: the biggest export (4K/8K) or the master; or one
    reel ("short:<path>"). He finishes the page in YouTube Studio and publishes."""
    from . import youtube
    msg = JOB.message or ""
    if msg.startswith("short:"):
        video = d / msg[6:]
        title = video.stem.split("-", 1)[-1].replace("-", " ") + " #shorts"
        desc = ""
    else:
        exports = sorted((d / "edit" / "exports").glob("*.mp4"), key=lambda f: int(re.sub(r"\D", "", f.stem.rsplit("-", 1)[-1]) or 0)) \
            if (d / "edit" / "exports").exists() else []
        big = [f for f in exports if int(re.sub(r"\D", "", f.stem.rsplit("-", 1)[-1]) or 0) >= 2160]
        video = big[-1] if big else d / "edit" / "final.mp4"
        title = _meta(d).get("name", d.name)
        parts = [(d / "edit" / f).read_text(encoding="utf-8").strip() for f in ("chapters.txt", "credits.txt") if (d / "edit" / f).exists()]
        desc = "\n\n".join(p for p in parts if p)
    if not video.is_file():
        JOB.say("❌ الملف مو موجود. طلّع النسخة الكاملة أول")
        return 1
    JOB.say(f"⬆️ أرفع «{video.name}» ({video.stat().st_size / 1e6:.0f} ميگا) على قناتك كفيديو خاص…")
    try:
        vid = youtube.upload(HOME, video, title, desc, progress=lambda p: JOB.say(f"@@ {p}"))
    except ValueError as exc:
        JOB.say(f"❌ {exc}")
        return 1
    (d / "edit" / "youtube.json").write_text(json.dumps({"id": vid, "file": video.name, "at": time.time()}), encoding="utf-8")
    JOB.say(f"✅ انرفع (خاص). كمّله من استوديو يوتيوب: https://studio.youtube.com/video/{vid}/edit")
    return 0


TITLES_PROMPT = """ترجم عنوان ووصف فيديو يوتيوب لصاحب القناة للغات هاي: {langs}.
العنوان: {title}
الوصف:
{desc}

قواعد: ترجمة طبيعية تجذب المشاهد بلغته (مو حرفية)، العنوان أقل من ٩٠ حرف، والوصف نفس معناه وطوله (الأوقات والروابط تبقى مثل ما هي).
اكتب النتيجة بـ Write بالملف {out} بهالشكل بالضبط (JSON): {{"es": {{"title": "...", "description": "..."}}, ...}}، وما تغيّر أي ملف ثاني."""


def _youtube_langs_step(d: Path) -> int:
    """Subtitles for every language he translated, and the title/description in those languages, on the video he
    uploaded. Dubbed voice tracks can only be added in YouTube Studio (Google gives no way to send them): the
    folder with them opens for him to drag in."""
    from . import youtube
    from editor.pipeline.options import LANGS
    yt = d / "edit" / "youtube.json"
    if not yt.exists():
        JOB.say("❌ ارفع الحلقة على يوتيوب أول")
        return 1
    vid = json.loads(yt.read_text(encoding="utf-8"))["id"]
    srts = {f.stem.split("-", 1)[1]: f for f in sorted((d / "edit").glob("subtitles-*.srt"))}
    if not srts:
        JOB.say("❌ ماكو ترجمات. سوّ الترجمة من «التصدير» ← اللغات أول")
        return 1
    bad = 0
    for lang, f in srts.items():
        try:
            youtube.upload_caption(HOME, vid, lang, f, LANGS.get(lang, lang))
            JOB.say(f"✅ ترجمة {LANGS.get(lang, lang)} انرفعت")
        except PermissionError as exc:
            JOB.say(f"❌ {exc}")
            return 1
        except (ValueError, OSError) as exc:
            JOB.say(f"⚠️ {exc}")
            bad += 1
    others = [x for x in srts if x != "ar"]
    if others:
        out = d / "edit" / "work" / "titles.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        desc = "\n\n".join((d / "edit" / f).read_text(encoding="utf-8").strip() for f in ("chapters.txt", "credits.txt")
                            if (d / "edit" / f).exists())
        JOB.say("✍️ المساعد يترجم العنوان والوصف…")
        if _claude(TITLES_PROMPT.format(langs="، ".join(f"{LANGS.get(x, x)} ({x})" for x in others),
                                        title=_meta(d).get("name", d.name), desc=desc or "(فارغ)", out=out), tier="mid") == 0 and out.exists():
            try:
                locs = {k: v for k, v in json.loads(out.read_text(encoding="utf-8")).items() if k in others and v.get("title")}
                youtube.set_languages(HOME, vid, locs)
                JOB.say(f"✅ العنوان والوصف صاروا بـ {len(locs)} لغة")
            except (ValueError, PermissionError, KeyError) as exc:
                JOB.say(f"⚠️ {exc}")
                bad += 1
    dubs = d / "edit" / "dubs"
    if dubs.exists() and any(dubs.glob("*.mp3")):
        JOB.say("🎙️ الأصوات المدبلجة: گوگل ما يسمح ترفعها من برّه استوديو يوتيوب. افتح الحلقة بالاستوديو ← «اللغات» ← «أضف صوت»، واسحب الملفات من المجلد الي انفتح")
        try:
            reveal(dubs)
        except (OSError, RuntimeError):
            pass
    JOB.say(f"كمّلها من هنا: https://studio.youtube.com/video/{vid}/translations")
    return 0


def _translate(d: Path) -> int:
    """Captions in other languages (owner, 2026-10-25: "ترجمة حقيقية ١٠٠٪… إسباني، صيني…"): his lines, translated by
    the assistant one language at a time, timed like his speech (edit/captions_<lang>.json) and written as subtitle
    files for YouTube (edit/subtitles-<lang>.srt). JOB.message "langs:en,es" (English alone when empty)."""
    from editor.pipeline.options import LANGS, subtitles_srt
    m = re.fullmatch(r"langs:([a-z,]+)", (JOB.message or "").strip())
    langs = [x for x in (m.group(1).split(",") if m else ["en"]) if x in LANGS] or ["en"]
    code = 0
    for lang in langs:
        code = _translate_one(d, lang) or code
        if JOB.stop_asked:
            break
    from editor.pipeline.paths import Episode
    ep = Episode(d)
    for lang in langs:
        if (d / "edit" / f"captions_{lang}.json").exists():
            (d / "edit" / f"subtitles-{lang}.srt").write_text(subtitles_srt(ep, lang), encoding="utf-8")
    return code


def _translate_one(d: Path, lang: str) -> int:
    from editor.pipeline.options import LANGS, caption_lines
    from editor.pipeline.paths import Episode
    ep = Episode(d)
    lines = caption_lines(ep)
    if not lines:
        JOB.say("❌ قُصّ المقطع أول، حتى يكون اكو كلام أترجمه")
        return 1
    work = d / "edit" / "work" / "app"
    work.mkdir(parents=True, exist_ok=True)
    src, out = work / "translate_in.json", work / f"translate_{lang}.json"
    src.write_text(json.dumps([{"i": x["i"], "text": x["text"]} for x in lines], ensure_ascii=False), encoding="utf-8")
    out.unlink(missing_ok=True)
    names = f'الأسماء الصحيحة بـ "{d / "edit" / "script_names.json"}".' if (d / "edit" / "script_names.json").exists() else ""
    JOB.say(f"🌐 أترجم للغة {LANGS[lang]}…")
    code = _claude(TRANSLATE_PROMPT.format(file=src, out=out, names=names, lang=LANGS[lang], code=lang), tier="mid")
    try:
        tr = {int(x["i"]): str(x.get("t") or x.get(lang) or x.get("en") or "").strip()
              for x in json.loads(out.read_text(encoding="utf-8"))["lines"]}
    except (OSError, ValueError, KeyError):
        JOB.say(f"❌ ترجمة {LANGS[lang]} ما كملت")
        return code or 1
    done = [{"s": x["s"], "e": x["e"], "text": tr[x["i"]]} for x in lines if tr.get(x["i"])]
    (d / "edit" / f"captions_{lang}.json").write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
    JOB.say(f"✅ {LANGS[lang]}: {len(done)} سطر")
    return 0


def _script_names(d: Path) -> int:
    """With the script he gave (owner, 2026-10-25: "أسماء صعبة اللفظ… انت راح تعرف منو"): its proper names go to
    the transcriber as words to expect (edit/vocab.txt) and to the assistant as who/what (edit/script_names.json)."""
    from editor.pipeline.align import find_script
    from editor.pipeline.paths import Episode
    ep = Episode(d)
    script = find_script(ep)
    out = d / "edit" / "script_names.json"
    if not script or out.exists():
        return 0
    if not claude_bin() or claude_logged_in() is False:
        JOB.say("ℹ️ كلود مو مربوط: الأسماء من السكربت تتعرف بعدين")
        return 0
    (d / "edit").mkdir(parents=True, exist_ok=True)
    code = _claude(NAMES_PROMPT.format(script=script, out=out), tier="fast")
    try:
        names = json.loads(out.read_text(encoding="utf-8"))["names"]
    except (OSError, ValueError, KeyError):
        JOB.say("⚠️ ما گدرت أطلّع الأسماء من السكربت (يكمل عادي)")
        return 0
    vocab = d / "edit" / "vocab.txt"
    have = vocab.read_text(encoding="utf-8").split() if vocab.exists() else []
    words = have + [w for n in names for w in str(n.get("ar", "")).split() if len(w) > 2]
    vocab.write_text(" ".join(dict.fromkeys(words)), encoding="utf-8")
    JOB.say(f"📜 لگيت {len(names)} اسم بالسكربت، والتفريغ راح يتوقعهم")
    return 0 if code == 0 or names else code


def style_from_reference(video: Path) -> int:
    """A style made from a video he likes (owner, 2026-10-25: "أدزلك فيديوهات بالستايلات الي تعجبني"): frames and
    cut rate are measured here, the assistant reads them and writes $MONTIER_HOME/styles/<id>.md, which the Styles
    panel shows under «ستايلاتي» and «طبّق» uses like any other."""
    from editor.pipeline.media import probe
    from editor.pipeline.plan import EFFECTS, KINDS, TRANSITIONS
    from editor.pipeline.grade import LOOKS
    from editor.pipeline.styles import load_style
    work = HOME / "refs" / (video.stem + ".work")
    work.mkdir(parents=True, exist_ok=True)
    info = probe(video)
    dur = max(info.duration, 1.0)
    sheets = []
    for k, (a, b) in enumerate(((0, 0.34), (0.33, 0.67), (0.66, 1.0))):
        out = work / f"sheet_{k}.jpg"
        span = dur * (b - a)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{dur * a:.2f}", "-t", f"{span:.2f}", "-i", str(video), "-vf",
                        f"fps={12 / span:.4f},scale=360:-2,tile=4x3", "-frames:v", "1", str(out)], timeout=300)
        if out.exists():
            sheets.append(str(out))
    scenes = subprocess.run(["ffmpeg", "-v", "info", "-i", str(video), "-vf", "select='gt(scene,0.3)',showinfo", "-f", "null", "-"],
                            capture_output=True, text=True, timeout=600).stderr.count("pts_time:")
    slug = re.sub(r"[^a-z0-9]+", "-", video.stem.lower()).strip("-")[:30]
    sid = "mine-" + (slug or time.strftime("%Y%m%d-%H%M%S"))   # Arabic file names: a date instead
    (HOME / "styles").mkdir(parents=True, exist_ok=True)
    out = HOME / "styles" / f"{sid}.md"
    code = _claude(STYLE_REF_PROMPT.format(
        sheets="، ".join(f'"{s}"' for s in sheets), dur=dur, cut=dur / max(scenes, 1), size=f"{info.width}×{info.height}",
        example=CODE / "editor" / "styles" / "noir.md", out=out, sid=sid,
        fonts="Cairo, Tajawal, Changa, Lalezar, Reem Kufi, El Messiri, Rakkas, Amiri, Aref Ruqaa, Noto Kufi Arabic, Noto Naskh Arabic",
        treatments="ken_burns, film_grain, parallax, cinematic_title, halftone_cutout, desk, silhouette, band, engraving_in_circle, newspaper, polaroid, crt, pinboard, paper_cutout",
        transitions=", ".join(TRANSITIONS), grades=", ".join(k for k in LOOKS if k != "none"),
        kinds=", ".join(k for k in KINDS)))
    try:
        st = load_style(sid)
    except Exception as exc:   # a broken file never stays in his library
        out.unlink(missing_ok=True)
        JOB.say(f"❌ الستايل ما انكتب صح ({exc})")
        return 1
    JOB.say(f"🎨 انضاف ستايل «{st.title_ar or sid}» لستايلاتك")
    return code


def _dub_step(d: Path) -> int:
    """The finished episode in his voice, in each language he ticked (ElevenLabs, his key and credit)."""
    from . import dubbing
    final = d / "edit" / "final.mp4"
    if not final.exists():
        JOB.say("❌ طلّع النسخة الكاملة أول")
        return 1
    m = re.fullmatch(r"langs:([a-z,]+)", (JOB.message or "").strip())
    langs = [x for x in (m.group(1).split(",") if m else []) if x in dubbing.LANGS]
    if not langs:
        JOB.say("❌ اختار لغة وحدة أقل شي")
        return 1
    bad = 0
    for k, lang in enumerate(langs):
        JOB.say(f"🎙️ دبلجة {dubbing.LANGS[lang]} ({k + 1} من {len(langs)})…")
        JOB.say(f"@@ {int(k / len(langs) * 100)}")
        try:
            out = dubbing.dub(HOME, final, lang, d / "edit" / "dubs", say=JOB.say)
            JOB.say(f"✅ {dubbing.LANGS[lang]} جاهزة: {out.name}")
        except (ValueError, requests_error(), subprocess.CalledProcessError) as exc:
            JOB.say(f"❌ {dubbing.LANGS[lang]}: {exc}")
            bad += 1
        if JOB.stop_asked:
            break
    return 1 if bad == len(langs) else 0


def requests_error():
    import requests
    return requests.RequestException


def _thumbs_step(d: Path) -> int:
    """Three AI thumbnail ideas into edit/thumbs/ (only with paid AI on)."""
    import requests
    p = prefs()
    if not p["ai_on"]:
        JOB.say("❌ شغّل «الذكاء الاصطناعي المدفوع» من الإعدادات أول")
        return 1
    out = d / "edit" / "work" / "app" / "thumbs.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    faces = [str(HOME / "face" / f) for f in p["faces"]]
    code = _claude(THUMBS_PROMPT.format(ep=d, title=_meta(d).get("name", d.name), out=out, budget=min(p["ai_budget"], 10),
                                        faces=("صور وجه صاحب القناة (يطلع هو بالصورة): " + "، ".join(faces)) if faces else ""),
                   tools=GEN_TOOLS)
    try:
        thumbs = json.loads(out.read_text(encoding="utf-8"))["thumbs"]
    except (OSError, ValueError, KeyError):
        JOB.say("❌ الصور المصغرة ما تولدت")
        return code or 1
    folder = d / "edit" / "thumbs"
    folder.mkdir(parents=True, exist_ok=True)
    n = 0
    for t in thumbs[:6]:
        try:
            r = requests.get(str(t["url"]), timeout=120)
            r.raise_for_status()
        except (requests.RequestException, KeyError):
            continue
        n += 1
        (folder / f"thumb-{int(time.time())}-{n}.png").write_bytes(r.content)
    JOB.say(f"🖼️ انسوت {n} صورة مصغرة")
    return 0 if n else 1


def _reels_pick(d: Path) -> int:
    """The assistant picks the reels pack; it lands in plan.shorts (main first) and edit/shorts/posts.txt."""
    from editor.pipeline.paths import Episode
    from editor.pipeline.shorts import LIMITS, MAIN_MAX, REELS_PACK, transcript_lines
    ep = Episode(d)
    if not ep.plan.exists():
        JOB.say("❌ ماكو خطة بعد: سوّ الحلقة أول")
        return 1
    work = d / "edit" / "work" / "app"
    work.mkdir(parents=True, exist_ok=True)
    src, out = work / "reels_input.txt", work / "reels.json"
    src.write_text("\n".join(transcript_lines(ep)), encoding="utf-8")
    out.unlink(missing_ok=True)
    n = REELS_PACK
    m = re.fullmatch(r"n:(\d+)", (JOB.message or "").strip())
    if m:
        n = max(1, min(10, int(m.group(1))))
    code = _claude(REELS_PROMPT.format(file=src, out=out, n=n, rest=max(n - 1, 0)), tier="mid")
    try:
        reels = json.loads(out.read_text(encoding="utf-8"))["reels"]
    except (OSError, ValueError, KeyError):
        JOB.say("❌ المساعد ما كتب الريلز")
        return code or 1
    plan = json.loads(ep.plan.read_text(encoding="utf-8"))
    good = []
    for k, r in enumerate(reels):
        fr, to = float(r.get("from", 0)), float(r.get("to", 0))
        top = MAIN_MAX if (r.get("main") or k == 0) else LIMITS[1]
        to = min(to, fr + top)
        if to - fr >= LIMITS[0]:
            good.append({"from": round(fr, 2), "to": round(to, 2), "title": str(r.get("title", ""))[:60],
                         "caption": str(r.get("caption", "")), "hashtags": str(r.get("hashtags", "")), "main": k == 0})
    if not good:
        JOB.say("❌ الريلز الي اختارها ما تنفع")
        return 1
    plan["shorts"] = good
    ep.plan.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    posts = d / "edit" / "shorts"
    posts.mkdir(parents=True, exist_ok=True)
    (posts / "posts.txt").write_text("\n\n".join(
        f"{k + 1}. {'(الرئيسي، يوتيوب شورتس) ' if r['main'] else ''}{r['title']} [{r['to'] - r['from']:.0f} ث]\n{r['caption']}\n{r['hashtags']}"
        for k, r in enumerate(good)), encoding="utf-8")
    JOB.say(f"✂️ اختار {len(good)} ريل")
    return 0


def _files_note(d: Path) -> str:
    """His own files (the app's «ملفاتي») and what he asked for each, for the assistant."""
    from editor.pipeline.paths import Episode
    from .studio import media_for_assistant
    lines = media_for_assistant(Episode(d))
    return ("\n- ملفات صاحب القناة (بـ edit/media) وشنو يريد بيها:\n" + "\n".join(lines)) if lines else ""


def _own_media(d: Path) -> None:
    from editor.pipeline.paths import Episode
    from .studio import apply_own_media
    try:
        n = apply_own_media(Episode(d))
    except (OSError, ValueError) as exc:
        JOB.say(f"⚠️ ما گدرت أحط ملفاتك: {exc}")
        return
    if n:
        JOB.say(f"📁 حطيت {n} من ملفاتك بالمشاهد")


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
    code = _claude(CHAT_PROMPT.format(ep=d, history=history, message=last["text"],
                                      context=_chat_context(d, last.get("ctx") or {}) + _files_note(d) + learning.prompt_block(HOME),
                                      looks="، ".join(LOOK_NAMES)), tier="mid")
    _own_media(d)
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


def _transcribe_file(f: Path) -> str:
    code = ("import sys\nfrom faster_whisper import WhisperModel\nfrom editor.pipeline.transcribe import WHISPER_MODEL\n"
            "m=WhisperModel(WHISPER_MODEL,device='cpu',compute_type='int8')\n"
            "s,_=m.transcribe(sys.argv[1],language='ar')\nprint(' '.join(x.text.strip() for x in s))")
    out = subprocess.run([sys.executable, "-c", code, str(f)], cwd=CODE, env=_env(), capture_output=True, text=True, timeout=300)
    return out.stdout.strip()


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
    code = _claude(REQ_PROMPT.format(ep=d, reqs=lines), tier="mid")
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


OPINION_PROMPT = """You are a senior YouTube documentary editor giving a second opinion to a colleague.
The channel: an Iraqi creator who talks to camera about global topics (company stories, documentaries, world trends).
Below is the edit plan for this episode (each scene: start–end seconds, kind, what is on screen) and what he says.
{taste}
Give the 5 most useful, concrete, SMALL improvements (the lead editor keeps the final say and will take only a few): a stronger hook, a dull stretch to fix, a better picture or
motion idea for a line, a cut, a sound moment. Each line: the time (m:ss), what to change, and why, in one or two
short sentences. Write in simple Iraqi Arabic. No intro, no outro, only the numbered list.

THE PLAN:
{plan}

WHAT HE SAYS (transcript):
{words}
"""

APP_IDEAS_PROMPT = """You help improve URU, a Mac video-editing app for one YouTube creator (Iraqi, global topics,
talking-head documentaries). The app already has: {features}.
What he likes and asked for before:
{taste}
Suggest the 10 most valuable new features or improvements a world-class editor app would add next, ordered by
value to him. Each: a short title, then one sentence on what it does for him. Simple Iraqi Arabic, numbered list,
nothing else."""

APP_FEATURES = ("automatic cutting of silences and retakes, transcription, Arabic captions with fonts, 85+ editing "
                "styles, 128 colour looks, motion graphics, sound effects and generated music, AI image/video "
                "generation (Higgsfield/Artlist), reels pack, YouTube private upload, subtitles in 14 languages, "
                "dubbing in his voice, versions of each build, a learned-taste file, self-check")


def _brain_answers(prompt: str, d: Path | None, out_dir: Path, label: str) -> int:
    """Ask each linked brain (ChatGPT, Gemini), one after the other; save and show what each said."""
    names = brains.active(HOME, HOME / "tools")
    if not names:
        JOB.say("❌ شات جي بي تي وجيميناي مو مربوطين. اربطهم من الإعدادات (مرة وحدة)")
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    got = 0
    for k in names:
        nm = brains.BRAINS[k]["name"]
        JOB.say(f"🤝 أسأل {nm}…")
        try:
            ans = brains.ask(k, prompt, HOME / "tools", workdir=d)
        except (RuntimeError, PermissionError, subprocess.SubprocessError, OSError) as exc:
            JOB.say(f"⚠️ {exc}")
            continue
        (out_dir / f"{k}.md").write_text(ans + "\n", encoding="utf-8")
        JOB.say(f"💬 {nm} ({label}):")
        for line in ans.splitlines()[:30]:
            JOB.say("   " + line)
        got += 1
    return 0 if got else 1


def _opinion_step(d: Path) -> int:
    plan_f = d / "edit" / "edit_plan.json"
    if not plan_f.exists():
        JOB.say("❌ اكتب الخطة أول، بعدين أسألهم")
        return 1
    plan = json.loads(plan_f.read_text(encoding="utf-8"))
    rows = [f"{b.get('start', 0):.0f}-{b.get('end', 0):.0f}s {b.get('kind', '')}: "
            + " | ".join(str(b.get(k)) for k in ("title", "caption", "query", "text", "effect") if b.get(k))
            for b in plan.get("beats", [])]
    try:
        from editor.pipeline.paths import Episode
        from editor.pipeline.transcribe import load_words
        words = " ".join(w.text for w in load_words(Episode(d).clean_words))[:9000]
    except Exception:   # the transcript is a bonus for them
        words = "(not available)"
    prompt = OPINION_PROMPT.format(plan="\n".join(rows)[:12000], words=words, taste=learning.prompt_block(HOME))
    return _brain_answers(prompt, d, d / "edit" / "opinions", "رأيه بالخطة")


COUNCIL_APPLY_PROMPT = """انت المونتير الرئيسي لحلقة صاحب القناة، والقرار الأخير إلك. ماكو أحد يجاوبك، فلا تسأل.
شات جي بي تي وجيميناي قروا خطتك واقترحوا تحسينات. صاحب القناة يثق بيك أكثر: هم يضيفون لمسات صغيرة بس، ما ياخذون القرار.

الحلقة: {ep}
الخطة: {ep}/edit/edit_plan.json

اقتراحاتهم:
{ideas}

القواعد:
- طبّق **٣ لمسات صغيرة بالأكثر**، وبس الي تحسّن الحلقة فعلاً بعين المشاهد: صورة أوضح لجملة، كلمة بالعنوان، مؤثر أو انتقال بمكانه، لحظة صوت، مشهد ممل تكسره.
- ممنوع: تغيّر الستايل، أو ترتيب الهوك والقصة، أو تشيل مشاهد كثيرة، أو تلمس أكثر من ٣ مشاهد، أو أي شي يعارض فكرة صاحب القناة وذوقه.
- إذا ماكو شي يستاهل، لا تغيّر شي. هذا مقبول.
- قبل ما تاخذ لمسة، اختبرها بطريقة the-fool (محامي الشيطان) وthinking-steel-manning: أقوى سبب يخليها صح، وأقوى سبب يخليها غلط. خذها بس إذا تصمد.
- عدّل {ep}/edit/edit_plan.json بـ Edit (نفس الشكل والحقول)، وبعدين اكتب {ep}/edit/opinions/applied.md: سطر لكل لمسة أخذتها (من منو، وشنو غيّرت)، وسطر قصير للي تركته وليش.
بالآخر سطر واحد: كم لمسة أخذت."""


SMART_COMMON = """انت مساعد المونتاج بتطبيق يو آر يو على حاسبة صاحب القناة (يوتيوبر عراقي، مواضيع عالمية: قصص شركات، وثائقيات، ترندات).
ماكو أحد يجاوبك، فلا تسأل. ممنوع صرف فلوس. كل كلامك بالعربي العراقي البسيط.
الحلقة: {ep} (اسمها: «{name}»). الخطة: {ep}/edit/edit_plan.json، والكلام بعد القص: {ep}/edit/clean_words.json (كل كلمة ووقتها).
"""
SMART = {
    "competitors": ("المنافسين بنفس الموضوع", SMART_COMMON + """دوّر بالنت (WebSearch) على أنجح ٨ فيديوات يوتيوب بنفس موضوع الحلقة (عربي وإنگليزي).
اكتب التقرير بـ Write بـ {out}: لكل فيديو: العنوان، القناة، المشاهدات تقريباً، شلون بدى الهوك بأول ١٥ ثانية، وشنو خلاه ينجح.
بالآخر قسم «شنو ناخذ منهم»: ٥ أفكار عملية لحلقتنا (هوك، عنوان، صورة مصغرة، مشهد). لا تغيّر أي ملف ثاني."""),
    "score": ("توقع النجاح", SMART_COMMON + """قيّم الحلقة قبل النشر مثل خبير يوتيوب: اقرا أول ٦٠ ثانية من الكلام والخطة.
اكتب بـ {out}: درجة من ١٠ لكل وحدة: الهوك (أول ٣٠ ثانية)، الإيقاع (تغيير كل كم ثانية)، وضوح القصة، العنوان (اسم الحلقة).
لكل درجة سطر «ليش» وسطر «شلون ترفعها». وبالآخر درجة عامة، و٣ أشياء لازم تتصلح قبل النشر. لا تغيّر أي ملف ثاني."""),
    "package": ("عناوين ووصف وتاگات", SMART_COMMON + """جهّز النشر على يوتيوب. اكتب بـ {out}:
١. ٥ عناوين (أقل من ٦٠ حرف، فضول بلا كذب)، وعلّم الأقوى.
٢. وصف كامل (أول سطرين يجذبون)، وتحته الفصول بالأوقات (٠:٠٠ … من الخطة: كل قسم كبير فصل، أول فصل ٠:٠٠، كل فصل ١٠ ثواني بالأقل).
٣. ١٥ تاگ (عربي وإنگليزي) و٣ هاشتاگات.
٤. ٣ أفكار للصورة المصغرة (شنو بيها وشنو مكتوب).
واكتب الفصول بس (سطر لكل فصل: الوقت والعنوان) بـ {ep}/edit/chapters.txt. لا تغيّر أي ملف ثاني."""),
    "graphics": ("رسوم من كلامك", SMART_COMMON + """دوّر بالكلام على: أماكن وسفر بين دول (خرائط)، وأرقام مهمة (مبالغ، نسب، سنين)، ومقارنات.
اختار الأقوى بس (٦ بالأكثر، بينهم ٢٠ ثانية بالأقل)، وحوّل المشهد الي بوقتها لرسم بالخطة: نوع graphic بـ type map (countries أو pins بأسماء عربية وlon/lat، أو route) أو number (value وlabel) أو chart، حسب سكيل editor.
لا تشيل صور حقيقية مهمة، ولا تلمس الهوك إذا ما يحتاج. افحص بـ python -m editor.pipeline validate "{ep}" لحد ما يطلع ✅.
اكتب بـ {out} سطر لكل رسم ضفته (الوقت وشنو)."""),
    "retention": ("صلّح الأماكن المملة", SMART_COMMON + """هاي الأماكن الي ممكن المشاهد يمل بيها (من فحص المونتير): {dull}
صلّح الأقوى منها (٥ بالأكثر): كسّر الوجه الطويل بصورة أو رسم أو تقريب، أو قصّر المشهد الثابت. لا تغيّر الستايل ولا ترتيب القصة.
افحص بـ python -m editor.pipeline validate "{ep}" لحد ما يطلع ✅. اكتب بـ {out} سطر لكل تصليح."""),
}


def _smart_step(d: Path, kind: str) -> int:
    if kind not in SMART:
        JOB.say("❌ أداة مو معروفة")
        return 1
    if kind != "competitors" and not (d / "edit" / "edit_plan.json").exists():
        JOB.say("❌ اكتب الخطة أول")
        return 1
    out = d / "edit" / "reports" / f"{kind}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    dull = ""
    if kind == "retention":
        dull = "، ".join(f"{_mmss(a)}–{_mmss(b)} ({why})" for a, b, why in retention(d)["dull"]) or "(ماكو)"
    if kind in ("graphics", "retention"):
        from editor.pipeline.paths import Episode
        from .studio import snapshot
        snapshot(Episode(d))
    JOB.say(f"🧠 {SMART[kind][0]}…")
    code = _claude(SMART[kind][1].format(ep=d, name=_meta(d).get("name", d.name), out=out, dull=dull) + learning.prompt_block(HOME), tier="mid")
    if code == 0 and out.exists():
        JOB.say("✅ التقرير جاهز بلوحة «أدوات ذكية»")
    return code


def _mmss(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def retention(d: Path) -> dict:
    """Where a viewer may get bored (the editor's own review rules), as a curve for the timeline: 1 = gripping."""
    from editor.pipeline.paths import Episode
    from editor.pipeline.plan import load_plan
    from editor.pipeline.review import dull_zones
    ep = Episode(d)
    if not ep.plan.exists():
        return {"dull": [], "curve": [], "length": 0}
    plan = load_plan(ep.plan)
    dull = dull_zones(plan.beats)
    length = plan.beats[-1].end if plan.beats else 0
    curve, step = [], 2.0
    t = 0.0
    while t < length:   # interest drops inside dull zones and slowly recovers after each change of picture
        since = min((t - b.start for b in plan.beats if b.start <= t), default=0)
        v = max(0.15, 1 - since / 20)
        if any(a <= t < b for a, b, _ in dull):
            v = min(v, 0.35)
        curve.append(round(v, 2))
        t += step
    return {"dull": [(round(a, 1), round(b, 1), w) for a, b, w in dull], "curve": curve, "step": step, "length": round(length, 1)}


def _council_step(d: Path) -> int:
    """ChatGPT and Gemini add small touches after every plan (owner, 2026-10-25: "يضيفون لمساتهم… قليلة، ما ياخذون
    رأي الأكبر"): they suggest, Claude decides and applies at most three. Never fails the job."""
    if not prefs().get("council", True) or not brains.active(HOME, HOME / "tools"):
        JOB.say("تخطيت (شات جي بي تي وجيميناي مو مربوطين أو مطفيين)")
        return 0
    if _opinion_step(d) != 0:
        JOB.say("⚠️ ما جاوبوا هالمرة. الخطة تبقى مثل ما هي")
        return 0
    od = d / "edit" / "opinions"
    ideas = "\n\n".join(f"— {brains.BRAINS[k]['name']}:\n{(od / f'{k}.md').read_text(encoding='utf-8')[:4000]}"
                         for k in brains.BRAINS if (od / f"{k}.md").exists())
    from editor.pipeline.paths import Episode
    from .studio import snapshot
    snapshot(Episode(d))   # their touches can be undone like any edit
    JOB.say("🎬 المساعد يختار من لمساتهم (٣ بالأكثر)…")
    if _claude(COUNCIL_APPLY_PROMPT.format(ep=d, ideas=ideas) + learning.prompt_block(HOME), tier="mid") != 0:
        JOB.say("⚠️ ما گدرت أطبق لمساتهم هالمرة. الخطة تبقى مثل ما هي")
    return 0


def _app_ideas_step(d: Path) -> int:
    prompt = APP_IDEAS_PROMPT.format(features=APP_FEATURES, taste=learning.taste(HOME) or "(nothing yet)")
    return _brain_answers(prompt, None, HOME / "app-ideas", "أفكار للتطبيق")


def _learn_step(d: Path) -> int:
    """After a final build: what he changed becomes his taste file. Never fails the job: learning is a bonus."""
    if not learning.pending(HOME) and not (d / "edit" / "versions").exists():
        JOB.say("ماكو تعديلات جديدة أتعلم منها")
        return 0
    before = learning.taste(HOME)
    code = _claude(LEARN_PROMPT.format(events=learning.digest(HOME), ep=d, taste_file=learning.taste_file(HOME),
                                       taste=before or "(لسه فارغ: هاي أول مرة)"), tier="fast")
    if code == 0:
        learning.mark_learned(HOME)
        JOB.say("🧠 تعلمت ذوقك من هاي الحلقة" if learning.taste(HOME) != before else "🧠 ذوقك نفسه، ما تغير شي")
    else:
        JOB.say("⚠️ ما گدرت أتعلم هالمرة. أحاول بالحلقة الجاية")
    return 0


def selfcheck(d: Path | None = None) -> list[dict]:
    """The app checks itself: tools, disk, the engine's files, and (if there is one) the last build of the episode."""
    out = []

    def add(ok, text):
        out.append({"ok": ok, "text": text})
    for tool in ("ffmpeg", "ffprobe"):
        add(bool(shutil.which(tool)), f"أداة {'الفيديو' if tool == 'ffmpeg' else 'فحص الفيديو'} موجودة" if shutil.which(tool) else f"أداة {tool} ناقصة: دوس «حدّث المونتير»")
    add(bool(claude_bin()), "كلود منصّب" if claude_bin() else "كلود مو منصّب: دوس «حدّث المونتير»")
    free = shutil.disk_usage(EPISODES if EPISODES.exists() else Path.home()).free / 2**30
    add(free > 15, f"المساحة الفاضية {free:.0f} گيگا" + ("" if free > 15 else ": قليلة، الحلقة الطويلة تحتاج ٢٠ گيگا تقريباً. امسح حلقات قديمة"))
    ui = Path(__file__).parent / "ui" / "index.html"
    add(ui.exists() and ui.stat().st_size > 10000, "واجهة التطبيق سليمة" if ui.exists() else "واجهة التطبيق ناقصة: دوس «حدّث المونتير»")
    for name in ("prefs.json",):
        f = HOME / name
        try:
            if f.exists():
                json.loads(f.read_text(encoding="utf-8"))
            add(True, "إعداداتك سليمة")
        except ValueError:
            f.rename(f.with_suffix(".broken"))       # a broken settings file must never stop the app
            add(False, "ملف إعداداتك كان خربان، رجّعته للأصل")
    if d is not None:
        for name, label in (("final.mp4", "الحلقة النهائية"), ("preview.mp4", "المعاينة")):
            v = d / "edit" / name
            if not v.exists():
                continue
            pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", str(v)],
                                capture_output=True, text=True) if shutil.which("ffprobe") else None
            try:
                info = json.loads(pr.stdout) if pr else {}
                kinds = {x.get("codec_type") for x in info.get("streams", [])}
                dur = float(info.get("format", {}).get("duration", 0))
                ok = {"video", "audio"} <= kinds and dur > 1
                add(ok, f"{label}: {dur / 60:.1f} دقيقة، صورة وصوت سليمين" if ok else f"{label} بيها مشكلة (صورة أو صوت ناقص). ابنيها مرة ثانية")
            except (ValueError, TypeError):
                add(False, f"{label} خربانة. ابنيها مرة ثانية")
    return out


def _selfcheck_step(d: Path) -> int:
    bad = 0
    for r in selfcheck(d):
        JOB.say(("✅ " if r["ok"] else "⚠️ ") + r["text"])
        bad += not r["ok"]
    final = d / "edit" / "final.mp4"
    if final.exists():   # the editor's own review of the finished video: black frames, loudness, dull stretches
        _run([sys.executable, "-m", "editor.pipeline", "qa", str(d)])
    JOB.say("كلشي سليم 👌" if not bad else f"لگيت {bad} شي يحتاج انتباه، مكتوبة فوگ")
    return 0


def _plan_extra(d: Path) -> str:
    """The owner's idea, his chosen look and sound, and his notes on the old plan's cards, for the plan prompt."""
    lines = []
    idea = d / "edit" / "idea.txt"
    if idea.exists() and idea.read_text(encoding="utf-8").strip():
        lines.append("- فكرة صاحب القناة للحلقة (التزم بيها): «" + idea.read_text(encoding="utf-8").strip() + "»")
    try:
        opts = json.loads((d / "edit" / "options.json").read_text(encoding="utf-8"))
        hook = int(opts.get("hook", 30))
        if hook != 30:
            lines.append(f"- الهوك: صاحب القناة يريد أول {hook} ثانية هي الأقوى بالحلقة: أسرع تغيير، أقوى صور وموشن، وأكبر سؤال يمسك المشاهد.")
        pace = {"calm": "هادئ (مشاهد أطول، وقفات أكثر)", "normal": "عادي", "fast": "سريع (مشاهد قصيرة، تغيير كل ٢–٤ ثواني، هوك سريع جداً)"}.get(opts.get("pace"))
        if pace:
            lines.append(f"- الرتم: صاحب القناة خلّاه عليك، وريده {pace}. اضبط طول المشاهد والانتقالات على هذا.")
    except (OSError, ValueError):
        pass
    try:   # the opening he picked in the hook step (owner, 2026-10-26)
        hk = json.loads((d / "edit" / "hook.json").read_text(encoding="utf-8"))
        lines.append(f"- الهوك الي اختاره صاحب القناة: حط كلامه من {hk['from']:.2f} لـ {hk['to']:.2f} ثانية (على الفيديو المقصوص) "
                     f"كتيزر بأول الحلقة (teaser: [[{hk['from']:.2f}, {hk['to']:.2f}]])، وأقوى صور وحركة على هذا الكلام: «{hk.get('text', '')}». "
                     f"الفكرة: {hk.get('title', '')}.")
    except (OSError, ValueError, KeyError, TypeError):
        pass
    if (d / "edit" / "script_names.json").exists():
        lines.append(f'- الأسماء بالسكربت ومنو هم: "{d / "edit" / "script_names.json"}". دوّر على صورهم ومقاطعهم الحقيقية بالإنگليزي (en)، وأول مرة ينذكر شخص مهم حط صورته (entity).')
    sf = d / "edit" / "style.txt"
    if sf.exists() and sf.read_text(encoding="utf-8").strip():
        sid = sf.read_text(encoding="utf-8").strip()
        lines.append(f"- الستايل: صاحب القناة اختار «{sid}» (style.primary = \"{sid}\"، إجباري). ابنِ الحلقة كلها على روحه:")
        try:
            from editor.pipeline.styles import load_style
            st = load_style(sid)
            lines.append("  " + st.notes.replace("\n", "\n  "))
            if st.layouts:
                lines.append(f"  - اعتمد أكثر على هالأنواع: {', '.join(st.layouts)}، والإيقاع حوالي {st.beat_seconds} ث بالجسم.")
        except (KeyError, OSError, ValueError):
            pass
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
    return "\n".join(lines) + learning.prompt_block(HOME)


SENT_FAST = """راجع قص فيديو يوتيوب: صاحب القناة يحچي للكاميرا (عراقي) وما يوقف التصوير لما يغلط، يعيد الجملة.
الحلقة عن: {topic}
تحت جمل الكلام بالترتيب، كل سطر: رقم|حالة|كلام. الحالة: ✓ القص الآلي خلّاها، ✗ حذفها (وبعدها السبب).
شغلك تلگى كل غلط ما انتبهله القص الآلي، وتصلّح الي حذفه غلط:
- إذا گال جملة (أو بدايتها) وعادها، تنحذف كل المحاولات وتبقى الأخيرة الكاملة. انتبه: الإعادة مرات تكون بنفس السطر («يوم من الايام كان اكو يوم من الايام عاش رجل…»): هنا اكتب بـ cut الكلام الي ينحذف من السطر بالضبط مثل ما مكتوب.
- البداية المتعثرة، والجملة الي انقطعت بنصها وما كملت، وكلام موجّه للي يصوّر («خلي اعيدها»، «من جديد»)، تنحذف.
- المزحة والسالفة الجانبية والمعلومة الإضافية تبقى. لا تحذف كلام مفيد، ولا تحذف جملة بس لأنها تشبه جملة بعيدة.
- إذا ✗ وهي كلام مفيد ما انعاد، رجّعها بـ keep.
{message}
{lines}
جاوب JSON بس: {{"drop": [أرقام جمل كاملة تنحذف], "keep": [أرقام جمل ✗ ترجع], "cut": [{{"i": رقم, "text": "الكلمات الي تنحذف من السطر بالضبط"}}], "why": {{"رقم": "سبب قصير"}}}}"""

CAP_FAST = """صحّح تفريغ كلام حلقة يوتيوب (عراقي محكي). الحلقة عن: {topic}
{context}
تحت الكلام كلمة كلمة: رقم:كلمة، و؟ بعد الكلمة الي التفريغ مو متأكد منها.
صحّح بس الغلط الواضح: أسماء أشخاص وشركات وبلدان انكتبت غلط (اكتبها مثل السكربت أو الأسماء المعروفة)، وكلمة عراقية انكتبت فصحى (اكتبها مثل ما انگالت)، وكلمة ما إلها معنى بمكانها. لا تغيّر أسلوب كلامه ولا تضيف كلام.
والكلمة الي مو متأكد منها وما تگدر تحسمها، اسأل عنها بخيارات.
{message}
{lines}
جاوب JSON بس: {{"fixes": [{{"i": رقم, "old": "الكلمة", "new": "الصح", "why": "سبب قصير"}}], "questions": [{{"i": رقم, "q": "السؤال", "options": ["خيار", "خيار"]}}]}}
للتصحيح الي يشمل أكثر من كلمة، حط i أول كلمة وnew كل الكلام."""

SENT_PIECE, SENT_OVERLAP, CAP_PIECE = 160, 12, 450


def _fast_json(prompt: str, tier: str = "mid") -> dict:
    """One quick answer from Claude with the data inside the question (no agent, no tools): seconds, not minutes."""
    exe = claude_bin()
    if not exe:
        raise RuntimeError("كلود مو منصّب. دوس «حدّث المونتير» بالإعدادات حتى ينصبه")
    return fastai.ask(exe, prompt, _model_for(tier), env=_env())


def _context_block(d: Path) -> str:
    ctx = []
    for name in ("04-script.md", "02-draft.md"):
        if (d / name).exists():
            ctx.append("السكربت الي قراه (للأسماء والكلمات):\n" + (d / name).read_text(encoding="utf-8")[:12000])
            break
    try:
        ents = json.loads((d / "edit" / "entities.json").read_text(encoding="utf-8"))
        names = [e.get("ar") or e.get("name") for e in (ents.get("entities", ents) if isinstance(ents, dict) else ents)
                 if isinstance(e, dict)]
        if names:
            ctx.append("الأسماء المعروفة بالحلقة: " + "، ".join(n for n in names if n)[:2000])
    except (OSError, ValueError, AttributeError):
        pass
    return "\n".join(ctx)


def _sentences_ai(d: Path) -> dict:
    """The AI pass over the cut: all pieces at once; whole sentences and words inside a sentence."""
    from editor.pipeline.clean import normalize_ar
    from editor.pipeline.paths import Episode
    from . import studio
    ep = Episode(d)
    items = studio.sentences(ep)["items"]
    msg = f"وصاحب القناة يگول: «{JOB.message}»" if JOB.message else ""
    topic = _meta(d).get("name", "")

    def one(piece):
        lines = "\n".join(f'{x["i"]}|{"✓" if x["keep"] else "✗ " + (x["why"] or "")}|{x["text"]}' for x in piece)
        return _fast_json(SENT_FAST.format(topic=topic, message=msg, lines=lines), "mid")
    pieces = fastai.chunks(items, SENT_PIECE, SENT_OVERLAP)
    JOB.say(f"المساعد يقرأ {len(items)} جملة" + (f" ({len(pieces)} قطع سوة)" if len(pieces) > 1 else "") + "…")
    answers = fastai.run_parallel(one, pieces)
    bad = [a for a in answers if isinstance(a, Exception)]
    if len(bad) == len(answers):
        raise bad[0] if bad else RuntimeError("ماكو جمل")
    drop, keep, cuts, why = set(), set(), [], {}
    for a in answers:
        if isinstance(a, Exception):
            continue
        drop |= {int(i) for i in a.get("drop", []) if str(i).lstrip("-").isdigit()}
        keep |= {int(i) for i in a.get("keep", []) if str(i).lstrip("-").isdigit()}
        cuts += [c for c in a.get("cut", []) if isinstance(c, dict)]
        why.update({str(k): v for k, v in (a.get("why") or {}).items()})
    keep -= drop
    cur = {x["i"]: x["keep"] for x in items}
    cur.update({i: False for i in drop if i in cur})
    cur.update({i: True for i in keep if i in cur})
    studio.set_sentences(ep, cur)
    # words inside a sentence that stays: their times go to the cutter like a word he deleted himself
    from editor.pipeline.transcribe import load_words
    units = studio.units(load_words(ep.transcript))
    spans = []
    for c in cuts:
        try:
            i = int(c.get("i"))
        except (TypeError, ValueError):
            continue
        if not 0 <= i < len(units) or i in drop:
            continue
        u = units[i]
        hit = fastai.find_run([w.text for w in u], str(c.get("text", "")), normalize_ar)
        if hit and hit[1] - hit[0] < len(u):
            spans.append([round(u[hit[0]].start - 0.01, 3), round(u[hit[1] - 1].end + 0.01, 3)])
    if spans:
        ov = studio._overrides(ep)
        ov["drop_words"] = ov.get("drop_words", []) + spans
        ov["drop"] = ov.get("drop", []) + spans
        (ep.edit / "cuts_override.json").write_text(json.dumps(ov, ensure_ascii=False, indent=1), encoding="utf-8")
    n = len(drop & {x["i"] for x in items if x["keep"]})
    summary = (f"حذفت {n} جملة معادة أو متعثرة" + (f"، وقصّيت إعادة من داخل {len(spans)} جملة" if spans else "")
               + (f"، ورجّعت {len(keep)}" if keep else "") + (" (قطعة وحدة ما جاوبت)" if bad else ""))
    return {"summary": summary if n or spans or keep else "ما لگيت إعادات زايدة 👍", "drop": sorted(drop),
            "keep": sorted(keep), "cut": spans, "why": why}


def _captions_ai(d: Path) -> dict:
    from editor.pipeline.paths import Episode
    from . import studio
    ep = Episode(d)
    caps = studio.captions(ep)
    words = [w for line in caps["lines"] for w in line]
    msg = f"وصاحب القناة يگول: «{JOB.message}»" if JOB.message else ""
    topic, ctx = _meta(d).get("name", ""), _context_block(d)

    def one(piece):
        lines = " ".join(f'{w["i"]}:{w["t"]}{"؟" if w["doubt"] else ""}' for w in piece)
        return _fast_json(CAP_FAST.format(topic=topic, context=ctx, message=msg, lines=lines), "mid")
    pieces = fastai.chunks(words, CAP_PIECE)
    JOB.say(f"المساعد يقرأ {len(words)} كلمة" + (f" ({len(pieces)} قطع سوة)" if len(pieces) > 1 else "") + "…")
    answers = fastai.run_parallel(one, pieces)
    if answers and all(isinstance(a, Exception) for a in answers):
        raise answers[0]
    fixes, qs = [], []
    for a in answers:
        if not isinstance(a, Exception):
            fixes += [f for f in a.get("fixes", []) if isinstance(f, dict) and "i" in f and f.get("new")]
            qs += [q for q in a.get("questions", []) if isinstance(q, dict) and "i" in q]
    # the fixes go straight into the words (owner, 2026-10-26: "التصحيح… ابد مكاعد يصلح"); he can still retype any
    n_words = len(words)
    by_i = {}
    for f in fixes:
        try:
            i = int(f["i"])
        except (TypeError, ValueError):
            continue
        new = str(f["new"]).strip()
        if 0 <= i < n_words and new and new != words[i]["t"]:
            by_i[i] = new
    if by_i:
        studio.edit_words(ep, by_i, [])
    fixes = [f for f in fixes if str(f.get("i")).isdigit() and int(f["i"]) in by_i]
    return {"summary": (f"صححت {len(fixes)} كلمة بالكلام" if fixes else "ما لگيت كلمات غلط") +
            (f"، وعندي {len(qs)} سؤال" if qs else ""), "fixes": fixes, "questions": qs, "applied": bool(fixes)}


HOOK_FAST = """انت مونتير يوتيوب خبير بالهوك (أول ٣٠ ثانية تحدد إذا المشاهد يكمل). الحلقة عن: {topic}
تحت كلام صاحب القناة بعد القص، كل سطر: [من–لحد بالثواني] الكلام.
اختار ٣ هوكات مختلفة من كلامه هو (ما تكتب كلام جديد)، كل واحد مقطع متصل طوله بين ٤ و٢٠ ثانية يبدي ويخلص على حدود الأسطر بالضبط:
١) سؤال أو لغز يخلي المشاهد يريد يعرف الجواب. ٢) رقم أو معلومة صادمة. ٣) أقوى لحظة بالقصة (من النص أو الآخر) تنعرض أول كتيزر.
لا تختار مقطع يكشف نهاية القصة كاملة.
{lines}
جاوب JSON بس: {{"hooks": [{{"title": "اسم قصير للفكرة", "from": 12.3, "to": 21.0, "text": "الكلام بالضبط", "why": "ليش يمسك المشاهد، سطر واحد"}}]}}"""

VIEWER_FAST = """انت مشاهد يوتيوب عادي، صبرك قليل، وتتفرج على حلقة عن: {topic}. وبعدين انت مونتير خبير يصلّح.
تحت الحلقة ثانية بثانية: الكلام، وشنو يطلع بالشاشة بكل مشهد، ومناطق خطر الملل الي لگتها القواعد.
{lines}
لگّي اللحظات الي ممكن تخليك تطلع أو ما تفهم: مشهد طويل بلا تغيير، صورة ما إلها علاقة بالكلام، كلام معاد، شرح ثقيل بلا رسم، هوك ضعيف، نهاية تطول.
لكل وحدة: الثانية، المشكلة بسطر، والتصليح بسطر (شي يگدر المونتير يسويه: صورة، رسم، تقريب، قص، موسيقى، نص على الشاشة).
وأعطِ الحلقة درجة من ١٠٠ لاحتمال إن المشاهد يكمل لآخرها.
جاوب JSON بس: {{"score": 70, "summary": "سطرين عربي عراقي", "notes": [{{"t": 12.5, "issue": "المشكلة", "fix": "التصليح", "level": "high|mid|low"}}]}}"""


def _clean_lines(ep) -> list[tuple[float, float, str]]:
    from editor.pipeline.transcribe import load_words
    words = load_words(ep.clean_words) if ep.clean_words.exists() else []
    out, cur = [], []
    for w in words:
        if cur and (w.start - cur[-1].end > 0.45 or len(cur) >= 14):
            out.append((cur[0].start, cur[-1].end, " ".join(x.text for x in cur)))
            cur = []
        cur.append(w)
    if cur:
        out.append((cur[0].start, cur[-1].end, " ".join(x.text for x in cur)))
    return out


def _hook_step(d: Path) -> int:
    """Three openings from his own words; he picks one in the hook step (owner, 2026-10-26)."""
    from editor.pipeline.paths import Episode
    ep = Episode(d)
    lines = _clean_lines(ep)
    if not lines:
        JOB.say("❌ قُص المقطع أول")
        return 1
    text = "\n".join(f"[{a:.1f}–{b:.1f}] {t}" for a, b, t in lines[:400])
    JOB.say(f"المساعد يدوّر أقوى بداية بين {len(lines)} سطر…")
    try:
        r = _fast_json(HOOK_FAST.format(topic=_meta(d).get("name", ""), lines=text), "best")
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        JOB.say("❌ ما گدر: " + str(exc)[:200])
        return 1
    hooks = []
    for h in r.get("hooks", [])[:3]:
        try:
            a, b = float(h["from"]), float(h["to"])
        except (KeyError, TypeError, ValueError):
            continue
        if 2 <= b - a <= 30:
            hooks.append({"title": str(h.get("title", "")), "from": round(a, 2), "to": round(b, 2),
                          "text": str(h.get("text", "")), "why": str(h.get("why", ""))})
    out = d / "edit" / "work" / "app" / "hook_review.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"hooks": hooks}, ensure_ascii=False), encoding="utf-8")
    if hooks and len(JOB.steps) > 1 and not (d / "edit" / "hook.json").exists():   # the one-button mode: the first
        save_hook(d, 0)
        JOB.say(f"💡 اخترت الهوك «{hooks[0]['title']}». تگدر تبدله من خانة الهوك")
        return 0
    JOB.say(f"💡 طلّعت {len(hooks)} بدايات. شوفها واختار")
    if not hooks and len(JOB.steps) > 1:
        return 0      # never stops the one-button mode
    return 0 if hooks else 1


def _viewer_step(d: Path) -> int:
    """The built episode through a bored viewer's eyes, then an editor's fixes (owner, 2026-10-26: «عين المشاهد»)."""
    from editor.pipeline.paths import Episode
    from . import studio
    ep = Episode(d)
    if not ep.plan.exists():
        JOB.say("❌ اكتب الخطة أول")
        return 1
    plan = json.loads(ep.plan.read_text(encoding="utf-8"))
    off = sum(e - s for s, e in plan.get("teaser", []))
    lines = _clean_lines(ep)
    rows = []
    for b in plan.get("beats", []):
        said = " ".join(t for a, e, t in lines if b["start"] - off <= a < b["end"] - off)
        shows = studio.KIND_AR.get(b["kind"], b["kind"])
        what = studio.ar(b.get("title")) or studio.ar(b.get("caption")) or (b.get("query") or "")
        rows.append(f"[{b['start']:.1f}–{b['end']:.1f}] يطلع: {shows}{(' (' + what + ')') if what else ''} | يحچي: {said[:220]}")
    try:
        dull = retention(d).get("dull", [])
    except Exception:   # noqa: BLE001 — the rules' curve is a help; the AI still watches without it
        dull = []
    text = "\n".join(rows[:300]) + ("\nمناطق ملل: " + "، ".join(f"{a}–{b} ({w})" for a, b, w in dull) if dull else "")
    JOB.say(f"المساعد يتفرج على {len(rows)} مشهد كأنه مشاهد…")
    try:
        r = _fast_json(VIEWER_FAST.format(topic=_meta(d).get("name", ""), lines=text), "best")
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        JOB.say("❌ ما گدر: " + str(exc)[:200])
        return 1
    notes = []
    for n in r.get("notes", []):
        try:
            notes.append({"t": round(float(n["t"]), 1), "issue": str(n.get("issue", "")), "fix": str(n.get("fix", "")),
                          "level": n.get("level") if n.get("level") in ("high", "mid", "low") else "mid"})
        except (KeyError, TypeError, ValueError):
            continue
    notes.sort(key=lambda n: n["t"])
    try:
        score = max(0, min(100, int(r.get("score", 0))))
    except (TypeError, ValueError):
        score = None
    out = d / "edit" / "work" / "app" / "viewer_review.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"score": score, "summary": str(r.get("summary", "")), "notes": notes},
                              ensure_ascii=False), encoding="utf-8")
    JOB.say(f"💡 لگيت {len(notes)} لحظة ممكن المشاهد يطلع بيها")
    return 0


def save_hook(d: Path, k: int) -> dict:
    rv = json.loads((d / "edit" / "work" / "app" / "hook_review.json").read_text(encoding="utf-8"))
    h = rv["hooks"][int(k)]
    (d / "edit" / "hook.json").write_text(json.dumps(h, ensure_ascii=False), encoding="utf-8")
    return h


def _review_step(d: Path, kind: str) -> int:
    """The assistant reads the sentences or the captions and writes its suggestions (the screen shows them)."""
    app = d / "edit" / "work" / "app"
    app.mkdir(parents=True, exist_ok=True)
    out = app / f"{kind}_review.json"
    out.unlink(missing_ok=True)
    t0 = time.monotonic()
    try:
        rev = _sentences_ai(d) if kind == "sentences" else _captions_ai(d)
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        JOB.say("❌ المساعد ما گدر يراجع: " + str(exc)[:200])
        return 1
    out.write_text(json.dumps(rev, ensure_ascii=False), encoding="utf-8")
    JOB.say(f"💡 {rev['summary']} ({time.monotonic() - t0:.0f} ثانية)")
    return 0


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
        elif step == "hook":
            code = _hook_step(d)
            if code and what != step:   # the plan picks its own opening then
                JOB.say("⚠️ كمّلت بلا هوك مختار. تگدر تختاره من خانة الهوك")
                code = 0
        elif step == "viewer":
            code = _viewer_step(d)
        elif step in ("sentences", "captions"):
            code = _review_step(d, step)
            if code and what != step:   # inside a longer job the rules' own cut still stands: carry on
                JOB.say("⚠️ كمّلت بقص القواعد. تگدر تعيد مراجعة المساعد من شاشة الجمل")
                code = 0
        elif step == "images":
            code = _pipe("images", d)
            if code:   # pictures are a nicety for the storyboard: a failed download never stops the episode
                JOB.say("⚠️ بعض الصور ما نزلت، تنجاب وقت النسخة الكاملة")
                code = 0
        elif step == "youtube":
            code = _youtube_step(d)
        elif step == "ai":
            code = _ai_step(d)
        elif step == "translate":
            code = _translate(d)
        elif step == "script-names":
            code = _script_names(d)
        elif step == "dub":
            code = _dub_step(d)
        elif step == "thumbs":
            code = _thumbs_step(d)
        elif step == "style-ref":
            code = style_from_reference(Path(JOB.message))
        elif step == "reels-pick":
            code = _reels_pick(d)
        elif step == "shorts":
            code = _pipe("shorts", d)
        elif step == "export" and (JOB.message or "").startswith("res:"):   # a copy at the size he picked
            code = _run([sys.executable, "-m", "editor.pipeline.export", str(d), JOB.message[4:]])
        elif step == "export":   # a smaller copy for sending (the full file stays as it is)
            mb = re.sub(r"[^0-9.]", "", JOB.message or "") or "200"
            code = _pipe("deliver", d, "--max-mb", mb)
        elif step == "chat":
            code = _chat_step(d)
        elif step == "assist":
            code = _claude(ASSIST_PROMPT.format(ep=d, message=JOB.message or "راجع الخطة وحسّنها") + learning.prompt_block(HOME), tier="mid")
        elif step == "smart":
            code = _smart_step(d, (JOB.message or "").strip())
        elif step == "youtube-langs":
            code = _youtube_langs_step(d)
        elif step == "opinion":
            code = _opinion_step(d)
        elif step == "council":
            code = _council_step(d)
        elif step == "app-ideas":
            code = _app_ideas_step(d)
        elif step == "learn":
            code = _learn_step(d)
        elif step == "selfcheck":
            code = _selfcheck_step(d)
        elif step == "plan":
            code = _claude(PLAN_PROMPT.format(ep=d, extra=_plan_extra(d) + _files_note(d), money=_money_rule()), tier="best")
            if code == 0:
                _own_media(d)
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
        if step in ("preview", "render"):   # every build is kept as a version he can go back to
            try:
                v = studio.save_version(Episode(d), auto=True)
                JOB.say(f"🗂️ انحفظت «{v['name']}» بالنسخ")
            except Exception as exc:   # a version is a bonus, never a reason to fail the job
                JOB.say(f"⚠️ ما گدرت أحفظ نسخة: {exc}")
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
    if what not in ("chat",):   # a Mac notification when something long ends (he may be in another app)
        name = _meta(EPISODES / ep_id).get("name", ep_id) if (EPISODES / ep_id).exists() else ep_id
        _safe(lambda: comfort.notify("يو آر يو", (f"✅ {STEP_NAMES.get(JOB.steps[-1] if JOB.steps else what, what)} خلص" if JOB.ok
                                                 else "⚠️ وگف قبل ما يكمل") + f" · {name}"))


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
APP_STATE = {"update": None}
PORT = [47823]   # None | "available" | "running"


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
    (HOME / "after_update").unlink(missing_ok=True)
    if not os.environ.get("URU_APP_PATH"):    # the first app (المونتير) does not say its version: always old
        installed = next((p for p in (Path("/Applications/URU.app"), Path.home() / "Applications" / "URU.app")
                          if (p / "Contents" / "MacOS" / "URU").exists()), None)
        tries = HOME / "app_swap_tries"
        n = int(tries.read_text() or 0) if tries.exists() else 0
        tries.write_text(str(n + 1))
        if installed and n >= 3:
            APP_STATE["update"] = "stuck"     # it keeps coming back: say where the new app is, stop trying
            return
        if installed:   # already there: open it, close this one, and put the old one in the bin (the Dock icon too)
            old = _parent_app()
            trash = f"mv '{old}' ~/.Trash/ 2>/dev/null;" if old.startswith(("/Applications/", str(Path.home() / "Applications"))) else ""
            subprocess.Popen(["/bin/bash", "-c", f"sleep 0.3; kill {os.getppid()}; kill {os.getpid()}; sleep 1; {trash} open '{installed}'"],
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
        APP_STATE["app_pending"] = True     # swapped quietly when he closes the app (apply_on_exit)


def auto_update() -> None:
    """Owner, 2026-10-25: never "updating…" when he opens the app; it should just be new. So the newest code is
    readied in the background (setup.sh --stage → code.next) while he works, and swapped in when the app closes."""
    if not os.environ.get("MONTIER_APP") or not (CODE / "app" / "setup.sh").exists():
        return
    log = HOME / "logs" / "update.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        subprocess.run(["/bin/bash", str(CODE / "app" / "setup.sh"), "--stage"], stdout=f, stderr=f,
                       env={**os.environ, "MONTIER_HOME": str(HOME)}, timeout=3600)


def apply_on_exit() -> None:
    """The app is closing: the staged code takes the place of the old (two renames), and a newer app window is
    swapped in quietly (it opens new next time)."""
    nxt, old = HOME / "code.next", HOME / "code.old"
    if (nxt / ".uru_version.json").exists() and CODE == HOME / "code":
        try:
            nm_old, nm_new = CODE / "editor/remotion/node_modules", nxt / "editor/remotion/node_modules"
            if nm_old.exists() and not nm_new.exists():
                nm_old.rename(nm_new)
            shutil.rmtree(old, ignore_errors=True)
            CODE.rename(old)
            nxt.rename(CODE)
            (CODE / ".uru_version.json").replace(HOME / "version.json")
            subprocess.Popen(["/bin/rm", "-rf", str(old)], start_new_session=True)
        except OSError:
            pass
    if APP_STATE.get("app_pending") and MAC and (CODE / "app" / "setup.sh").exists():
        subprocess.Popen(["/bin/bash", str(CODE / "app" / "setup.sh"), "--app", "quiet"], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def version() -> dict:
    try:
        return json.loads((HOME / "version.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


SFX_AR = {"whoosh_soft": "ووش ناعم", "whoosh_fast": "ووش سريع", "whoosh_heavy": "ووش ثقيل", "impact": "ضربة سينمائية",
          "impact_metal": "ضربة حديد", "riser_long": "صعود طويل", "downlifter": "نزول", "shutter": "كاميرا", "flash_pop": "فلاش",
          "typewriter": "آلة كاتبة", "keyboard": "كيبورد", "cash": "صندوق فلوس", "heartbeat": "نبض قلب", "clock_tick": "ساعة",
          "notification": "إشعار", "error_buzz": "غلط", "glitch_digital": "تشويش رقمي", "static_tv": "تلفزيون مشوّش",
          "tape_stop": "شريط يوگف", "record_scratch": "سكراتش", "swipe_ui": "سحبة شاشة", "bubble_pop": "فقاعة", "bell": "جرس",
          "gong": "گونگ", "drum_hit": "طبل", "laser": "ليزر", "sparkle": "لمعة", "page_flip": "قلب صفحة", "thunder": "رعد",
          "wind": "هوا", "phone_vibrate": "موبايل يهتز", "door_slam": "باب ينسد", "suspense_hit": "ضربة كشف",
          "transition_sweep": "انتقال", **{"whoosh": "ووش", "swoosh": "سحبة", "boom": "بووم", "pop": "طگة", "click": "كليك", "ding": "دينگ", "hit": "ضربة",
          "riser": "صعود", "paper": "ورق", "glitch": "تشويش", "tick": "تك تك", "switch": "مفتاح", "factory_machine": "مكينة مصنع",
          "old_factory": "مصنع قديم", "robot_arm": "ذراع روبوت", "camera": "كاميرا", "typing": "طباعة", "heartbeat": "نبض قلب", "boom_deep": "بوم عميق", "braam": "براام (تريلر)", "reverse_cymbal": "صنج معكوس", "whoosh_reverse": "ويش معكوس",
          "tick_soft": "تكة ناعمة", "pop_soft": "بوب ناعم", "ui_click": "نقرة واجهة", "coin": "عملة", "level_up": "مستوى جديد",
          "magic_chime": "رنة سحرية", "camera_flash": "فلاش كاميرا", "paper_slide": "ورقة تنسحب", "stamp": "ختم", "pen_scribble": "قلم يكتب",
          "radar_ping": "رادار", "sonar": "سونار", "crowd_gasp": "شهقة ناس", "heartbeat_fast": "قلب سريع", "breath_in": "نفس",
          "rumble": "هدير", "glass_break": "زجاج ينكسر", "power_down": "انطفاء", "swoosh_up": "ويش للفوگ", "drop_bass": "نزلة بيس"}}
STYLE_NAMES = {"investigation": "لوحة تحقيق", "noir": "سينما الليل", "retro-collage": "كولاج ريترو", "vox": "ورق وقص ولزق"}


def styles_list() -> list[dict]:
    """The style library for the app's Styles panel: Arabic name, group, colours and fonts (the card preview),
    and what it does to the video."""
    from editor.pipeline.styles import _style_files, load_style
    out = []
    for f in _style_files():
        st = load_style(f.stem)
        name = st.title_ar or STYLE_NAMES.get(f.stem) or re.split(r"\s+—\s+|\.|،", st.summary, maxsplit=1)[0].strip()[:30]
        how = re.search(r"^- (.+)$", st.notes, re.M)
        out.append({"id": f.stem, "name": name, "summary": re.sub(r"^[^—]{0,40}—\s*", "", st.summary),
                    "category": st.category or "الأساسية", "palette": st.palette, "fonts": st.fonts,
                    "texture": st.texture, "fits": st.fits, "how": how.group(1) if how else ""})
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
            if path == "/api/prefs":
                return self._json(prefs())
            if path == "/api/learning":
                return self._json(learning.status(HOME))
            if path == "/api/security":
                return self._json(comfort.security(HOME))
            if path == "/api/comfort":   # templates, backup, phone page
                ph = comfort.phone_settings(HOME)
                return self._json({"templates": comfort.templates(HOME), "backup": comfort.backup_status(HOME),
                                   "phone": {"on": bool(ph.get("on")), "url": f"http://{comfort.lan_ip()}:{PHONE_PORT}/m/{ph.get('code', '')}" if ph.get("on") else ""}})
            if path == "/api/brains":
                return self._json(brains.status(HOME, HOME / "tools"))
            m = re.match(r"^/api/episodes/([^/]+)/(reports|retention)$", path)
            if m:   # the smart tools: their reports, and where the viewer may get bored
                ed = episode_dir(m.group(1))
                if m.group(2) == "retention":
                    return self._json(retention(ed))
                rd = ed / "edit" / "reports"
                return self._json({k: (rd / f"{k}.md").read_text(encoding="utf-8") for k in SMART if (rd / f"{k}.md").exists()})
            m = re.match(r"^/api/episodes/([^/]+)/opinions$", path)
            if m:   # what ChatGPT and Gemini said about this plan
                od = episode_dir(m.group(1)) / "edit" / "opinions"
                return self._json({k: (od / f"{k}.md").read_text(encoding="utf-8") for k in (*brains.BRAINS, "applied") if (od / f"{k}.md").exists()})
            if path == "/api/selfcheck":
                return self._json(selfcheck())
            if path == "/api/eleven":
                from . import dubbing
                return self._json(dubbing.status(HOME))
            if path == "/api/ai-check":
                return self._json(ai_check())
            if path.startswith("/api/face-file/"):
                return self._file(HOME / "face" / Path(path.rsplit("/", 1)[1]).name)
            if path == "/api/fonts":
                from . import fonts
                return self._json(fonts.catalog(HOME))
            if path.startswith("/api/font-file/"):   # his fonts, for the previews in the app
                from . import fonts
                return self._file(fonts.folder(HOME) / Path(path.rsplit("/", 1)[1]).name)
            if path == "/api/youtube":
                from . import youtube
                return self._json(youtube.status(HOME))
            if path == "/oauth/youtube":   # Google sends him back here after he says yes
                from . import youtube
                try:
                    st = youtube.finish(HOME, q.get("code", ""), q.get("state", ""), _yt_redirect())
                    msg = f"✅ انربطت قناتك{(' «' + st['channel'] + '»') if st['channel'] else ''}. ارجع للتطبيق."
                except ValueError as exc:
                    msg = f"❌ {exc}"
                body = (f'<!doctype html><meta charset="utf-8"><body style="font:20px system-ui;background:#111;color:#eee;'
                        f'display:grid;place-items:center;height:90vh;direction:rtl">{msg}</body>').encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
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
            m = re.match(r"^/api/episodes/([^/]+)/cover$", path)
            if m:
                return self._file(episode_cover(episode_dir(m.group(1))))
            m = re.match(r"^/api/episodes/([^/]+)/(sentences|captions|plan|timeline|look|sound|idea|review|frame|voice-sample|media|effects|export-info|options|suggest|variants|versions|markers)$", path)
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
            from editor.pipeline.grade import LOOK_GROUPS, PACK_CATS
            return self._json({"settings": look_settings(ep), "names": LOOK_NAMES, "groups": LOOK_GROUPS, "group_of": PACK_CATS})
        if what == "sound":
            from editor.pipeline.compose import sound_settings
            return self._json(sound_settings(ep))
        if what == "idea":
            f, sf = d / "edit" / "idea.txt", d / "edit" / "style.txt"
            style = sf.read_text(encoding="utf-8").strip() if sf.exists() else ""
            name = next((x["name"] for x in styles_list() if x["id"] == style), "")
            return self._json({"text": f.read_text(encoding="utf-8") if f.exists() else "", "style": style, "style_name": name})
        if what == "review":
            kind = q.get("kind", "captions")
            if kind not in ("captions", "sentences", "hook", "viewer"):
                return self._err("لا", 400)
            f = d / "edit" / "work" / "app" / f"{kind}_review.json"
            return self._json(json.loads(f.read_text(encoding="utf-8")) if f.exists() else None)
        if what == "markers":
            return self._json(studio.markers(ep))
        if what == "hook":
            f = d / "edit" / "hook.json"
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
            exports = [{"name": f.name, "size": f.stat().st_size} for f in sorted((d / "edit" / "exports").glob("*.mp4"))] \
                if (d / "edit" / "exports").exists() else []
            try:
                from editor.pipeline.media import probe
                mi = probe(final) if final.exists() else None
                master = [mi.width, mi.height] if mi else None
            except Exception:
                master = None
            ch = d / "edit" / "chapters.txt"
            cr = d / "edit" / "credits.txt"
            shorts = sorted((d / "edit").glob("short_*.mp4")) + sorted((d / "edit" / "shorts").glob("*.mp4") if (d / "edit" / "shorts").exists() else [])
            return self._json({"final": final.exists(), "size": final.stat().st_size if final.exists() else 0,
                               "chapters": ch.read_text(encoding="utf-8") if ch.exists() else "",
                               "credits": cr.read_text(encoding="utf-8") if cr.exists() else "",
                               "shorts_plan": plan.get("shorts", []), "shorts": [str(f.relative_to(d)) for f in shorts],
                               "exports": exports, "master": master, "canvas": _canvas(d),
                               "subs": sorted(f.stem.split("-", 1)[1] for f in (d / "edit").glob("subtitles-*.srt")),
                               "dubs": sorted(f.stem for f in (d / "edit" / "dubs").glob("*.mp3")) if (d / "edit" / "dubs").exists() else [],
                               "minutes": round((master and 0) or _duration_min(final), 1),
                               "thumbs": [str(f.relative_to(d)) for f in sorted((d / "edit" / "thumbs").glob("*.png"))] if (d / "edit" / "thumbs").exists() else [],
                               "youtube": json.loads((d / "edit" / "youtube.json").read_text(encoding="utf-8")).get("id")
                               if (d / "edit" / "youtube.json").exists() else None,
                               "posts": (d / "edit" / "shorts" / "posts.txt").read_text(encoding="utf-8")
                               if (d / "edit" / "shorts" / "posts.txt").exists() else ""})
        if what == "options":
            from editor.pipeline.options import load_options
            return self._json(load_options(ep))
        if what == "versions":
            return self._json(studio.list_versions(ep))
        if what == "variants":
            return self._json(studio.ai_variants(ep, int(q.get("i", -1))))
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
        if what == "voicefix":   # a word re-said in his own voice (ElevenLabs); "remove" takes one back
            from . import dubbing
            lst = ep.edit / "voice_patches.json"
            if b.get("remove") is not None:
                items = [p for p in (json.loads(lst.read_text(encoding="utf-8")) if lst.exists() else []) if p["start"] != float(b["remove"])]
                lst.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
                return self._json({"patches": items})
            return self._json(dubbing.fix_word(HOME, d, float(b.get("start", 0)), float(b.get("end", 0)), str(b.get("text", ""))))
        if what == "markers":
            return self._json(studio.markers(ep, list(b.get("items", []))))
        if what == "still":   # the frame under the playhead as a picture (with his colours), into edit/stills
            t = float(b.get("t", 0))
            src = frame_with_look(ep, t)
            out = ep.edit / "stills"
            out.mkdir(parents=True, exist_ok=True)
            dest = out / f"still_{int(t // 60):02d}-{int(t % 60):02d}-{int((t % 1) * 100):02d}{src.suffix}"
            shutil.copyfile(src, dest)
            _safe(lambda: reveal(dest))
            return self._json({"file": dest.name})
        if what == "scene-clip":   # copy one scene's look (effect, transition, colours, sound) and paste it on another
            if b.get("do") == "copy":
                return self._json({"clip": studio.copy_scene(ep, int(b.get("i", 0)), HOME)})
            return self._json({"clip": studio.paste_scene(ep, int(b.get("i", 0)), HOME)})
        if what == "tool":   # one-click smart tools that change the plan right away (undo brings it back)
            tool = b.get("tool")
            if tool == "punch":
                n = studio.smart_punch(ep)
                return self._json({"message": f"ضفت {n} تقريب على كلماتك القوية. ابني معاينة حتى تشوفها" if n else "ما لگيت مكان مناسب للتقريب"})
            if tool == "beats":
                n = studio.beat_sync(ep)
                return self._json({"message": f"{n} تبديل مشهد صار على ضربة الموسيقى" if n else "التبديلات أصلاً قريبة من الإيقاع"})
            raise ValueError("أداة مو معروفة")
        if what == "version":   # save / use / rename / delete a version
            act, n = b.get("do"), int(b.get("n", 0))
            if act == "save":
                studio.save_version(ep, str(b.get("name", "")))
                return self._json(studio.list_versions(ep))
            if act == "use":
                return self._json(studio.use_version(ep, n))
            if act == "rename":
                return self._json(studio.rename_version(ep, n, str(b.get("name", ""))))
            if act == "delete":
                return self._json(studio.delete_version(ep, n))
            raise ValueError("شنو تريد تسوي بالنسخة؟")
        if what == "variant":
            studio.snapshot(ep)
            return self._json(studio.ai_variants(ep, int(b.get("i", -1))) if not b.get("name") else
                              studio.ai_choose(ep, int(b.get("i", -1)), str(b["name"])))
        if what == "srt":   # subtitle files for YouTube (Arabic and/or English), beside the episode
            from editor.pipeline.options import subtitles_srt
            lang = "en" if b.get("lang") == "en" else "ar"
            if lang == "en" and not (d / "edit" / "captions_en.json").exists():
                raise ValueError("ترجم أول: من «الإضافات» اختار كابشن إنگليزي")
            f = d / "edit" / f"subtitles-{lang}.srt"
            f.write_text(subtitles_srt(ep, lang), encoding="utf-8")
            return self._json({"ok": True, "file": str(f.relative_to(d))})
        if what == "restyle":   # the whole video in one style: remembered, then re-planned and rebuilt
            ok = {x["id"] for x in styles_list()}
            if b.get("style") not in ok:
                raise ValueError("هذا الستايل مو موجود")
            if not ep.plan.exists() and not (d / "work" / "plan_input.txt").exists():
                (d / "edit").mkdir(parents=True, exist_ok=True)
                (d / "edit" / "style.txt").write_text(b["style"], encoding="utf-8")
                return self._json({"ok": True, "started": False})
            studio.snapshot(ep)
            (d / "edit" / "style.txt").write_text(b["style"], encoding="utf-8")
            start_job(d.name, "restyle", "أعد الحلقة كلها بهذا الستايل")
            return self._json({"ok": True, "started": True})
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
        if what == "media-note":
            return self._json(studio.media_note(ep, str(b.get("name", "")), b.get("note"), b.get("use")))
        if what == "short":
            plan = json.loads(ep.plan.read_text(encoding="utf-8"))
            fr, to = float(b.get("from", 0)), float(b.get("to", 30))
            if not 15 <= to - fr <= 90:
                raise ValueError("الريل لازم بين ١٥ و٩٠ ثانية")
            plan["shorts"] = (plan.get("shorts") or []) + [{"from": round(fr, 2), "to": round(to, 2), "title": str(b.get("title", ""))}]
            ep.plan.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
            return self._json({"shorts": plan["shorts"]})
        if what == "hook":
            return self._json(save_hook(d, int(b.get("pick", 0))))
        if what == "sentences":
            return self._json(studio.set_sentences(ep, b.get("keep") or {}))
        if what == "captions":
            return self._json(studio.edit_words(ep, b.get("fixes") or {}, b.get("delete") or []))
        if what == "look":
            return self._json(studio.save_look(ep, b))
        if what == "sound":
            keep = {"clean": max(0, min(4, int(b.get("clean", 1)))), "music": str(b.get("music", "auto")),
                    "level": max(-38.0, min(-18.0, float(b.get("level", -28)))), "sfx": bool(b.get("sfx", True)), "v": 2}
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
            if path == "/api/look-thumbs":   # one group of the big colour library
                from .studio import group_thumbs
                b = self._body()
                src = Path(str(b.get("path", ""))).expanduser()
                if not src.is_file():
                    raise ValueError("ما لگيت الفيديو بهذا المكان")
                return self._json(group_thumbs(src, HOME / "cache", str(b.get("source", "rec709")), [str(x) for x in b.get("ids", [])][:40]))
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
                learning.note(HOME, m.group(1), "طلب من المساعد", text)
                start_job(m.group(1), "chat", text)
                return self._json({"ok": True, "messages": chat_load(d)})
            m = re.match(r"^/api/episodes/([^/]+)/(sentences|captions|look|sound|idea|beat|undo|redo|media|media-note|short|options|choose|restyle|srt|variant|version|tool|voicefix|markers|still|scene-clip)$", path)
            if m:
                b = self._body()
                if m.group(2) not in ("media",):   # what he changes is how the assistant learns his taste
                    try:
                        learning.note(HOME, m.group(1), m.group(2), b)
                    except OSError:
                        pass
                return self._studio_post(episode_dir(m.group(1)), m.group(2), b)
            if path == "/api/style-ref":   # a video he likes: saved beside his styles, then the style is made from it
                name = Path(q.get("name", "")).name
                if Path(name).suffix.lower() not in (".mp4", ".mov", ".m4v", ".webm") or name.startswith("."):
                    raise ValueError("دز فيديو (mp4 أو mov)")
                n = int(self.headers.get("Content-Length") or 0)
                dest = HOME / "refs" / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "wb") as f:
                    while n > 0:
                        chunk = self.rfile.read(min(n, 1 << 20))
                        if not chunk:
                            break
                        f.write(chunk)
                        n -= len(chunk)
                ep_id = q.get("ep") or ""
                start_job(ep_id, "style-ref", str(dest))
                return self._json({"ok": True})
            if path == "/api/extract-text":   # the script as a Word file: its text
                n = int(self.headers.get("Content-Length") or 0)
                return self._json({"text": extract_text(q.get("name", ""), self.rfile.read(min(n, 50 * 1024 * 1024)))})
            m = re.match(r"^/api/episodes/([^/]+)/upload$", path)
            if m:
                from editor.pipeline.paths import Episode
                from .studio import MEDIA_EXT, media_list
                d = episode_dir(m.group(1))
                q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))
                name = Path(q.get("name", "")).name
                if not name or Path(name).suffix.lower() not in MEDIA_EXT or name.startswith("."):
                    raise ValueError("هذا مو صورة ولا فيديو ولا صوت")
                n = int(self.headers.get("Content-Length") or 0)
                if n > 8 * 1024 ** 3:
                    raise ValueError("الملف كلش جبير")
                folder = d / "edit" / "media"
                folder.mkdir(parents=True, exist_ok=True)
                with open(folder / name, "wb") as f:
                    while n > 0:
                        chunk = self.rfile.read(min(n, 1 << 20))
                        if not chunk:
                            break
                        f.write(chunk)
                        n -= len(chunk)
                return self._json(media_list(Episode(d)))
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
                    target = {"final": d / "edit" / "final.mp4", "preview": d / "edit" / "preview.mp4", "exports": d / "edit" / "exports", "shorts": d / "edit" / "shorts", "edit": d / "edit", "thumbs": d / "edit" / "thumbs", "dubs": d / "edit" / "dubs"}.get(b.get("what"), d)
                    reveal(target if target.exists() else d)
                elif act == "rename":
                    meta = _meta(d)
                    meta["name"] = (b.get("name") or meta["name"]).strip()
                    _save_meta(d, meta)
                return self._json({"ok": True})
            if path == "/api/prefs":
                return self._json(prefs(self._body()))
            if path == "/api/security":
                act = self._body().get("do")
                if act == "fix":
                    return self._json(comfort.fix_permissions(HOME))
                if act == "unlink-all":
                    phone_server(False)
                    return self._json(comfort.unlink_all(HOME))
                raise ValueError("شنو تريد؟")
            if path == "/api/comfort":
                b = self._body()
                act = b.get("do")
                if act == "phone":
                    comfort.set_phone(HOME, bool(b.get("on")))
                    phone_server(bool(b.get("on")))
                elif act == "backup":
                    r = comfort.backup(HOME, EPISODES)
                    if not r.get("ok"):
                        raise ValueError(r["why"])
                elif act == "template-save":
                    comfort.save_template(HOME, episode_dir(str(b.get("ep", ""))) / "edit", str(b.get("name", "")))
                elif act == "template-use":
                    ed = episode_dir(str(b.get("ep", ""))) / "edit"
                    from editor.pipeline.paths import Episode
                    from .studio import snapshot
                    snapshot(Episode(ed.parent))
                    comfort.apply_template(HOME, ed, str(b.get("name", "")))
                elif act == "template-delete":
                    comfort.delete_template(HOME, str(b.get("name", "")))
                else:
                    raise ValueError("شنو تريد؟")
                ph = comfort.phone_settings(HOME)
                return self._json({"templates": comfort.templates(HOME), "backup": comfort.backup_status(HOME),
                                   "phone": {"on": bool(ph.get("on")), "url": f"http://{comfort.lan_ip()}:{PHONE_PORT}/m/{ph.get('code', '')}" if ph.get("on") else ""}})
            if path == "/api/listen":   # a voice command: his recorded words → text (the app's own speech model)
                n = int(self.headers.get("Content-Length") or 0)
                if not 0 < n < 30 * 2**20:
                    raise ValueError("التسجيل فارغ أو كبير")
                f = HOME / "tmp" / ("voice" + (".webm" if "webm" in (self.headers.get("Content-Type") or "") else ".m4a"))
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(self.rfile.read(n))
                return self._json({"text": _transcribe_file(f)})
            m = re.match(r"^/api/brains/(chatgpt|gemini)/link(/code|/cancel|/state)?$", path)
            if m:   # one button: install if needed, sign in in the browser, paste the code here if the page shows one
                lk, sub = brains.LINKS[m.group(1)], m.group(2) or ""
                if sub == "/code":
                    return self._json(lk.submit(str(self._body().get("code", ""))))
                if sub == "/cancel":
                    lk.cancel()
                    return self._json(lk.state())
                if sub == "/state":
                    return self._json(lk.state())
                return self._json(lk.start(HOME, HOME / "tools", opener=(lambda u: subprocess.Popen(["open", u])) if MAC else None))
            m = re.match(r"^/api/brains/(chatgpt|gemini)/(install|login|test|on|off)$", path)
            if m:   # install the maker's tool, sign in with his account (in Terminal), check it answers
                k, act = m.groups()
                if act == "install":
                    brains.install(k, HOME, HOME / "tools")
                elif act == "login":
                    open_terminal(brains.login_command(k, HOME / "tools").replace('"', '\\"'))
                elif act == "test":
                    return self._json(brains.test(k, HOME, HOME / "tools"))
                else:
                    brains.set_on(k, act == "on", HOME)
                return self._json(brains.status(HOME, HOME / "tools"))
            if path == "/api/learning":   # he reads, corrects or clears what the assistant learned
                learning.set_taste(HOME, str(self._body().get("taste", "")))
                return self._json(learning.status(HOME))
            if path == "/api/idea":   # kept on his Mac too, in case the GitHub page was closed
                with open(HOME / "ideas.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps({"t": time.time(), "text": str(self._body().get("text", ""))[:4000]}, ensure_ascii=False) + "\n")
                return self._json({"ok": True})
            if path in ("/api/eleven/key", "/api/eleven/unlink"):
                from . import dubbing
                return self._json(dubbing.set_key(HOME, str(self._body().get("key", ""))) if path.endswith("key") else dubbing.unlink(HOME))
            if path in ("/api/face/add", "/api/face/remove"):
                n = int(self.headers.get("Content-Length") or 0)
                if path.endswith("add"):
                    return self._json(face_files("add", q.get("name", ""), self.rfile.read(min(n, 300 * 1024 * 1024))))
                return self._json(face_files("remove", str(self._body().get("name", ""))))
            if path in ("/api/fonts/get", "/api/fonts/remove"):
                from . import fonts
                fam = str(self._body().get("family", ""))
                return self._json(fonts.download(HOME, fam) if path.endswith("get") else fonts.remove(HOME, fam))
            if path == "/api/fonts/add":
                from . import fonts
                n = int(self.headers.get("Content-Length") or 0)
                return self._json(fonts.add_own(HOME, q.get("name", ""), self.rfile.read(min(n, 30 * 1024 * 1024))))
            if path.startswith("/api/youtube/"):
                from . import youtube
                act, b = path.rsplit("/", 1)[1], self._body()
                if act == "client":
                    return self._json(youtube.set_client(HOME, str(b.get("id", "")), str(b.get("secret", ""))))
                if act == "start":
                    return self._json({"url": youtube.auth_url(HOME, _yt_redirect())})
                if act == "unlink":
                    return self._json(youtube.unlink(HOME))
                return self._err("مو موجود", 404)
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


PHONE_PORT = 47824
PHONE_PAGE = """<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>يو آر يو</title><style>body{margin:0;font-family:-apple-system,sans-serif;background:#051F20;color:#DAF1DE;padding:16px}
.c{background:#0B2B26;border:1px solid #235347;border-radius:16px;padding:14px;margin-bottom:12px}h1{font-size:20px;margin:0 0 12px}
.s{color:#8EB69B;font-size:13px}.b{display:inline-block;margin:8px 6px 0 0;padding:10px 16px;border-radius:99px;border:0;font-size:15px;font-weight:700;background:#8EB69B;color:#051F20}
.b.g{background:#163832;color:#DAF1DE}.log{font-size:12px;color:#b9d9c3;white-space:pre-wrap;line-height:1.6;margin-top:8px}.bar{height:5px;background:#235347;border-radius:3px;margin-top:8px}.bar i{display:block;height:100%;background:#8EB69B;border-radius:3px}</style></head>
<body><h1>يو آر يو · من تلفونك</h1><div id="job"></div><div id="eps"></div><script>
const B=location.pathname.replace(/\/$/,"");const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"})[c]);
async function go(ep,what){await fetch(B+"/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ep,what})});load();}
async function load(){const d=await (await fetch(B+"/state")).json();const j=d.job;
document.getElementById("job").innerHTML=j.running?`<div class="c"><b>⏳ شغّال هسة: ${esc(j.name)}</b><div class="s">${esc(j.step)}</div>${j.progress!=null?`<div class="bar"><i style="width:${j.progress}%"></i></div>`:""}<div class="log">${esc(j.lines.join("\n"))}</div><button class="b g" onclick="go('${esc(j.ep)}','stop')">وگّفه</button></div>`:(j.ep?`<div class="c"><b>${j.ok?"✅ آخر شغل خلص":"⚠️ آخر شغل وگف"}</b><div class="s">${esc(j.name)}</div></div>`:"");
document.getElementById("eps").innerHTML=d.episodes.map(e=>`<div class="c"><b>${esc(e.name)}</b><div class="s">${esc(e.stage)}</div>
${e.plan&&!e.running?`<button class="b" onclick="go('${esc(e.id)}','build')">ابني معاينة</button><button class="b g" onclick="go('${esc(e.id)}','final')">النسخة النهائية</button>`:""}</div>`).join("");}
load();setInterval(load,4000);</script></body></html>"""


class PhoneHandler(BaseHTTPRequestHandler):
    """The phone page on his home Wi-Fi (owner, 2026-10-25): see what is running, start a preview or the final build,
    stop a job. Nothing else is reachable, and every path needs his secret code."""

    def log_message(self, *a):
        pass

    def _ok(self) -> str | None:
        st = comfort.phone_settings(HOME)
        parts = self.path.split("?")[0].strip("/").split("/")
        if not st.get("on") or len(parts) < 2 or parts[0] != "m" or not secrets.compare_digest(parts[1].upper(), st.get("code", "-")):
            self.send_response(404)
            self.end_headers()
            return None
        return "/".join(parts[2:])

    def _send(self, body: bytes, ctype: str):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        rest = self._ok()
        if rest is None:
            return
        if rest == "":
            return self._send(PHONE_PAGE.encode("utf-8"), "text/html; charset=utf-8")
        if rest == "state":
            eps = []
            for e in list_episodes()[:12]:
                d = e["done"]
                stage = "جاهزة" if d["render"] else "المعاينة جاهزة" if d["preview"] else "الخطة جاهزة" if d["plan"] else "انقصّت" if d["cut"] else "تتجهز"
                eps.append({"id": e["id"], "name": e.get("name", e["id"]), "stage": stage, "plan": d["plan"], "running": e["running"]})
            name = _meta(EPISODES / JOB.ep).get("name", JOB.ep) if JOB.ep and (EPISODES / JOB.ep).exists() else ""
            job = {"running": JOB.running, "ok": JOB.ok, "ep": JOB.ep, "name": name, "progress": JOB.progress,
                   "step": STEP_NAMES.get(JOB.step or "", ""), "lines": [x for x in JOB.lines if x.strip()][-6:]}
            return self._send(json.dumps({"episodes": eps, "job": job}, ensure_ascii=False).encode("utf-8"), "application/json")
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        rest = self._ok()
        if rest != "run":
            if rest is not None:
                self.send_response(404)
                self.end_headers()
            return
        n = int(self.headers.get("Content-Length") or 0)
        b = json.loads(self.rfile.read(min(n, 4096)) or b"{}")
        what = b.get("what")
        try:
            if what == "stop":
                stop_job()
            elif what in ("build", "final"):
                start_job(str(b.get("ep", "")), what)
        except (ValueError, RuntimeError, FileNotFoundError) as exc:
            return self._send(json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8"), "application/json")
        return self._send(b'{"ok":true}', "application/json")


PHONE = [None]


def phone_server(on: bool) -> None:
    """Start or stop the phone page's own little server (all addresses of this Mac, port 47824)."""
    if on and PHONE[0] is None:
        try:
            ps = ThreadingHTTPServer(("0.0.0.0", PHONE_PORT), PhoneHandler)
        except OSError:
            return
        ps.daemon_threads = True
        PHONE[0] = ps
        threading.Thread(target=ps.serve_forever, daemon=True).start()
    elif not on and PHONE[0] is not None:
        ps, PHONE[0] = PHONE[0], None
        threading.Thread(target=ps.shutdown, daemon=True).start()


def nightly_backup() -> None:
    while True:
        if comfort.backup_status(HOME).get("auto", True) and comfort.drive_folder() and comfort.backup_due(HOME) and not JOB.running:
            _safe(lambda: comfort.backup(HOME, EPISODES))
        time.sleep(3600)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m editor.app.server")
    ap.add_argument("--port", type=int, default=47823)
    a = ap.parse_args(argv)
    EPISODES.mkdir(parents=True, exist_ok=True)
    PORT[0] = a.port
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    srv.daemon_threads = True

    def bye(*_):
        stop_job()
        _safe(apply_on_exit)
        os._exit(0)
    signal.signal(signal.SIGTERM, bye)
    print(f"URU شغّال: http://127.0.0.1:{a.port}  (الحلقات: {EPISODES})", flush=True)
    threading.Timer(2.0, lambda: _safe(check_app)).start()
    threading.Timer(25.0, lambda: _safe(auto_update)).start()
    threading.Timer(8.0, lambda: _safe(preload_libraries)).start()
    threading.Thread(target=nightly_backup, daemon=True).start()
    if comfort.phone_settings(HOME).get("on"):
        phone_server(True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
