"""Correct the Iraqi-dialect transcription against the episode script (the owner reads the script)."""
import difflib
import json
import re
from pathlib import Path

from .clean import normalize_ar
from .paths import Episode
from .transcribe import Word

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
    for name in ("04-script.md", "02-draft.md"):  # studio: 04 = fact-checked final, 02 = first draft
        if (ep.root / name).exists():
            return ep.root / name
    return None


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


def _no_pause(words: list[Word], gap: float = 0.5) -> bool:
    return all(b.start - a.end < gap for a, b in zip(words, words[1:]))


NAME_THRESHOLD = 0.3   # a name in the script wins even when he says it quite differently


def align_words(words: list[Word], script: list[str], names: set[str] = frozenset(),
                report: list[str] | None = None) -> tuple[list[Word], float]:
    """`names`: normalised words of people/companies (entities.json). `report` collects the spans
    that still differ from the script, for Claude to review."""
    a = [normalize_ar(w.text) for w in words]
    b = [normalize_ar(s) for s in script]
    out, matched = [], 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        threshold = NAME_THRESHOLD if names.intersection(b[j1:j2]) else 0.5
        if op == "equal":
            out += [Word(script[j1 + k], w.start, w.end) for k, w in enumerate(words[i1:i2])]
            matched += i2 - i1
        elif (op == "replace" and _similar(a[i1:i2], b[j1:j2], threshold)
              and _no_pause(words[i1:i2])):  # misheard words / mispronounced name
            out += _spread(words[i1:i2], script[j1:j2])
            matched += i2 - i1
        elif op in ("replace", "delete"):  # said, but not in the script (ad-lib): keep what was heard
            out += words[i1:i2]
            if report is not None:
                heard = " ".join(w.text for w in words[i1:i2])
                wanted = " ".join(script[j1:j2]) or "—"
                report.append(f"[{words[i1].start:.1f}] سمعت: {heard} | السكربت: {wanted}")
    return out, (matched / len(words) if words else 0.0)


def align_to_script(ep: Episode, words: list[Word], script_path: Path) -> list[Word]:
    """Fix the text of the KEPT words (after retakes are dropped); timings and cuts never change."""
    from .entities import entity_tokens
    report: list[str] = []
    fixed, ratio = align_words(words, script_words(Path(script_path).read_text(encoding="utf-8")),
                               entity_tokens(ep), report)
    (ep.work / "align_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (ep.work / "align.json").write_text(json.dumps({"ratio": round(ratio, 3), "script": str(script_path)},
                                                   ensure_ascii=False), encoding="utf-8")
    print(f"   التطابق ويه السكربت: {ratio:.0%}")
    if ratio < 0.5:
        print("⚠️  الكلام يختلف هواية عن السكربت — تأكد إنه نفس سكربت الحلقة")
    return fixed
