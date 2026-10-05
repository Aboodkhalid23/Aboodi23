"""محاكاة صفحة يوتيوب: أغلفتنا بين أغلفة المنافسين بنفس الموضوع، بشاشتين موبايل (غامق وفاتح).

    python3 designer/feed.py "evergrande" --ours A-mobile.jpg B-mobile.jpg C-mobile.jpg \
        --title "العنوان" -o feed.jpg [--limit 6] [--duration 25:00]

السؤال الي تجاوبه الصورة: غلافنا يبين ويسحب العين، لو يضيع بين الأغلفة الثانية؟
"""
import argparse
import io
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arabic import load_font, shape_word, visual_words  # noqa: E402
from pinterest import slug  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE_ROOT = ROOT / "designer/references/competitors"
FONT = Path(__file__).resolve().parent / "fonts" / "Cairo-Black.ttf"
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
THUMB = (720, 405)
TOP_BAR = 24
ITEM_H = THUMB[1] + 150
PAD = 16
AVATAR = 56
GAP = 40
THEMES = {
    True: {"bg": (15, 15, 15), "text": (255, 255, 255), "meta": (170, 170, 170), "avatar": (80, 80, 80)},
    False: {"bg": (255, 255, 255), "text": (15, 15, 15), "meta": (96, 96, 96), "avatar": (205, 205, 205)},
}


SEARCH_ATTEMPTS = 3


class FeedError(Exception):
    """خطأ بالمحاكاة، رسالته بالعربي."""


class _QuietLogger:
    """يسكّت رسائل yt-dlp الإنگليزية. الخطأ يوصل لصاحب القناة بالعربي عن طريق FeedError."""

    def debug(self, msg):
        pass

    info = warning = error = debug


def search(query: str, limit: int = 6) -> list[dict]:
    """يبحث بيوتيوب (بدون تنزيل فيديوهات) ويرجع الأرقام والعناوين والقنوات والمشاهدات والمدة."""
    try:
        import yt_dlp
    except ImportError as e:
        raise FeedError(f"ما گدرت أبحث بيوتيوب ({e}). نصّب: pip install -r designer/requirements-quality.txt")
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True,
            "noprogress": True, "logger": _QuietLogger()}
    info = None
    for attempt in range(SEARCH_ATTEMPTS):  # يوتيوب أحياناً يرفض الطلب (403)، والمحاولة الجاية غالباً تنجح
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            break
        except (yt_dlp.utils.DownloadError, OSError) as e:
            if attempt == SEARCH_ATTEMPTS - 1:
                raise FeedError(f"ما گدرت أبحث بيوتيوب ({e}).")
            time.sleep(2 * (attempt + 1))
    results = []
    for e in (info or {}).get("entries") or []:
        if not isinstance(e, dict) or not e.get("id"):
            continue
        views, duration = e.get("view_count"), e.get("duration")
        results.append({
            "id": str(e["id"]),
            "title": str(e.get("title") or ""),
            "channel": str(e.get("channel") or e.get("uploader") or ""),
            "views": int(views) if isinstance(views, (int, float)) else None,
            "duration": int(duration) if isinstance(duration, (int, float)) else None,
        })
    return results


def search_cached(query: str, limit: int, cache_dir: Path) -> list[dict]:
    """نفس search، بس النتيجة تنحفظ بـ search.json بمجلد البحث، والمرة الجاية تنقرا منه
    (يوتيوب يرفض الطلبات المتكررة ورا بعض)."""
    cache = Path(cache_dir) / "search.json"
    try:
        cached = json.loads(cache.read_text(encoding="utf-8"))
        if cached.get("limit", 0) >= limit and isinstance(cached.get("results"), list):
            return cached["results"][:limit]
    except (OSError, ValueError, AttributeError):
        pass
    results = search(query, limit)
    if results:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"limit": limit, "results": results}, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    return results


def fetch_thumb(video_id: str, cache_dir: Path) -> Path:
    """ينزّل غلاف الفيديو من i.ytimg.com (أو ياخذه من الكاش) ويحفظه 16:9."""
    if not VIDEO_ID.match(video_id):
        raise FeedError(f"رقم فيديو مو صحيح: {video_id}")
    cache_dir = Path(cache_dir)
    path = cache_dir / f"{video_id}.jpg"
    if path.exists():
        return path
    cache_dir.mkdir(parents=True, exist_ok=True)
    last = None
    for name, crop in (("maxresdefault", None), ("hqdefault", (0, 45, 480, 315))):
        try:
            with urllib.request.urlopen(f"https://i.ytimg.com/vi/{video_id}/{name}.jpg", timeout=30) as r:
                img = Image.open(io.BytesIO(r.read())).convert("RGB")
        except (OSError, UnidentifiedImageError) as e:
            last = e
            continue
        (img.crop(crop) if crop else img).save(path, quality=92)
        return path
    raise FeedError(f"ما گدرت أنزّل غلاف الفيديو {video_id} ({last}).")


def fmt_views(n: int | None) -> str:
    if n is None:
        return ""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} مليون مشاهدة"
    if n >= 1_000:
        return f"{n // 1_000} ألف مشاهدة"
    return f"{n} مشاهدة"


def fmt_duration(sec: int | None) -> str:
    if sec is None:
        return ""
    h, rest = divmod(int(sec), 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def interleave(ours: list, others: list, positions=(1, 4, 7)) -> list:
    """أغلفتنا بالأماكن المحددة (من صفر)، والمنافسين يملون الباقي بالترتيب."""
    out, ours, others = [], list(ours), list(others)
    while ours or others:
        if ours and (len(out) in positions or not others):
            out.append(ours.pop(0))
        else:
            out.append(others.pop(0))
    return out


def _line_width(draw, words, font) -> float:
    space = draw.textlength(" ", font=font)
    widths = [draw.textlength(t, font=font, **kw) for t, kw in (shape_word(w) for w in words)]
    return sum(widths) + space * max(0, len(words) - 1)


def _draw_rtl(draw, right: float, y: float, line: str, font, fill) -> None:
    """يرسم السطر منتهي عند right (محاذاة يمين، مثل واجهة يوتيوب العربية)."""
    words = visual_words(line)
    x = right - _line_width(draw, words, font)
    space = draw.textlength(" ", font=font)
    for w in words:
        text, kw = shape_word(w)
        draw.text((x, y), text, font=font, fill=fill, **kw)
        x += draw.textlength(text, font=font, **kw) + space


def _meta_layout(draw, right: float, channel: str, meta: str, font) -> list[tuple[str, float]]:
    """سطر "القناة · المعلومات": كل قطعة تنرسم لحالها (القناة يمين، والمشاهدات يسارها)،
    حتى اسم قناة إنگليزي جنب رقم ما يتخربط ترتيبه. يرجع (النص، حافته اليمنى)."""
    parts = [p for p in (channel, "·" if channel and meta else "", meta) if p]
    space = draw.textlength(" ", font=font)
    layout, x = [], right
    for p in parts:
        layout.append((p, x))
        x -= _line_width(draw, visual_words(p), font) + space
    return layout


def _wrap(draw, text: str, font, max_w: float, max_lines: int = 2) -> list[str]:
    lines, cur = [], []
    for w in text.split():
        if cur and _line_width(draw, visual_words(" ".join(cur + [w])), font) > max_w:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] += "…"
    return lines


def phone_screen(items: list[dict], dark: bool, width: int = 720) -> Image.Image:
    theme = THEMES[dark]
    img = Image.new("RGB", (width, TOP_BAR + ITEM_H * len(items)), theme["bg"])
    d = ImageDraw.Draw(img)
    title_font, meta_font, badge_font = load_font(FONT, 30), load_font(FONT, 22), load_font(FONT, 22)
    for i, it in enumerate(items):
        y = TOP_BAR + i * ITEM_H
        with Image.open(it["thumb"]) as t:
            img.paste(ImageOps.fit(t.convert("RGB"), (width, THUMB[1]), Image.LANCZOS), (0, y))
        if it.get("duration"):
            tw = d.textlength(it["duration"], font=badge_font)
            box = (12, y + THUMB[1] - 12 - 34, 12 + tw + 16, y + THUMB[1] - 12)
            d.rounded_rectangle(box, radius=6, fill=(0, 0, 0))
            d.text((box[0] + 8, box[1] + 2), it["duration"], font=badge_font, fill=(255, 255, 255))
        ay = y + THUMB[1] + PAD
        d.ellipse((width - PAD - AVATAR, ay, width - PAD, ay + AVATAR), fill=it.get("avatar", theme["avatar"]))
        right = width - PAD - AVATAR - 14
        lines = _wrap(d, it["title"], title_font, right - PAD)
        for j, line in enumerate(lines):
            _draw_rtl(d, right, ay - 6 + j * 40, line, title_font, theme["text"])
        for text, edge in _meta_layout(d, right, it.get("channel", ""), it.get("meta", ""), meta_font):
            _draw_rtl(d, edge, ay - 2 + len(lines) * 40, text, meta_font, theme["meta"])
    return img


def make_feed(ours: list, title: str, competitors: list[dict], cache_dir: Path,
              duration: str = "25:00") -> Image.Image:
    ours_items = [{"thumb": Path(p), "title": title, "channel": "قناتك", "meta": "جديد", "duration": duration,
                   "avatar": (229, 9, 20)} for p in ours]
    comp_items = []
    for c in competitors:
        try:
            thumb = fetch_thumb(c["id"], cache_dir)
        except FeedError:
            continue
        comp_items.append({"thumb": thumb, "title": c["title"], "channel": c["channel"],
                           "meta": fmt_views(c["views"]), "duration": fmt_duration(c["duration"])})
    items = interleave(ours_items, comp_items)
    screens = [phone_screen(items, dark=True), phone_screen(items, dark=False)]
    w = sum(s.width for s in screens) + GAP * (len(screens) + 1)
    h = max(s.height for s in screens) + 2 * GAP
    canvas = Image.new("RGB", (w, h), (42, 42, 42))
    x = GAP
    for s in screens:
        canvas.paste(s, (x, GAP))
        x += s.width + GAP
    canvas.info["competitors"] = len(comp_items)
    return canvas


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يحاكي صفحة يوتيوب ويا أغلفة المنافسين")
    ap.add_argument("query")
    ap.add_argument("--ours", nargs="+", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--duration", default="25:00")
    args = ap.parse_args(argv)
    try:
        cache = CACHE_ROOT / slug(args.query)
        comps = search_cached(args.query, args.limit, cache)
        img = make_feed(args.ours, args.title, comps, cache, args.duration)
    except FeedError as e:
        print(f"✗ خطأ: {e}")
        return 1
    except (OSError, UnidentifiedImageError) as e:
        print(f"✗ خطأ: وحدة من صور أغلفتنا مو موجودة أو خربانة ({e})")
        return 1
    out = Path(args.out)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out, quality=90)
    except OSError as e:
        print(f"✗ خطأ: ما گدرت أحفظ الصورة ({e})")
        return 1
    print(f"✓ انحفظ: {out} ({img.info['competitors']} منافس)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
