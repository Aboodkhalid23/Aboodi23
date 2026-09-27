"""Correct the Iraqi-dialect transcription against the episode script (the owner reads the script)."""
import difflib
import re
from pathlib import Path

from .clean import normalize_ar
from .paths import Episode
from .transcribe import Word, load_words, save_words

_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_NOTE = re.compile(r"\[[^\]]*\]|\([^)]*\)")
_SYMBOL = re.compile(r"[^\w\s]|_")


def script_words(text: str) -> list[str]:
    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    text = _NOTE.sub(" ", _LINK.sub(r"\1", "\n".join(lines)))
    return _SYMBOL.sub(" ", text).split()


def find_script(ep: Episode) -> Path | None:
    finals = sorted(ep.root.glob("*final*.md"), key=lambda p: p.stat().st_mtime)
    if finals:
        return finals[-1]
    draft = ep.root / "02-draft.md"
    return draft if draft.exists() else None


def _spread(heard: list[Word], texts: list[str]) -> list[Word]:
    """Give `texts` the time span of `heard`, split by character length."""
    start, end = heard[0].start, heard[-1].end
    total = sum(len(t) for t in texts) or 1
    out, t = [], start
    for i, txt in enumerate(texts):
        nxt = end if i == len(texts) - 1 else t + (end - start) * len(txt) / total
        out.append(Word(txt, round(t, 3), round(nxt, 3)))
        t = nxt
    return out


def _similar(heard: list[str], script: list[str], threshold: float = 0.5) -> bool:
    return difflib.SequenceMatcher(None, "".join(heard), "".join(script), autojunk=False).ratio() >= threshold


def align_words(words: list[Word], script: list[str]) -> tuple[list[Word], float]:
    a = [normalize_ar(w.text) for w in words]
    b = [normalize_ar(s) for s in script]
    out, matched = [], 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            out += [Word(script[j1 + k], w.start, w.end) for k, w in enumerate(words[i1:i2])]
            matched += i2 - i1
        elif op == "replace" and _similar(a[i1:i2], b[j1:j2]):  # misheard script words
            out += _spread(words[i1:i2], script[j1:j2])
            matched += i2 - i1
        elif op in ("replace", "delete"):  # said, but not in the script (ad-lib): keep what was heard
            out += words[i1:i2]
    return out, (matched / len(words) if words else 0.0)


def align(ep: Episode, script_path: Path) -> float:
    raw = ep.work / "transcript_raw.json"
    if not raw.exists():
        raw.write_bytes(ep.transcript.read_bytes())
    words, ratio = align_words(load_words(raw), script_words(Path(script_path).read_text(encoding="utf-8")))
    save_words(words, ep.transcript)
    print(f"   التطابق ويه السكربت: {ratio:.0%}")
    if ratio < 0.5:
        print("⚠️  الكلام يختلف هواية عن السكربت — تأكد إنه نفس سكربت الحلقة")
    return ratio
