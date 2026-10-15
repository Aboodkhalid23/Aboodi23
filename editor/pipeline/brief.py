"""The compact text Claude reads to write the edit plan (the only token cost)."""
import json
from pathlib import Path

from .clean import split_phrases
from .paths import Episode
from .transcribe import load_words

def rules() -> str:
    """The plan rules, built from plan.py so the brief never falls behind the code."""
    from .plan import GRAPHIC_TYPES, KINDS, PAPER_TYPES, STICKERS, TRANSITIONS
    return f"""القواعد:
- الوقت بالثواني على الفيديو المنظف. teaser = 3–4 لقطات (1.5–2.5 ث) من أقوى اللحظات، تنعرض أول شي.
- beats تغطي (teaser + الفيديو المنظف) كامل، بلا فراغ ولا تداخل.
- أول 30 ثانية zone=hook، كل beat بين 1.5 و 3 ث (face_paper 2–6). بعدها zone=body، كل beat بين 4 و 6 ث (face_paper 4–10).
- ما يتكرر نفس kind مرتين ورا بعض. الوجه (face*) بين 40% و 65% من وقت الجسم (face_paper ينحسب نصه وجه).
- الأنواع: {', '.join(KINDS)}.
- face_paper (الأساس لما يذكر خبر أو وثيقة أو رقم أو تصريح): هو يبقى بالكادر والأوراق تطلع يمّه. papers 1–4، type من {', '.join(PAPER_TYPES)}،
  و at (ثانية من بداية المشهد، ورقة كل 2–3 ث). newspaper (title, highlight, query?)، document (title, lines, highlight?, stamp?)، photo (query)، quote (text, who)، number (value, label)، page (query). enter = fly|turn|drop، و link: true بكل ورقة = لوحة تحقيق بخيط أحمر.
- image / footage: query إنگليزي قصير + caption عربي (+ prompt إنگليزي إذا ممكن ما تنلگى صورة حقيقية: يتحول ai_image لحاله).
- ai_image / ai_video / avatar: prompt إنگليزي + caption عربي؛ الحقيقي أول، وai_budget بالرصيد.
- entity: id من entities.json، أول مرة ينذكر الاسم.
- face_fx: fx = subscribe | tv | none؛ stickers من {', '.join(STICKERS)} (كل واحد type و text و at).
- transition (بحدود، عند تغيير فكرة أو صدمة): {', '.join(TRANSITIONS)}. sfx اختياري: whoosh, pop, click, ding, hit, riser, paper, glitch.
- graphic.type: {', '.join(GRAPHIC_TYPES)}."""


MOMENTS = {
    "subscribe": ("شترك", "شتراك", "سبسكرايب", "لايك", "الجرس", "فعلو", "تفعيل"),   # اشترك، تشتركون، الاشتراك، مشترك
    "tv": ("السلام عليكم", "هلا بيكم", "هلا والله", "مرحبا", "اهلا وسهلا", "هلو"),
}


def _ts(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:04.1f}"


def _chunks(phrases, max_seconds: float = 5.0):
    """Split long breathless phrases into lines of at most ~max_seconds."""
    for p in phrases:
        line = []
        for w in p:
            if line and w.end - line[0].start > max_seconds:
                yield line
                line = []
            line.append(w)
        if line:
            yield line


# He steps out of the episode for a moment: a joke, a side fact, a word to the viewers. These are KEPT (owner:
# "مو لازم تنكص") and get their own look (face_fx none + a "على الهامش" tape), so the viewer feels the aside.
ASIDES = ("مزحه", "امزح", "دا امزح", "اضحك", "ههه", "بالمناسبه", "على الطاري", "عالطاري", "خارج الموضوع",
          "مو موضوعنا", "خلي اگولكم شغله", "خلي اكولكم شغله", "سالفه صغيره", "المهم نرجع", "نرجع لموضوعنا",
          "بيني وبينك", "بيني وبينكم", "شغله جانبيه", "معلومه جانبيه", "على الهامش")


def find_asides(phrases) -> list[tuple[float, float, str]]:
    """(start, end, words) of every aside: a phrase with an aside marker, up to the next pause."""
    from .clean import normalize_ar
    marks = [normalize_ar(m) for m in ASIDES]
    out = []
    for p in phrases:
        text = " ".join(normalize_ar(w.text) for w in p)
        if any(m in text for m in marks):
            out.append((p[0].start, p[-1].end, " ".join(w.text for w in p)))
    return out


# Where a paper beside him fits (face_paper): news, documents, what someone said, numbers and years.
PAPER_HINTS = {
    "newspaper": ("جريدة", "جرايد", "صحيفة", "خبر", "اخبار", "عنوان", "نشرت", "نشروا", "مجلة"),
    "document": ("تقرير", "وثيقة", "وثايق", "دراسة", "بحث", "رسالة", "عقد", "قانون", "ورقة", "سجل", "براءة"),
    "quote": ("گال", "قال", "صرح", "تصريح", "كتب", "يگول", "يقول"),
}


def find_moments(phrases) -> list[str]:
    """Hints for Claude: subscribe / greeting moments (face_fx) and moments for a paper beside him (face_paper)."""
    import re
    from .clean import normalize_ar
    out = []
    keys = {fx: [normalize_ar(k) for k in ks] for fx, ks in MOMENTS.items()}
    papers = {t: [normalize_ar(k) for k in ks] for t, ks in PAPER_HINTS.items()}
    for p in phrases:
        words = [normalize_ar(w.text) for w in p]
        text = " ".join(words)
        said = " ".join(w.text for w in p)
        hit = next((fx for fx, ks in keys.items() if any(k in text for k in ks)), None)
        if hit:
            out.append(f"[{_ts(p[0].start)}] face_fx {hit}: " + said)
            continue
        kind = next((t for t, ks in papers.items() if any(w.startswith(k) or w.startswith("ال" + k) or
                                                           w.startswith("و" + k) for w in words for k in ks)), None)
        if kind is None and any(re.fullmatch(r"[0-9٠-٩][0-9٠-٩,.٫]+%?", w.text.strip("،,.؟!")) for w in p):
            kind = "number"
        if kind:
            out.append(f"[{_ts(p[0].start)}] face_paper {kind}: " + said)
    return out


def visual_cues(ep: Episode, words) -> list[str]:
    """The studio's visual director planned the episode before filming (episodes/<ep>/07-visuals.md, lines like
    `- «first words of a sentence» → face_paper newspaper: …`). Each cue is placed at the moment he actually said
    that sentence (fuzzy match on the transcript), so the plan starts from the director's ideas with real times."""
    import re
    from .clean import normalize_ar
    f = ep.root / "07-visuals.md"
    if not f.exists() or not words:
        return []
    said = [normalize_ar(w.text) for w in words]
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*-\s*«([^»]+)»\s*(?:→|->)\s*(.+)", line)
        if not m:
            continue
        anchor = [normalize_ar(w) for w in m[1].split() if w.strip()]
        if not anchor:
            continue
        best, at = 0.0, None
        n = len(anchor)
        for i in range(0, max(1, len(said) - n + 1)):
            window = set(said[i:i + n + 2])   # a little slack: he may add or drop a word
            score = sum(a in window for a in anchor) / n + (0.01 if said[i] == anchor[0] else 0)
            if score > best:
                best, at = score, i
        if at is not None and best >= 0.6:
            out.append(f"[{_ts(words[at].start)}] {m[2].strip()}  ← «{m[1].strip()}»")
    return out


def write_brief(ep: Episode, styles_summary: str) -> Path:
    cuts = json.loads(ep.cuts.read_text(encoding="utf-8"))
    duration = round(sum(e - s for s, e in cuts), 2)
    lines = [f"مدة الفيديو المنظف: {duration} ثانية", rules(), "", "الستايلات:", styles_summary]
    from .entities import load_entities
    ents = load_entities(ep)
    if ents:
        lines += ["", "الأسماء (entities.json):"] + [f"{k}: {e['name']} ({e.get('role', e.get('kind', ''))})"
                                                     for k, e in ents.items()]
    all_words = load_words(ep.clean_words)
    chunks = list(_chunks(split_phrases(all_words)))
    director = visual_cues(ep, all_words)
    if director:
        lines += ["", "خطة المخرج البصري (من الاستوديو، بوقتها الحقيقي — ابدي منها):"] + director
    moments = find_moments(chunks)
    if moments:
        lines += ["", "لحظات مقترحة:"] + moments
    asides = find_asides(split_phrases(all_words))
    if asides:
        lines += ["", "سوالف جانبية (تبقى، و autofix يحطلها شكل «على الهامش»):"] + [f"[{_ts(a)}–{_ts(z)}] {t}" for a, z, t in asides]
    names_check = ep.work / "names_check.txt"
    if names_check.exists() and names_check.read_text(encoding="utf-8").strip():
        lines += ["", "أسماء مو متأكد منها (اعرفها من القصة، اكتبها بـ edit/names.json، وعيد names):",
                  names_check.read_text(encoding="utf-8").rstrip()]
    lines += ["", "الكلام:"]
    for p in chunks:
        lines.append(f"[{_ts(p[0].start)}–{_ts(p[-1].end)}] " + " ".join(w.text for w in p))
    ep.plan_input.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ep.plan_input
