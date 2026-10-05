"""من المشاهد للأغلفة الجاهزة بأمر واحد (بعد concepts.py والتوليد).

    python3 designer/make.py <المجلد>

لكل غلاف مختار بـ picked.json (حرفه A أو B أو C) لازم scene-<الحرف>.png بالمجلد. الأداة:
تكبّر لـ 4K، وتكتب spec-<الحرف>.json إذا ما موجود (الكتابة بخط البطاقة ومكانها)، وتركّب thumb-<الحرف>.jpg
ونسخة الموبايل، وتسوي compare.jpg، وتفحص كل غلاف. الطباعة مختصرة: سطر لكل غلاف.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402
import sheet  # noqa: E402
import upscale  # noqa: E402
from arabic import is_rtl  # noqa: E402
from concepts import ZONE_BOX  # noqa: E402  نفس مناطق الكتابة الي بالمخطط

LABEL = re.compile(r"[A-D]")
MAX_SIZE, MIN_SIZE = 0.2, 0.08
FINISH = {"contrast": 1.12, "saturation": 1.2, "sharpen": 0.5, "vignette": 0.35}
TEXT_STYLE = {"size": 0.2, "line_colors": ["#FFFFFF", ["#FFC400", "#FF6A00"]],
              "stroke": {"color": "#0B0B0F", "width": 0.1}, "shadow": True, "rotate": 5}


class MakeError(Exception):
    """خطأ بالمجلد، رسالته بالعربي."""


MEASURE = (640, 360)  # القياس بنسخة صغيرة (كل الأرقام نسبية)، أسرع بهواية


def _ink(layer: dict) -> tuple:
    """حدود حبر الكتابة بنسب الغلاف (x0، y0، x1، y1)، ويا الميلان والظل.

    القياس بدون ميلان (الميلان على لوحة كبيرة بطيء)، وبعدين زوايا المستطيل تندار حسابياً حول مركزه
    (المركّب يدير حول نفس المركز)، فالنتيجة أكبر شوية من الحبر الحقيقي، يعني أأمن.
    """
    W, H = MEASURE
    box, _ = render._text_layer(Image.new("RGBA", MEASURE), dict(layer, shadow=False, rotate=0))
    x0, y0, x1, y1 = box
    if layer.get("shadow"):  # الظل: إزاحة 0.05 من حجم الخط وتغبيش 0.06 (شوف _text_layer)
        grow = 0.11 * layer.get("size", 0.14) * H
        x1, y1 = x1 + grow, y1 + grow
    a = math.radians(layer.get("rotate", 0))
    if a:
        cx, cy, hw, hh = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        rw = abs(hw * math.cos(a)) + abs(hh * math.sin(a))
        rh = abs(hw * math.sin(a)) + abs(hh * math.cos(a))
        x0, y0, x1, y1 = cx - rw, cy - rh, cx + rw, cy + rh
    return x0 / W, y0 / H, x1 / W, y1 / H


def _placed(layer: dict, zone: str) -> tuple[dict, bool]:
    """يوسّط حبر الكتابة بالمنطقة، ويرجع (الطبقة، تساع المنطقة وبعيدة عن زوايا يوتيوب؟)."""
    zx0, zy0, zx1, zy1 = ZONE_BOX[zone]
    for _ in range(2):  # الميلان والحد يزحزحون الحبر عن المركز
        x0, y0, x1, y1 = _ink(layer)
        layer = dict(layer, x=round(layer["x"] + (zx0 + zx1) / 2 - (x0 + x1) / 2, 4),
                     y=round(layer["y"] + (zy0 + zy1) / 2 - (y0 + y1) / 2, 4))
    x0, y0, x1, y1 = _ink(layer)
    tol = 0.005
    inside = x0 >= zx0 - tol and x1 <= zx1 + tol and y0 >= zy0 - tol and y1 <= zy1 + tol
    on_image = x0 >= 0 and y0 >= 0 and x1 <= 1 and y1 <= 1
    clear = all(x1 <= ux0 or x0 >= ux1 or y1 <= uy0 or y0 >= uy1
                for _, ux0, uy0, ux1, uy1 in render.UNSAFE["youtube"])
    return layer, inside and on_image and clear


def fit_text(layer: dict, zone: str) -> dict:
    """أكبر حجم (لحد 0.2) يخلي الكتابة داخل منطقتها بالمخطط وبعيدة عن زوايا يوتيوب، وبنص المنطقة."""
    zx0, zy0, zx1, zy1 = ZONE_BOX[zone]
    base = dict(layer, x=(zx0 + zx1) / 2, y=(zy0 + zy1) / 2)
    best, ok = _placed(dict(base, size=MAX_SIZE), zone)
    if ok:
        return best
    lo, hi = MIN_SIZE, MAX_SIZE
    best = _placed(dict(base, size=MIN_SIZE), zone)[0]
    for _ in range(7):  # بحث ثنائي على الحجم
        mid = round((lo + hi) / 2, 4)
        cand, ok = _placed(dict(base, size=mid), zone)
        if ok:
            best, lo = cand, mid
        else:
            hi = mid
    return best


def auto_spec(card: dict, scene: str | None = None) -> dict:
    """ملف طبقات 4K من بطاقة مختارة: المشهد + اللمسة الأخيرة، والكتابة (إذا اكو) بقالب brand.md،
    بحجم يساع منطقتها بالمخطط. source = رقم البطاقة، حتى ما ينستخدم لبطاقة ثانية بالغلط."""
    stem = Path(scene).stem if scene else f"scene-{card['label']}"
    spec = {"source": card.get("id"), "size": "youtube4k",
            "background": {"image": f"{stem}-4k.png", **FINISH}, "layers": []}
    text = card.get("text")
    if text:
        latin_line = any(line.strip() and not is_rtl(line) for line in text.split("\n"))
        layer = {"type": "text", "text": text, "font": card.get("font", "Baloo"),
                 "line_spacing": 0.85 if latin_line else 0.62, **TEXT_STYLE}
        if card.get("font_latin"):
            layer["font_latin"] = card["font_latin"]
        spec["layers"].append(fit_text(layer, card["layout"]["text_zone"]))
    return spec


def _load_picked(folder: Path) -> list:
    path = folder / "picked.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        picked = data["picked"]
        if not isinstance(picked, list) or not all(isinstance(c, dict) and "label" in c for c in picked):
            raise TypeError
    except FileNotFoundError:
        raise MakeError(f"ماكو picked.json بـ {folder}. شغّل concepts.py أول.")
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError):
        raise MakeError(f"picked.json خربان بـ {folder}. أعد تشغيل concepts.py.")
    except OSError:
        raise MakeError(f"ما گدرت أقرا picked.json بـ {folder}.")
    labels = [c["label"] for c in picked]
    if not 1 <= len(picked) <= 4 or len(set(labels)) != len(labels) or \
            not all(isinstance(lb, str) and LABEL.fullmatch(lb) for lb in labels):
        raise MakeError("picked.json لازم بيه 1-4 أغلفة بحروف A-D مختلفة. أعد تشغيل concepts.py.")
    return picked


def scene_for(folder: Path, card: dict) -> Path | None:
    """مشهد البطاقة: scene-<رقم البطاقة>.png أول (ما يتلخبط إذا الحروف تغيرت)، وبعدين scene-<الحرف>.png."""
    for name in (f"scene-{card.get('id')}.png", f"scene-{card['label']}.png"):
        if (folder / name).exists():
            return folder / name
    return None


def _good_4k(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            im.load()
            return im.size == upscale.TARGET
    except (OSError, UnidentifiedImageError):
        return False


def _upscaled(scene: Path) -> str:
    """يكبّر المشهد لـ 4K إذا النسخة الكبيرة ناقصة أو أقدم أو خربانة، ويرجع الطريقة."""
    big = scene.with_name(scene.stem + "-4k.png")
    if big.exists() and big.stat().st_mtime >= scene.stat().st_mtime and _good_4k(big):
        return "classic"
    with Image.open(scene) as img:
        img.load()
        result, method = upscale.upscale(img)
    result.save(big)
    return method


def build_one(folder: Path, card: dict, scene: Path) -> list[str]:
    """يسوي غلاف وحد ويرجع التحذيرات."""
    label = card["label"]
    warnings = []
    if _upscaled(scene) == "fallback":
        warnings.append("التكبير الذكي ما اشتغل، استخدمت العادي (الصورة أنعم شوية).")
    spec_path = folder / f"spec-{label}.json"
    if spec_path.exists():
        old = render.load_spec(spec_path)
        if isinstance(old, dict) and old.get("source") not in (None, card.get("id")):
            warnings.append(f"ملف الطبقات القديم كان لفكرة ثانية ({old.get('source')})، سويت واحد جديد.")
            spec_path.unlink()
    if not spec_path.exists():
        spec = auto_spec(card, scene.name)
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    spec = render.load_spec(spec_path)
    img, render_warnings = render.render(spec, folder)
    warnings += render_warnings
    out = folder / f"thumb-{label}.jpg"
    render.save(img, out)
    render.save_mobile(img, out)
    return warnings


def _check(paths: list) -> tuple[dict, str | None]:
    """تحذيرات فحص الغلاف لكل نسخة موبايل (وملاحظات الوجه)، وملاحظة إذا الفحص ما اشتغل."""
    try:
        import check
        stats = check.load_stats()
        result = {}
        for p in paths:
            with Image.open(p) as im:
                im.load()
                r = check.analyze(im, stats)
            result[p] = r["warnings"] + [n for n in r["notes"] if not n.startswith("الإضاءة")]
        return result, None
    except ImportError:
        return {}, "• فحص الغلاف ما اشتغل (مكتبات الجودة ناقصة: pip install -r designer/requirements-quality.txt)."


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يسوي الأغلفة الجاهزة من المشاهد")
    ap.add_argument("folder")
    ap.add_argument("--no-check", action="store_true", help="بدون فحص الغلاف (أسرع)")
    args = ap.parse_args(argv)
    folder = Path(args.folder)
    try:
        picked = _load_picked(folder)
    except MakeError as e:
        print(f"✗ خطأ: {e}")
        return 1
    lines, mobiles, labels = [], [], []
    for card in picked:
        label = card["label"]
        scene = scene_for(folder, card)
        if scene is None:
            lines.append(f"⚠️ {label}: المشهد scene-{card.get('id')}.png ناقص، ما سويته.")
            continue
        try:
            warnings = build_one(folder, card, scene)
        except render.SpecError as e:
            lines.append(f"✗ {label}: {e}")
            continue
        except (UnidentifiedImageError, OSError):
            lines.append(f"✗ {label}: المشهد خربان أو ما ينحفظ.")
            continue
        mobiles.append(folder / f"thumb-{label}-mobile.jpg")
        labels.append(label)
        lines.append(f"✓ {label}" + "".join(f" ⚠️ {w}" for w in warnings))
    if not mobiles:
        print("\n".join(lines))
        print("✗ خطأ: ولا غلاف انسوى.")
        return 1
    checked, note = ({}, None) if args.no_check else _check(mobiles)
    for i, label in enumerate(labels):
        extra = checked.get(mobiles[i], [])
        if extra:
            idx = next(n for n, line in enumerate(lines) if line.startswith(f"✓ {label}"))
            lines[idx] += "".join(f" ⚠️ {w}" for w in extra)
    if note:
        lines.append(note)
    try:
        sheet.make_sheet(mobiles, labels).save(folder / "compare.jpg", quality=90)
    except OSError:
        print("\n".join(lines))
        print("✗ خطأ: ما گدرت أحفظ compare.jpg.")
        return 1
    print("\n".join(lines))
    print(f"✓ compare.jpg ({len(mobiles)} أغلفة)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
