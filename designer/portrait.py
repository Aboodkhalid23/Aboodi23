"""صورة شخصية احترافية: يقص المقدم من خلفيته، ويضوّي وجهه، ويحطه على خلفية استوديو (أبيض، رصاصي، أسود).
الوجه نفسه ما يتغير (ماكو ذكاء اصطناعي يرسمه من جديد)، بس الإضاءة والخلفية.

    python3 designer/portrait.py <الصورة> -o <مجلد>

يطلع لكل خلفية: نسخة 4:5 (1080×1350) للبوستات والخلفيات، ونسخة مربعة (1080×1080) لصورة الحساب،
وورقة sheet.jpg بيها كلشي ويا معاينة الدائرة (مثل ما تبين بإنستگرام ويوتيوب).
الصور بيها وجهه: تنحفظ بمجلد يتجاهله git (مثل designer/faces/) وما تنرفع للريبو العام.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

BACKGROUNDS = {
    # الاسم: (لون النص، لون الأطراف، ظل؟)
    "white": ("#FFFFFF", "#DADBDC", True),
    "gray": ("#A4A7AA", "#4B4E52", True),
    "black": ("#3A3D41", "#08090A", False),
}
NAMES = {"white": "أبيض", "gray": "رصاصي", "black": "أسود"}


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cutout(img: Image.Image) -> Image.Image:
    """قناع الشخص (أبيض = الشخص)، بموديل مجاني يشتغل على الجهاز."""
    from rembg import new_session, remove
    session = new_session("isnet-general-use")
    return remove(img, session=session, only_mask=True, post_process_mask=True)


def relight(img: Image.Image, mask: Image.Image) -> Image.Image:
    """يضوّي الصورة (يرفع الغامق أكثر من الفاتح)، ويخفف الحمار الي ضرب على الوجه من الخلفية الحمرة."""
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    m = np.asarray(mask, np.float32) / 255
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])
    person = lum[m > 0.5]
    mean = float(person.mean()) if person.size else 0.35
    gain = np.clip(0.30 / max(mean, 0.05), 1.0, 1.6)          # التعريض: نوصل متوسط الشخص لـ 0.30
    a = 1 - (1 - np.clip(a * gain, 0, 1)) ** 1.15              # منحنى ناعم يحمي الفاتح من الاحتراق
    shadows = (1 - lum[..., None]) ** 3 * 0.05                 # رفع الظلال شوية
    a = np.clip(a + shadows, 0, 1)
    a[..., 0] *= 0.98                                          # تخفيف الحمار شوية بس
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def despill(img: Image.Image, mask: Image.Image) -> Image.Image:
    """أطراف الشخص (الشعر والكتاف) تاخذ لون أحمر من الخلفية القديمة: نشيل التشبع منها."""
    edge = mask.filter(ImageFilter.MaxFilter(9))
    inner = mask.filter(ImageFilter.MinFilter(21))
    band = Image.fromarray(np.clip(np.asarray(edge, np.int16) - np.asarray(inner, np.int16), 0, 255).astype(np.uint8))
    band = band.filter(ImageFilter.GaussianBlur(6))
    gray = ImageOps.grayscale(img).convert("RGB")
    return Image.composite(Image.blend(img, gray, 0.4), img, band)


def backdrop(size, center, edge):
    """خلفية استوديو: ضو بالنص وتغميق ناعم للأطراف."""
    W, H = size
    g = Image.radial_gradient("L").resize((int(W * 1.6), int(H * 1.6)))
    g = g.crop((int(W * 0.3), int(H * 0.15), int(W * 0.3) + W, int(H * 0.15) + H))
    return Image.composite(Image.new("RGB", size, rgb(edge)), Image.new("RGB", size, rgb(center)), g)


def place(subject: Image.Image, mask: Image.Image, size, bg_key):
    center, edge, shadow = BACKGROUNDS[bg_key]
    W, H = size
    canvas = backdrop(size, center, edge)
    box = mask.getbbox()
    subj = subject.crop(box)
    m = mask.crop(box)
    scale = min(H * 0.96 / subj.height, W * 1.05 / subj.width)
    sw, sh = int(subj.width * scale), int(subj.height * scale)
    subj = subj.resize((sw, sh), Image.LANCZOS)
    m = m.resize((sw, sh), Image.LANCZOS)
    x, y = (W - sw) // 2, H - sh
    if shadow:  # ظل ناعم ورا الشخص (يعطي عمق مثل الاستوديو)
        sh_mask = Image.new("L", size)
        sh_mask.paste(m.point(lambda v: v * 0.35), (x + int(W * 0.03), y + int(H * 0.01)))
        sh_mask = sh_mask.filter(ImageFilter.GaussianBlur(W * 0.025))
        canvas = Image.composite(Image.new("RGB", size, (0, 0, 0)), canvas, sh_mask)
    canvas.paste(subj, (x, y), m)
    return canvas


def avatar(tall, key):
    """صورة الحساب: الوجه والكتاف كبار بالدائرة (قص مربع من فوق، حول الراس)."""
    W, H = tall.size
    side = int(H * 0.58)
    x0 = int(W * 0.5 - side * 0.5)
    return tall.crop((x0, 0, x0 + side, side)).resize((1080, 1080), Image.LANCZOS)


def circle_preview(img, d=300):
    sq = ImageOps.fit(img, (d, d))
    out = Image.new("RGB", (d, d), (30, 31, 33))
    m = Image.new("L", (d, d))
    ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=255)
    out.paste(sq, (0, 0), m)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="صورة شخصية احترافية بخلفية استوديو")
    ap.add_argument("image")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        src = Image.open(args.image)
        src = ImageOps.exif_transpose(src).convert("RGB")
    except (OSError, ValueError):
        print(f"✗ خطأ: الصورة {args.image} مو موجودة أو خربانة")
        return 1
    mask = cutout(src)
    lit = despill(relight(src, mask), mask)
    tiles = []
    for key in BACKGROUNDS:
        tall = place(lit, mask, (1080, 1350), key)
        square = avatar(tall, key)
        tall.save(out / f"portrait-{key}.jpg", quality=95)
        square.save(out / f"avatar-{key}.jpg", quality=95)
        tiles.append((key, tall, square))
    tw, th = 540, 675
    sheet = Image.new("RGB", (3 * tw + 80, th + 380), (30, 31, 33))
    for i, (key, tall, square) in enumerate(tiles):
        x = 20 + i * (tw + 20)
        sheet.paste(tall.resize((tw, th), Image.LANCZOS), (x, 20))
        sheet.paste(circle_preview(square), (x + (tw - 300) // 2, th + 50))
    sheet.save(out / "sheet.jpg", quality=92)
    print(f"✓ انسوت 3 صور (أبيض، رصاصي، أسود) بـ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
