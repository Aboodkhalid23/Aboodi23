"""هوية "سالوفة" الكاملة، من التصميم الي اختاره صاحب القناة (روس الحروف مسامير، خط ReemKufi).

    python3 brand/salufa/identity.py -o brand/salufa/identity

الألوان (طلبه، 22 تشرين الأول 2026): أسود، وزيتوني، ورصاصي، ونيلي، ونفطي. ماكو ألوان بناتية.
النقاط مرسومة بإيدنا حتى تبين واضحة: نقطة الفاء دائرة مدوّرة، ونقطتين التاء جنب بعض فوق التاء
(الخط الأصلي يحطهن فوق بعض ولاصقات، فما يبينن). وبعض النسخ النقاط بلون ثاني حتى تبرز.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logos import CUNEI_WORD, dot_blobs, font, rgb, shape_word, wedge, wedge_heads  # noqa: E402

FONT, PX, S = "ReemKufi-Variable.ttf", 330, 1200
BLACK, OLIVE, OLIVE_LIGHT = "#111214", "#4B5530", "#A3AD6E"
LEAD, LEAD_LIGHT, INDIGO, PETROL, BONE = "#6E7378", "#C9CCCF", "#2A3478", "#134A55", "#E9E6DF"
TAGLINE = "سوالف من الزمن الأول"


def layers(fa_dot="round", ta_dots="round", keep_stroke=False):
    """يرجع (قناع الحروف، قناع النقاط) منفصلين، حتى النقاط تاخذ لون ثاني إذا ردنا.

    fa_dot: round | wedge | istikan.  ta_dots: round | wedge.
    """
    f = font(FONT, PX)
    fa, _ = dot_blobs("سالوفة", "سالوڡة", f)
    ta, body = dot_blobs("سالوڡة", "سالوڡه", f)
    fx, fy, fw, fh = fa[0]
    r = max(fw, fh) / 2 * 1.05
    tx = ta[0][0]
    tops = [body.crop((int(tx + k), 0, int(tx + k) + 1, body.height)).getbbox() for k in range(-30, 31, 6)]
    bowl_top = min(t[1] for t in tops if t)
    # التاء بهذا الخط إلها خط طويل فوق (يخليها تشبه اللام): نشيله، ونخلي القوس بس
    if not keep_stroke:
        ImageDraw.Draw(body).rectangle((0, 0, int(fx - fw * 2), int(bowl_top) - 2), fill=0)
    body = wedge_heads(body, 1.2)
    dots = Image.new("L", body.size)
    d = ImageDraw.Draw(dots)
    # نقطتين التاء: جنب بعض، فوق قوس التاء بمسافة واضحة
    ty = bowl_top - r * 1.9
    gap = r * 1.25
    if keep_stroke:  # الخط الطويل يمين النقاط: نزحزحهن لليسار حتى ما يلمسنه
        tx -= gap * 0.9
    for x, y, style in ((fx, fy, fa_dot), (tx - gap, ty, ta_dots), (tx + gap, ty, ta_dots)):
        if style == "wedge":
            wedge(d, x, y - r * 0.9, r * 2.3)
        elif style == "istikan":
            hh = r * 5.6
            ww = hh * 0.42
            base = y + r
            top, mid = base - hh, base - hh * 0.45
            d.polygon([(x - ww / 2, top), (x + ww / 2, top), (x + ww * 0.2, mid), (x + ww * 0.42, base),
                       (x - ww * 0.42, base), (x - ww * 0.2, mid)], fill=255)
            for k in range(3):  # بخار مسماري
                wedge(d, x + (k - 1) * ww * 0.45, top - hh * 0.2 - (k == 1) * hh * 0.08, ww * 0.32)
        else:
            d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    return body, dots


def compose(body, dots, bg, fg, dot_color=None, tagline=TAGLINE, tag_color=None, cunei=False, size=S):
    img = Image.new("RGB", (size, size), rgb(bg))
    both = ImageChops.lighter(body, dots)
    box = both.getbbox()
    cw, ch = box[2] - box[0], box[3] - box[1]
    tw = int(size * 0.72)
    th = int(ch * tw / cw)
    x0, y0 = (size - tw) // 2, int(size * 0.44 - th / 2)
    for mask, color in ((body, fg), (dots, dot_color or fg)):
        part = mask.crop(box).resize((tw, th), Image.LANCZOS)
        img.paste(rgb(color), (x0, y0), part)
    d = ImageDraw.Draw(img)
    yy = y0 + th + size * 0.08
    if cunei:
        d.text((size / 2, yy), CUNEI_WORD, font=font("NotoSansCuneiform-Regular.ttf", int(size * 0.05)),
               fill=rgb(tag_color or fg), anchor="mm")
        yy += size * 0.08
    if tagline:
        t, kw = shape_word(tagline)
        d.text((size / 2, yy), t, font=font("Alexandria-Variable.ttf", int(size * 0.034)),
               fill=rgb(tag_color or fg), anchor="mm", **kw)
    return img


def clear(body, dots, color):
    both = ImageChops.lighter(body, dots)
    crop = both.crop(both.getbbox())
    out = Image.new("RGBA", crop.size, rgb(color) + (0,))
    out.putalpha(crop)
    return out


def bubble(body, dots, bg, bubble_color, fg, size=S):
    """الشعار جوه فقاعة حچي (صورة الحساب)."""
    img = Image.new("RGB", (size, size), rgb(bg))
    d = ImageDraw.Draw(img)
    pad = size * 0.12
    d.rounded_rectangle((pad, pad, size - pad, size * 0.78), radius=size * 0.16, fill=rgb(bubble_color))
    d.polygon([(size * 0.26, size * 0.74), (size * 0.40, size * 0.76), (size * 0.2, size * 0.9)],
              fill=rgb(bubble_color))
    both = ImageChops.lighter(body, dots)
    crop = both.crop(both.getbbox())
    tw = int(size * 0.6)
    th = int(crop.height * tw / crop.width)
    img.paste(rgb(fg), ((size - tw) // 2, int(size * 0.45 - th / 2)), crop.resize((tw, th), Image.LANCZOS))
    return img


def mockup(mark):
    """العلامة البيضاء بزاوية فيديو (فوق يسار، شفافية 70%، 12% من العرض)."""
    W, H = 1600, 900
    g = Image.linear_gradient("L").resize((W, H)).rotate(90)
    bg = Image.merge("RGB", [g.point(lambda v: 18 + v // 8), g.point(lambda v: 30 + v // 7), g.point(lambda v: 34 + v // 6)])
    d = ImageDraw.Draw(bg)
    d.ellipse((900, 200, 1350, 900), fill=(48, 60, 64))
    d.ellipse((1020, 120, 1230, 360), fill=(64, 76, 80))
    bg = bg.filter(ImageFilter.GaussianBlur(6))
    w = int(W * 0.12)
    m = mark.resize((w, int(mark.height * w / mark.width)), Image.LANCZOS)
    m.putalpha(m.getchannel("A").point(lambda v: int(v * 0.7)))
    bg.paste(m, (int(W * 0.035), int(H * 0.05)), m)
    return bg


def palette_strip(width):
    colors = [(BLACK, "أسود"), (OLIVE, "زيتوني"), (LEAD, "رصاصي"), (INDIGO, "نيلي"), (PETROL, "نفطي"),
              (BONE, "عاجي")]
    img = Image.new("RGB", (width, 160), rgb("#1A1B1D"))
    d = ImageDraw.Draw(img)
    w = width // len(colors)
    f = font("Alexandria-Variable.ttf", 24)
    for i, (c, name) in enumerate(colors):
        d.rectangle((i * w + 16, 12, (i + 1) * w - 16, 100), fill=rgb(c), outline=rgb("#3A3B3E"), width=2)
        t, kw = shape_word(f"{name} {c}")
        d.text((i * w + w / 2, 132), t, font=f, fill=rgb(BONE), anchor="mm", **kw)
    return img


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يرسم هوية سالوفة الكاملة")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*"):
        old.unlink()
    plain = layers()
    ist = layers(fa_dot="istikan")
    cun = layers(fa_dot="wedge", ta_dots="wedge")
    pieces = [
        ("main", "1. الأساسي: أسود، والنقاط زيتوني", compose(*plain, BLACK, BONE, OLIVE_LIGHT, tag_color=LEAD_LIGHT)),
        ("petrol", "2. نفطي", compose(*plain, PETROL, BONE, tag_color=LEAD_LIGHT)),
        ("indigo", "3. نيلي", compose(*plain, INDIGO, BONE, LEAD_LIGHT, tag_color=LEAD_LIGHT)),
        ("olive", "4. زيتوني", compose(*plain, OLIVE, BLACK, BONE, tag_color=BLACK)),
        ("lead", "5. رصاصي", compose(*plain, LEAD_LIGHT, BLACK, PETROL, tag_color=BLACK)),
        ("istikan", "6. نقطة الفاء استكان چاي", compose(*ist, BLACK, BONE, OLIVE_LIGHT, "تعالوا أحچيلكم",
                                                        LEAD_LIGHT)),
        ("cuneiform", "7. النقاط أسافين، والتوقيع المسماري", compose(*cun, PETROL, BONE, OLIVE_LIGHT, None,
                                                                     LEAD_LIGHT, cunei=True)),
        ("bubble", "8. صورة الحساب", bubble(*ist, OLIVE, BLACK, BONE)),
    ]
    for key, _, img in pieces:
        img.save(out / f"{key}.png")
    mark = clear(*ist, "#FFFFFF")
    mark.save(out / "watermark.png")
    clear(*ist, BLACK).save(out / "watermark-black.png")
    mock = mockup(mark)
    mock.save(out / "mockup.jpg", quality=92)
    tile, gap, cols = 430, 22, 4
    Wd = cols * tile + (cols + 1) * gap
    rows = 2
    Ht = 96 + rows * (tile + 56) + int(Wd * 9 / 32) + 70 + 170
    board = Image.new("RGB", (Wd, Ht), rgb("#1A1B1D"))
    d = ImageDraw.Draw(board)
    t, kw = shape_word("هوية سالوفة")
    d.text((Wd / 2, 52), t, font=font("Alexandria-Variable.ttf", 44), fill=rgb(BONE), anchor="mm", **kw)
    fs = font("Alexandria-Variable.ttf", 22)
    for i, (_, name, img) in enumerate(pieces):
        x = gap + (i % cols) * (tile + gap)
        y = 96 + (i // cols) * (tile + 56)
        board.paste(img.resize((tile, tile), Image.LANCZOS), (x, y))
        t, kw = shape_word(name)
        d.text((x + tile / 2, y + tile + 28), t, font=fs, fill=rgb(BONE), anchor="mm", **kw)
    y = 96 + rows * (tile + 56)
    mw = Wd // 2
    board.paste(mock.resize((mw, int(mw * 9 / 16)), Image.LANCZOS), ((Wd - mw) // 2, y))
    t, kw = shape_word("9. العلامة على الفيديو")
    d.text((Wd / 2, y + int(mw * 9 / 16) + 30), t, font=fs, fill=rgb(BONE), anchor="mm", **kw)
    board.paste(palette_strip(Wd), (0, Ht - 165))
    board.save(out / "board.jpg", quality=92)
    print(f"✓ انرسمت الهوية بـ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
