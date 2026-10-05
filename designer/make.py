"""من المشاهد للأغلفة الجاهزة بأمر واحد (بعد concepts.py والتوليد).

    python3 designer/make.py <المجلد>

لكل غلاف مختار بـ picked.json (حرفه A أو B أو C) لازم scene-<الحرف>.png بالمجلد. الأداة:
تكبّر لـ 4K، وتكتب spec-<الحرف>.json إذا ما موجود (الكتابة بخط البطاقة ومكانها)، وتركّب thumb-<الحرف>.jpg
ونسخة الموبايل، وتسوي compare.jpg، وتفحص كل غلاف. الطباعة مختصرة: سطر لكل غلاف.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402
import sheet  # noqa: E402
import upscale  # noqa: E402
from arabic import is_rtl  # noqa: E402

# مكان الكتابة (x، y) لكل منطقة بالمخطط، بنسب الغلاف
ZONE_XY = {"top_left": (0.27, 0.3), "top_right": (0.73, 0.3), "bottom_left": (0.38, 0.6)}
FINISH = {"contrast": 1.12, "saturation": 1.2, "sharpen": 0.5, "vignette": 0.35}
TEXT_STYLE = {"size": 0.2, "line_colors": ["#FFFFFF", ["#FFC400", "#FF6A00"]],
              "stroke": {"color": "#0B0B0F", "width": 0.1}, "shadow": True, "rotate": 5}


class MakeError(Exception):
    """خطأ بالمجلد، رسالته بالعربي."""


def auto_spec(card: dict) -> dict:
    """ملف طبقات 4K من بطاقة مختارة: المشهد + اللمسة الأخيرة، والكتابة (إذا اكو) بقالب brand.md."""
    label = card["label"]
    spec = {"size": "youtube4k", "background": {"image": f"scene-{label}-4k.png", **FINISH}, "layers": []}
    text = card.get("text")
    if text:
        x, y = ZONE_XY[card["layout"]["text_zone"]]
        latin_line = any(line.strip() and not is_rtl(line) for line in text.split("\n"))
        layer = {"type": "text", "text": text, "font": card.get("font", "Baloo"), "x": x, "y": y,
                 "line_spacing": 0.85 if latin_line else 0.62, **TEXT_STYLE}
        if card.get("font_latin"):
            layer["font_latin"] = card["font_latin"]
        spec["layers"].append(layer)
    return spec


def _load_picked(folder: Path) -> list:
    path = folder / "picked.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        picked = data["picked"]
        if not isinstance(picked, list) or not all(isinstance(c, dict) and "label" in c for c in picked):
            raise TypeError
        return picked
    except FileNotFoundError:
        raise MakeError(f"ماكو picked.json بـ {folder}. شغّل concepts.py أول.")
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError):
        raise MakeError(f"picked.json خربان بـ {folder}. أعد تشغيل concepts.py.")
    except OSError:
        raise MakeError(f"ما گدرت أقرا picked.json بـ {folder}.")


def _upscaled(folder: Path, label: str) -> Path:
    scene, big = folder / f"scene-{label}.png", folder / f"scene-{label}-4k.png"
    if big.exists() and big.stat().st_mtime >= scene.stat().st_mtime:
        return big
    with Image.open(scene) as img:
        img.load()
        result, _ = upscale.upscale(img)
    result.save(big)
    return big


def build_one(folder: Path, card: dict) -> list[str]:
    """يسوي غلاف وحد ويرجع تحذيرات المركّب."""
    label = card["label"]
    _upscaled(folder, label)
    spec_path = folder / f"spec-{label}.json"
    if not spec_path.exists():
        spec_path.write_text(json.dumps(auto_spec(card), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    spec = render.load_spec(spec_path)
    img, warnings = render.render(spec, folder)
    out = folder / f"thumb-{label}.jpg"
    render.save(img, out)
    render.save_mobile(img, out)
    return warnings


def _check(paths: list) -> dict:
    """تحذيرات فحص الغلاف لكل نسخة موبايل، أو {} إذا مكتبات الجودة ماكو."""
    try:
        import check
        stats = check.load_stats()
    except ImportError:
        return {}
    result = {}
    for p in paths:
        with Image.open(p) as im:
            im.load()
            result[p] = check.analyze(im, stats)["warnings"]
    return result


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
        if not (folder / f"scene-{label}.png").exists():
            lines.append(f"⚠️ {label}: المشهد scene-{label}.png ناقص، ما سويته.")
            continue
        try:
            warnings = build_one(folder, card)
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
    checked = {} if args.no_check else _check(mobiles)
    for i, label in enumerate(labels):
        extra = checked.get(mobiles[i], [])
        if extra:
            idx = next(n for n, line in enumerate(lines) if line.startswith(f"✓ {label}"))
            lines[idx] += "".join(f" ⚠️ {w}" for w in extra)
    sheet.make_sheet(mobiles, labels).save(folder / "compare.jpg", quality=90)
    print("\n".join(lines))
    print(f"✓ compare.jpg ({len(mobiles)} أغلفة)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
