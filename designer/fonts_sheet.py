"""ورقة نماذج الخطوط: صف لكل خط بستايلنا (أبيض وحد أسود عريض) على خلفية غامقة.

    python3 designer/fonts_sheet.py -o fonts.jpg

الخط العربي ينرسم بيه "نهاية الكون!" و"300 BILLION"، واللاتيني "300 BILLION" بس.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arabic import load_font, shape_word, visual_words  # noqa: E402
from render import FONTS, FONTS_DIR, LATIN_FONTS  # noqa: E402

SHEET_W = 1600
HEADER = 90
ROW_H = 150
SAMPLE_X = 360
SAMPLE_PX = 90
GAP = 60
AR_SAMPLE = "نهاية الكون!"
LATIN_SAMPLE = "300 BILLION"
BG = "#15151C"
STROKE = "#0B0B0F"
CAIRO = FONTS_DIR / FONTS["Cairo"]


def _line_width(line: str, font) -> float:
    widths = [font.getlength(t, **kw) for t, kw in (shape_word(w) for w in visual_words(line))]
    return sum(widths) + font.getlength(" ") * (len(widths) - 1)


def _row_font(path: Path, lines: list):
    """أكبر حجم (لحد SAMPLE_PX) يخلي نماذج الصف كلها تساع العرض."""
    room = SHEET_W - SAMPLE_X - 40
    px = SAMPLE_PX
    while True:
        font = load_font(path, px)
        if sum(_line_width(line, font) for line in lines) + GAP * (len(lines) - 1) <= room or px <= 30:
            return font, px
        px -= 4


def _draw_line(d, x: float, y: float, line: str, font, px: int) -> float:
    """يرسم سطر (عربي أو لاتيني) من x، ويرجع وين خلص."""
    space = font.getlength(" ")
    sw = int(px * 0.08)
    for word in visual_words(line):
        text, kw = shape_word(word)
        d.text((x, y), text, font=font, fill="#FFFFFF", anchor="lm", stroke_width=sw, stroke_fill=STROKE, **kw)
        x += font.getlength(text, **kw) + space
    return x


def make_sheet() -> Image.Image:
    sheet = Image.new("RGB", (SHEET_W, HEADER + ROW_H * len(FONTS)), BG)
    d = ImageDraw.Draw(sheet)
    title = load_font(CAIRO, 46)
    text, kw = shape_word("نماذج الخطوط")
    d.text((SHEET_W / 2, HEADER / 2), text, font=title, fill="#FFFFFF", anchor="mm", **kw)
    label = load_font(CAIRO, 34)
    for i, (name, file_name) in enumerate(FONTS.items()):
        top = HEADER + i * ROW_H
        mid = top + ROW_H / 2
        d.line((24, top, SHEET_W - 24, top), fill="#2A2A35", width=2)
        d.text((32, mid), name, font=label, fill="#C8C8D0", anchor="lm")
        lines = [LATIN_SAMPLE] if name in LATIN_FONTS else [AR_SAMPLE, LATIN_SAMPLE]
        font, px = _row_font(FONTS_DIR / file_name, lines)
        x = SAMPLE_X
        for line in lines:
            x = _draw_line(d, x, mid, line, font, px) + GAP
    return sheet


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يرسم ورقة نماذج الخطوط")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    out = Path(args.out)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        sheet = make_sheet()
        if out.suffix.lower() in (".jpg", ".jpeg"):
            sheet.save(out, quality=90)
        else:
            sheet.save(out)
    except (OSError, ValueError) as e:
        print(f"✗ خطأ: ما گدرت أحفظ الورقة ({e})")
        return 1
    print(f"✓ انحفظت ورقة الخطوط ({len(FONTS)} خط): {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
