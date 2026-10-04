"""The compact text Claude reads to write the edit plan (the only token cost)."""
import json
from pathlib import Path

from .clean import split_phrases
from .paths import Episode
from .transcribe import load_words

RULES = """القواعد:
- الوقت بالثواني على الفيديو المنظف. teaser = 3–4 لقطات (1.5–2.5 ث) من أقوى اللحظات، تنعرض أول شي.
- beats تغطي (teaser + الفيديو المنظف) كامل، بلا فراغ ولا تداخل.
- أول 30 ثانية zone=hook، كل beat بين 1.5 و 3 ث. بعدها zone=body، كل beat بين 4 و 6 ث.
- ما يتكرر نفس kind مرتين ورا بعض. الوجه (face*) بين 40% و 65% من وقت الجسم.
- الأنواع: face, face_zoom_in, face_zoom_out, face_framed, face_punch (تقريب ثابت للتأكيد), face_fx,
  image (query بالإنگليزي لويكيميديا + caption عربي ينكتب إذا ما انلگت صورة), graphic,
  ai_image / ai_video (prompt إنگليزي يوصف المشهد + caption عربي بديل؛ الصور رخيصة والفيديو للحظات الكبيرة بس، وai_budget بالرصيد),
  entity (entity = id من entities.json: صورة حقيقية للشخص أو شعار الشركة، أول مرة ينذكر الاسم).
- face_fx: fx = subscribe (لحظة "اشتركوا") أو tv (بعد الهوك والسلام) أو none؛ و stickers اختيارية: قائمة، كل ملصق بيه type (stamp|arrow|burst|tape|circle) و text و at (ثانية من بداية المشهد).
- transition اختياري على أي beat: zoom, flash, whip, glitch (بحدود، عند تغيير فكرة أو صدمة). sfx اختياري: whoosh, pop, click, ding, hit, riser, paper, glitch.
- graphic.type: number, headline, quote, map, timeline, chart, text."""

MOMENTS = {
    "subscribe": ("اشترك", "اشتركو", "الاشتراك", "لايك", "الجرس", "فعلو", "تفعيل"),
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


def find_moments(phrases) -> list[str]:
    """Where he asks to subscribe or greets the viewers: hints for face_fx subscribe / tv beats."""
    from .clean import normalize_ar
    out = []
    keys = {fx: [normalize_ar(k) for k in ks] for fx, ks in MOMENTS.items()}
    for p in phrases:
        text = " ".join(normalize_ar(w.text) for w in p)
        for fx, ks in keys.items():
            if any(k in text for k in ks):
                out.append(f"[{_ts(p[0].start)}] face_fx {fx}: " + " ".join(w.text for w in p))
                break
    return out


def write_brief(ep: Episode, styles_summary: str) -> Path:
    cuts = json.loads(ep.cuts.read_text(encoding="utf-8"))
    duration = round(sum(e - s for s, e in cuts), 2)
    lines = [f"مدة الفيديو المنظف: {duration} ثانية", RULES, "", "الستايلات:", styles_summary]
    from .entities import load_entities
    ents = load_entities(ep)
    if ents:
        lines += ["", "الأسماء (entities.json):"] + [f"{k}: {e['name']} ({e.get('role', e.get('kind', ''))})"
                                                     for k, e in ents.items()]
    chunks = list(_chunks(split_phrases(load_words(ep.clean_words))))
    moments = find_moments(chunks)
    if moments:
        lines += ["", "لحظات مقترحة:"] + moments
    lines += ["", "الكلام:"]
    for p in chunks:
        lines.append(f"[{_ts(p[0].start)}–{_ts(p[-1].end)}] " + " ".join(w.text for w in p))
    ep.plan_input.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ep.plan_input
