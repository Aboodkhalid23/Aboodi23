"""محرك الأفكار: من بطاقات الأفكار (فكرة من كل زاوية) يختار 3 أغلفة ويرسم مخطط لكل وحدة.

    python3 designer/concepts.py <المجلد>/concepts.json -o <المجلد>

الاختيار: 2 بدون كتابة + 1 بكتابة، بزوايا وتعابير وألوان مختلفة.
صيغة البطاقة والزوايا الـ 12 بـ studio/thumbnail-angles.md.
"""
import colorsys
import itertools
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render import FONTS  # noqa: E402

ANGLES = {
    "metaphor": "التشبيه البصري",
    "before_disaster": "اللحظة قبل الكارثة",
    "before_after": "قبل وبعد",
    "scale": "الرقم الخيالي",
    "mystery": "الشي الغامض",
    "villain": "الشرير أو المتهم",
    "pov": "انت مكانه",
    "two_objects": "المقارنة بشيئين",
    "wrong_detail": "الشي الغلط",
    "offscreen": "يباوع لشي ما نشوفه",
    "miniature": "العالم المصغّر",
    "icon_twist": "الرمز المكسور",
}
WEIGHTS = {"clarity": 2, "curiosity": 2, "honesty": 2, "emotion": 1.5, "novelty": 1.5, "producible": 1, "face": 1}
CAMERAS = ("wide_close", "standard", "top_down")
FACE_POS = ("right", "left", "center")
HERO_POS = ("left", "right", "center", "foreground")
TEXT_ZONES = (None, "top_left", "top_right", "bottom_left")
MAX_WORDS = 4
MIN_HUE_GAP = 30
GRAY_SATURATION = 0.15
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
REQUIRED_TEXT = ("idea", "hero", "setting", "why")
SUBJECT_FIELDS = ("outfit", "expression", "action")
LABELS = "ABC"

IDENTITY = (
    "Cinematic photorealistic YouTube thumbnail photo. Main subject: the man in the reference image.\n"
    "Preserve his exact facial identity: face shape, eyes, eyebrows, nose, thin black mustache, short trimmed beard, "
    "short dark hair with faded sides, skin tone. Change only his expression, clothes, pose and lighting."
)
NO_TEXT = "No text, no letters, no captions, no logos, no watermark."
FACE_LINES = {
    "right": "He is on the right third of the frame",
    "left": "He is on the left third of the frame",
    "center": "He is in the center of the frame",
}
HERO_LINES = {
    "left": "On the left side of the frame: {}.",
    "right": "On the right side of the frame: {}.",
    "center": "In the center of the frame: {}.",
    "foreground": "In the foreground, large and close to the camera: {}.",
}
CAMERA_LINES = {
    "wide_close": "Shot with a wide-angle lens very close to the subject, slight fisheye perspective, "
                  "the main object big in the foreground.",
    "standard": "",
    "top_down": "Top-down camera angle, looking down at him and the scene from above.",
}
ZONE_NAMES = {"top_left": "upper-left", "top_right": "upper-right", "bottom_left": "lower-left"}
COLORS = {
    "black": (12, 12, 14), "white": (245, 245, 245), "gray": (128, 128, 128),
    "red": (220, 30, 30), "orange": (255, 120, 0), "yellow": (255, 210, 0), "gold": (212, 175, 55),
    "green": (40, 170, 60), "toxic green": (130, 255, 40), "teal": (0, 128, 128), "cyan": (0, 200, 255),
    "blue": (30, 90, 220), "navy": (15, 30, 75), "purple": (120, 40, 170), "magenta": (230, 30, 170),
    "pink": (255, 130, 180), "brown": (110, 60, 25), "beige": (225, 205, 170),
    # الخلفيات الغامقة (أغلب الألوان المسيطرة)
    "dark navy": (11, 26, 45), "dark red": (90, 10, 12), "dark green": (10, 50, 25), "dark purple": (40, 12, 60),
}


class ConceptError(ValueError):
    """خطأ ببطاقات الأفكار، رسالته بالعربي."""


def _rgb(color: str) -> tuple[int, int, int]:
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _check_card(c, n: int) -> None:
    if not isinstance(c, dict):
        raise ConceptError(f"البطاقة رقم {n}: لازم تكون كائن {{}}")
    cid = c.get("id")
    if not isinstance(cid, str) or not cid.strip():
        raise ConceptError(f"البطاقة رقم {n}: ناقصها id (رقم مثل \"A1\")")
    where = f"البطاقة {cid}"

    def need(cond, field, msg):
        if not cond:
            raise ConceptError(f"{where}: {field} {msg}")

    need(c.get("angle") in ANGLES, "angle", f"مو معروفة. المسموح: {', '.join(ANGLES)}")
    for field in REQUIRED_TEXT:
        need(isinstance(c.get(field), str) and c[field].strip(), field, "ناقص أو فارغ")
    subject = c.get("subject")
    need(isinstance(subject, dict), "subject", "ناقص (لازم outfit وexpression وaction)")
    for field in SUBJECT_FIELDS:
        need(isinstance(subject.get(field), str) and subject[field].strip(), f"subject.{field}", "ناقص أو فارغ")
    need(c.get("camera") in CAMERAS, "camera", f"مو معروفة. المسموح: {', '.join(CAMERAS)}")
    layout = c.get("layout")
    need(isinstance(layout, dict), "layout", "ناقص (لازم face وhero وtext_zone)")
    need(layout.get("face") in FACE_POS, "layout.face", f"مو معروف. المسموح: {', '.join(FACE_POS)}")
    need(layout.get("hero") in HERO_POS, "layout.hero", f"مو معروف. المسموح: {', '.join(HERO_POS)}")
    need("text_zone" in layout and layout["text_zone"] in TEXT_ZONES, "layout.text_zone",
         "مو معروف. المسموح: null، top_left، top_right، bottom_left")
    palette = c.get("palette")
    need(isinstance(palette, list) and 2 <= len(palette) <= 4
         and all(isinstance(p, str) and HEX.match(p) for p in palette),
         "palette", "لازم 2-4 ألوان بصيغة #RRGGBB")
    scores = c.get("scores")
    need(isinstance(scores, dict), "scores", f"ناقص (لازم {', '.join(WEIGHTS)})")
    for key in WEIGHTS:
        need(_is_number(scores.get(key)) and 0 <= scores[key] <= 10, f"scores.{key}", "لازم رقم من 0 لـ 10")
    for key in scores:
        need(key in WEIGHTS, f"scores.{key}", f"مو معروف. المسموح: {', '.join(WEIGHTS)}")
    text = c.get("text")
    need(text is None or (isinstance(text, str) and text.strip()), "text", "لازم null أو كتابة")
    if text is not None:
        need(len(text.split("\n")) <= 2, "text", "سطرين بالأكثر (سطر ثالث مو مسموح)")
        need(len(text.split()) <= MAX_WORDS, "text", f"{len(text.split())} كلمات، والحد {MAX_WORDS}")
        need(layout["text_zone"] is not None, "layout.text_zone", "لازم مكان للكتابة (البطاقة بيها كتابة)")
    else:
        need(layout["text_zone"] is None, "layout.text_zone", "لازم null (البطاقة بدون كتابة)")
    for field in ("font", "font_latin"):
        if field in c:
            need(c[field] in FONTS, field, f"خط مو معروف: {c[field]}. المتوفر: {', '.join(FONTS)}")


def validate(cards) -> None:
    """يتأكد من البطاقات، وأي غلط يرفع ConceptError برسالة عربية."""
    if not isinstance(cards, list):
        raise ConceptError("ملف الأفكار لازم يكون قائمة بطاقات [ ... ]")
    if not cards:
        raise ConceptError("ملف الأفكار فارغ، ماكو ولا بطاقة")
    seen = set()
    for n, c in enumerate(cards, 1):
        _check_card(c, n)
        if c["id"] in seen:
            raise ConceptError(f"البطاقة {c['id']}: الرقم مكرر، كل بطاقة لازم رقمها غير")
        seen.add(c["id"])


def score(card: dict) -> float:
    """الدرجة من 100 حسب الأوزان."""
    total = sum(WEIGHTS[k] * card["scores"][k] for k in WEIGHTS)
    return round(total / (10 * sum(WEIGHTS.values())) * 100, 1)


def _hsv(color: str):
    return colorsys.rgb_to_hsv(*(v / 255 for v in _rgb(color)))


def _colors_differ(a: str, b: str) -> bool:
    (ha, sa, _), (hb, sb, _) = _hsv(a), _hsv(b)
    if sa < GRAY_SATURATION or sb < GRAY_SATURATION:
        return True
    gap = abs(ha - hb) * 360
    return min(gap, 360 - gap) >= MIN_HUE_GAP


def _ok(trio, rules) -> bool:
    for a, b in itertools.combinations(trio, 2):
        if "angle" in rules and a["angle"] == b["angle"]:
            return False
        if "expression" in rules and (a["subject"]["expression"].strip().lower()
                                      == b["subject"]["expression"].strip().lower()):
            return False
        if "color" in rules and not _colors_differ(a["palette"][0], b["palette"][0]):
            return False
    return True


RELAX = [
    ({"angle", "expression", "color"}, None),
    ({"angle", "expression"}, "• ما لگيت 3 أفكار يختلف بيها اللون المسيطر، فسمحت بلون متقارب."),
    ({"angle"}, "• ما لگيت 3 أفكار يختلف بيها اللون والتعبير، فسمحت بلون وتعبير متقاربين."),
    (set(), "• ما لگيت 3 أفكار تختلف بيها الزاوية، فسمحت بزاوية مكررة، ولون وتعبير متقاربين."),
]


def select(cards: list) -> tuple[list[dict], list[str]]:
    """يختار 2 بدون كتابة + 1 بكتابة، بأعلى مجموع درجات يطابق الشروط.

    إذا الشروط ما تنطبق، ينزل الأضعف أول (اللون، بعده التعبير، بعده الزاوية) ويكتب ملاحظة.
    يرجع (المختارة مرتبة بالدرجة ووياها label وscore، الملاحظات).
    """
    plain = [c for c in cards if c.get("text") is None]
    texted = [c for c in cards if c.get("text") is not None]
    if len(plain) < 2:
        raise ConceptError(f"لازم فكرتين بدون كتابة على الأقل، والموجود {len(plain)}")
    if not texted:
        raise ConceptError("لازم فكرة وحدة بكتابة على الأقل، والموجود 0")
    order = {id(c): i for i, c in enumerate(cards)}
    for rules, note in RELAX:
        best = None
        for pair in itertools.combinations(plain, 2):
            for t in texted:
                trio = (*pair, t)
                if not _ok(trio, rules):
                    continue
                key = (sum(score(c) for c in trio), [-order[id(c)] for c in trio])
                if best is None or key > best[0]:
                    best = (key, trio)
        if best:
            ranked = sorted(best[1], key=lambda c: (-score(c), order[id(c)]))
            picked = [dict(c, label=LABELS[i], score=score(c)) for i, c in enumerate(ranked)]
            return picked, [note] if note else []
    raise ConceptError("ما گدرت أختار 3 أفكار")  # ما يوصلها: المستوى الأخير بلا شروط


def color_name(color: str) -> str:
    """أقرب اسم لون إنگليزي (للأمر)."""
    r, g, b = _rgb(color)
    return min(COLORS, key=lambda n: (COLORS[n][0] - r) ** 2 + (COLORS[n][1] - g) ** 2 + (COLORS[n][2] - b) ** 2)


def _clause(text: str) -> str:
    return text.strip().rstrip(".")


def build_prompt(card: dict) -> str:
    """أمر التوليد الإنگليزي (Nano Banana Pro) من البطاقة."""
    s, layout, palette = card["subject"], card["layout"], card["palette"]
    dominant, accent = color_name(palette[0]), color_name(palette[1])
    rim = color_name(palette[2]) if len(palette) > 2 else accent
    lines = [
        IDENTITY,
        f"{FACE_LINES[layout['face']]}, chest-up and large (his head and shoulders fill about 40% of the frame "
        f"width), looking straight into the camera. He wears {s['outfit']}. "
        f"Expression: {s['expression']}, natural and believable, not exaggerated. Pose: {_clause(s['action'])}.",
        HERO_LINES[layout["hero"]].format(card["hero"]),
        f"Setting: {_clause(card['setting'])}.",
        f"Colors: {dominant} dominant, {accent} as the one strong accent color, {rim} rim light on his face and "
        f"shoulders, high contrast, vivid saturated colors, sharp detailed skin texture, background slightly "
        f"darker and softer than his face.",
    ]
    if CAMERA_LINES[card["camera"]]:
        lines.append(CAMERA_LINES[card["camera"]])
    if layout["text_zone"]:
        lines.append(f"Keep the {ZONE_NAMES[layout['text_zone']]} part of the frame dark and empty for a headline.")
    lines.append(NO_TEXT)
    return "\n".join(lines)
