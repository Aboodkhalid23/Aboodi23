"""شعار "سالوفة" (الجولة الثالثة): الحروف نفسها تصير أشكال، والكلمة تبقى تنقرا صح.

    python3 brand/salufa/logos.py -o brand/salufa/out

الحروف من خطوط عربية قوية (حتى الكلمة تنقرا صح)، وبعدين حروف معيّنة تتبدل بأشكال:
الألف استكان چاي، والتاء المربوطة فقاعة حچي، والنقاط أسافين مسمارية، والكشيدة سطر لوح طين،
وروس الألف واللام أسافين مسمارية. المسماري 𒊓𒇻𒉺 = سا-لو-پا (كتابة صوتية للاسم).
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
S = 1200
OLIVE, OLIVE_DEEP, CREAM = "#3E4A2C", "#262E1B", "#F1E7D0"
SAFFRON, CLAY_ROSE, PISTACHIO, LILAC, INK = "#E8A33D", "#D9734E", "#B8C97A", "#B9A6D8", "#17150F"


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def font(name, px):
    return load_font(FONTS / name, px)


def text_mask(text, f, size=(S * 2, S)):
    """قناع النص على خط كتابة ثابت."""
    m = Image.new("L", size)
    t, kw = shape_word(text)
    ImageDraw.Draw(m).text((size[0] // 2 - f.getlength(t, **kw) / 2, size[1] * 0.6), t, font=f, fill=255,
                           anchor="ls", **kw)
    return m


def place(text, f, x_right, base, canvas):
    """يرسم نص طرفه اليمين عند x_right وعلى خط base. يرجع طرفه اليسار."""
    t, kw = shape_word(text)
    w = f.getlength(t, **kw)
    ImageDraw.Draw(canvas).text((x_right - w, base), t, font=f, fill=255, anchor="ls", **kw)
    return x_right - w


def wedge(d, x, y, s, angle=90):
    """إسفين مسماري: رأس مثلث وذيل، باتجاه angle (90 = نازل)."""
    a = math.radians(angle)
    dx, dy, px, py = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    d.polygon([(x + px * s * 0.6, y + py * s * 0.6), (x - px * s * 0.6, y - py * s * 0.6),
               (x + dx * s * 0.75, y + dy * s * 0.75)], fill=255)
    d.polygon([(x + dx * s * 0.4 + px * s * 0.13, y + dy * s * 0.4 + py * s * 0.13),
               (x + dx * s * 0.4 - px * s * 0.13, y + dy * s * 0.4 - py * s * 0.13),
               (x + dx * s * 1.35, y + dy * s * 1.35)], fill=255)


def dot_blobs(dotted, plain, f):
    """مراكز النقاط: الفرق بين الكلمة المنقوطة وبلا نقاط، كتل حسب الأعمدة."""
    a, b = text_mask(dotted, f), text_mask(plain, f)
    diff = ImageChops.subtract(a, b.filter(ImageFilter.MaxFilter(5))).point(lambda v: 255 if v > 128 else 0)
    blobs, cur = [], []
    for x in range(diff.width):
        bb = diff.crop((x, 0, x + 1, diff.height)).getbbox()
        if bb:
            cur.append((x, bb))
        elif cur:
            blobs.append(cur)
            cur = []
    out = []
    for blob in blobs:
        if len(blob) < 4:
            continue
        x0, x1 = blob[0][0], blob[-1][0]
        y0, y1 = min(bb[1] for _, bb in blob), max(bb[3] for _, bb in blob)
        out.append(((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0))
    return out, b


def wedge_dots(fname, px, heads=False):
    """الكلمة بلا نقاط، والنقاط أسافين بنفس أماكنها (نقطتين لاصقات = إسفينين).
    heads: روس الألف واللام هم أسافين (تنرسم قبل النقاط حتى ما تتلخبط)."""
    f = font(fname, px)
    blobs, m = dot_blobs("سالوفة", "سالوڡه", f)
    if heads:
        m = wedge_heads(m)
    d = ImageDraw.Draw(m)
    for x, y, w, h in blobs:
        n = 2 if w > h * 1.6 else 1
        s = h * 0.95
        for k in range(n):
            wedge(d, x + (k - (n - 1) / 2) * w / 2, y - s * 0.45, s)
    return m


def istikan_word(fname, px, gap=0.12):
    """سـ + استكان چاي (بمكان الألف) + لوفة، وفوق الاستكان بخار مسماري."""
    f = font(fname, px)
    m = Image.new("L", (S * 2, S))
    base = S * 0.6
    left = place("سـ", f, S * 1.55, base, m)
    t, kw = shape_word("ا")
    alef = f.getbbox(t, anchor="ls", **kw)
    h = (alef[3] - alef[1]) * 1.02
    w = h * 0.36
    d = ImageDraw.Draw(m)
    cx = left - w / 2 + 2
    top, mid = base - h, base - h * 0.45
    d.polygon([(cx - w / 2, top), (cx + w / 2, top), (cx + w * 0.22, mid), (cx + w * 0.42, base),
               (cx - w * 0.42, base), (cx - w * 0.22, mid)], fill=255)
    for k in range(3):
        wedge(d, cx + (k - 1) * w * 0.42, top - h * 0.24 - abs(k - 1) * h * 0.04, w * 0.3)
    place("لوفة", f, left - w - px * gap, base, m)
    return m


def bubble_word(fname, px):
    """سالوفـ + التاء المربوطة فقاعة حچي لاصقة بآخر الكشيدة، ونقطتيها أسافين."""
    f = font(fname, px)
    m = Image.new("L", (S * 2, S))
    base = S * 0.6
    left = place("سالوفـ", f, S * 1.55, base, m)
    d = ImageDraw.Draw(m)
    r = px * 0.25
    stroke = px * 0.085
    cx, cy = left - r * 0.9, base - r * 1.05
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, width=int(stroke))
    d.polygon([(cx + r * 0.2, cy + r * 0.9), (left + stroke * 0.6, base + stroke * 0.05),
               (cx + r * 0.85, cy + r * 0.35)], fill=255)
    for k in (-1, 1):
        wedge(d, cx + k * r * 0.45, cy - r * 1.9, r * 0.55)
    return m


def kashida_word(fname, px, n=7):
    """كشيدة طويلة: سالوفـــــة (نفس الخط، بس الوصل ممدود)."""
    return text_mask("سالوف" + "ـ" * n + "ة", font(fname, px))


def wedge_heads(m, scale=0.75):
    """روس الخطوط الطويلة (الألف واللام) تصير أسافين."""
    bbox = m.getbbox()
    top = bbox[1]
    limit = top + (bbox[3] - bbox[1]) * 0.12
    cols = []
    for x in range(bbox[0], bbox[2]):
        bb = m.crop((x, 0, x + 1, m.height)).getbbox()
        if bb and bb[1] <= limit:
            cols.append(x)
    groups, cur = [], []
    for x in cols:
        if cur and x != cur[-1] + 1:
            groups.append(cur)
            cur = []
        cur.append(x)
    if cur:
        groups.append(cur)
    d = ImageDraw.Draw(m)
    for g in groups:
        cx, sw = (g[0] + g[-1]) / 2, g[-1] - g[0] + 1
        s = sw * scale
        d.polygon([(cx - s, top - s * 0.25), (cx + s, top - s * 0.25), (cx, top + s * 1.2)], fill=255)
    return m


def compose(mask, bg, fg, shadow=None, cunei=False, tagline=None, accent=None, extrude=0):
    img = Image.new("RGB", (S, S), rgb(bg))
    crop = mask.crop(mask.getbbox())
    tw = int(S * 0.74)
    th = int(crop.height * tw / crop.width)
    if th > S * 0.5:
        th = int(S * 0.5)
        tw = int(crop.width * th / crop.height)
    word = crop.resize((tw, th), Image.LANCZOS)
    x0, y0 = (S - tw) // 2, int(S * 0.44 - th / 2)
    for k in range(extrude, 0, -1):  # بروز ثلاثي الأبعاد (ريترو)
        img.paste(rgb(shadow), (x0 + k, y0 + k), word)
    if shadow and not extrude:
        img.paste(rgb(shadow), (x0 + tw // 45, y0 + tw // 45), word)
    img.paste(rgb(fg), (x0, y0), word)
    d = ImageDraw.Draw(img)
    yy = y0 + th + S * 0.08
    if cunei:
        f = font("NotoSansCuneiform-Regular.ttf", int(S * 0.05))
        d.text((S / 2, yy), CUNEI_WORD, font=f, fill=rgb(accent or fg), anchor="mm")
        yy += S * 0.08
    if tagline:
        t, kw = shape_word(tagline)
        d.text((S / 2, yy), t, font=font("Alexandria-Variable.ttf", int(S * 0.034)), fill=rgb(accent or fg),
               anchor="mm", **kw)
    return img


def designs():
    return [
        ("الاستكان بمكان الألف", istikan_word("Kufam-Variable.ttf", 330), OLIVE, CREAM, None, False,
         "تعالوا أحچيلكم", SAFFRON, 0),
        ("الاستكان: ريترو", istikan_word("Lalezar-Regular.ttf", 360), CLAY_ROSE, CREAM, OLIVE_DEEP, False,
         None, CREAM, 14),
        ("التاء فقاعة حچي", bubble_word("ReemKufi-Variable.ttf", 330), CREAM, OLIVE_DEEP, None, True, None,
         CLAY_ROSE, 0),
        ("فقاعة حچي: زعفراني", bubble_word("Alexandria-Variable.ttf", 300), SAFFRON, OLIVE_DEEP, None, False,
         "تعالوا أحچيلكم", OLIVE_DEEP, 0),
        ("النقاط أسافين", wedge_dots("Kufam-Variable.ttf", 330), OLIVE_DEEP, CREAM, None, True, None, PISTACHIO, 0),
        ("أسافين: ليلكي", wedge_dots("Kufam-Variable.ttf", 330, heads=True), LILAC, INK, None, False,
         "سوالف من الزمن الأول", INK, 0),
        ("الكشيدة الطويلة", kashida_word("Kufam-Variable.ttf", 280), CREAM, OLIVE, None, True, None, CLAY_ROSE, 0),
        ("ريترو جريء", text_mask("سالوفة", font("Lalezar-Regular.ttf", 360)), PISTACHIO, OLIVE_DEEP, SAFFRON, False,
         "تعالوا أحچيلكم", OLIVE_DEEP, 12),
    ]


def sheet(images, names, title):
    tile, gap, cols = 540, 26, 4
    rows = math.ceil(len(images) / cols)
    Wd = cols * tile + (cols + 1) * gap
    Ht = rows * (tile + 64) + gap + 96
    out = Image.new("RGB", (Wd, Ht), rgb("#EDE6D8"))
    d = ImageDraw.Draw(out)
    t, kw = shape_word(title)
    d.text((Wd / 2, 52), t, font=font("Alexandria-Variable.ttf", 40), fill=rgb(INK), anchor="mm", **kw)
    fs = font("Alexandria-Variable.ttf", 24)
    for i, (im, name) in enumerate(zip(images, names)):
        x = gap + (i % cols) * (tile + gap)
        y = 96 + (i // cols) * (tile + 64)
        out.paste(im.resize((tile, tile), Image.LANCZOS), (x, y))
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
    for i, (name, mask, bg, fg, shadow, cunei, tag, accent, ex) in enumerate(designs(), 1):
        img = compose(mask, bg, fg, shadow, cunei, tag, accent, ex)
        img.save(out / f"logo-{i}.png")
        crop = mask.crop(mask.getbbox())
        clear = Image.new("RGBA", crop.size, rgb(fg) + (0,))
        clear.putalpha(crop)
        clear.save(out / f"logo-{i}-clear.png")
        images.append(img)
        names.append(name)
    sheet(images, names, "سالوفة: الجولة الثالثة").save(out / "sheet.jpg", quality=92)
    print(f"✓ انرسمت {len(images)} تصاميم بـ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
