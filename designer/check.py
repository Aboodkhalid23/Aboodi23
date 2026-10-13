"""فحص الغلاف: يكشف الغلاف الضعيف قبل ما يوصل ليوتيوب.

    python3 designer/check.py thumb-A.jpg thumb-B.jpg thumb-C.jpg -o check.jpg
    python3 designer/check.py --calibrate designer/references/drive

- الوجه: إذا أقصر من 20% من ارتفاع الغلاف، ما ينقرا بالموبايل.
- الإضاءة والحيوية (colorfulness): مقارنة ويا أغلفة المراجع.
- اختبار التغبيش: check.jpg بيه لكل غلاف نسخة صغيرة، ومغبّشة، وأبيض وأسود.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError

sys.path.insert(0, str(Path(__file__).resolve().parent))
import face  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STATS_FILE = ROOT / "designer/references/stats.json"
# محسوبة من 44 غلاف مرجعي (مجلد Drive) بـ 4 تشرين الأول 2026
DEFAULT_STATS = {"brightness_p5": 39.6, "brightness_p50": 89.7, "colorfulness_p10": 25.6, "colorfulness_p50": 48.0}
MIN_FACE_RATIO = 0.20
SAMPLE = 320
TILE = (320, 180)
GAP = 20
INSTALL_HINT = "✗ خطأ: نصّب مكتبات الجودة: pip install -r designer/requirements-quality.txt"


def _sample(img: Image.Image) -> Image.Image:
    small = img.convert("RGB")
    small.thumbnail((SAMPLE, SAMPLE))
    return small


def brightness(img: Image.Image) -> float:
    import numpy as np
    return float(np.asarray(ImageOps.grayscale(_sample(img)), np.float64).mean())


def colorfulness(img: Image.Image) -> float:
    """مقياس Hasler وSüsstrunk: صفر للرمادي، ويكبر كل ما الألوان أقوى."""
    import numpy as np
    a = np.asarray(_sample(img), np.float64)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    rg, yb = r - g, 0.5 * (r + g) - b
    return float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean()))


def analyze(img: Image.Image, stats: dict = DEFAULT_STATS) -> dict:
    b, c = brightness(img), colorfulness(img)
    b50, c50 = round(stats["brightness_p50"]), round(stats["colorfulness_p50"])
    warnings, notes, ratio = [], [], None
    try:
        boxes = face.detect_faces(img)
        if boxes:
            ratio = boxes[0][3] / img.height
            if ratio < MIN_FACE_RATIO:
                warnings.append(f"الوجه صغير ({round(ratio * 100)}% من الارتفاع)، ما ينقرا بالموبايل. "
                                "الأحسن 20% أو أكثر.")
        else:
            notes.append("ماكو وجه بالغلاف، متأكد؟")
    except face.FaceUnavailable as e:
        notes.append(f"فحص الوجه ما اشتغل ({e})")
    if b < stats["brightness_p5"] and c < stats["colorfulness_p50"]:
        warnings.append(f"غامق وباهت: الإضاءة {round(b)} (المراجع {b50}). فتّح المشهد أو قوّي لون الشي البطل.")
    if c < stats["colorfulness_p10"]:
        warnings.append(f"الألوان باهتة: الحيوية {round(c)} (المراجع {c50}). ضيف لون قوي واحد.")
    notes.append(f"الإضاءة {round(b)} (المراجع {b50})، الحيوية {round(c)} (المراجع {c50})")
    return {"face_ratio": ratio, "brightness": b, "colorfulness": c, "warnings": warnings, "notes": notes}


def load_stats() -> dict:
    try:
        stats = json.loads(STATS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict(DEFAULT_STATS)
    if not isinstance(stats, dict) or set(stats) != set(DEFAULT_STATS):
        return dict(DEFAULT_STATS)
    return stats


def calibrate(folder: Path) -> dict:
    """يحسب أرقام المراجع من كل صور المجلد ويحفظها بـ STATS_FILE."""
    import numpy as np
    paths = sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not paths:
        raise ValueError(f"ماكو صور بالمجلد {folder}")
    bs, cs = [], []
    for p in paths:
        with Image.open(p) as im:
            bs.append(brightness(im))
            cs.append(colorfulness(im))
    stats = {"brightness_p5": round(float(np.percentile(bs, 5)), 1),
             "brightness_p50": round(float(np.percentile(bs, 50)), 1),
             "colorfulness_p10": round(float(np.percentile(cs, 10)), 1),
             "colorfulness_p50": round(float(np.percentile(cs, 50)), 1)}
    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATS_FILE.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats


def squint_sheet(paths: list) -> Image.Image:
    """لكل غلاف صف: صغير بحجم الموبايل، ومغبّش (اختبار التغبيش)، وأبيض وأسود (التباين)."""
    w = 3 * TILE[0] + 4 * GAP
    h = len(paths) * (TILE[1] + GAP) + GAP
    sheet = Image.new("RGB", (w, h), (40, 40, 40))
    for row, p in enumerate(paths):
        with Image.open(p) as im:
            small = ImageOps.fit(im.convert("RGB"), TILE, Image.LANCZOS)
        versions = (small, small.filter(ImageFilter.GaussianBlur(4)), ImageOps.grayscale(small).convert("RGB"))
        y = GAP + row * (TILE[1] + GAP)
        for col, v in enumerate(versions):
            sheet.paste(v, (GAP + col * (TILE[0] + GAP), y))
    return sheet


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يفحص الأغلفة قبل النشر")
    ap.add_argument("images", nargs="*")
    ap.add_argument("-o", "--out")
    ap.add_argument("--calibrate", metavar="DIR", help="يحسب أرقام المراجع من مجلد صور")
    args = ap.parse_args(argv)
    try:
        import numpy  # noqa: F401
    except ImportError:
        print(INSTALL_HINT)
        return 1
    if args.calibrate:
        try:
            stats = calibrate(Path(args.calibrate))
        except (OSError, ValueError, UnidentifiedImageError) as e:
            print(f"✗ خطأ: ما گدرت أعاير ({e})")
            return 1
        print(f"✓ انحفظت أرقام المراجع: {STATS_FILE} {stats}")
        return 0
    if not args.images or not args.out:
        print("✗ خطأ: انطيني صور الأغلفة و -o check.jpg")
        return 1
    if Path(args.out).suffix.lower() not in (".jpg", ".jpeg", ".png"):
        print("✗ خطأ: اسم ملف الفحص لازم ينتهي بـ .jpg أو .png")
        return 1
    stats = load_stats()
    for p in args.images:
        try:
            with Image.open(p) as im:
                im.load()
                r = analyze(im, stats)
        except (FileNotFoundError, UnidentifiedImageError, OSError):
            print(f"✗ خطأ: الصورة {p} مو موجودة أو خربانة")
            return 1
        print(f"— {Path(p).name}")
        for w in r["warnings"]:
            print(f"⚠️ {w}")
        if not r["warnings"]:
            print("✓ ماكو مشاكل")
        for n in r["notes"]:
            print(f"• {n}")
    out = Path(args.out)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        squint_sheet(args.images).save(out, quality=90)
    except OSError as e:
        print(f"✗ خطأ: ما گدرت أحفظ ورقة الفحص ({e})")
        return 1
    print(f"✓ انحفظ: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
