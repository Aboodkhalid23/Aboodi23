"""Fast one-shot questions to Claude for the core steps (owner, 2026-10-26: a 2-minute video took over half an hour
on the sentences; "فيديو الساعة… ما يصير ياخذ أيام").

The old way ran a full agent for every review: it started up, read a file with a tool, thought, wrote a file with a
tool. Here the data goes inside the question, no tools are loaded, the answer comes back as JSON on stdout, and a long
video is split into pieces that are asked at the same time. A 1-hour video is ~10 pieces, all at once: about as fast as
a 5-minute one.
"""
import json
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

SYSTEM = ("You are a precise assistant inside a video-editing app. The user's material is Iraqi Arabic. "
          "Answer with one JSON object only: no prose, no code fences.")
WORKERS = 6
TIMEOUT = 300


def parse_json(text: str) -> dict:
    """The first JSON object in an answer (models sometimes wrap it in a fence or a sentence)."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except ValueError:
        pass
    start = text.find("{")
    while start >= 0:
        depth, in_str, esc = 0, False, False
        for k in range(start, len(text)):
            c = text[k]
            if in_str:
                esc = (c == "\\" and not esc)
                if c == '"' and not esc:
                    in_str = False
                continue
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:k + 1])
                    except ValueError:
                        break
        start = text.find("{", start + 1)
    raise ValueError("ما رجع جواب مفهوم")


def ask(exe: str, prompt: str, model: str | None = None, timeout: int = TIMEOUT, env: dict | None = None,
        cwd: str | None = None, runner=subprocess.run) -> dict:
    """One question, one JSON answer. No tools: it can't read or change anything, it only answers."""
    # outside the project folder and with only his own settings: no project start-up hooks, no skills to load
    cmd = [exe, "-p", "--output-format", "text", "--tools", "", "--strict-mcp-config", "--setting-sources", "user",
           "--system-prompt", SYSTEM, *(["--model", model] if model else [])]
    last = None
    for _ in range(2):          # one retry: a dropped connection or an answer that isn't JSON
        r = runner(cmd, input=prompt, capture_output=True, text=True, timeout=timeout, env=env,
                   cwd=cwd or tempfile.gettempdir())
        if r.returncode == 0:
            try:
                return parse_json(r.stdout)
            except ValueError as exc:
                last = exc
        else:
            last = RuntimeError((r.stderr or r.stdout or "").strip()[-300:] or "كلود ما جاوب")
    raise last


def chunks(items: list, size: int, overlap: int = 0) -> list[list]:
    """Pieces of `size`, each starting `overlap` items before the last one ended (a retake can sit on the edge)."""
    if len(items) <= size:
        return [items] if items else []
    out, i = [], 0
    while i < len(items):
        out.append(items[max(0, i - overlap):i + size])
        i += size
    return out


def run_parallel(fn, pieces: list, workers: int = WORKERS) -> list:
    """fn(piece) for every piece at the same time; a failed piece gives its exception in its place."""
    def safe(p):
        try:
            return fn(p)
        except Exception as exc:   # noqa: BLE001 — one bad piece must not lose the others
            return exc
    if len(pieces) <= 1:
        return [safe(p) for p in pieces]
    with ThreadPoolExecutor(max_workers=min(workers, len(pieces))) as pool:
        return list(pool.map(safe, pieces))


def find_run(tokens: list[str], phrase: str, norm) -> tuple[int, int] | None:
    """Where the words of `phrase` sit inside `tokens` (both normalised): (first, last+1), or None."""
    want = [norm(t) for t in phrase.split() if norm(t)]
    have = [norm(t) for t in tokens]
    if not want:
        return None
    for i in range(len(have) - len(want) + 1):
        if have[i:i + len(want)] == want:
            return i, i + len(want)
    return None
