"""The compact text Claude reads to write the edit plan (the only token cost)."""
import json
from pathlib import Path

from .clean import split_phrases
from .paths import Episode
from .transcribe import load_words

RULES = """القواعد:
- الوقت بالثواني على الفيديو المنظف. teaser = 3–4 لقطات (1.5–2.5 ث) من أقوى اللحظات، تنعرض أول شي.
- beats تغطي (teaser + الفيديو المنظف) كامل، بلا فراغ ولا تداخل.
- أول 30 ثانية zone=hook، كل beat بين 1.5 و 2.5 ث. بعدها zone=body، كل beat بين 4 و 6 ث.
- ما يتكرر نفس kind مرتين ورا بعض. الوجه (face*) بين 35% و 55% من وقت الجسم.
- الأنواع: face, face_zoom_in, face_zoom_out, face_framed, image (query بالإنگليزي لويكيميديا), graphic.
- graphic.type: number, headline, quote, map, timeline, chart, text."""


def _ts(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:04.1f}"


def write_brief(ep: Episode, styles_summary: str) -> Path:
    cuts = json.loads(ep.cuts.read_text(encoding="utf-8"))
    duration = round(sum(e - s for s, e in cuts), 2)
    lines = [f"مدة الفيديو المنظف: {duration} ثانية", RULES, "", "الستايلات:", styles_summary, "", "الكلام:"]
    for p in split_phrases(load_words(ep.clean_words)):
        lines.append(f"[{_ts(p[0].start)}–{_ts(p[-1].end)}] " + " ".join(w.text for w in p))
    ep.plan_input.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ep.plan_input
