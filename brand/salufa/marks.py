"""سالوفة: الشعار الشفاف للفيديو (الحروف ملوّنة بنفسها) + رمز مسماري يوحي بالسالوفة.

    python3 brand/salufa/marks.py -o brand/salufa/marks

الشعار ينحط فوق الفيديو، فلازم يبين على أي خلفية: الحروف بلون، وحولها حد بلون ثاني.
كل تصميم = رمز مسماري (يمين) + كلمة سالوفة (يسار)، بخلفية شفافة (PNG).
الرموز:
  1. لوح الطين: لوح صغير محفور بيه سالوفة بالمسماري 𒊓𒇻𒉺.
  2. فقاعة الحچي المسمارية: فقاعة كلام مرسومة من أسافين، وجوها ثلاث أسافين (يعني "يحچي").
  3. الختم البابلي: دائرة ختم حولها أسافين، وبالنص إسفين كبير.
  4. سطر اللوح: الكلمة وتحتها سطر أسافين، كأن الحكاية تنكتب على لوح.
"""
import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identity import BLACK, BONE, OLIVE, OLIVE_LIGHT, PETROL, LEAD_LIGHT, layers  # noqa: E402
from logos import CUNEI_WORD, font, rgb, shape_word  # noqa: E402

K = 2  # دقة مضاعفة للرموز


def wedge(d, x, y, s, angle=90, fill=255):
    a = math.radians(angle)
    dx, dy, px, py = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    d.polygon([(x + px * s * 0.6, y + py * s * 0.6), (x - px * s * 0.6, y - py * s * 0.6),
               (x + dx * s * 0.75, y + dy * s * 0.75)], fill=fill)
    d.polygon([(x + dx * s * 0.4 + px * s * 0.13, y + dy * s * 0.4 + py * s * 0.13),
               (x + dx * s * 0.4 - px * s * 0.13, y + dy * s * 0.4 - py * s * 0.13),
               (x + dx * s * 1.35, y + dy * s * 1.35)], fill=fill)


def word_layers():
    body, dots = layers()
    both = ImageChops.lighter(body, dots)
    box = both.getbbox()
    return body.crop(box), dots.crop(box)


# ---------- الرموز (قناع شكل + قناع تفاصيل) بحجم مربع ----------
def tablet(size):
    """لوح طين صغير مايل شوية، محفور بيه 𒊓𒇻𒉺."""
    shape = Image.new("L", (size, size))
    detail = Image.new("L", (size, size))
    ImageDraw.Draw(shape).rounded_rectangle((size * 0.12, size * 0.08, size * 0.88, size * 0.92),
                                            radius=size * 0.14, fill=255)
    d = ImageDraw.Draw(detail)
    f = font("NotoSansCuneiform-Regular.ttf", int(size * 0.24))
    for i, ch in enumerate(CUNEI_WORD):
        d.text((size / 2, size * (0.25 + i * 0.25)), ch, font=f, fill=255, anchor="mm")
    return shape.rotate(-6, resample=Image.BICUBIC), detail.rotate(-6, resample=Image.BICUBIC)


def bubble(size):
    """فقاعة كلام حدودها أسافين، وجوها ثلاث أسافين نايمة (يحچي)."""
    shape = Image.new("L", (size, size))
    detail = Image.new("L", (size, size))
    s = ImageDraw.Draw(shape)
    cx, cy, r = size * 0.5, size * 0.44, size * 0.38
    n = 14
    for i in range(n):
        ang = 360 * i / n
        x = cx + r * math.cos(math.radians(ang))
        y = cy + r * math.sin(math.radians(ang))
        wedge(s, x, y, size * 0.12, ang + 90)
    s.polygon([(cx - r * 0.35, cy + r * 0.85), (cx - r * 0.85, cy + r * 1.35), (cx - r * 0.05, cy + r * 0.95)],
              fill=255)  # ذيل الفقاعة
    d = ImageDraw.Draw(detail)
    for k in (-1, 0, 1):
        wedge(d, cx + k * r * 0.45 + r * 0.12, cy, size * 0.11, 180)
    return shape, detail


def seal(size):
    """ختم بابلي: دائرة، وحولها أسافين، وبالنص إسفين كبير."""
    shape = Image.new("L", (size, size))
    detail = Image.new("L", (size, size))
    ImageDraw.Draw(shape).ellipse((size * 0.06, size * 0.06, size * 0.94, size * 0.94), fill=255)
    d = ImageDraw.Draw(detail)
    cx = cy = size / 2
    r = size * 0.36
    for i in range(12):
        ang = 360 * i / 12
        wedge(d, cx + r * math.cos(math.radians(ang)), cy + r * math.sin(math.radians(ang)), size * 0.08, ang + 180)
    wedge(d, cx, cy - size * 0.16, size * 0.24, 90)
    return shape, detail


def lockup(mark_fn, fill, dot_fill, edge, mark_fill, mark_detail, underline=False, height=420):
    """رمز يمين + كلمة يسار، كلهم بخلفية شفافة، والحروف ملوّنة ويا حد حتى تبين على أي فيديو."""
    body, dots = word_layers()
    wh = height
    ww = int(body.width * wh / body.height)
    body = body.resize((ww, wh), Image.LANCZOS)
    dots = dots.resize((ww, wh), Image.LANCZOS)
    msz = int(wh * 1.05) if mark_fn else 0
    gap = int(wh * 0.18) if mark_fn else 0
    pad = int(wh * 0.12)
    line_h = int(wh * 0.3) if underline else 0
    W = ww + gap + msz + pad * 2
    H = max(wh, msz) + line_h + pad * 2
    ink = Image.new("L", (W, H))     # كل الحبر (للحد)
    out = Image.new("RGBA", (W, H))
    wx, wy = pad, pad + (max(wh, msz) - wh) // 2
    layers_to_paint = [(body, (wx, wy), fill), (dots, (wx, wy), dot_fill)]
    if mark_fn:
        shape, detail = mark_fn(msz * K)
        shape = shape.resize((msz, msz), Image.LANCZOS)
        detail = detail.resize((msz, msz), Image.LANCZOS)
        mx, my = wx + ww + gap, pad + (max(wh, msz) - msz) // 2
        layers_to_paint = [(shape, (mx, my), mark_fill), (detail, (mx, my), mark_detail)] + layers_to_paint
        ink.paste(255, (mx, my), shape)
    ink.paste(255, (wx, wy), body)
    ink.paste(255, (wx, wy), dots)
    if underline:
        ul = Image.new("L", (W, H))
        ud = ImageDraw.Draw(ul)
        n = 11
        y = wy + wh + line_h * 0.45
        for i in range(n):
            x = wx + ww * (i + 0.5) / n
            wedge(ud, x, y - wh * 0.08, wh * (0.13 if i % 2 else 0.09), 90)
        layers_to_paint.append((ul, (0, 0), dot_fill))
        ink = ImageChops.lighter(ink, ul)
    # الحد: نوسّع الحبر ونصبغه، وظل خفيف تحته
    grow = max(3, wh // 28)
    halo = ink.filter(ImageFilter.MaxFilter(grow * 2 + 1)).filter(ImageFilter.GaussianBlur(1))
    shadow = halo.filter(ImageFilter.GaussianBlur(grow * 1.5)).point(lambda v: v * 0.55)
    out.paste(rgb("#000000") + (255,), (grow // 2, grow), shadow)
    out.paste(rgb(edge) + (255,), (0, 0), halo)
    for mask, pos, color in layers_to_paint:
        out.paste(rgb(color) + (255,), pos, mask)
    return out


def frames():
    """خلفيتين تجريبيتين: فيديو غامق وفيديو فاتح، حتى نتأكد إن الشعار يبين على الاثنين."""
    W, H = 960, 540
    dark = Image.linear_gradient("L").resize((W, H)).rotate(90)
    dark = Image.merge("RGB", [dark.point(lambda v: 20 + v // 7), dark.point(lambda v: 28 + v // 7),
                               dark.point(lambda v: 30 + v // 6)])
    light = Image.linear_gradient("L").resize((W, H))
    light = Image.merge("RGB", [light.point(lambda v: 235 - v // 6), light.point(lambda v: 228 - v // 5),
                                light.point(lambda v: 210 - v // 4)])
    for im, c in ((dark, (60, 72, 76)), (light, (170, 160, 140))):
        d = ImageDraw.Draw(im)
        d.ellipse((560, 120, 820, 560), fill=c)
        d.ellipse((630, 40, 760, 190), fill=c)
    return dark.filter(ImageFilter.GaussianBlur(5)), light.filter(ImageFilter.GaussianBlur(5))


DESIGNS = [
    ("1. لوح الطين", tablet, OLIVE_LIGHT, BONE, BLACK, PETROL, BONE, False),
    ("2. فقاعة الحچي المسمارية", bubble, BONE, OLIVE_LIGHT, BLACK, OLIVE_LIGHT, BONE, False),
    ("3. الختم البابلي", seal, "#7FA7B0", BONE, BLACK, OLIVE, BONE, False),
    ("4. سطر اللوح", None, BONE, OLIVE_LIGHT, BLACK, None, None, True),
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يرسم شعار سالوفة الشفاف للفيديو ويا الرمز المسماري")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dark, light = frames()
    tiles = []
    for i, (name, fn, fill, dot, edge, mfill, mdet, ul) in enumerate(DESIGNS, 1):
        logo = lockup(fn, fill, dot, edge, mfill, mdet, ul)
        logo.save(out / f"mark-{i}.png")
        row = []
        for bg in (dark, light):
            frame = bg.copy()
            w = int(frame.width * 0.5)
            lg = logo.resize((w, int(logo.height * w / logo.width)), Image.LANCZOS)
            frame.paste(lg, ((frame.width - w) // 2, (frame.height - lg.height) // 2), lg)
            row.append(frame)
        tiles.append((name, row))
    tw, th, gap = 960, 540, 20
    board = Image.new("RGB", (2 * tw + 3 * gap, 100 + len(tiles) * (th + 70)), rgb("#1A1B1D"))
    d = ImageDraw.Draw(board)
    t, kw = shape_word("سالوفة: الشعار الشفاف ويا الرمز المسماري (على فيديو غامق وفاتح)")
    d.text((board.width / 2, 50), t, font=font("Alexandria-Variable.ttf", 38), fill=rgb(BONE), anchor="mm", **kw)
    fs = font("Alexandria-Variable.ttf", 30)
    for r, (name, row) in enumerate(tiles):
        y = 100 + r * (th + 70)
        for c, im in enumerate(row):
            board.paste(im, (gap + c * (tw + gap), y))
        t, kw = shape_word(name)
        d.text((board.width / 2, y + th + 34), t, font=fs, fill=rgb(LEAD_LIGHT), anchor="mm", **kw)
    board.save(out / "board.jpg", quality=90)
    print(f"✓ انرسمت {len(tiles)} شعارات شفافة بـ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
