"""ChatGPT and Gemini beside Claude (owner, 2026-10-25: "اريد اربط الحساب مالتي… مشترك بيهم بنسخة pro").

Each one runs through its maker's own command-line tool, signed in with his own subscription account on his Mac:
  - ChatGPT: OpenAI's Codex CLI ("Sign in with ChatGPT"; `codex exec` uses his plan's limits).
  - Gemini:  Google's Antigravity CLI (`agy`, sign-in with his Google account; replaced Gemini CLI in 2026).
They only read and answer (read-only): second opinions on a plan, ideas, image prompts, feature suggestions.
They never change his files; Claude stays the one that edits. Their sign-in tokens stay where their tools keep
them (the Mac's keychain or their own folder), never in this app or the repository.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

BRAINS = {
    "chatgpt": {"name": "شات جي بي تي", "by": "أوپن إي آي",
                "install": "npm", "package": "@openai/codex", "exe": "codex"},
    "gemini": {"name": "جيميناي", "by": "گوگل",
               "install": "script", "script": "https://antigravity.google/cli/install.sh", "exe": "agy"},
}
TIMEOUT = 900
_jobs: dict[str, dict] = {}
_lock = threading.Lock()


def _state_file(home: Path) -> Path:
    return Path(home) / "brains.json"


def _state(home: Path) -> dict:
    try:
        return json.loads(_state_file(home).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(home: Path, st: dict) -> None:
    _state_file(home).parent.mkdir(parents=True, exist_ok=True)
    _state_file(home).write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")


def exe(name: str, tools: Path) -> str | None:
    b = BRAINS[name]
    for p in (Path(tools) / "brains" / "bin" / b["exe"], Path.home() / ".local" / "bin" / b["exe"],
              Path("/opt/homebrew/bin") / b["exe"], Path("/usr/local/bin") / b["exe"]):
        if p.exists():
            return str(p)
    return shutil.which(b["exe"])


def _env(tools: Path) -> dict:
    env = dict(os.environ)
    node = Path(tools) / "node" / "bin"
    env["PATH"] = os.pathsep.join([str(Path(tools) / "brains" / "bin"), str(node), str(Path.home() / ".local" / "bin"),
                                   env.get("PATH", "")])
    return env


def status(home: Path, tools: Path) -> dict:
    st = _state(home)
    out = {}
    for k, b in BRAINS.items():
        e = exe(k, tools)
        job = _jobs.get(k, {})
        out[k] = {"name": b["name"], "by": b["by"], "installed": bool(e), "linked": bool(st.get(k, {}).get("ok")),
                  "on": st.get(k, {}).get("on", True), "busy": job.get("busy", False), "msg": job.get("msg", ""),
                  "last": st.get(k, {}).get("last", "")}
    return out


def install(name: str, home: Path, tools: Path) -> None:
    """Put the official tool on his Mac, in the background (a minute or two)."""
    b = BRAINS[name]
    if _jobs.get(name, {}).get("busy"):
        return

    def work():
        _jobs[name] = {"busy": True, "msg": "دا أنصّب أداة " + b["name"] + "…"}
        try:
            if b["install"] == "npm":
                npm = Path(tools) / "node" / "bin" / "npm"
                cmd = [str(npm) if npm.exists() else "npm", "install", "-g", "--prefix", str(Path(tools) / "brains"),
                       "--no-audit", "--no-fund", b["package"]]
                r = subprocess.run(cmd, env=_env(tools), capture_output=True, text=True, timeout=900)
            else:   # the maker's own installer (puts the tool in ~/.local/bin)
                r = subprocess.run(["bash", "-c", f"curl -fsSL {b['script']} | bash"], env=_env(tools),
                                   capture_output=True, text=True, timeout=900)
            ok = r.returncode == 0 and exe(name, tools)
            _jobs[name] = {"busy": False, "msg": "انصّب ✅ هسة اربط حسابك" if ok else
                           "ما گدرت أنصّبه: " + (r.stderr or r.stdout or "")[-200:]}
        except (OSError, subprocess.SubprocessError) as exc:
            _jobs[name] = {"busy": False, "msg": "ما گدرت أنصّبه: " + str(exc)[:200]}
    threading.Thread(target=work, daemon=True).start()


def login_command(name: str, tools: Path) -> str:
    """What runs in the Mac's Terminal so he signs in with his own account in the browser."""
    e = exe(name, tools)
    if not e:
        raise RuntimeError("نصّبه أول")
    if name == "chatgpt":
        return f"'{e}' login"
    return f"'{e}' -p 'Reply with one word: ready'"   # the first run opens Google's sign-in page


def ask(name: str, prompt: str, tools: Path, workdir: Path | None = None, timeout: int = TIMEOUT) -> str:
    """One question, one answer. Read-only: neither tool may change files."""
    e = exe(name, tools)
    if not e:
        raise RuntimeError(BRAINS[name]["name"] + " مو منصّب")
    cwd = str(workdir) if workdir else tempfile.gettempdir()
    if name == "chatgpt":
        with tempfile.NamedTemporaryFile("r", suffix=".txt", delete=False) as fh:
            out = fh.name
        try:
            r = subprocess.run([e, "exec", "--skip-git-repo-check", "--sandbox", "read-only", "-o", out, prompt],
                               cwd=cwd, env=_env(tools), capture_output=True, text=True, timeout=timeout,
                               stdin=subprocess.DEVNULL)
            text = Path(out).read_text(encoding="utf-8").strip() if Path(out).exists() else ""
        finally:
            Path(out).unlink(missing_ok=True)
    else:
        args = [e, "-p", prompt] + (["--add-dir", cwd] if workdir else [])
        r = subprocess.run(args, cwd=cwd, env=_env(tools), capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
        text = r.stdout.strip()
    if r.returncode != 0 or not text:
        err = (r.stderr or r.stdout or "").strip()[-300:]
        if any(w in err.lower() for w in ("login", "log in", "sign in", "auth", "unauthorized", "credential")):
            raise PermissionError(BRAINS[name]["name"] + " مو مربوط بحسابك. اربطه من الإعدادات")
        raise RuntimeError(BRAINS[name]["name"] + " ما جاوب: " + err)
    return text


def test(name: str, home: Path, tools: Path) -> dict:
    """A tiny question: if it answers, the link works (marked as linked)."""
    import time
    st = _state(home)
    try:
        ans = ask(name, "Reply with exactly one word: ready", tools, timeout=180)
        st.setdefault(name, {}).update(ok=True, last=time.strftime("%Y-%m-%d %H:%M"))
        _save_state(home, st)
        return {"ok": True, "answer": ans[:200]}
    except (RuntimeError, PermissionError, subprocess.SubprocessError, OSError) as exc:
        st.setdefault(name, {})["ok"] = False
        _save_state(home, st)
        return {"ok": False, "error": str(exc)}


def set_on(name: str, on: bool, home: Path) -> None:
    st = _state(home)
    st.setdefault(name, {})["on"] = bool(on)
    _save_state(home, st)


def active(home: Path, tools: Path) -> list[str]:
    """The ones he linked and left switched on."""
    s = status(home, tools)
    return [k for k, v in s.items() if v["installed"] and v["linked"] and v["on"]]


class Link:
    """One-button linking inside the app (owner, 2026-10-25: "اريد ربط سريع وسهل"). The maker's login runs in a
    hidden pseudo-terminal with the app's own Node on the PATH (the Mac's Terminal has no Node, so it failed there).
    It installs the tool first when needed, opens the sign-in page in the browser, and when the page shows a code
    (Gemini does) he pastes it in the app. ChatGPT finishes by itself once he approves in the browser."""
    ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07")

    def __init__(self, name: str):
        self.name, self.status, self.url, self.error, self.pid, self.fd, self.out = name, "idle", "", "", None, None, ""
        self.lock = threading.Lock()

    def state(self) -> dict:
        return {"status": self.status, "url": self.url, "error": self.error, "code": self.name == "gemini"}

    def start(self, home: Path, tools: Path, opener=None) -> dict:
        self.cancel()
        with self.lock:
            self.status, self.url, self.error, self.out = "installing" if not exe(self.name, tools) else "starting", "", "", ""
        threading.Thread(target=self._run, args=(home, tools, opener), daemon=True).start()
        return self.state()

    def _run(self, home: Path, tools: Path, opener) -> None:
        import fcntl
        import pty
        import select
        import struct
        import termios
        if not exe(self.name, tools):
            install(self.name, home, tools)
            for _ in range(900):
                if not _jobs.get(self.name, {}).get("busy"):
                    break
                threading.Event().wait(1)
            if not exe(self.name, tools):
                self.status, self.error = "error", _jobs.get(self.name, {}).get("msg") or "ما گدرت أنصّبه"
                return
        e = exe(self.name, tools)
        args = [e, "login"] if self.name == "chatgpt" else [e, "-p", "Reply with exactly one word: ready"]
        env = _env(tools)
        env["TERM"] = "xterm-256color"
        pid, fd = pty.fork()
        if pid == 0:
            try:
                os.chdir(tempfile.gettempdir())
                os.execvpe(args[0], args, env)
            finally:
                os._exit(127)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 50, 1000, 0, 0))
        with self.lock:
            self.pid, self.fd, self.status = pid, fd, "starting"
        while True:
            try:
                r, _, _ = select.select([fd], [], [], 1.0)
                if not r:
                    if self.status in ("idle",):
                        break
                    continue
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            with self.lock:
                self.out = (self.out + self.ANSI.sub(" ", chunk.decode("utf-8", "replace")))[-20000:]
                m = re.search(r"https://(?:auth\.openai\.com|accounts\.google\.com|[\w.-]*google[\w.-]*|[\w.-]*openai[\w.-]*)/\S+", self.out)
                if m and not self.url:
                    self.url, self.status = m.group(0).rstrip(".,)"), "waiting"
                    if opener:
                        opener(self.url)
        code = 1
        try:
            _, st = os.waitpid(pid, 0)
            code = os.waitstatus_to_exitcode(st)
        except (OSError, ChildProcessError):
            pass
        with self.lock:
            self.pid, self.fd = None, None
            if self.status == "idle":
                return
            if code == 0:
                s = _state(home)
                s.setdefault(self.name, {}).update(ok=True, on=True)
                _save_state(home, s)
                self.status = "done"
            else:
                tail = re.sub(r"\s+", " ", self.out)[-200:]
                self.status, self.error = "error", "ما كمل الربط. جرّب مرة ثانية" + (f" ({tail})" if tail.strip() else "")

    def submit(self, code: str) -> dict:
        code = re.sub(r"\s+", "", code or "")
        if not code:
            raise ValueError("الصق الرمز أول")
        with self.lock:
            if self.fd is None:
                raise RuntimeError("ابدأ الربط من جديد")
            os.write(self.fd, code.encode() + b"\r")
            self.status = "checking"
        return self.state()

    def cancel(self) -> None:
        with self.lock:
            if self.pid:
                try:
                    os.kill(self.pid, 15)
                except OSError:
                    pass
            self.status = "idle"


LINKS = {k: Link(k) for k in BRAINS}
