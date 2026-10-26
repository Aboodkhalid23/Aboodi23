"""سالوفة: التصميم المسماري داخل الحروف نفسها (مو جنب الكلمة ولا تحتها ولا وراها).

    python3 brand/salufa/inner.py -o brand/salufa/inner

الأفكار:
  1. كل روس الحروف مسامير: أسنان السين والألف واللام كلها تنتهي بإسفين، والنقاط أسافين.
  2. فتحات الحروف أسافين: الفتحات الصغيرة داخل الواو والفاء والتاء صارت بشكل إسفين.
  3. حروف من طين محفور: داخل كل حرف كتابة مسمارية محفورة، كأن الحرف نفسه لوح.
  4. الكل سوا: روس مسامير + فتحات أسافين + نقاط أسافين.
الشعار شفاف، والحروف ملوّنة ويا حد غامق حتى يبين على أي فيديو.
"""
import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identity import BLACK, BONE, LEAD_LIGHT, OLIVE, OLIVE_LIGHT, PETROL, dot_blobs  # noqa: E402
from logos import font, rgb, shape_word, wedge  # noqa: E402
from marks import frames  # noqa: E402

FONT, PX = "ReemKufi-Variable.ttf", 330


def base():
    """الكلمة بلا نقاط (والتاء بلا خطها الطويل)، ومكان نقطة الفاء ونقطتين التاء."""
    f = font(FONT, PX)
    fa, _ = dot_blobs("سالوفة", "سالوڡة", f)
    ta, body = dot_blobs("سالوڡة", "سالوڡه", f)
    fx, fy, fw, fh = fa[0]
    r = max(fw, fh) / 2 * 1.05
    tx = ta[0][0]
    tops = [body.crop((int(tx + k), 0, int(tx + k) + 1, body.height)).getbbox() for k in range(-30, 31, 6)]
    bowl_top = min(t[1] for t in tops if t)
    ImageDraw.Draw(body).rectangle((0, 0, int(fx - fw * 2), int(bowl_top) - 2), fill=0)
    gap = r * 1.25
    dots = [(fx, fy), (tx - gap, bowl_top - r * 1.9), (tx + gap, bowl_top - r * 1.9)]
    return body, dots, r


def add_dots(m, dots, r, style):
    d = ImageDraw.Draw(m)
    for x, y in dots:
        if style == "wedge":
            wedge(d, x, y - r * 0.9, r * 2.3)
        else:
            d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    return m


def stem_tips(m):
    """روس الخطوط (الألف واللام وأسنان السين): مجموعات أعمدة نحيفة طالعة فوق خط الوصل."""
    box = m.getbbox()
    tops = []
    for x in range(box[0], box[2]):
        bb = m.crop((x, 0, x + 1, m.height)).getbbox()
        tops.append((x, bb[1] if bb else None))
    valid = [t for _, t in tops if t is not None]
    join = sorted(valid)[int(len(valid) * 0.9)]          # أعلى خط الوصل (الأكثر تكرار تحت)
    runs, cur = [], []
    for x, t in tops:
        if t is not None and t < join - 20:
            cur.append((x, t))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    out = []
    for r in runs:
        width = r[-1][0] - r[0][0] + 1
        if 15 <= width <= 70:   # الأعرض = رووس الفاء والواو والتاء، مو خطوط
            out.append(((r[0][0] + r[-1][0]) / 2, min(t for _, t in r), width))
    return out


def nail_heads(m):
    d = ImageDraw.Draw(m)
    for cx, top, sw in stem_tips(m):
        s = sw * 1.0
        d.polygon([(cx - s, top - s * 0.35), (cx + s, top - s * 0.35), (cx, top + s * 1.3)], fill=255)
    return m


def holes(m):
    """الفتحات المسكّرة داخل الحروف (مثل فتحة الواو والفاء والتاء)."""
    work = m.point(lambda v: 255 if v > 128 else 0)
    ImageDraw.floodfill(work, (0, 0), 128)
    inner = work.point(lambda v: 255 if v == 0 else 0)
    found, cur = [], []
    for x in range(inner.width):
        bb = inner.crop((x, 0, x + 1, inner.height)).getbbox()
        if bb:
            cur.append((x, bb))
        elif cur:
            found.append(cur)
            cur = []
    res = []
    for blob in found:
        x0, x1 = blob[0][0], blob[-1][0]
        y0, y1 = min(b[1] for _, b in blob), max(b[3] for _, b in blob)
        res.append(((x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0)))
    return inner, res


def wedge_holes(m):
    """كل فتحة تصير إسفين: نسد الفتحة ونحفر إسفين بنصها."""
    inner, hs = holes(m)
    m = ImageChops.lighter(m, inner)
    d = ImageDraw.Draw(m)
    for x, y, size in hs:
        s = size * 1.7
        d.polygon([(x - s * 0.62, y - s * 0.6), (x + s * 0.62, y - s * 0.6), (x, y + s * 0.25)], fill=0)
        d.polygon([(x - s * 0.13, y - s * 0.1), (x + s * 0.13, y - s * 0.1), (x, y + s * 0.75)], fill=0)
    return m


def carved(m, spacing=64):
    """كتابة مسمارية محفورة داخل الحروف (قناع الحفر)، ما تطلع برا الحرف."""
    inside = m.filter(ImageFilter.MinFilter(15))
    pattern = Image.new("L", m.size)
    d = ImageDraw.Draw(pattern)
    box = m.getbbox()
    row = 0
    for y in range(box[1], box[3], spacing):
        for i, x in enumerate(range(box[0] + (row % 2) * spacing // 2, box[2], spacing)):
            wedge(d, x, y - spacing * 0.2, spacing * 0.4, 90)
        row += 1
    return ImageChops.multiply(pattern, inside)


def colorize(m, fill, edge, carve=None, carve_color=None, dot_mask=None, dot_color=None):
    box = m.getbbox()
    pad = 40
    m = m.crop((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad))
    out = Image.new("RGBA", m.size)
    grow = 9
    halo = m.filter(ImageFilter.MaxFilter(grow * 2 + 1)).filter(ImageFilter.GaussianBlur(1))
    shadow = halo.filter(ImageFilter.GaussianBlur(12)).point(lambda v: v * 0.5)
    out.paste((0, 0, 0, 255), (4, 8), shadow)
    out.paste(rgb(edge) + (255,), (0, 0), halo)
    out.paste(rgb(fill) + (255,), (0, 0), m)
    if carve is not None:
        c = carve.crop((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad))
        out.paste(rgb(carve_color) + (255,), (0, 0), c)
    if dot_mask is not None:
        dm = dot_mask.crop((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad))
        out.paste(rgb(dot_color) + (255,), (0, 0), dm)
    return out


def designs():
    body, dots, r = base()
    res = []
    # 1. روس مسامير + نقاط أسافين
    m1 = nail_heads(body.copy())
    dm = add_dots(Image.new("L", body.size), dots, r, "wedge")
    res.append(("1. كل روس الحروف مسامير", colorize(ImageChops.lighter(m1, dm), BONE, BLACK, dot_mask=dm,
                                                       dot_color=OLIVE_LIGHT)))
    # 2. فتحات الحروف أسافين + نقاط مدوّرة
    m2 = wedge_holes(body.copy())
    dm2 = add_dots(Image.new("L", body.size), dots, r, "round")
    res.append(("2. فتحات الحروف أسافين", colorize(ImageChops.lighter(m2, dm2), OLIVE_LIGHT, BLACK,
                                                     dot_mask=dm2, dot_color=BONE)))
    # 3. حروف طين محفور بيها مسماري
    m3 = add_dots(body.copy(), dots, r, "round")
    res.append(("3. حروف محفور بيها مسماري", colorize(m3, PETROL, BLACK, carve=carved(m3),
                                                       carve_color="#5FA3AF")))
    # 4. الكل سوا
    m4 = wedge_holes(nail_heads(body.copy()))
    dm4 = add_dots(Image.new("L", body.size), dots, r, "wedge")
    res.append(("4. الكل سوا: مسامير وفتحات ونقاط", colorize(ImageChops.lighter(m4, dm4), BONE, BLACK,
                                                              dot_mask=dm4, dot_color=OLIVE_LIGHT)))
    # 5. الكل سوا بالزيتوني ويا حفر خفيف
    m5 = ImageChops.lighter(m4, dm4)
    res.append(("5. الكل سوا: زيتوني محفور", colorize(m5, OLIVE, BLACK, carve=carved(m5, 52),
                                                       carve_color="#8E9A5C")))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="سالوفة: التصميم داخل الحروف")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dark, light = frames()
    items = designs()
    tw, th, gap = 960, 540, 20
    board = Image.new("RGB", (2 * tw + 3 * gap, 100 + len(items) * (th + 70)), rgb("#1A1B1D"))
    d = ImageDraw.Draw(board)
    t, kw = shape_word("سالوفة: المسماري داخل الحروف (على فيديو غامق وفاتح)")
    d.text((board.width / 2, 50), t, font=font("Alexandria-Variable.ttf", 38), fill=rgb(BONE), anchor="mm", **kw)
    fs = font("Alexandria-Variable.ttf", 30)
    for i, (name, logo) in enumerate(items):
        logo.save(out / f"inner-{i + 1}.png")
        y = 100 + i * (th + 70)
        for c, bg in enumerate((dark, light)):
            frame = bg.copy()
            w = int(tw * 0.62)
            lg = logo.resize((w, int(logo.height * w / logo.width)), Image.LANCZOS)
            frame.paste(lg, ((tw - w) // 2, (th - lg.height) // 2), lg)
            board.paste(frame, (gap + c * (tw + gap), y))
        t, kw = shape_word(name)
        d.text((board.width / 2, y + th + 34), t, font=fs, fill=rgb(LEAD_LIGHT), anchor="mm", **kw)
    board.save(out / "board.jpg", quality=90)
    print(f"✓ انرسمت {len(items)} تصاميم بـ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
