"""هوية "سالوفة" الكاملة، من التصميم الي اختاره صاحب القناة (الليلكي، وروس الحروف مسامير).

    python3 brand/salufa/identity.py -o brand/salufa/identity

يطلع:
  main.png        الشعار الأساسي (ليلكي وحبر)
  dark.png        النسخة الغامقة
  istikan.png     نقطة الفاء استكان چاي وبخاره مسماري (لمسة السالوفة)
  cuneiform.png   نقاط التاء أسافين، وتحت الكلمة التوقيع المسماري
  bubble.png      الشعار جوه فقاعة حچي (صورة الحساب)
  watermark.png   العلامة الشفافة للفيديو (أبيض)، و watermark-ink.png (حبر)
  mockup.jpg      شكل العلامة على فيديو
  board.jpg       كلشي بورقة وحدة، ويا الألوان
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import logos  # noqa: E402
from logos import (CREAM, INK, LILAC, OLIVE, SAFFRON, CUNEI_WORD, compose, dot_blobs, font,  # noqa: E402
                   rgb, shape_word, wedge, wedge_heads)

FONT = "ReemKufi-Variable.ttf"
PX = 330
TAGLINE = "سوالف من الزمن الأول"
LILAC_DEEP = "#8F78C2"


def word(fa_dot="round"):
    """الكلمة وروسها مسامير، والتاء المربوطة مثل الخط. نقطة الفاء حسب الطلب:
    round = دائرة مثل الخط، wedge = إسفين مسماري، istikan = استكان چاي وبخاره مسماري."""
    f = font(FONT, PX)
    blobs, m = dot_blobs("سالوفة", "سالوڡة", f)
    m = wedge_heads(m, 1.2)
    d = ImageDraw.Draw(m)
    x, y, w, h = max(blobs, key=lambda b: b[2] * b[3])  # نقطة الفاء
    r = h / 2
    if fa_dot == "wedge":
        wedge(d, x, y - r * 0.9, h * 1.15)
    elif fa_dot == "istikan":
        hh = h * 2.9
        ww = hh * 0.42
        base = y + r
        top, mid = base - hh, base - hh * 0.45
        d.polygon([(x - ww / 2, top), (x + ww / 2, top), (x + ww * 0.2, mid), (x + ww * 0.42, base),
                   (x - ww * 0.42, base), (x - ww * 0.2, mid)], fill=255)
        for k in range(3):  # بخار مسماري
            wedge(d, x + (k - 1) * ww * 0.45, top - hh * 0.2 - (k == 1) * hh * 0.08, ww * 0.32)
    else:
        d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    return m


def clear(mask, color):
    crop = mask.crop(mask.getbbox())
    out = Image.new("RGBA", crop.size, rgb(color) + (0,))
    out.putalpha(crop)
    return out


def bubble(mask, size=1200):
    """الشعار جوه فقاعة حچي غامقة (صورة الحساب والأيقونة)."""
    img = Image.new("RGB", (size, size), rgb(LILAC))
    d = ImageDraw.Draw(img)
    pad = size * 0.12
    d.rounded_rectangle((pad, pad, size - pad, size * 0.78), radius=size * 0.16, fill=rgb(INK))
    d.polygon([(size * 0.26, size * 0.74), (size * 0.40, size * 0.76), (size * 0.2, size * 0.9)], fill=rgb(INK))
    crop = mask.crop(mask.getbbox())
    tw = int(size * 0.6)
    th = int(crop.height * tw / crop.width)
    wd = crop.resize((tw, th), Image.LANCZOS)
    img.paste(rgb(LILAC), ((size - tw) // 2, int(size * 0.45 - th / 2)), wd)
    return img


def mockup(mark):
    """العلامة البيضاء بزاوية فيديو (فوق يسار، شفافية 70%، 12% من العرض)."""
    W, H = 1600, 900
    frame = Image.linear_gradient("L").resize((W, H)).rotate(90, expand=False)
    bg = Image.merge("RGB", [frame.point(lambda v: 40 + v // 5), frame.point(lambda v: 35 + v // 6),
                             frame.point(lambda v: 50 + v // 4)])
    d = ImageDraw.Draw(bg)
    d.ellipse((900, 200, 1350, 900), fill=(70, 62, 88))          # شكل مقدم تقريبي (مكان الوجه)
    d.ellipse((1020, 120, 1230, 360), fill=(90, 80, 110))
    bg = bg.filter(ImageFilter.GaussianBlur(6))
    w = int(W * 0.12)
    m = mark.resize((w, int(mark.height * w / mark.width)), Image.LANCZOS)
    alpha = m.getchannel("A").point(lambda v: int(v * 0.7))
    m.putalpha(alpha)
    bg.paste(m, (int(W * 0.035), int(H * 0.05)), m)
    return bg


def palette_strip(width):
    colors = [(LILAC, "ليلكي"), (INK, "حبر"), (CREAM, "كريمي"), (OLIVE, "زيتوني"), (SAFFRON, "زعفراني")]
    img = Image.new("RGB", (width, 150), rgb("#EDE6D8"))
    d = ImageDraw.Draw(img)
    w = width // len(colors)
    f = font("Alexandria-Variable.ttf", 24)
    for i, (c, name) in enumerate(colors):
        d.rectangle((i * w + 20, 10, (i + 1) * w - 20, 100), fill=rgb(c))
        t, kw = shape_word(f"{name} {c}")
        d.text((i * w + w / 2, 125), t, font=f, fill=rgb(INK), anchor="mm", **kw)
    return img


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يرسم هوية سالوفة الكاملة")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = word()
    pieces = {
        "main": compose(base, LILAC, INK, tagline=TAGLINE, accent=INK),
        "dark": compose(base, INK, LILAC, tagline=TAGLINE, accent=CREAM),
        "istikan": compose(word(fa_dot="istikan"), LILAC, INK, tagline="تعالوا أحچيلكم", accent=INK),
        "cuneiform": compose(word(fa_dot="wedge"), CREAM, INK, cunei=True, accent=LILAC_DEEP),
        "bubble": bubble(word(fa_dot="istikan")),
    }
    for name, img in pieces.items():
        img.save(out / f"{name}.png")
    mark = clear(word(fa_dot="istikan"), "#FFFFFF")
    mark.save(out / "watermark.png")
    clear(word(fa_dot="istikan"), INK).save(out / "watermark-ink.png")
    mock = mockup(mark)
    mock.save(out / "mockup.jpg", quality=92)
    # ورقة وحدة: 5 نسخ + الفيديو + الألوان
    tile, gap = 560, 24
    Wd = 3 * tile + 4 * gap
    board = Image.new("RGB", (Wd, 96 + 2 * (tile + 60) + 170), rgb("#EDE6D8"))
    d = ImageDraw.Draw(board)
    t, kw = shape_word("هوية سالوفة")
    d.text((Wd / 2, 52), t, font=font("Alexandria-Variable.ttf", 44), fill=rgb(INK), anchor="mm", **kw)
    names = {"main": "1. الأساسي", "dark": "2. الغامق", "istikan": "3. نقطة الفاء استكان",
             "cuneiform": "4. نقطة الفاء مسمار، والتوقيع المسماري", "bubble": "5. صورة الحساب"}
    fs = font("Alexandria-Variable.ttf", 26)
    for i, (key, img) in enumerate(pieces.items()):
        x = gap + (i % 3) * (tile + gap)
        y = 96 + (i // 3) * (tile + 60)
        board.paste(img.resize((tile, tile), Image.LANCZOS), (x, y))
        t, kw = shape_word(names[key])
        d.text((x + tile / 2, y + tile + 30), t, font=fs, fill=rgb(INK), anchor="mm", **kw)
    x, y = gap + 2 * (tile + gap), 96 + tile + 60
    board.paste(mock.resize((tile, int(tile * 9 / 16)), Image.LANCZOS), (x, y + 120))
    t, kw = shape_word("6. العلامة على الفيديو")
    d.text((x + tile / 2, y + tile + 30), t, font=fs, fill=rgb(INK), anchor="mm", **kw)
    board.paste(palette_strip(Wd), (0, board.height - 160))
    board.save(out / "board.jpg", quality=92)
    print(f"✓ انرسمت الهوية بـ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
