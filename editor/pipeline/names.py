"""`names`: the right name for every person and company, even when the owner says it wrong (round 9).

He finds foreign names hard to say, so Whisper writes what it heard ("ايدن استي" for Idan Segev). This stage:
  1. finds the name-like spans in the cleaned words: after a title (البروفيسور، الرئيس، شركة، مؤسس…), and words
     Whisper itself was unsure of (low confidence);
  2. matches them by SOUND (Arabic letters that sound alike collapse to one key: ث/س/ص, ذ/ز/ظ/ض, ق/گ/ك, ت/ط,
     ح/ه, vowels and hamza dropped) against the names the episode already knows: entities.json (name, en, heard),
     edit/names.json (Claude's answers), and the names in the studio's research and script;
  3. writes the right name into the words (subtitles, kinetic text and the plan all read them) and adds the
     person/company to entities.json, so `entities` fetches a real photo of them;
  4. lists what it could not resolve in work/names_check.txt, with the sentence around it, for Claude to identify
     from the story (web search) and answer in edit/names.json:
       {"ايدن استي": {"name": "إيدان سيغيف", "en": "Idan Segev", "kind": "person", "role": "عالم أعصاب"}}
"""
import difflib
import json
import re
from pathlib import Path

from .clean import normalize_ar
from .paths import Episode
from .transcribe import Word, load_words, save_words

TITLES = {"البروفيسور", "بروفيسور", "الدكتور", "دكتور", "الرئيس", "رئيس", "السيد", "المهندس", "الملياردير", "مؤسس",
          "المؤسس", "مدير", "المدير", "الباحث", "الكاتب", "الصحفي", "المخترع", "اسمه", "اسمها", "يسمونه",
          "شركة", "شركه", "الشركة", "الشركه", "جامعة", "جامعه", "مستر", "الأمير", "الامير", "الملك", "الوزير",
          "المستثمر", "رجل", "سيدة", "الممثل", "اللاعب", "الفنان", "المغني", "صاحب"}
STOP = {"و", "بس", "هو", "هي", "الي", "اللي", "هذا", "هاي", "من", "على", "ب", "في", "عن", "كان", "جان", "صار",
        "گال", "قال", "يعني", "سوا", "سووا", "وفريقه", "وفريقها", "ويه", "مال", "اكو", "شي", "لان", "حتى", "قبل", "بعد",
        "سنة", "سنه", "يوم", "هسة", "هسه", "هواية", "كلش", "جدا", "مرة", "مره", "كلهم", "الي", "اللي", "ما", "لا"}
LOW = 0.55        # Whisper confidence under this: the word may be a name he said unclearly
MATCH = 0.62      # sound-alike score to accept a known name without asking

_SOUND = str.maketrans({"ث": "س", "ص": "س", "ش": "س", "ذ": "ز", "ظ": "ز", "ض": "ز", "ق": "ك", "گ": "ك", "ج": "ك",
                        "چ": "ك", "غ": "ك", "ط": "ت", "ح": "ه", "خ": "ه", "ة": "ه", "پ": "ب", "ف": "ب", "ڤ": "ب",
                        "ى": "ي"})


def sound(text: str, joined: bool = True) -> str:
    """A key for how a name sounds: letters that Iraqi speech (and Whisper) mix up become one, vowels go.
    `joined`: also drop a و/ب/ل stuck to the front ("وفورد") — off for names that really start with them."""
    out = []
    for word in normalize_ar(text).split():
        word = re.sub(r"^ال(?=..)", "", word)               # the article is not the name
        if joined:
            word = re.sub(r"^(و|ب|ل)(?=...)", "", word)
        key = word.translate(_SOUND)
        key = key[0] + re.sub(r"[اويءأإآئؤع]", "", key[1:]) if key else key
        out.append(re.sub(r"(.)\1+", r"\1", key))
    return " ".join(k for k in out if k)


def similarity(a: str, b: str) -> float:
    best = 0.0
    for ja in (True, False):
        for jb in (True, False):
            ka, kb = sound(a, ja).replace(" ", ""), sound(b, jb).replace(" ", "")
            if ka and kb:
                best = max(best, difflib.SequenceMatcher(None, ka, kb, autojunk=False).ratio())
    return best


def candidates(words: list[Word]) -> list[tuple[int, int]]:
    """(first, last+1) word index of every name-like span: 1–3 words after a title, or unsure words in a row."""
    spans, i, n = [], 0, len(words)
    norm = [normalize_ar(w.text) for w in words]
    titles = {normalize_ar(t) for t in TITLES}
    while i < n:
        if (norm[i] in titles or re.sub(r"^(و|ب|ل)", "", norm[i]) in titles) and i + 1 < n:
            j = i + 1
            while j < n and j - i <= 3 and norm[j] not in STOP and not norm[j].isdigit():
                j += 1
                if re.search(r"[،,.؟?!:]$", words[j - 1].text):   # the name ends at a comma or full stop
                    break
            if j > i + 1:
                spans.append((i + 1, j))
                i = j
                continue
        if words[i].p < LOW and norm[i] not in STOP and len(norm[i]) >= 3:
            j = i + 1
            while j < n and j - i < 3 and words[j].p < LOW and norm[j] not in STOP:
                j += 1
            spans.append((i, j))
            i = j
            continue
        i += 1
    return spans


def known_names(ep: Episode) -> list[dict]:
    """Every name the episode knows, with the ways it may be heard."""
    from .entities import load_entities
    out = []
    for eid, e in load_entities(ep).items():
        out.append({"name": e.get("name", ""), "en": e.get("en", ""), "kind": e.get("kind", "person"), "id": eid,
                    "heard": list(e.get("heard") or [])})
    answers = ep.edit / "names.json"
    if answers.exists():
        for heard, a in json.loads(answers.read_text(encoding="utf-8")).items():
            out.append({**a, "heard": [heard] + list(a.get("heard") or [])})
    return [k for k in out if k.get("name")]


def _best(text: str, known: list[dict]) -> tuple[float, dict | None]:
    best, hit = 0.0, None
    for k in known:
        for form in [k["name"], *k.get("heard", [])]:
            s = 1.0 if normalize_ar(form) == normalize_ar(text) else similarity(text, form)
            if s > best:
                best, hit = s, k
    return best, hit


def _slug(en: str, name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (en or "").lower()).strip("_")
    return s or "n" + str(abs(hash(name)) % 10 ** 6)


def resolve(ep: Episode) -> dict:
    """Correct the names in the cleaned words; returns {"fixed": [...], "unsure": [...]}"""
    from .entities import entities_file, load_entities
    if not ep.clean_words.exists():
        return {"fixed": [], "unsure": []}
    words = load_words(ep.clean_words)
    known = known_names(ep)
    fixed, unsure, out, last = [], [], [], 0
    for a, z in candidates(words):
        heard = " ".join(w.text for w in words[a:z])
        # try the whole span, then shorter heads of it (a title is often followed by a verb)
        best, hit, cut = 0.0, None, z
        for end in range(z, a, -1):
            s, k = _best(" ".join(w.text for w in words[a:end]), known)
            if s > best:
                best, hit, cut = s, k, end
        if hit and best >= MATCH:
            name = hit["name"].split()
            span = words[a:cut]
            t0, t1 = span[0].start, span[-1].end
            step = (t1 - t0) / len(name)
            out += words[last:a] + [Word(nm, round(t0 + i * step, 3), round(t0 + (i + 1) * step, 3)) for i, nm in enumerate(name)]
            last = cut
            if normalize_ar(" ".join(w.text for w in span)) != normalize_ar(hit["name"]):
                fixed.append({"at": round(t0, 2), "heard": " ".join(w.text for w in span), "name": hit["name"],
                              "score": round(best, 2)})
            if hit.get("en") and hit.get("kind") in ("person", "company"):
                _add_entity(ep, hit)
        else:
            ctx = " ".join(w.text for w in words[max(0, a - 8):min(len(words), z + 8)])
            unsure.append({"at": round(words[a].start, 2), "heard": heard, "context": ctx,
                           "guess": hit["name"] if hit and best >= 0.45 else None})
    out += words[last:]
    if fixed:
        raw = ep.edit / "clean_words.raw.json"
        if not raw.exists():
            raw.write_text(ep.clean_words.read_text(encoding="utf-8"), encoding="utf-8")
        save_words(out, ep.clean_words)
    lines = []
    for u in unsure:
        m, s = divmod(u["at"], 60)
        lines.append(f"[{int(m):02d}:{s:04.1f}] سمعت «{u['heard']}»" + (f" (يمكن: {u['guess']})" if u["guess"] else "")
                     + f" — {u['context']}")
    (ep.work / "names_check.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    (ep.work / "names_fixed.json").write_text(json.dumps(fixed, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"fixed": fixed, "unsure": unsure}


def _add_entity(ep: Episode, k: dict) -> None:
    """Every person or company named becomes an entity, so its real photo is fetched."""
    from .entities import entities_file, load_entities
    ents = load_entities(ep)
    if any(e.get("en", "").lower() == k["en"].lower() for e in ents.values()):
        return
    f = entities_file(ep)
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    rows = data if isinstance(data, list) else [{"id": i, **e} for i, e in data.items()]
    rows.append({"id": k.get("id") or _slug(k["en"], k["name"]), "name": k["name"], "en": k["en"], "kind": k["kind"],
                 **({"role": k["role"]} if k.get("role") else {}), **({"qid": k["qid"]} if k.get("qid") else {})})
    f.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
