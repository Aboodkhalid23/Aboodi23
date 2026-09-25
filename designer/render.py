"""المركّب: يقرا ملف طبقات JSON ويطلع غلاف PNG أو JPG.

    python3 designer/render.py spec.json -o out.jpg [--guides]

كل المقاسات بالملف نسبية (من 0 لـ 1) حتى نفس الفكرة تتحول لمقاس ثاني.
المسارات النسبية تنحسب من مجلد ملف الطبقات، وإذا ما لگاها، من جذر الريبو.
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arabic import load_font, shape_word, visual_words  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = Path(__file__).resolve().parent / "fonts"
FONTS = {
    "Baloo": "BalooBhaijaan2-ExtraBold.ttf",
    "Rubik": "Rubik-Black.ttf",
    "Cairo": "Cairo-Black.ttf",
    "Lalezar": "Lalezar-Regular.ttf",
}
CANVAS = {"youtube": (1280, 720), "reels": (1080, 1920)}
# المناطق الي تغطيها واجهة التطبيق: (اسم، x0، y0، x1، y1) كنسب من العرض والارتفاع
UNSAFE = {
    "youtube": [
        ("زاوية مدة الفيديو", 0.80, 0.82, 1.0, 1.0),
        ("زاوية مدة الفيديو", 0.0, 0.82, 0.20, 1.0),
    ],
    "reels": [
        ("أعلى الشاشة", 0.0, 0.0, 1.0, 0.125),
        ("منطقة الكابشن", 0.0, 0.75, 1.0, 1.0),
        ("أزرار اليمين", 0.85, 0.0, 1.0, 1.0),
    ],
}
MAX_WORDS = 4
YOUTUBE_MAX_BYTES = 2 * 1024 * 1024
PUNCT = "؟?!.,،:؛\"'«»()"


class SpecError(ValueError):
    """خطأ بملف الطبقات، رسالته بالعربي."""


def load_spec(path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SpecError(f"ملف الطبقات مو موجود: {path}")
    except json.JSONDecodeError as e:
        raise SpecError(f"ملف الطبقات بيه غلط بالصيغة (سطر {e.lineno}): {path}")


def size_name(spec: dict):
    """اسم المقاس (youtube أو reels)، أو None إذا المقاس أرقام."""
    size = spec.get("size", "youtube")
    return size if isinstance(size, str) else None


def canvas_size(spec: dict) -> tuple[int, int]:
    size = spec.get("size", "youtube")
    if isinstance(size, str):
        if size not in CANVAS:
            raise SpecError(f"مقاس مو معروف: {size}. المسموح: {', '.join(CANVAS)}")
        return CANVAS[size]
    if isinstance(size, list) and len(size) == 2 and all(isinstance(v, int) and v > 0 for v in size):
        return size[0], size[1]
    raise SpecError("size لازم يكون youtube أو reels أو [عرض، ارتفاع]")


def resolve(src: str, base_dir: Path) -> Path:
    p = Path(src)
    for candidate in (p, base_dir / p, ROOT / p):
        if candidate.is_file():
            return candidate
    raise SpecError(f"الصورة مو موجودة: {src}")


def hex_rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    c = str(color).lstrip("#")
    try:
        return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), alpha
    except ValueError:
        raise SpecError(f"لون غلط: {color}. اكتبه مثل #FFD400")


def _background(bg: dict, size, base_dir: Path) -> Image.Image:
    w, h = size
    if "image" in bg:
        img = Image.open(resolve(bg["image"], base_dir)).convert("RGB")
        focus = tuple(bg.get("focus", [0.5, 0.5]))
        img = ImageOps.fit(img, size, Image.LANCZOS, centering=focus)
    elif "gradient" in bg:
        top, bottom = bg["gradient"]
        mask = Image.linear_gradient("L").resize(size)
        img = Image.composite(Image.new("RGB", size, hex_rgba(bottom)[:3]),
                              Image.new("RGB", size, hex_rgba(top)[:3]), mask)
    elif "color" in bg:
        img = Image.new("RGB", size, hex_rgba(bg["color"])[:3])
    else:
        raise SpecError("background لازم بيه image أو gradient أو color")
    if bg.get("blur"):
        img = img.filter(ImageFilter.GaussianBlur(bg["blur"] * h))
    if bg.get("darken"):
        img = ImageEnhance.Brightness(img).enhance(1 - bg["darken"])
    if bg.get("contrast"):
        img = ImageEnhance.Contrast(img).enhance(bg["contrast"])
    if bg.get("saturation"):
        img = ImageEnhance.Color(img).enhance(bg["saturation"])
    if bg.get("sharpen"):
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=int(120 * bg["sharpen"]), threshold=3))
    img = img.convert("RGBA")
    if bg.get("vignette"):
        mask = Image.radial_gradient("L").resize(size)
        mask = mask.point(lambda v: int(v * bg["vignette"]))
        img = Image.composite(Image.new("RGBA", size, (0, 0, 0, 255)), img, mask)
    return img


def _silhouette(alpha: Image.Image, grow: float, color: str) -> Image.Image:
    """حد ملون حول الشخص: نكبّر شكله بمقدار grow بكسل ونلونه."""
    spread = alpha.filter(ImageFilter.GaussianBlur(grow)).point(lambda a: 255 if a > 8 else 0)
    layer = Image.new("RGBA", alpha.size, hex_rgba(color))
    layer.putalpha(spread)
    return layer


def _image_layer(canvas: Image.Image, layer: dict, base_dir: Path) -> list[str]:
    W, H = canvas.size
    warnings = []
    img = Image.open(resolve(layer["src"], base_dir)).convert("RGBA")
    if img.getchannel("A").getextrema()[0] == 255 and ("outline" in layer or "glow" in layer):
        warnings.append(f"الصورة {layer['src']} ما بيها شفافية، فالحد راح يطلع مربع. شيل خلفيتها أول.")
    if "h" in layer:
        th = max(1, int(layer["h"] * H))
        img = img.resize((max(1, int(img.width * th / img.height)), th), Image.LANCZOS)
    elif "w" in layer:
        tw = max(1, int(layer["w"] * W))
        img = img.resize((tw, max(1, int(img.height * tw / img.width))), Image.LANCZOS)
    if layer.get("flip"):
        img = ImageOps.mirror(img)
    pad = int(0.05 * H)
    padded = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad))
    padded.paste(img, (pad, pad), img)
    alpha = padded.getchannel("A")
    out = Image.new("RGBA", padded.size)
    if "glow" in layer:
        g = layer["glow"]
        glow = alpha.filter(ImageFilter.GaussianBlur(g.get("radius", 0.02) * H))
        glow_layer = Image.new("RGBA", padded.size, hex_rgba(g["color"]))
        glow_layer.putalpha(glow)
        out = Image.alpha_composite(out, glow_layer)
    if "outline" in layer:
        o = layer["outline"]
        out = Image.alpha_composite(out, _silhouette(alpha, o.get("width", 0.012) * H, o["color"]))
    out = Image.alpha_composite(out, padded)
    x, y = layer.get("x", 0.5) * W, layer.get("y", 1.0) * H
    anchor = layer.get("anchor", "bottom-center")
    left = int(x - out.width / 2)
    if anchor == "bottom-center":
        top = int(y - img.height - pad)
    elif anchor == "center":
        top = int(y - out.height / 2)
    else:
        raise SpecError(f"anchor للصورة مو معروف: {anchor}. المسموح: bottom-center، center")
    full = Image.new("RGBA", canvas.size)
    full.paste(out, (left, top), out)
    canvas.alpha_composite(full)
    return warnings


def _layout_text(layer: dict, W: int, H: int):
    """يرجع الخط وحجمه ومكان كل كلمة: [(x، y، النص، معاملات، اللون، رقم السطر)].

    اللون نص مثل "#FFFFFF"، أو تدرج عمودي [لون فوق، لون جوه].
    """
    font_name = layer.get("font", "Baloo")
    if font_name not in FONTS:
        raise SpecError(f"خط مو معروف: {font_name}. المتوفر: {', '.join(FONTS)}")
    px = max(8, int(layer.get("size", 0.14) * H))
    font = load_font(FONTS_DIR / FONTS[font_name], px)
    ascent, descent = font.getmetrics()
    line_h = int((ascent + descent) * layer.get("line_spacing", 0.95))
    space = font.getlength(" ")
    color = layer.get("color", "#FFFFFF")
    line_colors = layer.get("line_colors", [])
    hl = layer.get("highlight", {})
    hl_words = {w.strip(PUNCT) for w in hl.get("words", [])}
    if "word" in hl:
        hl_words.add(hl["word"].strip(PUNCT))
    lines = []
    for line in layer["text"].split("\n"):
        words = []
        for word in visual_words(line):
            text, kw = shape_word(word)
            words.append((word, text, kw, font.getlength(text, **kw)))
        width = sum(w[3] for w in words) + space * max(0, len(words) - 1)
        lines.append((words, width))
    x, y = layer.get("x", 0.5) * W, layer.get("y", 0.5) * H
    align = layer.get("align", "center")
    top = y - line_h * len(lines) / 2
    placed = []
    for i, (words, width) in enumerate(lines):
        if align == "center":
            lx = x - width / 2
        elif align == "right":
            lx = x - width
        elif align == "left":
            lx = x
        else:
            raise SpecError(f"align مو معروف: {align}. المسموح: center، right، left")
        ly = top + i * line_h
        base = line_colors[i] if i < len(line_colors) else color
        for word, text, kw, wlen in words:
            fill = hl.get("color", "#FFD400") if word.strip(PUNCT) in hl_words else base
            placed.append((lx, ly, text, kw, fill, i))
            lx += wlen + space
    return font, px, placed


def _fill_image(fill, y0: float, y1: float, size) -> Image.Image:
    """صورة بحجم الغلاف: لون واحد، أو تدرج عمودي من y0 لـ y1."""
    W, H = size
    if isinstance(fill, str):
        return Image.new("RGBA", size, hex_rgba(fill))
    if not (isinstance(fill, list) and len(fill) == 2):
        raise SpecError(f"لون الكتابة لازم لون واحد أو [لون فوق، لون جوه]: {fill}")
    top, bottom = hex_rgba(fill[0]), hex_rgba(fill[1])
    y0 = max(0, min(H - 1, int(y0)))
    y1 = max(y0 + 1, min(H, int(y1)))
    col = Image.new("RGBA", (1, H), bottom)
    if y0 > 0:
        col.paste(top, (0, 0, 1, y0))
    mask = Image.linear_gradient("L").resize((1, y1 - y0))
    col.paste(Image.composite(Image.new("RGBA", (1, y1 - y0), bottom),
                              Image.new("RGBA", (1, y1 - y0), top), mask), (0, y0))
    return col.resize(size, Image.NEAREST)


def _paper(target: Image.Image, box, color: str, seed: str) -> None:
    """رقعة ورق ممزق الأطراف خلف الكتابة، مع ظل خفيف."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    jit = (y1 - y0) * 0.05
    step = max(8.0, (x1 - x0) / 20)
    pts = []
    for ax, ay, bx, by in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        n = max(2, int(math.hypot(bx - ax, by - ay) / step))
        for i in range(n):
            t = i / n
            pts.append((ax + (bx - ax) * t + rnd.uniform(-jit, jit), ay + (by - ay) * t + rnd.uniform(-jit, jit)))
    mask = Image.new("L", target.size)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    shadow_mask = Image.new("L", target.size)
    shadow_mask.paste(mask, (int(jit), int(jit)))
    shadow = Image.new("RGBA", target.size, (0, 0, 0, 0))
    shadow.putalpha(shadow_mask.point(lambda a: a * 150 // 255).filter(ImageFilter.GaussianBlur(max(1.0, jit))))
    target.alpha_composite(shadow)
    paper = Image.blend(Image.new("RGB", target.size, hex_rgba(color)[:3]),
                        Image.effect_noise(target.size, 60).convert("RGB"), 0.10).convert("RGBA")
    paper.putalpha(mask)
    target.alpha_composite(paper)


def _text_layer(canvas: Image.Image, layer: dict) -> tuple[int, int, int, int]:
    """يرسم الكتابة (مع الظل والصندوق والميلان) ويرجع حدود الحبر الحقيقي بالبكسل (x0، y0، x1، y1).

    الرسم يصير على لوحة أوسع من الغلاف بهامش M، حتى الحدود تنحسب صح
    حتى لو الكتابة طالعة برا الصورة.
    """
    W, H = canvas.size
    M = int(0.25 * max(W, H))
    size = (W + 2 * M, H + 2 * M)
    font, px, placed = _layout_text(layer, W, H)
    placed = [(x + M, y + M, t, kw, fill, line) for x, y, t, kw, fill, line in placed]
    stroke = layer.get("stroke")
    sw = int(stroke.get("width", 0.08) * px) if stroke else 0
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    boxes = [probe.textbbox((p[0], p[1]), p[2], font=font, anchor="la", stroke_width=sw, **p[3]) for p in placed]
    bbox = (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))
    line_span = {}
    for b, p in zip(boxes, placed):
        y0, y1 = line_span.get(p[5], (b[1], b[3]))
        line_span[p[5]] = (min(y0, b[1]), max(y1, b[3]))
    out = Image.new("RGBA", size)
    if layer.get("shadow"):
        shadow = Image.new("RGBA", size)
        d = ImageDraw.Draw(shadow)
        off = 0.05 * px
        for x, y, t, kw, *_ in placed:
            d.text((x + off, y + off), t, font=font, anchor="la", fill=(0, 0, 0, 200),
                   stroke_width=sw, stroke_fill=(0, 0, 0, 200), **kw)
        out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(0.06 * px)))
    if "box" in layer:
        b = layer["box"]
        pad = int(b.get("pad", 0.18) * px)
        box = (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad)
        if b.get("style") == "paper":
            _paper(out, box, b.get("color", "#E9E1D2"), layer["text"])
        else:
            ImageDraw.Draw(out).rounded_rectangle(
                box, radius=int(b.get("radius", 0.1) * px), fill=hex_rgba(b.get("color", "#E50914")))
    if stroke:
        d = ImageDraw.Draw(out)
        sc = hex_rgba(stroke["color"])
        for x, y, t, kw, *_ in placed:
            d.text((x, y), t, font=font, anchor="la", fill=sc, stroke_width=sw, stroke_fill=sc, **kw)
    for x, y, t, kw, fill, line in placed:
        mask = Image.new("L", size)
        ImageDraw.Draw(mask).text((x, y), t, font=font, anchor="la", fill=255, **kw)
        out.paste(_fill_image(fill, *line_span[line], size), (0, 0), mask)
    angle = layer.get("rotate", 0)
    if angle:
        center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
        out = out.rotate(angle, resample=Image.BICUBIC, center=center)
    ink = out.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
    canvas.alpha_composite(out.crop((M, M, M + W, M + H)))
    if ink is None:
        return (0, 0, 0, 0)
    return (ink[0] - M, ink[1] - M, ink[2] - M, ink[3] - M)


def _shape_layer(canvas: Image.Image, layer: dict) -> None:
    W, H = canvas.size
    d = ImageDraw.Draw(canvas)
    color = hex_rgba(layer.get("color", "#E50914"))
    width = max(1, int(layer.get("width", 0.02) * H))
    kind = layer.get("shape")
    if kind == "arrow":
        (x0, y0), (x1, y1) = [(p[0] * W, p[1] * H) for p in (layer["from"], layer["to"])]
        ang = math.atan2(y1 - y0, x1 - x0)
        head = width * 3.2
        tip = (x1, y1)
        left = (x1 - head * math.cos(ang - 0.5), y1 - head * math.sin(ang - 0.5))
        right = (x1 - head * math.cos(ang + 0.5), y1 - head * math.sin(ang + 0.5))
        base = (x1 - head * 0.8 * math.cos(ang), y1 - head * 0.8 * math.sin(ang))
        border = (0, 0, 0, 255)
        d.line([(x0, y0), base], fill=border, width=width + max(4, width // 2))
        d.polygon([tip, left, right], fill=border, outline=border, width=max(4, width // 3))
        d.line([(x0, y0), base], fill=color, width=width)
        d.polygon([tip, left, right], fill=color)
    elif kind == "circle":
        cx, cy = layer["center"][0] * W, layer["center"][1] * H
        r = layer.get("r", 0.15) * H
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=width)
    elif kind == "rect":
        x0, y0, x1, y1 = layer["box"]
        box = (x0 * W, y0 * H, x1 * W, y1 * H)
        radius = int(layer.get("radius", 0) * H)
        if layer.get("fill"):
            d.rounded_rectangle(box, radius=radius, fill=color)
        else:
            d.rounded_rectangle(box, radius=radius, outline=color, width=width)
    else:
        raise SpecError(f"شكل مو معروف: {kind}. المسموح: arrow، circle، rect")


def _overlaps(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def render(spec: dict, base_dir) -> tuple[Image.Image, list[str]]:
    """يرسم الغلاف ويرجع الصورة وقائمة تحذيرات بالعربي."""
    size = canvas_size(spec)
    if "background" not in spec:
        raise SpecError("ملف الطبقات ناقصه background")
    base_dir = Path(base_dir)
    canvas = _background(spec["background"], size, base_dir)
    W, H = size
    zones = UNSAFE.get(size_name(spec), [])
    warnings, words = [], 0
    for i, layer in enumerate(spec.get("layers", []), 1):
        kind = layer.get("type")
        if kind == "image":
            warnings += _image_layer(canvas, layer, base_dir)
        elif kind == "text":
            if not str(layer.get("text", "")).strip():
                raise SpecError(f"الطبقة {i}: الكتابة فارغة")
            bbox = _text_layer(canvas, layer)
            words += len(layer["text"].split())
            for name, x0, y0, x1, y1 in zones:
                if _overlaps(bbox, (x0 * W, y0 * H, x1 * W, y1 * H)):
                    warnings.append(f"الكتابة \"{layer['text']}\" داخلة بمنطقة مغطاة ({name}).")
            if bbox[0] < 0 or bbox[1] < 0 or bbox[2] > W or bbox[3] > H:
                warnings.append(f"الكتابة \"{layer['text']}\" طالعة برا حدود الصورة.")
        elif kind == "shape":
            _shape_layer(canvas, layer)
        else:
            raise SpecError(f"الطبقة {i}: نوع مو معروف: {kind}. المسموح: image، text، shape")
    if words > MAX_WORDS:
        warnings.append(f"الكتابة {words} كلمات، والحد {MAX_WORDS}.")
    return canvas, warnings


def draw_guides(img: Image.Image, name) -> Image.Image:
    """يلوّن المناطق المغطاة بالأحمر، للفحص الداخلي بس. الإطار الأزرق = قص شبكة إنستگرام."""
    out = img.copy()
    overlay = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(overlay)
    W, H = img.size
    for _, x0, y0, x1, y1 in UNSAFE.get(name, []):
        d.rectangle((x0 * W, y0 * H, x1 * W, y1 * H), fill=(255, 0, 0, 90), outline=(255, 0, 0, 255), width=3)
    if name == "reels":
        d.rectangle((0, 0.125 * H, W, 0.875 * H), outline=(0, 200, 255, 255), width=4)
    out.alpha_composite(overlay)
    return out


def save(img: Image.Image, out: Path) -> None:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() in (".jpg", ".jpeg"):
        img.convert("RGB").save(out, quality=92, optimize=True)
    else:
        img.save(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يركّب غلاف من ملف طبقات JSON")
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--guides", action="store_true", help="يرسم مناطق الأمان للفحص")
    args = ap.parse_args(argv)
    try:
        spec = load_spec(args.spec)
        img, warnings = render(spec, Path(args.spec).parent)
    except SpecError as e:
        print(f"✗ خطأ: {e}")
        return 1
    if args.guides:
        img = draw_guides(img, size_name(spec))
    out = Path(args.out)
    save(img, out)
    if size_name(spec) == "youtube" and out.stat().st_size > YOUTUBE_MAX_BYTES:
        warnings.append("حجم الملف أكبر من 2MB ويوتيوب ما يقبله. احفظه .jpg")
    for w in warnings:
        print(f"⚠️ {w}")
    print(f"✓ انحفظ: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
