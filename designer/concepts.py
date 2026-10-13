"""محرك الأفكار: من بطاقات الأفكار (فكرة من كل زاوية) يختار 3 أغلفة ويرسم مخطط لكل وحدة.

    python3 designer/concepts.py <المجلد>/concepts.json -o <المجلد>

الاختيار: 2 بدون كتابة + 1 بكتابة، بزوايا وتعابير وألوان مختلفة.
صيغة البطاقة والزوايا الـ 12 بـ studio/thumbnail-angles.md.
"""
import argparse
import colorsys
import itertools
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arabic import is_rtl, load_font, shape_word, visual_words  # noqa: E402
from render import FONTS, FONTS_DIR, LATIN_FONTS  # noqa: E402

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
SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,30}")
REQUIRED_TEXT = ("idea", "hero", "setting", "why")
# وصف عربي اختياري يبين بالمخطط (لأن hero وexpression بالإنگليزي للأمر)
ARABIC_LABELS = ("hero_ar", "expression_ar")
SUBJECT_FIELDS = ("outfit", "expression", "action")
LABELS = "ABC"

IDENTITY = (
    "Cinematic photorealistic YouTube thumbnail photo. Main subject: the man in the reference image.\n"
    "Preserve his exact facial identity: face shape, eyes, eyebrows, nose, thin black mustache, short trimmed beard, "
    "short dark hair with faded sides, skin tone. Change only his expression, clothes, pose and lighting."
)
NO_TEXT = "No text, no letters, no captions, no logos, no watermark."
GAZE_CAMERA = "looking straight into the camera"
# زاوية offscreen: يباوع لشي برا الصورة، فما يباوع للكاميرا
GAZE_OFFSCREEN = "looking off to the side at something outside the frame that we cannot see"
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
    "wide_close": "Shot with a wide-angle lens very close to the subject, slight fisheye perspective.",
    "standard": "",
    "top_down": "Top-down camera angle, looking down at him and the scene from above.",
}
ZONE_NAMES = {"top_left": "upper-left", "top_right": "upper-right", "bottom_left": "lower-left"}
# الألوان الرمادية (تشبع أقل من GRAY_SATURATION) تاخذ اسمها من سلّم الإضاءة بس
GRAYS = ((0.1, "black"), (0.22, "charcoal"), (0.4, "dark gray"), (0.65, "gray"), (0.88, "silver"), (1.01, "white"))
COLORS = {
    "red": (220, 30, 30), "orange": (255, 120, 0), "yellow": (255, 210, 0), "gold": (212, 175, 55),
    "green": (40, 170, 60), "toxic green": (130, 255, 40), "teal": (0, 128, 128), "cyan": (0, 200, 255),
    "blue": (30, 90, 220), "navy": (15, 30, 75), "purple": (120, 40, 170), "magenta": (230, 30, 170),
    "pink": (255, 130, 180), "brown": (110, 60, 25), "beige": (225, 205, 170),
    "light blue": (150, 220, 255), "spring green": (0, 255, 150),
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
    if not isinstance(cid, str) or not SAFE_ID.fullmatch(cid):
        raise ConceptError(f"البطاقة رقم {n}: id لازم حروف إنگليزية وأرقام بس (مثل \"A1\")، 30 حرف بالأكثر")
    where = f"البطاقة {cid}"

    def need(cond, field, msg):
        if not cond:
            raise ConceptError(f"{where}: {field} {msg}")

    def pick(value, allowed) -> bool:
        return isinstance(value, (str, type(None))) and value in allowed

    need(pick(c.get("angle"), ANGLES), "angle", f"مو معروفة. المسموح: {', '.join(ANGLES)}")
    for field in REQUIRED_TEXT:
        need(isinstance(c.get(field), str) and c[field].strip(), field, "ناقص أو فارغ")
    subject = c.get("subject")
    need(isinstance(subject, dict), "subject", "ناقص (لازم outfit وexpression وaction)")
    for field in SUBJECT_FIELDS:
        need(isinstance(subject.get(field), str) and subject[field].strip(), f"subject.{field}", "ناقص أو فارغ")
    need(pick(c.get("camera"), CAMERAS), "camera", f"مو معروفة. المسموح: {', '.join(CAMERAS)}")
    layout = c.get("layout")
    need(isinstance(layout, dict), "layout", "ناقص (لازم face وhero وtext_zone)")
    need(pick(layout.get("face"), FACE_POS), "layout.face", f"مو معروف. المسموح: {', '.join(FACE_POS)}")
    need(pick(layout.get("hero"), HERO_POS), "layout.hero", f"مو معروف. المسموح: {', '.join(HERO_POS)}")
    need("text_zone" in layout and pick(layout["text_zone"], TEXT_ZONES), "layout.text_zone",
         "مو معروف. المسموح: null، top_left، top_right، bottom_left")
    palette = c.get("palette")
    need(isinstance(palette, list) and 2 <= len(palette) <= 4
         and all(isinstance(p, str) and HEX.fullmatch(p) for p in palette),
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
    for field in ARABIC_LABELS:
        if field in c:
            need(isinstance(c[field], str) and c[field].strip(), field, "لازم كتابة، أو احذفه")
    for field in ("font", "font_latin"):
        if field in c:
            need(pick(c[field], FONTS), field, f"خط مو معروف: {c[field]}. المتوفر: {', '.join(FONTS)}")
    font = c.get("font", "Baloo")
    need(not (font in LATIN_FONTS and text and is_rtl(text)), "font",
         f"الخط {font} ما بيه حروف عربية، والكتابة عربية. حط خط عربي بـ font، و{font} بـ font_latin")


def validate(cards) -> None:
    """يتأكد من البطاقات، وأي غلط يرفع ConceptError برسالة عربية."""
    if not isinstance(cards, list):
        raise ConceptError("ملف الأفكار لازم يكون قائمة بطاقات [ ... ]")
    if not cards:
        raise ConceptError("ملف الأفكار فارغ، ماكو ولا بطاقة")
    seen = set()
    for n, c in enumerate(cards, 1):
        _check_card(c, n)
        if c["id"].lower() in seen:
            raise ConceptError(f"البطاقة {c['id']}: الرقم مكرر، كل بطاقة لازم رقمها غير")
        seen.add(c["id"].lower())


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


def select(cards: list, no_text: bool = False) -> tuple[list[dict], list[str]]:
    """يختار 2 بدون كتابة + 1 بكتابة (أو 3 بدون كتابة إذا no_text)، بأعلى مجموع درجات يطابق الشروط.

    إذا الشروط ما تنطبق، ينزل الأضعف أول (اللون، بعده التعبير، بعده الزاوية) ويكتب ملاحظة.
    يرجع (المختارة مرتبة بالدرجة ووياها label وscore، الملاحظات).
    """
    plain = [c for c in cards if c.get("text") is None]
    texted = [c for c in cards if c.get("text") is not None]
    if no_text:
        if len(plain) < 3:
            raise ConceptError(f"لازم 3 أفكار بدون كتابة على الأقل، والموجود {len(plain)}")
        texted = plain
    elif len(plain) < 2:
        raise ConceptError(f"لازم فكرتين بدون كتابة على الأقل، والموجود {len(plain)}")
    if not texted:
        raise ConceptError("لازم فكرة وحدة بكتابة على الأقل، والموجود 0")
    order = {id(c): i for i, c in enumerate(cards)}
    for rules, note in RELAX:
        best = None
        for pair in itertools.combinations(plain, 2):
            for t in texted:
                if t is pair[0] or t is pair[1] or (no_text and order[id(t)] < order[id(pair[1])]):
                    continue
                trio = (*pair, t)
                if not _ok(trio, rules):
                    continue
                key = (round(sum(score(c) for c in trio), 1), [-order[id(c)] for c in trio])
                if best is None or key > best[0]:
                    best = (key, trio)
        if best:
            ranked = sorted(best[1], key=lambda c: (-score(c), order[id(c)]))
            picked = [dict(c, label=LABELS[i], score=score(c)) for i, c in enumerate(ranked)]
            return picked, [note] if note else []
    raise ConceptError("ما گدرت أختار 3 أفكار")  # ما يوصلها: المستوى الأخير بلا شروط


def color_name(color: str) -> str:
    """أقرب اسم لون إنگليزي (للأمر). الرمادي ينسمى حسب إضاءته، والملوّن من جدول COLORS."""
    _, sat, val = _hsv(color)
    if sat < GRAY_SATURATION:
        return next(name for limit, name in GRAYS if val < limit)
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
        f"width), {GAZE_OFFSCREEN if card['angle'] == 'offscreen' else GAZE_CAMERA}. He wears {s['outfit']}. "
        f"Expression: {s['expression']}, natural and believable, not exaggerated. Pose: {_clause(s['action'])}.",
        HERO_LINES[layout["hero"]].format(card["hero"]),
        f"Setting: {_clause(card['setting'])}.",
        f"Colors: {dominant} dominant, {accent} as the one strong accent color, {rim} rim light on his face and "
        f"shoulders, high contrast, vivid saturated colors, sharp detailed skin texture, background slightly "
        f"darker and softer than his face.",
    ]
    if CAMERA_LINES[card["camera"]]:
        lines.append(CAMERA_LINES[card["camera"]])
    if card["camera"] == "wide_close" and layout["hero"] == "foreground":
        lines.append("The main object is big in the foreground, close to the lens.")
    if layout["text_zone"]:
        lines.append(f"Keep the {ZONE_NAMES[layout['text_zone']]} part of the frame dark and empty for a headline.")
    lines.append(NO_TEXT)
    return "\n".join(lines)


# ---------------- المخطط واللوحة ----------------
SKETCH = (1280, 720)
TILE = (320, 180)
GAP = 16
COLS = 4
BOARD_HEADER = 80
CAIRO = FONTS_DIR / FONTS["Cairo"]
CAMERA_AR = {"wide_close": "عدسة عريضة قريبة", "standard": "كاميرا عادية", "top_down": "من فوق"}
FACE_X = {"right": 0.75, "left": 0.25, "center": 0.5}
HERO_BOX = {
    "left": (0.04, 0.22, 0.46, 0.84),
    "right": (0.54, 0.22, 0.96, 0.84),
    "center": (0.3, 0.2, 0.7, 0.8),
    "foreground": (0.18, 0.62, 0.82, 0.9),
}
ZONE_BOX = {"top_left": (0.03, 0.12, 0.5, 0.5), "top_right": (0.5, 0.12, 0.97, 0.5),
            "bottom_left": (0.03, 0.52, 0.5, 0.86)}
LINE_COLORS = ("#FFFFFF", "#FF9A00")
GOLD = "#FFC400"


def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def _words(line: str, font, latin=None) -> list:
    """كلمات السطر بترتيب الرسم: [(النص، المعاملات، الخط، العرض)]."""
    out = []
    for word in visual_words(line):
        text, kw = shape_word(word)
        f = latin if latin and not is_rtl(word) else font
        out.append((text, kw, f, f.getlength(text, **kw)))
    return out


def _line_width(words, space: float) -> float:
    return sum(w[3] for w in words) + space * max(0, len(words) - 1)


def _draw_words(d, words, x: float, y: float, fill, stroke=0, space=None, ascent=None):
    """يرسم الكلمات من x (يسار). y = أعلى السطر بالخط الأساسي. الكلمة اللاتينية تنزل لنفس الخط الأساسي."""
    space = space if space is not None else words[0][2].getlength(" ")
    ascent = ascent if ascent is not None else words[0][2].getmetrics()[0]
    for text, kw, f, width in words:
        d.text((x, y + ascent - f.getmetrics()[0]), text, font=f, fill=fill, anchor="la",
               stroke_width=stroke, stroke_fill="#0B0B0F", **kw)
        x += width + space


def _label(d, text: str, cx: float, cy: float, px: int, fill="#FFFFFF", stroke=2) -> None:
    """كتابة عربية بسطر واحد، بالنص حول (cx، cy)."""
    font = load_font(CAIRO, px)
    words = _words(text, font)
    space = font.getlength(" ")
    width = _line_width(words, space)
    ascent, descent = font.getmetrics()
    _draw_words(d, words, cx - width / 2, cy - (ascent + descent) / 2, fill, stroke, space, ascent)


def _label_right(d, text: str, right: float, top: float, px: int, fill="#FFFFFF") -> None:
    font = load_font(CAIRO, px)
    words = _words(text, font)
    space = font.getlength(" ")
    _draw_words(d, words, right - _line_width(words, space), top, fill, 0, space)


def _dashed_rect(d, box, color, width=4, dash=22) -> None:
    x0, y0, x1, y1 = box
    for ax, ay, bx, by in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        length = math.hypot(bx - ax, by - ay)
        n = max(1, int(length // (2 * dash)))
        for i in range(n + 1):
            t0, t1 = 2 * i * dash / length, min(1.0, (2 * i + 1) * dash / length)
            if t0 >= 1:
                break
            d.line((ax + (bx - ax) * t0, ay + (by - ay) * t0, ax + (bx - ax) * t1, ay + (by - ay) * t1),
                   fill=color, width=width)


def _headline(target: Image.Image, card: dict, box) -> None:
    """الكتابة نفسها بخط البطاقة، بأكبر حجم يساع المنطقة (يقيس الحبر الحقيقي ويا الحد)، بنص المنطقة."""
    x0, y0, x1, y1 = box
    lines = card["text"].split("\n")
    font_path = FONTS_DIR / FONTS[card.get("font", "Baloo")]
    latin_path = FONTS_DIR / FONTS[card["font_latin"]] if card.get("font_latin") else None
    px = int((y1 - y0) / (len(lines) * 1.1))
    while True:
        font = load_font(font_path, px)
        latin = load_font(latin_path, px) if latin_path else None
        space = font.getlength(" ")
        ascent, descent = font.getmetrics()
        line_h = (ascent + descent) * 0.9
        layer = Image.new("RGBA", target.size)
        d = ImageDraw.Draw(layer)
        for i, line in enumerate(lines):
            row = _words(line, font, latin)
            width = _line_width(row, space)
            _draw_words(d, row, (x0 + x1) / 2 - width / 2, y0 + i * line_h, LINE_COLORS[min(i, 1)],
                        max(2, int(px * 0.08)), space, ascent)
        ink = layer.getchannel("A").getbbox()
        fits = ink and ink[2] - ink[0] <= (x1 - x0) * 0.92 and ink[3] - ink[1] <= (y1 - y0) * 0.9
        if fits or px <= 14:
            break
        px = int(px * 0.92)
    if not ink:
        return
    dx = (x0 + x1) / 2 - (ink[0] + ink[2]) / 2
    dy = (y0 + y1) / 2 - (ink[1] + ink[3]) / 2
    target.alpha_composite(layer.transform(layer.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy)))


def _rgba(color: str, alpha: int) -> tuple:
    return (*_rgb(color), alpha)


def draw_sketch(card: dict, score_value: float) -> Image.Image:
    """المخطط 📐: أماكن الوجه والشي البطل والكتابة والألوان، بدون أي صورة."""
    W, H = SKETCH
    palette, layout = card["palette"], card["layout"]
    r, g, b = _rgb(palette[0])
    if (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.35:
        r, g, b = int(r * 0.6), int(g * 0.6), int(b * 0.6)
    img = Image.new("RGBA", SKETCH, (r, g, b, 255))
    over = Image.new("RGBA", SKETCH)
    d = ImageDraw.Draw(over)
    for i in (1, 2):
        d.line((W * i / 3, 0, W * i / 3, H), fill=(255, 255, 255, 35), width=2)
        d.line((0, H * i / 3, W, H * i / 3), fill=(255, 255, 255, 35), width=2)

    def hero():
        bx = HERO_BOX[layout["hero"]]
        box = (bx[0] * W, bx[1] * H, bx[2] * W, bx[3] * H)
        d.rounded_rectangle(box, radius=18, fill=_rgba(palette[1], 120), outline=_rgba(palette[1], 255), width=5)
        _label(d, "الشي البطل", (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 - 24, 34)
        if card.get("hero_ar"):
            _label(d, _cut(card["hero_ar"], 34), (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 24, 26)

    if layout["hero"] != "foreground":
        hero()
    cx, cy, rx, ry = FACE_X[layout["face"]] * W, 0.6 * H, 0.17 * W, 0.3 * H
    glow = palette[-1]
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=_rgba(glow, 70), outline=_rgba(glow, 255), width=6)
    # الكلام بالنص الفوگاني من الدائرة، حتى الشي البطل بالمقدمة ما يغطيه
    _label(d, "وجهك", cx, cy - 0.15 * H, 46)
    if card.get("expression_ar"):
        _label(d, _cut(card["expression_ar"], 30), cx, cy - 0.15 * H + 54, 26)
    if layout["hero"] == "foreground":
        hero()
    if layout["text_zone"]:
        zb = ZONE_BOX[layout["text_zone"]]
        box = (zb[0] * W, zb[1] * H, zb[2] * W, zb[3] * H)
        _dashed_rect(d, box, (255, 255, 255, 230))
        _headline(over, card, box)
    # فوق: الزاوية والدرجة والكاميرا
    d.rectangle((0, 0, W, 64), fill=(0, 0, 0, 170))
    _label_right(d, ANGLES[card["angle"]], W - 24, 6, 34)
    _label(d, f"{score_value:g}/100", W / 2, 32, 34, fill=GOLD, stroke=0)
    _label(d, CAMERA_AR[card["camera"]], 150, 32, 26, fill="#DDDDDD", stroke=0)
    # جوه: الفكرة والألوان
    d.rectangle((0, H - 60, W, H), fill=(0, 0, 0, 170))
    _label_right(d, _cut(card["idea"], 60), W - 24, H - 54, 28)
    for i, color in enumerate(palette):
        x = 24 + i * 64
        d.rectangle((x, H - 46, x + 52, H - 14), fill=_rgba(color, 255), outline=(255, 255, 255, 200), width=2)
    img.alpha_composite(over)
    return img.convert("RGB")


def draw_board(cards: list, picked) -> Image.Image:
    """لوحة كل الأفكار مرتبة بالدرجة. picked: أرقام المختارة (set) أو {الرقم: الحرف}."""
    labels = picked if isinstance(picked, dict) else {cid: "" for cid in picked}
    ranked = sorted(cards, key=lambda c: -score(c))
    rows = math.ceil(len(ranked) / COLS)
    W = COLS * TILE[0] + (COLS + 1) * GAP
    H = BOARD_HEADER + rows * (TILE[1] + GAP) + GAP
    board = Image.new("RGB", (W, H), (24, 24, 30))
    d = ImageDraw.Draw(board)
    _label(d, f"لوحة الأفكار: {len(cards)} فكرة، والمختارة بإطار ذهبي", W / 2, BOARD_HEADER / 2, 34, stroke=0)
    for i, c in enumerate(ranked):
        x = GAP + (i % COLS) * (TILE[0] + GAP)
        y = BOARD_HEADER + (i // COLS) * (TILE[1] + GAP)
        board.paste(draw_sketch(c, score(c)).resize(TILE, Image.LANCZOS), (x, y))
        d.rectangle((x, y + TILE[1] - 34, x + TILE[0], y + TILE[1]), fill=(0, 0, 0))
        _label_right(d, ANGLES[c["angle"]], x + TILE[0] - 8, y + TILE[1] - 34, 20)
        d.text((x + 8, y + TILE[1] - 30), f"{c['id']}  {score(c):g}", font=load_font(CAIRO, 20), fill=GOLD)
        if c["id"] in labels:
            d.rectangle((x - 4, y - 4, x + TILE[0] + 3, y + TILE[1] + 3), outline=GOLD, width=6)
            if labels[c["id"]]:
                d.ellipse((x + 8, y + 8, x + 52, y + 52), fill=GOLD)
                d.text((x + 30, y + 30), labels[c["id"]], font=load_font(CAIRO, 28), fill="#000000", anchor="mm")
    return board


def _table(cards: list, labels: dict) -> str:
    rows = ["الترتيب | الرقم | الزاوية | الدرجة | الكتابة"]
    for rank, c in enumerate(sorted(cards, key=lambda c: -score(c)), 1):
        mark = f"  ★ {labels[c['id']]}" if c["id"] in labels else ""
        kind = "بكتابة" if c.get("text") else "بدون"
        rows.append(f"{rank} | {c['id']} | {ANGLES[c['angle']]} | {score(c):g} | {kind}{mark}")
    return "\n".join(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يختار 3 أغلفة من بطاقات الأفكار ويرسم مخططاتها")
    ap.add_argument("concepts", help="ملف concepts.json")
    ap.add_argument("-o", "--out", required=True, help="مجلد النتائج")
    ap.add_argument("--no-text", action="store_true", help="3 أغلفة كلها بدون كتابة (إذا صاحب القناة طلب)")
    args = ap.parse_args(argv)
    path = Path(args.concepts)
    try:
        cards = json.loads(path.read_text(encoding="utf-8-sig"))
        validate(cards)
        picked, notes = select(cards, no_text=args.no_text)
    except FileNotFoundError:
        print(f"✗ خطأ: ملف الأفكار مو موجود: {path}")
        return 1
    except json.JSONDecodeError as e:
        print(f"✗ خطأ: ملف الأفكار بيه غلط بالصيغة (سطر {e.lineno}): {path}")
        return 1
    except UnicodeDecodeError:
        print(f"✗ خطأ: ملف الأفكار لازم يكون نص UTF-8: {path}")
        return 1
    except IsADirectoryError:
        print(f"✗ خطأ: هذا مجلد مو ملف أفكار: {path}")
        return 1
    except OSError:
        print(f"✗ خطأ: ما گدرت أقرا ملف الأفكار: {path}")
        return 1
    except ConceptError as e:
        print(f"✗ خطأ: {e}")
        return 1
    labels = {p["id"]: p["label"] for p in picked}
    print(_table(cards, labels))
    for note in notes:
        print(note)
    out = Path(args.out)
    try:
        out.mkdir(parents=True, exist_ok=True)
        result = {"notes": notes, "picked": [dict(p, prompt=build_prompt(p)) for p in picked]}
        for old in out.glob("sketch-*.jpg"):
            old.unlink()
        (out / "picked.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for p in picked:
            draw_sketch(p, p["score"]).save(out / f"sketch-{p['id']}.jpg", quality=90)
        draw_board(cards, labels).save(out / "board.jpg", quality=90)
    except OSError:
        print(f"✗ خطأ: ما گدرت أكتب النتائج بـ {out} (تأكد إنه مجلد مو ملف، وإنه ينكتب بيه)")
        return 1
    print(f"✓ انكتب picked.json و{len(picked)} مخططات وboard.jpg بـ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
