"""Motion graphics for the archive look, drawn frame by frame (owner, 2026-10-29: "موشن جرافك فاشل… ماكو ولا موشن
جرافك"). What his references do between the photos (Omar Abu Al-Roub's channel system, editor/styles/channel-system.md,
and the reels he sent):
  headline  a newspaper cutting on cream paper; the key line is struck with a yellow marker, right to left, while
            the camera creeps in on it
  person    the photo in a coloured circle, the name written in big letters right to left, the role on a torn strip
  number    a year or a figure filling the screen, counting up to its value, a short line under it
  map       the world, the camera flies to the countries, they light up, a route draws itself between them
  text      a big sentence on black, one word after the other (a question, a quote)
Each takes the shot dict and a frame count, and yields RGB frames (numpy) at 1920x1080; Film adds grain on top.
"""
import json
import math
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

W, H = 1920, 1080
FONTS = Path(__file__).resolve().parent.parent / "fonts"
ATLAS = Path(__file__).resolve().parent.parent / "remotion" / "node_modules" / "world-atlas" / "countries-110m.json"
CREAM, INK, MARKER = (239, 232, 216), (24, 22, 20), (255, 214, 10)
RED, GOLD, MAROON = (196, 56, 46), (226, 177, 62), (122, 31, 43)
AR = {"direction": "rtl", "language": "ar"}


def _font(name: str, size: int):
    from PIL import ImageFont
    return ImageFont.truetype(str(FONTS / name), size, layout_engine=ImageFont.Layout.RAQM)


def ease(t: float) -> float:
    return 1 - (1 - min(max(t, 0.0), 1.0)) ** 3


def back(t: float) -> float:   # overshoots a little, then settles (a card that lands)
    t = min(max(t, 0.0), 1.0)
    c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def dark(seed: int = 5) -> Image.Image:
    rng = np.random.default_rng(seed)
    base = np.full((H, W, 3), (20, 18, 17), np.float32) + rng.normal(0, 4, (H, W, 1))
    yy, xx = np.mgrid[0:H, 0:W]
    glow = np.exp(-(((xx - W * 0.5) / (W * 0.55)) ** 2 + ((yy - H * 0.45) / (H * 0.6)) ** 2))[..., None] * 22
    return Image.fromarray(np.clip(base + glow, 0, 255).astype(np.uint8))


def camera(img: Image.Image, z: float, cx: float, cy: float) -> Image.Image:
    """The frame seen through a camera at zoom z (1 = all of it) centred on (cx, cy) in the image."""
    cw, ch = img.width / z, img.height / z
    x = min(max(cx - cw / 2, 0), img.width - cw)
    y = min(max(cy - ch / 2, 0), img.height - ch)
    return img.transform((W, H), Image.EXTENT, (x, y, x + cw, y + ch), Image.BILINEAR)


def wrap(text: str, font, width: int, gap: str = " ") -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        t = (cur + gap + w).strip()
        if cur and font.getlength(t, **AR) > width:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + ([cur] if cur else [])


# ---------- headline: a newspaper cutting, the key line marked ----------

def headline(shot: dict, n: int, fps: float):
    src = shot.get("source") or "أرشيف"
    # Amiri's space is narrow and its «ر» swings under the next word: doubled spaces read as a newspaper line
    head = " ".join((shot.get("headline") or shot.get("word") or "").split()).replace(" ", "  ")
    mark = " ".join((shot.get("highlight") or "").split()).replace(" ", "  ")
    f_src, f_head, f_body = _font("Amiri-Bold.ttf", 54), _font("Amiri-Bold.ttf", 84), _font("Amiri-Regular.ttf", 34)
    pw = 1360
    lines = wrap(head, f_head, pw - 160, gap="  ")
    lh = 118
    ph = 210 + lh * len(lines) + 190
    rng = np.random.default_rng(len(head))
    paper = Image.fromarray(np.clip(np.full((ph, pw, 3), CREAM, np.float32) + rng.normal(0, 5, (ph, pw, 1)), 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(paper)
    d.text((pw // 2, 70), src, font=f_src, fill=INK, anchor="mm", **AR)
    d.line((80, 120, pw - 80, 120), fill=INK, width=3)
    d.line((80, 128, pw - 80, 128), fill=INK, width=1)
    top = 170
    marks = []   # (x0, y0, x1, y1) of the marked words, right to left order
    for k, line in enumerate(lines):
        y = top + k * lh
        xr = pw - 80
        if mark and mark in line:
            # measured on the ink of the line's own beginning, drawn the same way (right-aligned): an advance
            # width drops the trailing space and put the marker a letter off (seen 2026-10-29)
            pre = line[: line.index(mark)].rstrip()
            left = f_head.getbbox(line[: line.index(mark) + len(mark)], anchor="ra", **AR)[0]
            right = f_head.getbbox(pre, anchor="ra", **AR)[0] - 8 if pre else 0
            marks.append((xr + left - 12, y + 14, xr + right + 6, y + lh - 8))
        d.text((xr, y), line, font=f_head, fill=INK, anchor="ra", **AR)
    if mark and not marks and lines:   # the marked words span lines: mark the last line
        y = top + (len(lines) - 1) * lh
        marks.append((pw - 80 - f_head.getlength(lines[-1], **AR) - 10, y + 14, pw - 70, y + lh - 8))
    body_y = top + lh * len(lines) + 30
    for k in range(3):   # a few grey lines of "text" under the headline
        d.line((80, body_y + k * 46, pw - 80 - (k == 2) * 420, body_y + k * 46), fill=(150, 144, 132), width=10)
    if shot.get("date"):
        d.text((80, 70), str(shot["date"]), font=f_body, fill=(90, 86, 80), anchor="lm", **AR)
    clean = paper.copy()
    angle = -1.6
    scene_bg = dark(3)
    px, py = (W - pw) // 2, max(40, (H - ph) // 2)
    focus = marks[0] if marks else (pw * 0.3, top, pw * 0.7, top + lh)
    fx, fy = px + (focus[0] + focus[2]) / 2, py + (focus[1] + focus[3]) / 2
    rot0 = clean.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC)
    shadow = Image.new("RGBA", rot0.size, (0, 0, 0, 0))
    shadow.putalpha(rot0.getchannel("A").point(lambda a: int(a * 0.6)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    last = (None, rot0)   # the paper is turned again only while the marker moves
    for i in range(n):
        t = i / fps
        prog = round(ease((t - 0.25) / 0.55), 3)
        if prog != last[0]:
            p = clean
            if prog > 0:
                layer = Image.new("RGBA", clean.size, (0, 0, 0, 0))
                ld = ImageDraw.Draw(layer)
                for x0, y0, x1, y1 in marks:   # the marker runs right to left
                    ld.rectangle((x1 - (x1 - x0) * prog, y0, x1, y1), fill=MARKER + (150,))
                p = _multiply(clean, layer)
            last = (prog, p.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC) if prog > 0 else rot0)
        rot = last[1]
        scene = scene_bg.copy()
        land = back(t / 0.35)
        y = py + int((1 - land) * 60)
        scene.paste(shadow, (px + 16, y + 24), shadow)
        scene.paste(rot, (px, y), rot)
        z = 1.0 + 0.32 * ease(t / max(0.5, n / fps))   # creeps in on the marked line
        yield np.asarray(camera(scene, z, W / 2 + (fx - W / 2) * min(1, z - 1) * 2.4, H / 2 + (fy - H / 2) * min(1, z - 1) * 2.4))


def _multiply(img: Image.Image, layer: Image.Image) -> Image.Image:
    """A highlighter: the ink stays black under the colour (multiply), the paper turns yellow."""
    a = np.asarray(layer, np.float32)
    base = np.asarray(img, np.float32)
    alpha = a[..., 3:4] / 255
    mult = base * (a[..., :3] / 255)
    return Image.fromarray(np.clip(base * (1 - alpha) + mult * alpha, 0, 255).astype(np.uint8))


# ---------- person: photo in a circle, the name written big ----------

def _face_box(img: Image.Image):
    try:
        import cv2
        from .face import face_detector
        g = np.asarray(img.convert("L"))
        faces = face_detector().detectMultiScale(g, 1.1, 5, minSize=(max(40, g.shape[1] // 12),) * 2)
        if len(faces):
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            return x + w / 2, y + h / 2, w
    except Exception:   # noqa: BLE001 — no detector: the top middle of the picture
        pass
    return img.width / 2, img.height * 0.38, img.width * 0.35


def person(img: Image.Image, shot: dict, n: int, fps: float, look):
    name = shot.get("label") or shot.get("name") or ""
    role = shot.get("role") or ""
    colour = {"red": RED, "gold": GOLD}.get(shot.get("colour"), MAROON)
    d = 600
    cx, cy, fw = _face_box(img)
    side = max(fw * 3.0, min(img.size) * 0.5)
    crop = img.crop((cx - side / 2, cy - side * 0.45, cx + side / 2, cy + side * 0.55))
    face = look(crop).resize((d - 40, d - 40), Image.LANCZOS)
    mask = Image.new("L", face.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, face.width - 1, face.height - 1), fill=255)
    f_name, f_role = _font("Alexandria-ExtraBold.ttf", 132), _font("Amiri-Bold.ttf", 52)
    nb = f_name.getbbox(name, **AR)
    name_img = Image.new("RGBA", (nb[2] - nb[0] + 40, nb[3] - nb[1] + 40), (0, 0, 0, 0))
    ImageDraw.Draw(name_img).text((20 - nb[0], 20 - nb[1]), name, font=f_name, fill=GOLD if colour != GOLD else (245, 240, 230), **AR)
    bg = dark(11)
    circ_x, circ_y = int(W * 0.70), H // 2
    strip = None
    if role:   # the role on a cream strip, underlined in red, slightly tilted
        rb = f_role.getbbox(role, **AR)
        strip = Image.new("RGBA", (rb[2] - rb[0] + 50, rb[3] - rb[1] + 34), CREAM + (255,))
        sd = ImageDraw.Draw(strip)
        sd.text((25 - rb[0], 14 - rb[1]), role, font=f_role, fill=INK, **AR)
        sd.line((20, strip.height - 6, strip.width - 20, strip.height - 6), fill=RED, width=5)
        strip = strip.rotate(1.5, expand=True, resample=Image.BICUBIC)
    for i in range(n):
        t = i / fps
        frame = bg.copy()
        s = back(t / 0.4)
        if s > 0.02:
            r = int(d / 2 * s)
            ImageDraw.Draw(frame).ellipse((circ_x - r, circ_y - r, circ_x + r, circ_y + r), fill=colour)
            fs = max(1, int((d - 40) * min(1, s)))
            fimg, fmask = face.resize((fs, fs)), mask.resize((fs, fs))
            frame.paste(fimg, (circ_x - fs // 2, circ_y - fs // 2), fmask)
        # the name: written right to left (a wipe), on the left of the circle
        prog = ease((t - 0.2) / 0.5)
        if prog > 0:
            wv = int(name_img.width * prog)
            part = name_img.crop((name_img.width - wv, 0, name_img.width, name_img.height))
            xr = int(W * 0.70) - d // 2 - 60
            frame.paste(part, (xr - wv, circ_y - name_img.height // 2 - (40 if role else 0)), part)
        if strip is not None and t > 0.55:
            a = ease((t - 0.55) / 0.3)
            lay = strip.copy()
            lay.putalpha(strip.getchannel("A").point(lambda v: int(v * a)))
            xr = int(W * 0.70) - d // 2 - 60
            frame.paste(lay, (xr - lay.width, circ_y + 70), lay)
        z = 1.0 + 0.05 * t / max(0.5, n / fps)
        yield np.asarray(camera(frame, z, W / 2, H / 2))


# ---------- number: a year or a figure, counting up ----------

AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def number(shot: dict, n: int, fps: float, backdrop: Image.Image | None = None):
    raw = str(shot.get("value") or shot.get("word") or "")
    m = re.search(r"\d[\d,.]*", raw.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))
    target = float(m.group(0).replace(",", "")) if m else None
    is_year = target is not None and 1000 <= target <= 2100 and float(target).is_integer() and len(m.group(0)) == 4
    start = (target - 30 if is_year else 0) if target is not None else None
    pre, post = (raw[: m.start()], raw[m.end():]) if m else (raw, "")
    f_big, f_cap = _font("Alexandria-ExtraBold.ttf", 300), _font("Amiri-Italic.ttf", 70)
    caption = shot.get("caption") or ""
    bg = dark(17)
    if backdrop is not None:
        dim = ImageOps.grayscale(backdrop).convert("RGB")
        from .archive import cover
        dim = cover(dim, W, H).filter(ImageFilter.GaussianBlur(14))
        bg = Image.blend(bg, dim, 0.35)
    for i in range(n):
        t = i / fps
        if target is not None:
            v = start + (target - start) * ease(t / 0.8)
            txt = f"{int(round(v))}" if (is_year or float(target).is_integer()) else f"{v:.1f}"
            txt = pre + (txt if is_year else f"{int(round(v)):,}" if float(target).is_integer() else txt) + post
        else:
            txt = raw
        frame = bg.copy()
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).text((W // 2, H // 2 - 40), txt, font=f_big, fill=GOLD + (190,), anchor="mm", **AR)
        glow = glow.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BILINEAR)
        frame.paste(glow, (0, 0), glow)
        dr = ImageDraw.Draw(frame)
        s = back(t / 0.3)
        dr.text((W // 2, H // 2 - 40 + int((1 - s) * 50)), txt, font=f_big, fill=(248, 244, 236), anchor="mm", **AR)
        if caption and t > 0.35:
            a = int(255 * ease((t - 0.35) / 0.3))
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(lay).text((W // 2, H // 2 + 170), caption, font=f_cap, fill=(236, 226, 205, a), anchor="mm", **AR)
            frame.paste(lay, (0, 0), lay)
        yield np.asarray(frame)


# ---------- map: the countries light up, a route draws between them ----------

@lru_cache(maxsize=1)
def _world():
    d = json.loads(ATLAS.read_text(encoding="utf-8"))
    sx, sy = d["transform"]["scale"]
    tx, ty = d["transform"]["translate"]
    arcs = []
    for arc in d["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(idx):
        out = []
        for i in idx:
            pts = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(pts if not out else pts[1:])
        return out
    def unwrap(pts):   # a ring that crosses the date line (Russia, Fiji) is drawn on one side, not as a stripe
        lons = [p[0] for p in pts]
        if max(lons) - min(lons) > 300:
            return [(x + 360 if x < 0 else x, y) for x, y in pts]
        return pts
    countries = {}
    for g in d["objects"]["countries"]["geometries"]:
        name = g["properties"]["name"]
        if name == "Antarctica":
            continue
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]] if g["type"] == "Polygon" else []
        countries[name] = [[unwrap(ring(r)) for r in poly] for poly in polys]
    return countries


ALIASES = {"usa": "United States of America", "us": "United States of America", "united states": "United States of America",
           "america": "United States of America", "uk": "United Kingdom", "russia": "Russia", "korea": "South Korea",
           "uae": "United Arab Emirates"}


def _country(name: str):
    world = _world()
    key = ALIASES.get(name.strip().lower(), name.strip())
    for k, v in world.items():
        if k.lower() == key.lower():
            return k, v
    return None, None


def _proj(lon, lat, view):
    x0, y0, x1, y1 = view
    return (lon - x0) / (x1 - x0) * W, (y1 - lat) / (y1 - y0) * H


def _bbox(polys):
    pts = max((poly[0] for poly in polys), key=len)   # the main land (not Alaska's islands across the world)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _centroid(polys):
    poly = max((p[0] for p in polys), key=len)
    return sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly)


def _fit(b, pad=0.25):
    x0, y0, x1, y1 = b
    w, h = (x1 - x0) * (1 + pad * 2), (y1 - y0) * (1 + pad * 2)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if w / h < W / H:
        w = h * W / H
    else:
        h = w * H / W
    return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2


def world_map(shot: dict, n: int, fps: float):
    names = [c for c in (shot.get("countries") or []) if c][:4]
    found = [(k, v) for k, v in (_country(c) for c in names) if k]
    world = _world()
    full = (-170.0, -58.0, 190.0, 84.0)
    if found:
        bx = [_bbox(v) for _, v in found]
        target = _fit((min(b[0] for b in bx), min(b[1] for b in bx), max(b[2] for b in bx), max(b[3] for b in bx)))
    else:
        target = full
    lit = {k for k, _ in found}
    cents = [_centroid(v) for _, v in found]
    label = shot.get("label") or shot.get("word") or ""
    f_lab = _font("Alexandria-ExtraBold.ttf", 76)
    for i in range(n):
        t = i / fps
        a = ease(t / 0.7)
        view = tuple(full[j] + (target[j] - full[j]) * a for j in range(4))
        frame = Image.new("RGB", (W, H), (16, 18, 22))
        dr = ImageDraw.Draw(frame)
        for k, polys in world.items():
            on = k in lit
            fill = RED if on and t > 0.45 else (58, 56, 54) if not on else (90, 60, 56)
            for poly in polys:
                pts = [_proj(x, y, view) for x, y in poly[0]]
                if len(pts) > 2:
                    dr.polygon(pts, fill=fill, outline=(28, 28, 30))
        if len(cents) >= 2 and t > 0.6:   # the route draws itself from the first country to the second
            p0, p1 = _proj(*cents[0], view), _proj(*cents[1], view)
            prog = ease((t - 0.6) / 0.5)
            mx, my = (p0[0] + p1[0]) / 2, min(p0[1], p1[1]) - abs(p1[0] - p0[0]) * 0.22
            pts = []
            for s in np.linspace(0, prog, 40):
                pts.append(((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * mx + s ** 2 * p1[0],
                            (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * my + s ** 2 * p1[1]))
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(glow).line(pts, fill=GOLD + (200,), width=14, joint="curve")
            frame.paste(glow.filter(ImageFilter.GaussianBlur(10)), (0, 0), glow.filter(ImageFilter.GaussianBlur(10)))
            dr = ImageDraw.Draw(frame)
            dr.line(pts, fill=(255, 236, 170), width=5, joint="curve")
            for c in (p0, pts[-1]):
                dr.ellipse((c[0] - 11, c[1] - 11, c[0] + 11, c[1] + 11), fill=(255, 236, 170))
        if label and t > 0.3:
            al = int(255 * ease((t - 0.3) / 0.3))
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            bb = f_lab.getbbox(label, **AR)
            bw = bb[2] - bb[0] + 70
            ld.rectangle((W // 2 - bw // 2, H - 190, W // 2 + bw // 2, H - 80), fill=(14, 14, 14, int(al * 0.85)))
            ld.text((W // 2, H - 135), label, font=f_lab, fill=(248, 244, 236, al), anchor="mm", **AR)
            frame.paste(lay, (0, 0), lay)
        yield np.asarray(frame)


# ---------- text: a big sentence, word after word ----------

def big_text(shot: dict, n: int, fps: float):
    text = shot.get("text") or shot.get("word") or ""
    quote = bool(shot.get("quote"))
    f = _font("Amiri-Bold.ttf", 104 if len(text) < 40 else 82)
    words = text.split()
    lines = wrap(text, f, W - 360)
    bg = dark(23)
    total = max(1, len(words))
    for i in range(n):
        t = i / fps
        shown = min(total, int(total * ease(t / max(0.4, min(1.2, n / fps * 0.6)))) + 1)
        frame = bg.copy()
        dr = ImageDraw.Draw(frame)
        y0 = H // 2 - (len(lines) * 140) // 2
        k = 0
        for li, line in enumerate(lines):
            lw = line.split()
            vis = " ".join(lw[: max(0, min(len(lw), shown - k))])
            k += len(lw)
            if not vis:
                continue
            # right-aligned to where the full line ends, so words appear in place (right to left)
            full_w = f.getlength(line, **AR)
            xr = W // 2 + full_w / 2
            dr.text((xr, y0 + li * 140), vis, font=f, fill=(246, 241, 230), anchor="ra", **AR)
        if quote:
            dr.text((W // 2 + f.getlength(lines[0], **AR) / 2 + 30, y0 - 40), "«", font=_font("Amiri-Bold.ttf", 160),
                    fill=GOLD, anchor="la", **AR)
            if shot.get("by") and shown >= total:
                dr.text((W // 2, y0 + len(lines) * 140 + 40), "— " + shot["by"], font=_font("Amiri-Italic.ttf", 56),
                        fill=GOLD, anchor="ma", **AR)
        yield np.asarray(frame)


KINDS = ("headline", "person", "number", "map", "text")
