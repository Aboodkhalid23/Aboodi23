"""ورقة المقارنة: لحد 4 أغلفة بصورة وحدة، وتحتها نفس الأغلفة بحجم الموبايل الصغير.

    python3 designer/sheet.py A.jpg B.jpg C.jpg D.jpg -o grid.jpg

الصف الصغير هو "اختبار الثانية الوحدة": إذا ما تنقرا هنا، ما تنقرا بالموبايل.
فوق خلفية بيضاء وتحت خلفية داكنة، مثل وضعي يوتيوب.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arabic import load_font  # noqa: E402

FONT = Path(__file__).resolve().parent / "fonts" / "Cairo-Black.ttf"
TILE = (640, 360)
MINI = (168, 94)
GAP = 20
SHEET_W = 2 * TILE[0] + 3 * GAP
GRID_H = 2 * TILE[1] + 3 * GAP
STRIP_H = 2 * MINI[1] + 3 * GAP
SHEET_SIZE = (SHEET_W, GRID_H + STRIP_H)
LIGHT_ROW_Y = GRID_H + GAP // 2
DARK_ROW_Y = GRID_H + GAP + MINI[1] + GAP


def make_sheet(paths: list, labels: list | None = None) -> Image.Image:
    if not 1 <= len(paths) <= 4:
        raise ValueError("ورقة المقارنة تاخذ من 1 لـ 4 صور")
    labels = labels or [Path(p).stem for p in paths]
    sheet = Image.new("RGB", SHEET_SIZE, (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    big = load_font(FONT, 34)
    small = load_font(FONT, 16)
    d.rectangle((0, GRID_H, SHEET_W, DARK_ROW_Y - GAP // 2), fill=(255, 255, 255))
    d.rectangle((0, DARK_ROW_Y - GAP // 2, SHEET_W, SHEET_SIZE[1]), fill=(15, 15, 15))
    for i, (path, label) in enumerate(zip(paths, labels)):
        img = Image.open(path).convert("RGB")
        x = GAP + (i % 2) * (TILE[0] + GAP)
        y = GAP + (i // 2) * (TILE[1] + GAP)
        sheet.paste(img.resize(TILE, Image.LANCZOS), (x, y))
        d.ellipse((x + 12, y + 12, x + 68, y + 68), fill=(255, 212, 0), outline=(0, 0, 0), width=3)
        d.text((x + 40, y + 40), label, font=big, fill=(0, 0, 0), anchor="mm")
        mini = img.resize(MINI, Image.LANCZOS)
        mx = GAP + i * (MINI[0] + GAP * 2)
        sheet.paste(mini, (mx, LIGHT_ROW_Y))
        sheet.paste(mini, (mx, DARK_ROW_Y))
        d.text((mx + MINI[0] + 4, LIGHT_ROW_Y), label, font=small, fill=(0, 0, 0))
    return sheet


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يجمع الأغلفة بورقة مقارنة")
    ap.add_argument("images", nargs="+")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    try:
        sheet = make_sheet([Path(p) for p in args.images])
    except (ValueError, FileNotFoundError) as e:
        print(f"✗ خطأ: {e}")
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() in (".jpg", ".jpeg"):
        sheet.save(out, quality=90)
    else:
        sheet.save(out)
    print(f"✓ انحفظ: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
