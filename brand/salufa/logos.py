"""شعار "سالوفة" (الجولة الثانية): حروف مرسومة من الصفر هندسياً، مو خطوط جاهزة.

    python3 brand/salufa/logos.py -o brand/salufa/out

الكلمة تنبني من 3 مقاطع (من اليمين): "سا" و"لو" و"فة"، كل مقطع خطوط وأقواس بسمك واحد.
الاتجاهات الأربعة (اختارهن صاحب القناة):
  1. الكشيدة الطويلة: خط وصل الفاء والتاء يمتد مثل "سالوفة طويلة".
  2. الفاء فم يحچي: رأس الفاء فم مفتوح يحچي باقي الكلمة.
  3. أطراف مسمارية: كل خط عمودي راسه إسفين مسماري.
  4. ريترو عراقي جريء: حروف ثقيلة مدوّرة وظل ملوّن مثل بوسترات بغداد القديمة.
النقاط تصير أسافين مسمارية بأغلب النسخ. المسماري الصغير 𒊓𒇻𒉺 = سا-لو-پا (كتابة صوتية للاسم).
"""
import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "designer"))
from arabic import load_font, shape_word  # noqa: E402

FONTS = ROOT / "designer" / "fonts"
CUNEI_WORD = "\U00012293\U000121FB\U0001227A"
K = 4            # رسم بدقة ×4 وبعدين تصغير، حتى الحواف تطلع ناعمة
W, H = 2400, 1000

# ألوان سالوفة: زيتوني وكريمي أساس، ووياهم زعفراني وطين وردي وفستقي وليلكي
OLIVE, OLIVE_DEEP, CREAM = "#3E4A2C", "#262E1B", "#F1E7D0"
SAFFRON, CLAY_ROSE, PISTACHIO, LILAC, INK = "#E8A33D", "#D9734E", "#B8C97A", "#B9A6D8", "#17150F"


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Pen:
    """يرسم بقناع (أبيض = حبر) بدقة K، بسمك ثابت ونهايات مدوّرة أو مقطوعة."""

    def __init__(self, w, round_caps=True):
        self.mask = Image.new("L", (W * K, H * K))
        self.d = ImageDraw.Draw(self.mask)
        self.w = w
        self.round = round_caps

    def _p(self, pts):
        return [(x * K, y * K) for x, y in pts]

    def line(self, pts, w=None):
        w = (w or self.w) * K
        pts = self._p(pts)
        if len(pts) > 2:  # منحني: نطبع دوائر متلاصقة (أنظف من وصلات PIL)
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                n = max(1, int(math.hypot(x1 - x0, y1 - y0) / (w / 6)))
                for i in range(n + 1):
                    x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
                    self.d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=255)
            return
        self.d.line(pts, fill=255, width=int(w))
        if self.round:
            for x, y in (pts[0], pts[-1]):
                self.d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=255)

    def arc(self, cx, cy, rx, ry, a0, a1, w=None, steps=90):
        pts = [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
                cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]
        self.line(pts, w)

    def bezier(self, p0, p1, p2, w=None, steps=60):
        pts = [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
               for t in (i / steps for i in range(steps + 1))]
        self.line(pts, w)

    def ring(self, cx, cy, r, w=None):
        w = (w or self.w)
        R = r + w / 2  # PIL يرسم الحافة للداخل، فنكبّر حتى الخط يتوسط نصف القطر
        self.d.ellipse(((cx - R) * K, (cy - R) * K, (cx + R) * K, (cy + R) * K), outline=255, width=int(w * K))

    def disc(self, cx, cy, r):
        self.d.ellipse(((cx - r) * K, (cy - r) * K, (cx + r) * K, (cy + r) * K), fill=255)

    def poly(self, pts, fill=255):
        self.d.polygon(self._p(pts), fill=fill)

    def wedge(self, x, y, size):
        """إسفين مسماري عمودي: رأس مثلث فوق وذيل نازل."""
        s = size
        self.poly([(x - s * 0.62, y - s * 0.55), (x + s * 0.62, y - s * 0.55), (x, y + s * 0.35)])
        self.poly([(x - s * 0.14, y), (x + s * 0.14, y), (x, y + s * 1.05)])

    def wedge_head(self, x, y_top, w):
        """رأس إسفين فوق خط عمودي (الاتجاه 3)."""
        self.poly([(x - w * 1.05, y_top - w * 0.15), (x + w * 1.05, y_top - w * 0.15), (x, y_top + w * 1.35)])

    def done(self):
        return self.mask.resize((W, H), Image.LANCZOS)


def build(style):
    """يبني قناع كلمة سالوفة حسب الستايل.

    style: w (السمك)، kashida (طول وصل الفاء والتاء)، verticals (plain|wedge)، fa (ring|mouth|disc)،
    dots (round|wedge)، caps (round|butt)، teeth (طول أسنان السين).
    """
    w = style["w"]
    pen = Pen(w, style.get("caps", "round") == "round")
    B = 600                         # خط الكتابة
    tall = style.get("tall", 300)   # طول الألف واللام
    tooth = style.get("teeth", 80)
    gap = style.get("gap", w * 1.3 + 12)  # المسافة بين المقاطع
    r = max(style.get("head", 52), w * 1.2)  # نصف قطر رأس الفاء والواو (الفتحة تبقى واضحة بالثقيل)
    kash = style.get("kashida", 120)
    x = style.get("right", 2150)

    def vertical(xv, top):
        pen.line([(xv, top), (xv, B)])
        if style.get("verticals") == "wedge":
            pen.wedge_head(xv, top - w * 0.2, w)

    def dots(xs, y):
        for xd in xs:
            if style.get("dots") == "wedge":
                pen.wedge(xd, y, w * 1.25)
            else:
                pen.disc(xd, y, w * 0.62)

    # المقطع 1: "سا" (سين أولية بثلاث أسنان، وألف)
    step = tooth * 0.75 + w * 0.6
    teeth_x = [x, x - step, x - 2 * step]
    for tx in teeth_x:
        vertical(tx, B - tooth)
    alef_x = teeth_x[-1] - step * 1.6
    pen.line([(x, B), (alef_x, B)])
    vertical(alef_x, B - tall)
    x = alef_x - gap - w

    # المقطع 2: "لو" (لام أولية وواو نهائية)
    vertical(x, B - tall)
    waw_cx = x - w * 0.5 - r * 1.55
    pen.line([(x, B), (waw_cx + r * 0.6, B)])
    pen.ring(waw_cx, B - r + w / 2, r)
    # ذيل الواو: من أسفل يسار الحلقة، نازل ويلتف لليسار تحت الخط
    pen.bezier((waw_cx - r * 0.55, B), (waw_cx - r * 0.6, B + r * 1.9), (waw_cx - r * 2.3, B + r * 1.7))
    x = waw_cx - r - gap

    # المقطع 3: "فة" (فاء أولية ووصل كشيدة وتاء مربوطة)
    fa_cx = x - r
    fa_cy = B - r + w / 2
    if style.get("fa") == "mouth":
        # فم مفتوح باتجاه الكلمة (يسار): حلقة ناقصة وشفة
        pen.arc(fa_cx, fa_cy, r, r, 222, 498)   # فتحة الفم لفوق-يسار
    elif style.get("fa") == "disc":
        pen.ring(fa_cx, fa_cy, r)
    else:
        pen.ring(fa_cx, fa_cy, r)
    dots([fa_cx], B - 2 * r - w * 1.7)
    end = fa_cx - r - kash
    pen.line([(fa_cx + r * 0.2, B), (end, B)])
    # التاء المربوطة: حلقة بيضوية لاصقة بآخر الكشيدة
    ta_cx = end - r * 0.95
    pen.d.ellipse(((ta_cx - r * 1.05 - w / 2) * K, (B - r * 2.1 - w / 2) * K, (ta_cx + r * 1.05 + w / 2) * K,
                   (B + w / 2) * K), outline=255, width=int(w * K))
    dots([ta_cx - w * 0.95, ta_cx + w * 0.95], B - 2.1 * r - w * 1.7)
    mask = pen.done()
    bbox = mask.getbbox()
    return mask, bbox


def fit(mask, bbox, size, scale_w=0.72):
    """يقص الكلمة ويوسّطها بلوحة size بعرض نسبة scale_w."""
    crop = mask.crop(bbox)
    tw = int(size[0] * scale_w)
    th = int(crop.height * tw / crop.width)
    if th > size[1] * 0.55:
        th = int(size[1] * 0.55)
        tw = int(crop.width * th / crop.height)
    return crop.resize((tw, th), Image.LANCZOS)


def compose(word, bg, fg, size=(1200, 1200), shadow=None, tagline=None, cunei=None, accent=None, y=0.45):
    """يحط الكلمة على خلفية، ويا ظل ملوّن (ريترو)، وسطر صغير، والمسماري."""
    img = Image.new("RGB", size, rgb(bg))
    x0 = (size[0] - word.width) // 2
    y0 = int(size[1] * y - word.height / 2)
    if shadow:
        off = max(8, word.width // 60)
        img.paste(rgb(shadow), (x0 + off, y0 + off), word)
    img.paste(rgb(fg), (x0, y0), word)
    d = ImageDraw.Draw(img)
    yy = y0 + word.height + size[1] * 0.07
    if cunei:
        f = load_font(FONTS / "NotoSansCuneiform-Regular.ttf", int(size[1] * 0.05))
        d.text((size[0] / 2, yy), CUNEI_WORD, font=f, fill=rgb(accent or fg), anchor="mm")
        yy += size[1] * 0.08
    if tagline:
        f = load_font(FONTS / "Alexandria-Variable.ttf", int(size[1] * 0.034))
        t, kw = shape_word(tagline)
        d.text((size[0] / 2, yy), t, font=f, fill=rgb(accent or fg), anchor="mm", **kw)
    return img


DESIGNS = [
    # (الاسم، الستايل، الخلفية، الحبر، الظل، سطر، مسماري، لون إضافي)
    ("الكشيدة الطويلة: زيتوني", dict(w=34, kashida=330, dots="wedge"), OLIVE, CREAM, None, "تعالوا أحچيلكم", False, SAFFRON),
    ("الكشيدة الطويلة: كريمي", dict(w=46, kashida=260, dots="round", caps="butt"), CREAM, OLIVE_DEEP, None, None, True, CLAY_ROSE),
    ("الفاء فم يحچي: زعفراني", dict(w=44, fa="mouth", kashida=150, dots="wedge"), SAFFRON, OLIVE_DEEP, None, "تعالوا أحچيلكم", False, OLIVE_DEEP),
    ("الفاء فم يحچي: زيتوني", dict(w=40, fa="mouth", kashida=200, dots="round"), OLIVE_DEEP, CREAM, None, None, True, PISTACHIO),
    ("أطراف مسمارية: كريمي", dict(w=26, verticals="wedge", dots="wedge", kashida=170, tall=330), CREAM, OLIVE, None, None, True, CLAY_ROSE),
    ("أطراف مسمارية: ليلكي", dict(w=30, verticals="wedge", dots="wedge", kashida=230, caps="butt"), LILAC, INK, None, "سوالف من الزمن الأول", False, INK),
    ("ريترو جريء: طين وردي", dict(w=72, fa="disc", kashida=110, teeth=95, head=58, tall=290), CLAY_ROSE, CREAM, OLIVE_DEEP, None, False, CREAM),
    ("ريترو جريء: فستقي", dict(w=78, kashida=90, teeth=95, head=60, dots="round"), PISTACHIO, OLIVE_DEEP, SAFFRON, "تعالوا أحچيلكم", False, OLIVE_DEEP),
]


def icon(style, bg, fg):
    """أيقونة صغيرة (لزاوية الفيديو وصورة الحساب): الكلمة داخل مربع مدوّر."""
    mask, bbox = build(style)
    word = fit(mask, bbox, (600, 600), 0.78)
    img = Image.new("RGBA", (600, 600))
    box = Image.new("L", (600, 600))
    ImageDraw.Draw(box).rounded_rectangle((0, 0, 599, 599), radius=140, fill=255)
    img.paste(rgb(bg) + (255,), (0, 0), box)
    img.paste(rgb(fg) + (255,), ((600 - word.width) // 2, (600 - word.height) // 2), word)
    return img


def sheet(images, names):
    tile, gap, cols = 540, 26, 4
    rows = math.ceil(len(images) / cols)
    Wd = cols * tile + (cols + 1) * gap
    Ht = rows * (tile + 64) + gap + 96
    out = Image.new("RGB", (Wd, Ht), rgb("#EDE6D8"))
    d = ImageDraw.Draw(out)
    f = load_font(FONTS / "Alexandria-Variable.ttf", 40)
    t, kw = shape_word("سالوفة: الجولة الثانية")
    d.text((Wd / 2, 52), t, font=f, fill=rgb(INK), anchor="mm", **kw)
    fs = load_font(FONTS / "Alexandria-Variable.ttf", 24)
    for i, (im, name) in enumerate(zip(images, names)):
        x = gap + (i % cols) * (tile + gap)
        y = 96 + (i // cols) * (tile + 64)
        out.paste(im.convert("RGB").resize((tile, tile), Image.LANCZOS), (x, y))
        t, kw = shape_word(f"{i + 1}. {name}")
        d.text((x + tile / 2, y + tile + 30), t, font=fs, fill=rgb(INK), anchor="mm", **kw)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يرسم تصاميم شعار سالوفة")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*"):
        old.unlink()
    images, names = [], []
    for i, (name, style, bg, fg, shadow, tag, cunei, accent) in enumerate(DESIGNS, 1):
        mask, bbox = build(style)
        word = fit(mask, bbox, (1200, 1200))
        img = compose(word, bg, fg, shadow=shadow, tagline=tag, cunei=cunei, accent=accent)
        img.save(out / f"logo-{i}.png")
        # نسخة شفافة للفيديو (الحبر بس)
        clear = Image.new("RGBA", word.size, rgb(fg) + (0,))
        clear.putalpha(word)
        clear.save(out / f"logo-{i}-clear.png")
        images.append(img)
        names.append(name)
    sheet(images, names).save(out / "sheet.jpg", quality=92)
    print(f"✓ انرسمت {len(images)} تصاميم بـ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
