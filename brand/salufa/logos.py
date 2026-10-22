"""شعار "سالوفة": 8 تصاميم مبدئية (عربي + روح الكتابة المسمارية)، كلها مرسومة بالكود.

    python3 brand/salufa/logos.py -o brand/salufa/out

يطلع logo-1.png … logo-8.png (1000×1000، خلفية شفافة إذا التصميم يسمح) و sheet.jpg (كلهن بورقة وحدة).
المسماري: 𒊓𒇻𒉺 (سا-لو-پا). الأكدية ما بيها حرف "ف"، فأقرب نطق بالمقاطع المسمارية هو "پا".
"""
import argparse
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "designer"))
from arabic import load_font, shape_word  # noqa: E402

FONTS = ROOT / "designer" / "fonts"
CUNEI = FONTS / "NotoSansCuneiform-Regular.ttf"
WORD = "سالوفة"
CUNEI_WORD = "\U00012293\U000121FB\U0001227A"  # SA LU PA
S = 1000

# ألوان بلاد الرافدين: لازورد بوابة عشتار، وذهب، وطين، وكريمي
LAPIS, LAPIS_DEEP, GOLD, CLAY, CLAY_DARK, CREAM, INK = (
    "#1E3F8F", "#0E1F4D", "#D9A521", "#B9773E", "#7A4521", "#F3E6CC", "#1A1410")


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def font(name, px):
    return load_font(FONTS / name, px)


def text_center(d, xy, text, f, fill, stroke=0, stroke_fill=None, anchor="mm"):
    t, kw = shape_word(text)
    d.text(xy, t, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill, **kw)


def wedge(d, x, y, length, angle, head, fill):
    """إسفين مسماري: رأس مثلث وذيل يضعف."""
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    tip = (x + dx * length, y + dy * length)
    hw = head / 2
    d.polygon([(x + px * hw, y + py * hw), (x - px * hw, y - py * hw),
               (x + dx * head * 0.9, y + dy * head * 0.9)], fill=fill)
    d.polygon([(x + dx * head * 0.5 + px * head * 0.14, y + dy * head * 0.5 + py * head * 0.14),
               (x + dx * head * 0.5 - px * head * 0.14, y + dy * head * 0.5 - py * head * 0.14), tip], fill=fill)


def clay_texture(size, base, seed=7):
    """سطح طين: لون أساسي وضوضاء ناعمة وبقع."""
    rnd = random.Random(seed)
    img = Image.new("RGB", size, rgb(base))
    noise = Image.effect_noise(size, 40).convert("RGB")
    img = Image.blend(img, ImageChops.multiply(img, noise.point(lambda v: 170 + v // 3)), 0.6)
    spots = Image.new("L", size)
    sd = ImageDraw.Draw(spots)
    for _ in range(60):
        r = rnd.randint(4, 30)
        x, y = rnd.randint(0, size[0]), rnd.randint(0, size[1])
        sd.ellipse((x - r, y - r, x + r, y + r), fill=rnd.randint(20, 60))
    spots = spots.filter(ImageFilter.GaussianBlur(8))
    return Image.composite(Image.new("RGB", size, (0, 0, 0)), img, spots.point(lambda v: v // 3))


def carve(base, mask, depth=6):
    """يحفر الشكل بالطين: ظل غامق فوق-يسار وضو تحت-يمين، مثل الكتابة على لوح."""
    dark = Image.new("RGB", base.size, (40, 22, 10))
    light = Image.new("RGB", base.size, (255, 230, 190))
    sh = ImageChops.offset(mask, -depth // 2, -depth // 2)
    hi = ImageChops.offset(mask, depth // 2, depth // 2)
    out = Image.composite(light, base, ImageChops.subtract(hi, mask).point(lambda v: v * 0.5))
    out = Image.composite(dark, out, mask.point(lambda v: int(v * 0.75)))
    return Image.composite(dark, out, ImageChops.subtract(sh, mask).point(lambda v: v * 0.4))


def word_mask(text, f, size, center):
    m = Image.new("L", size)
    text_center(ImageDraw.Draw(m), center, text, f, 255)
    return m


def rounded_mask(size, box, r):
    m = Image.new("L", size)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=r, fill=255)
    return m


# ---------------- التصاميم ----------------
def logo_1():
    """اللوح الطيني: الكلمة محفورة بلوح طين، والمسماري تحتها."""
    img = Image.new("RGBA", (S, S))
    box = (110, 200, 890, 800)
    tablet = clay_texture((S, S), CLAY)
    tablet = carve(tablet, word_mask(WORD, font("Kufam-Variable.ttf", 165), (S, S), (500, 440)), 9)
    tablet = carve(tablet, word_mask(CUNEI_WORD, load_font(CUNEI, 120), (S, S), (500, 660)), 6)
    m = rounded_mask((S, S), box, 90).filter(ImageFilter.GaussianBlur(2))
    shadow = rounded_mask((S, S), (box[0] + 14, box[1] + 22, box[2] + 14, box[3] + 22), 90).filter(
        ImageFilter.GaussianBlur(18))
    img.paste((0, 0, 0, 140), (0, 0), shadow)
    img.paste(tablet, (0, 0), m)
    return img


def dots_of(text_dotted, text_plain, f, center):
    """مراكز النقاط: الفرق بين الكلمة المنقوطة والكلمة بلا نقاط، مقسوم لكتل حسب الأعمدة."""
    a = word_mask(text_dotted, f, (S, S), center)
    b = word_mask(text_plain, f, (S, S), center)
    diff = ImageChops.subtract(a, b.filter(ImageFilter.MaxFilter(5))).point(lambda v: 255 if v > 128 else 0)
    cols = [diff.crop((x, 0, x + 1, S)).getbbox() for x in range(S)]
    blobs, cur = [], []
    for x, bb in enumerate(cols):
        if bb:
            cur.append((x, bb))
        elif cur:
            blobs.append(cur)
            cur = []
    out = []
    for blob in blobs:
        if len(blob) < 6:
            continue
        x0, x1 = blob[0][0], blob[-1][0]
        y0 = min(bb[1] for _, bb in blob)
        y1 = max(bb[3] for _, bb in blob)
        out.append(((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0))
    return out, b


def logo_2():
    """الأسافين بدل النقاط: نقاط الفاء والتاء صارت أسافين مسمارية ذهبية."""
    img = Image.new("RGBA", (S, S), rgb(LAPIS_DEEP) + (255,))
    d = ImageDraw.Draw(img)
    f = font("ReemKufi-Variable.ttf", 240)
    dots, plain = dots_of("سالوفة", "سالوڡه", f, (500, 460))
    img.paste(rgb(CREAM), (0, 0), plain)
    for x, y, w in dots:
        n = 2 if w > 60 else 1   # كتلة عريضة = نقطتين
        for k in range(n):
            cx = x + (k - (n - 1) / 2) * w / 2
            wedge(d, cx, y - 32, 62, 90, 36, GOLD)
    for i in range(9):  # شريط أسافين مثل سطر لوح
        wedge(d, 230 + i * 62, 690, 50, 25 if i % 2 else -25, 30, GOLD)
    text_center(d, (500, 800), CUNEI_WORD, load_font(CUNEI, 70), GOLD)
    return img


def logo_3():
    """الختم الأسطواني: دائرة ختم بيها مسماري بالحافة، والكلمة بالنص."""
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    d.ellipse((90, 90, 910, 910), fill=GOLD)
    d.ellipse((120, 120, 880, 880), fill=LAPIS)
    d.ellipse((215, 215, 785, 785), outline=GOLD, width=6)
    cf = load_font(CUNEI, 58)
    ring = (CUNEI_WORD + " ") * 5
    n = len(ring)
    for i, ch in enumerate(ring):
        if ch == " ":
            continue
        ang = -90 + 360 * i / n
        layer = Image.new("RGBA", (120, 120))
        ImageDraw.Draw(layer).text((60, 60), ch, font=cf, fill=CREAM, anchor="mm")
        layer = layer.rotate(-ang - 90, resample=Image.BICUBIC)
        r = 335
        x = 500 + r * math.cos(math.radians(ang)) - 60
        y = 500 + r * math.sin(math.radians(ang)) - 60
        img.alpha_composite(layer, (int(x), int(y)))
    text_center(d, (500, 490), WORD, font("Blaka-Regular.ttf", 190), GOLD)
    return img


def logo_4():
    """الأيقونة: حرف السين، أسنانه 3 أسافين مسمارية وقوسه تحت الخط، علامة صغيرة لزاوية الفيديو."""
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((100, 100, 900, 900), radius=200, fill=LAPIS_DEEP)
    base = 540
    for x in (720, 590, 460):  # أسنان السين: أسافين نازلة لخط الكتابة
        wedge(d, x, base - 250, 250, 90, 104, GOLD)
    d.line((330, base, 745, base), fill=GOLD, width=46)                     # خط الكتابة
    d.arc((180, base - 150, 480, base + 150), start=0, end=180, fill=GOLD, width=46)  # قوس السين
    text_center(d, (500, 800), WORD, font("Alexandria-Variable.ttf", 90), CREAM)
    return img


def logo_5():
    """الاستكان والحكاية: استكان چاي عراقي، وبخاره خط مسماري، والكلمة تحته."""
    img = Image.new("RGBA", (S, S), rgb(CREAM) + (255,))
    d = ImageDraw.Draw(img)
    # الاستكان: خصر ضيق
    cx, top, bot = 500, 330, 620
    d.polygon([(cx - 120, top), (cx + 120, top), (cx + 70, (top + bot) / 2), (cx + 105, bot),
               (cx - 105, bot), (cx - 70, (top + bot) / 2)], fill=rgb(CLAY_DARK))
    d.polygon([(cx - 108, top + 30), (cx + 108, top + 30), (cx + 64, (top + bot) / 2 + 4),
               (cx + 94, bot - 12), (cx - 94, bot - 12), (cx - 64, (top + bot) / 2 + 4)], fill="#B3261E")
    d.ellipse((cx - 170, bot - 10, cx + 170, bot + 40), fill=GOLD)              # الصحن
    for i, ch in enumerate(CUNEI_WORD):                                       # البخار مسماري
        text_center(d, (cx - 60 + i * 60, 250 - i * 55), ch, load_font(CUNEI, 70), LAPIS)
    text_center(d, (500, 790), WORD, font("ArefRuqaa-Bold.ttf", 200), INK)
    return img


def logo_6():
    """فقاعة الحچي: فقاعة كلام بشكل لوح طين، والكلمة جوه."""
    img = Image.new("RGBA", (S, S))
    size = (S, S)
    bubble = Image.new("L", size)
    bd = ImageDraw.Draw(bubble)
    bd.rounded_rectangle((120, 220, 880, 700), radius=150, fill=255)
    bd.polygon([(300, 660), (420, 690), (230, 830)], fill=255)
    clay = clay_texture(size, CLAY, 11)
    clay = carve(clay, word_mask(WORD, font("Lalezar-Regular.ttf", 240), size, (500, 440)), 10)
    clay = carve(clay, word_mask(CUNEI_WORD, load_font(CUNEI, 80), size, (500, 600)), 5)
    shadow = ImageChops.offset(bubble, 12, 20).filter(ImageFilter.GaussianBlur(16))
    img.paste((0, 0, 0, 130), (0, 0), shadow)
    img.paste(clay, (0, 0), bubble)
    return img


def logo_7():
    """بوابة عشتار: قوس بوابة لازوردي بطابوق، والكلمة ذهبية بالباب."""
    img = Image.new("RGBA", (S, S))
    gate = Image.new("L", (S, S))
    gd = ImageDraw.Draw(gate)
    gd.rectangle((150, 300, 850, 880), fill=255)
    gd.pieslice((150, 120, 850, 480), 180, 360, fill=255)
    wall = Image.new("RGBA", (S, S), rgb(LAPIS) + (255,))
    wd = ImageDraw.Draw(wall)
    for y in range(120, 880, 40):  # طابوق
        off = 0 if (y // 40) % 2 else 35
        for x in range(150 - 70 + off, 850, 70):
            wd.rectangle((x, y, x + 66, y + 36), outline=LAPIS_DEEP, width=3)
    img.paste(wall, (0, 0), gate)
    d = ImageDraw.Draw(img)
    d.rectangle((300, 470, 700, 880), fill=LAPIS_DEEP)                       # الباب
    d.pieslice((300, 330, 700, 610), 180, 360, fill=LAPIS_DEEP)
    for x in range(200, 820, 62):                                             # شريط أسافين ذهبية
        wedge(d, x, 268, 34, 90, 22, GOLD)
    text_center(d, (500, 640), WORD, font("Kufam-Variable.ttf", 120), GOLD)
    text_center(d, (500, 780), CUNEI_WORD, load_font(CUNEI, 60), CREAM)
    return img


def logo_8():
    """البسيط الحديث: الكلمة نظيفة، وتحتها 3 علامات مسمارية صغيرة مثل توقيع."""
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    text_center(d, (500, 450), WORD, font("Alexandria-Variable.ttf", 220), INK)
    d.line((250, 600, 750, 600), fill=GOLD, width=6)
    text_center(d, (500, 690), CUNEI_WORD, load_font(CUNEI, 90), GOLD)
    return img


LOGOS = [logo_1, logo_2, logo_3, logo_4, logo_5, logo_6, logo_7, logo_8]
NAMES = ["اللوح الطيني", "أسافين بدل النقاط", "الختم الأسطواني", "أيقونة السين",
         "الاستكان والحكاية", "فقاعة الحچي", "بوابة عشتار", "البسيط الحديث"]


def contact_sheet(images):
    tile, gap, cols = 460, 30, 4
    rows = math.ceil(len(images) / cols)
    W = cols * tile + (cols + 1) * gap
    H = rows * (tile + 70) + gap + 90
    sheet = Image.new("RGB", (W, H), (236, 230, 220))
    d = ImageDraw.Draw(sheet)
    text_center(d, (W / 2, 50), "تصاميم شعار سالوفة", font("Cairo-Black.ttf", 44), INK)
    for i, im in enumerate(images):
        x = gap + (i % cols) * (tile + gap)
        y = 90 + (i // cols) * (tile + 70)
        checker = Image.new("RGB", (tile, tile), (250, 247, 240))
        checker.paste(im.resize((tile, tile), Image.LANCZOS), (0, 0), im.resize((tile, tile), Image.LANCZOS))
        sheet.paste(checker, (x, y))
        text_center(d, (x + tile / 2, y + tile + 32), f"{i + 1}. {NAMES[i]}", font("Cairo-Black.ttf", 28), INK)
    return sheet


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يرسم تصاميم شعار سالوفة")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    images = []
    for i, fn in enumerate(LOGOS, 1):
        im = fn()
        im.save(out / f"logo-{i}.png")
        images.append(im)
    contact_sheet(images).save(out / "sheet.jpg", quality=92)
    print(f"✓ انرسمت {len(images)} تصاميم بـ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
