"""المكبّر: يكبّر المشهد لـ 4K (3840×2160) مجاناً.

    python3 designer/upscale.py scene-A.png -o scene-A-4k.png [--strength 0.6] [--force-ai]

- صورة كبيرة (عرضها 2400 أو أكثر، مثل مشاهد Higgsfield): تكبير عادي + حدّة. البشرة تبقى طبيعية.
- صورة صغيرة (مثل صور Canva): موديل Real-ESRGAN الذكي، ياخذ منه التفاصيل الدقيقة بس،
  والألوان تبقى من الصورة الأصلية، وتأثيره ينزل للنص على الوجه.
"""
import argparse
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps, UnidentifiedImageError

sys.path.insert(0, str(Path(__file__).resolve().parent))
import face  # noqa: E402
import models  # noqa: E402

TARGET = (3840, 2160)
MIN_AI_WIDTH = 2400
DEFAULT_STRENGTH = 0.6
METHOD_NAMES = {"classic": "عادية", "ai": "ذكية", "fallback": "بديلة"}


def fit_16x9(img: Image.Image) -> Image.Image:
    """يقص 16:9 من نص الصورة بدون تكبير."""
    w, h = img.size
    if w * 9 > h * 16:
        cw, ch = int(h * 16 / 9), h
    else:
        cw, ch = w, int(w * 9 / 16)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    return img.crop((x0, y0, x0 + cw, y0 + ch))


def _edge_weights(n: int, ramp: int, open_start: bool, open_end: bool):
    """أوزان قطعة على محور واحد: الجهة الي تتداخل ويا قطعة ثانية تبدي بوزن صغير ويكبر تدريجياً،
    وجهة حافة الصورة وزنها 1 (ماكو قطعة ثانية تغطيها)."""
    import numpy as np
    w = np.ones(n, np.float32)
    r = min(ramp, n // 2)
    if r > 0:
        up = ((np.arange(r, dtype=np.float32) + 1) / (r + 1)) ** 2  # تربيعي: الحواف الخربانة تختفي حتى بالزوايا
        if open_start:
            w[:r] = up
        if open_end:
            w[n - r:] = np.minimum(w[n - r:], up[::-1])
    return w


def tile_apply(arr, fn, scale: int, tile: int = 256, overlap: int = 16):
    """يطبّق fn (تكبير ×scale) على المصفوفة قطعة قطعة. بمناطق التداخل، القطع تندمج بأوزان متدرجة،
    فأغلاط الموديل بحواف كل قطعة ما تطلع خطوط بالصورة."""
    import numpy as np
    H, W, C = arr.shape
    t = min(tile, H, W)
    stride = max(1, t - 2 * overlap)
    ramp = 2 * overlap * scale
    out = np.zeros((H * scale, W * scale, C), np.float32)
    weight = np.zeros((H * scale, W * scale, 1), np.float32)
    ys = sorted({min(y, H - t) for y in range(0, H, stride)})
    xs = sorted({min(x, W - t) for x in range(0, W, stride)})
    n = t * scale
    for y0 in ys:
        wy = _edge_weights(n, ramp, y0 > 0, y0 + t < H)
        for x0 in xs:
            wx = _edge_weights(n, ramp, x0 > 0, x0 + t < W)
            w = (wy[:, None] * wx[None, :])[..., None]
            r = fn(arr[y0:y0 + t, x0:x0 + t])
            out[y0 * scale:(y0 + t) * scale, x0 * scale:(x0 + t) * scale] += r * w
            weight[y0 * scale:(y0 + t) * scale, x0 * scale:(x0 + t) * scale] += w
    return out / weight


def classic_upscale(img: Image.Image, size=TARGET) -> Image.Image:
    big = ImageOps.fit(img.convert("RGB"), size, Image.LANCZOS)
    return big.filter(ImageFilter.UnsharpMask(radius=2.5, percent=60, threshold=2))


def detail_transfer(base: Image.Image, up: Image.Image, strength: float,
                    mask: Image.Image | None = None) -> Image.Image:
    """الألوان والإضاءة من base، والتفاصيل الدقيقة من up بنسبة strength (تنزل للنص جوه القناع)."""
    import numpy as np

    def arr(im):
        return np.asarray(im, np.float32)
    B, U = arr(base.convert("RGB")), arr(up.convert("RGB"))
    blur_b = arr(base.convert("RGB").filter(ImageFilter.GaussianBlur(3)))
    blur_u = arr(up.convert("RGB").filter(ImageFilter.GaussianBlur(3)))
    k = strength
    if mask is not None:
        k = strength * (1 - 0.5 * arr(mask.convert("L"))[..., None] / 255)
    out = B + k * ((U - blur_u) - (B - blur_b))
    return Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8))


def face_mask(img: Image.Image) -> Image.Image | None:
    """قناع أبيض ناعم على الوجوه، أو None إذا ماكو وجوه أو الكاشف ما اشتغل."""
    try:
        boxes = face.detect_faces(img)
    except Exception:  # FaceUnavailable أو خطأ داخلي من OpenCV: نكمّل بدون حماية الوجه، المهم الشغل ما يوقف
        return None
    if not boxes:
        return None
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    feather = 0.0
    for x, y, w, h in boxes:
        dx, dy = w * 0.15 / 2, h * 0.15 / 2
        d.ellipse((x - dx, y - dy, x + w + dx, y + h + dy), fill=255)
        feather = max(feather, 0.05 * h)
    return mask.filter(ImageFilter.GaussianBlur(feather))


def _onnx_model_fn():
    import numpy as np
    import onnxruntime as ort
    session = ort.InferenceSession(str(models.ensure_model("upscaler")), providers=["CPUExecutionProvider"])
    name = session.get_inputs()[0].name

    def run(tile):
        x = np.ascontiguousarray(tile.transpose(2, 0, 1)[None], np.float32)
        return session.run(None, {name: x})[0][0].transpose(1, 2, 0)
    return run


def ai_upscale(img: Image.Image, size=TARGET, strength=DEFAULT_STRENGTH, model_fn=None) -> Image.Image:
    import numpy as np
    run = model_fn or _onnx_model_fn()
    src = fit_16x9(img.convert("RGB"))
    big = tile_apply(np.asarray(src, np.float32) / 255, run, 4)
    up = ImageOps.fit(Image.fromarray((np.clip(big, 0, 1) * 255).round().astype(np.uint8)), size, Image.LANCZOS)
    base = ImageOps.fit(img.convert("RGB"), size, Image.LANCZOS)
    return detail_transfer(base, up, strength, face_mask(base))


def upscale(img: Image.Image, size=TARGET, strength=DEFAULT_STRENGTH,
            force_ai=False) -> tuple[Image.Image, str]:
    """يختار الطريقة حسب حجم الصورة، ويرجع (الصورة، الطريقة)."""
    img = img.convert("RGB")
    if img.width >= MIN_AI_WIDTH and not force_ai:
        return classic_upscale(img, size), "classic"
    try:
        return ai_upscale(img, size, strength), "ai"
    except Exception:  # أخطاء onnxruntime ما ترث RuntimeError؛ المكبّر ما يوقف الشغل أبداً (التصميم، القسم 7)
        return classic_upscale(img, size), "fallback"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يكبّر المشهد لـ 4K")
    ap.add_argument("image")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--strength", type=float, default=DEFAULT_STRENGTH)
    ap.add_argument("--force-ai", action="store_true", help="الموديل الذكي حتى للصور الكبيرة")
    args = ap.parse_args(argv)
    out = Path(args.out)
    if out.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        print("✗ خطأ: اسم الملف لازم ينتهي بـ .jpg أو .png")
        return 1
    try:
        img = Image.open(args.image)
        img.load()
    except (FileNotFoundError, UnidentifiedImageError, OSError):
        print(f"✗ خطأ: الصورة {args.image} مو موجودة أو خربانة")
        return 1
    start = time.time()
    result, method = upscale(img, strength=args.strength, force_ai=args.force_ai)
    if method == "fallback":
        print("⚠️ الموديل الذكي ما اشتغل، استخدمت التكبير العادي.")
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.suffix.lower() in (".jpg", ".jpeg"):
            result.save(out, quality=95)
        else:
            result.save(out)
    except OSError as e:
        print(f"✗ خطأ: ما گدرت أحفظ الصورة ({e})")
        return 1
    print(f"✓ انحفظ: {out} (الطريقة: {METHOD_NAMES[method]}، {time.time() - start:.0f} ثانية)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
