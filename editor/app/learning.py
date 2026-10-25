"""The assistant learns his taste by itself (owner, 2026-10-25: "كل مونتاج يسويه يعلم نفسه بنفسه").

Every change he makes in the app is noted (events.jsonl). After each final build the assistant reads what he changed
and rewrites a short taste file (preferences.md), and every plan, chat and assist prompt starts from it.
All of it stays on his computer, under the app's home folder.
"""
import json
import time
from pathlib import Path

MAX_EVENTS = 4000          # the log is trimmed to this many lines
MAX_TASTE = 5000           # characters of the taste file fed into prompts
# what a change looks like in the log: only the parts that say something about taste
SKIP_KEYS = {"words", "lines", "data", "b64", "content"}


def _dir(home: Path) -> Path:
    d = Path(home) / "learning"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _short(v, n=300):
    if isinstance(v, dict):
        v = {k: x for k, x in v.items() if k not in SKIP_KEYS}
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


def note(home: Path, ep: str, kind: str, detail=None) -> None:
    """One thing he did: a scene edit, a style he picked, a look, a version he went back to, a chat request."""
    f = _dir(home) / "events.jsonl"
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": round(time.time(), 3), "ep": ep, "kind": kind, "detail": _short(detail)}, ensure_ascii=False) + "\n")
    if f.stat().st_size > MAX_EVENTS * 400:
        lines = f.read_text(encoding="utf-8").splitlines()[-MAX_EVENTS:]
        f.write_text("\n".join(lines) + "\n", encoding="utf-8")


def events(home: Path, since: float = 0) -> list[dict]:
    f = _dir(home) / "events.jsonl"
    out = []
    for line in f.read_text(encoding="utf-8").splitlines() if f.exists() else []:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("at", 0) > since:
            out.append(e)
    return out


def _state(home: Path) -> dict:
    try:
        return json.loads((_dir(home) / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def pending(home: Path) -> list[dict]:
    """What he did since the assistant last learned."""
    return events(home, _state(home).get("learned_at", 0))


def mark_learned(home: Path) -> None:
    st = _state(home)
    st["learned_at"], st["lessons"] = time.time(), st.get("lessons", 0) + 1
    (_dir(home) / "state.json").write_text(json.dumps(st), encoding="utf-8")


def taste_file(home: Path) -> Path:
    return _dir(home) / "preferences.md"


def taste(home: Path) -> str:
    f = taste_file(home)
    return f.read_text(encoding="utf-8").strip()[:MAX_TASTE] if f.exists() else ""


def set_taste(home: Path, text: str) -> None:
    """He can read and correct what was learned, or clear it."""
    f = taste_file(home)
    if str(text).strip():
        f.write_text(str(text).strip()[:MAX_TASTE * 2] + "\n", encoding="utf-8")
    else:
        f.unlink(missing_ok=True)


def prompt_block(home: Path) -> str:
    t = taste(home)
    if not t:
        return ""
    return ("\n- ذوق صاحب القناة الي تعلمته من حلقاته وتعديلاته القديمة (امشِ عليه من البداية حتى ما يحتاج يعدّل نفس الشي مرة ثانية،"
            " إلا إذا طلب هسة شي غيره، طلبه هسة يغلب):\n" + t + "\n")


def status(home: Path) -> dict:
    st = _state(home)
    return {"taste": taste(home), "pending": len(pending(home)), "lessons": st.get("lessons", 0),
            "learned_at": st.get("learned_at")}


def digest(home: Path, limit: int = 250) -> str:
    """The pending changes as short lines for the learning prompt, newest last."""
    ev = pending(home)[-limit:]
    return "\n".join(f"- [{e.get('ep', '')}] {e.get('kind')}: {e.get('detail', '')}" for e in ev) or "(ماكو تعديلات جديدة)"
