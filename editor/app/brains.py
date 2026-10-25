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
