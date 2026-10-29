"""«أرشيف»: the documentary look of the reels he sent as his target (owner, 2026-10-29: "اريد نفس هذا الستايل").

What those reels do, measured on them: a new picture every ~1 second, real archive photos in black and white with
film grain and a slow push-in, a print of a photo that drops onto a dark desk, the key word in an elegant serif in
the middle, a yellow label on a name, hard cuts on the beat of the talk. Here his own talk carries it: the cleaned
video's sound runs from start to end, his face comes back between the picture runs, and every picture is chosen for
the exact words said under it.

The pictures are drawn frame by frame here (Pillow), not in a browser: smooth sub-pixel moves, Arabic shaped right
(Raqm), and a 1-minute episode in a few minutes on a laptop.
"""
import json
import math
import random
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from .paths import Episode

W, H = 1920, 1080
FONTS = Path(__file__).resolve().parent.parent / "fonts"
YELLOW = (255, 221, 0)

SHOTS_PROMPT = """انت مونتير وثائقيات محترف. هاي حلقة يوتيوب لصاحب قناة عراقي يحچي للكاميرا. اكتب قائمة لقطات تخلط أسلوبين
يعجبوه: ريلز الأرشيف (صور حقيقية تتبدل كل ثانية تقريباً) وموشن جرافك قناة عمر أبو الروب (جريدة يتظلل بيها السطر المهم،
بطاقة شخص، أرقام وسنين ضخمة، خرائط). كل لقطة تطابق الكلام الي ينگال وياها بالضبط.

الكلام بالثواني (على الفيديو المقصوص، مدته {dur:.2f} ثانية):
{words}

أنواع اللقطات:
- "face": وجهه يحچي. 1.5–4 ثواني.
- "photo": صورة أرشيف تغطي الشاشة وصوته مستمر. 0.9–2.2 ثانية. حقولها:
  "queries" (2–3 كلمات بحث إنگليزية، الأولى اسم الشي بس كما عنوانه بويكيبيديا: "Ren Zhengfei"، "Motorola"، "Shenzhen"، والباقي أدق.
  ⛔ لا كلمات عامة مثل "business meeting" إلا إذا ماكو شي محدد، وبعدها مشاهد أرشيفية حقيقية "1990s Shenzhen street")،
  "word" (1–3 كلمات عربية من الي ينگال هسه، بخط أنيق بنص الصورة؛ لنص الصور تقريباً)، "label" (اسم الشخص أو الشركة بالعربي إذا ينذكر هسه، وإلا "")،
  "print" (true = صورة مطبوعة تنرمي على مكتب، لثلث الصور تقريباً).
- "person": أول مرة ينذكر شخص مهم: صورته بدائرة ملونة واسمه ضخم. 2–3 ثواني. حقولها: "queries" (اسمه بالإنگليزي أول)، "label" (اسمه بالعربي)، "role" (2–4 كلمات: منو هو).
- "headline": حدث أو قرار أو خبر (عقد، رفض، حظر): قصاصة جريدة والسطر المهم يتظلل أصفر. 2.5–3.5 ثواني. حقولها: "headline" (عنوان خبر قصير 4–9 كلمات يعيد صياغة الي يگوله بالضبط، بلا معلومة مو بكلامه)، "highlight" (2–3 كلمات من العنوان نفسه)، "source" (السنة إذا معروفة من كلامه، وإلا "أرشيف". ⛔ لا تنسب العنوان لجريدة أو وكالة حقيقية).
- "number": سنة أو رقم ينذكر (1987، 10 مليار، 50٪): الرقم ضخم يعدّ لحد قيمته. 1.8–2.5 ثانية. حقولها: "value" (مثل "1987" أو "10 مليار")، "caption" (2–5 كلمات تحته).
- "map": بلدين أو أكثر بصراع أو صفقة أو رحلة: خريطة تقرب عليهم وخط ينرسم بينهم. 2.5–3.5 ثواني. حقولها: "countries" (أسماء إنگليزية مثل "China", "United States of America")، "label" (1–2 كلمة عربية).
- "text": جملة قوية، سؤال، أو كلام منقول («قال جملة غيرت كل شي»): الجملة تطلع كلمة كلمة على أسود. 2–3.5 ثواني. حقولها: "text" (الجملة بالعربي، 3–9 كلمات)، "quote" (true إذا كلام شخص)، "by" (منو گالها، إذا quote).

القواعد:
- اللقطات تغطي من 0 لـ {dur:.2f} بلا فراغ ولا تداخل، مرتبة، وتبدي وتخلص على حدود الكلمات.
- أول 3 ثواني بلا وجهه (هوك قوي: صورة أو رقم أو جريدة).
- بعدها: سلسلة (2–5 لقطات مو وجه) ثم وجهه، وهيچ. اللقطات الي مو وجه تقريباً 65٪ من الوقت.
- الموشن جرافك (person, headline, number, map, text) تقريباً 40٪ من اللقطات الي مو وجه، والباقي صور. لا تحط نفس النوع مرتين ورا بعض إلا photo.
- كل رقم أو سنة ينذكر = number. كل شخص مهم أول مرة = person. كل صراع بين بلدين = map.
- نوّع: نفس نوع الموشن جرافك بالكثير مرة كل 20 ثانية (مو ثلاث جرايد بدقيقة)، ولا تعيد نفس الخريطة أو نفس الجملة.
- آخر لقطة وجهه (الختام والسلام).
- "mood": مزاج الموسيقى للحلقة كلها: tension, dark, wonder, sad, drive.

جاوب JSON بس: {{"mood": "...", "shots": [{{"start": 0.0, "end": 2.2, "kind": "number", "value": "1987", "caption": "..."}}, {{"start": 2.2, "end": 3.4, "kind": "photo", "queries": ["..."], "word": "...", "label": "", "print": false}}, {{"start": 3.4, "end": 5.0, "kind": "face"}}]}}"""

MOTION = ("headline", "person", "number", "map", "text")
PICTURED = ("photo", "person")   # the shots that need a real picture
SFX = {"headline": "paper_slide", "number": "impact", "person": "swoosh", "map": "whoosh_soft", "text": "tick_soft",
       "photo": "whoosh_soft"}


# ---------- the shot list ----------

def words_block(ep: Episode) -> str:
    from .transcribe import load_words
    ws = load_words(ep.clean_words)
    lines, cur, t0 = [], [], None
    for w in ws:
        if t0 is None:
            t0 = w.start
        cur.append(w.text)
        if len(cur) >= 6 or w.text.endswith((".", "،", "؟", "!")):
            lines.append(f"[{t0:.2f}–{w.end:.2f}] {' '.join(cur)}")
            cur, t0 = [], None
    if cur:
        lines.append(f"[{t0:.2f}–{ws[-1].end:.2f}] {' '.join(cur)}")
    return "\n".join(lines)


def tidy(shots: list[dict], dur: float) -> list[dict]:
    """Cover 0..dur exactly, in order, no slivers: the model's times are close, never exact."""
    shots = sorted((s for s in shots if s.get("end", 0) > s.get("start", 0)), key=lambda s: s["start"])
    out = []
    for s in shots:
        s = dict(s, start=max(0.0, float(s["start"])), end=min(dur, float(s["end"])))
        if out:
            s["start"] = out[-1]["end"]
        if s["end"] - s["start"] < 0.5:
            if out:
                out[-1]["end"] = s["end"]
            continue
        out.append(s)
    if not out:
        return [{"start": 0.0, "end": dur, "kind": "face"}]
    out[0]["start"] = 0.0
    out[-1]["end"] = dur
    return out


def vary(shots: list[dict]) -> list[dict]:
    """The same map twice reads as a mistake (seen 2026-10-29): a repeat becomes a photo of the two sides;
    and the goodbye is on his face."""
    seen = set()
    for s in shots:
        if s.get("kind") == "map":
            key = tuple(sorted(s.get("countries") or []))
            if key in seen:
                names = list(key)
                s.update(kind="photo", queries=[" ".join(names) + " relations", *names][:3], word=s.get("label", ""),
                          label="", print=False)
            seen.add(key)
    if shots and shots[-1].get("kind") != "face" and shots[-1]["end"] - shots[-1]["start"] < 3:
        shots[-1] = {"start": shots[-1]["start"], "end": shots[-1]["end"], "kind": "face"}
    return shots


def shot_list(ep: Episode, ask) -> dict:
    """`ask(prompt) -> dict` (one quick Claude answer)."""
    dur = clean_duration(ep)
    ans = ask(SHOTS_PROMPT.format(dur=dur, words=words_block(ep)))
    ans["shots"] = vary(tidy(ans.get("shots") or [], dur))
    (ep.work / "archive_shots.json").write_text(json.dumps(ans, ensure_ascii=False, indent=1), encoding="utf-8")
    return ans


def clean_duration(ep: Episode) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(ep.clean_video)], capture_output=True, text=True).stdout
    return float(out.strip())


# ---------- the pictures ----------

WIKI = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "URU-editor/1.0 (documentary editing app; contact via github.com/Aboodkhalid23)"}
# scans of book pages, plans and the like come up in a plain search for almost anything: never the right picture
STOP = {"the", "and", "of", "in", "on", "at", "with", "from", "for", "street", "building", "office", "photo",
        "view", "old", "new", "city", "people", "man", "woman", "headquarters", "campus", "logo", "store", "news"}
JUNK = ("page", ".pdf", ".djvu", "book", "title", "plan of", "floor plan", "scan", "map of", "diagram", "coat of arms",
        "signature", "logo.svg", "icon", "flag of")


def wikipedia_picture(q: str, session):
    """The lead picture of the Wikipedia article that matches `q` (the person, the company, the event itself),
    only when it is a free file on Wikimedia Commons. Far more on topic than a plain picture search."""
    from .sources import Found
    r = session.get(WIKI, params={"action": "query", "generator": "search", "gsrsearch": q, "gsrlimit": 1,
                                  "prop": "pageimages", "piprop": "name", "format": "json"}, headers=UA, timeout=12)
    if r.status_code != 200:
        return None
    pages = (r.json().get("query") or {}).get("pages") or {}
    name = next((p.get("pageimage") for p in pages.values() if p.get("pageimage")), None)
    if not name or any(j in name.lower() for j in JUNK):
        return None
    r = session.get(WIKI, params={"action": "query", "titles": "File:" + name, "prop": "imageinfo",
                                  "iiprop": "url|size|extmetadata", "iiurlwidth": 2400, "format": "json"}, headers=UA, timeout=12)
    if r.status_code != 200:
        return None
    page = next(iter(((r.json().get("query") or {}).get("pages") or {}).values()), {})
    if page.get("imagerepository") != "shared":   # a non-free file kept on Wikipedia itself: not ours to use
        return None
    info = (page.get("imageinfo") or [{}])[0]
    meta = info.get("extmetadata") or {}
    return Found("Wikimedia Commons", name, info.get("thumburl") or info.get("url"), info.get("width", 0),
                 info.get("height", 0), (meta.get("LicenseShortName") or {}).get("value", ""),
                 re.sub(r"<[^>]+>", "", (meta.get("Artist") or {}).get("value", ""))[:80], info.get("descriptionurl", ""))


PICK_PROMPT = """انت مونتير وثائقيات. لكل لقطة، هاي أسماء ملفات صور لگيناها (كل ملف إله رقم ثابت).
اختار لكل لقطة رقم الصورة الأنسب للكلام بهاللحظة: الشخص أو الشركة أو المكان أو الحدث نفسه، وإذا ماكو، شي يمثل الفكرة أو
الجو بوضوح (تلفون قديم لـ«مكالمة»، بورصة لـ«السوق ينهار»). ⛔ لا تختار نفس الرقم للقطتين.
-1 بس إذا كل الصور غلط واضح (صفحة كتاب، شخص ثاني، شي مالة علاقة): تطلع لقطة وجهه بدالها.
أول ٣ لقطات (الهوك) لازم صور إذا ممكن.
{shots}

جاوب JSON بس: {{"pick": {{"<رقم اللقطة>": <رقم الصورة أو -1>}}}}"""


def fetch_pictures(ep: Episode, shots: list[dict], ask=None) -> None:
    """A real picture for every photo shot (all searches at once); none found → his face there instead."""
    import requests
    from .sources import download, find
    folder = ep.assets / "archive"
    folder.mkdir(parents=True, exist_ok=True)
    used: set = set()

    def candidates(q, session):
        try:
            lead = wikipedia_picture(q, session)
        except Exception:   # noqa: BLE001 — the plain search still runs
            lead = None
        if lead and lead.url not in used:
            yield lead
        # a plain search answers anything: keep only files whose own name shares a real word of the query
        # (an airport photo came up for «1990s Shenzhen street», a German street for «Trump Huawei ban»)
        keys = {w for w in re.findall(r"[a-z]{3,}", q.lower()) if w not in STOP}
        for f in find(q, "image", None, session, used, [])[:6]:
            title = (f.title or "").lower()
            if keys and not any(k in title for k in keys):
                continue
            if not any(j in title for j in JUNK) and not title.endswith((".webm", ".ogv", ".pdf")):
                yield f

    def gather(k_s):   # up to 6 candidates per shot: names only, nothing downloaded yet
        k, s = k_s
        session, seen, out = requests.Session(), set(), []
        for q in (s.get("queries") or [])[:3]:
            try:
                for f in candidates(q, session):
                    if f.url not in seen:
                        seen.add(f.url)
                        out.append(f)
            except Exception:   # noqa: BLE001 — a library that failed: the others still count
                pass
            if len(out) >= 6:
                break
        return k, out[:6]

    def save(k, s, f, session) -> bool:
        try:
            img = Image.open(BytesIO(download(f, session))).convert("RGB")
        except Exception:   # noqa: BLE001 — a broken file
            return False
        if min(img.size) < 400:
            return False
        used.add(f.url)
        img.thumbnail((2600, 2600))
        img.save(folder / f"shot_{k}.jpg", quality=92)
        (folder / f"shot_{k}.json").write_text(json.dumps({"q": s.get("queries"), "url": f.url, "credit":
                                                            f"{f.title} — {f.artist} ({f.license}, {f.provider})"},
                                                           ensure_ascii=False), encoding="utf-8")
        return True

    todo = [(k, s) for k, s in enumerate(shots) if s.get("kind") in PICTURED
            and not ((folder / f"shot_{k}.jpg").exists()
                     and json.loads((folder / f"shot_{k}.json").read_text()).get("q") == s.get("queries"))]
    with ThreadPoolExecutor(max_workers=3) as pool:   # Wikimedia blocks a burst of requests for minutes
        found = dict(pool.map(gather, todo))
    # the editor picks, for each moment, the file whose name fits what is said (a book's title page or a
    # random street came up for «the market crashed»): one short question for all the shots at once
    picks = {}
    if ask and any(found.values()):
        ids, files, lines = {}, [], []   # one number per file, so the same picture is never picked twice
        for k, s in todo:
            if found.get(k):
                rows = []
                for f in found[k]:
                    if f.url not in ids:
                        ids[f.url] = len(files)
                        files.append(f)
                    rows.append(f"  {ids[f.url]}: {f.title[:110]}")
                lines.append(f"shot {k}: يگول «{s.get('said', '')}» · بحثنا: {', '.join(s.get('queries') or [])}\n" + "\n".join(rows))
        try:
            ans = ask(PICK_PROMPT.format(shots="\n".join(lines)))
            taken = set()
            for k, v in (ans.get("pick") or {}).items():
                v = int(v)
                if 0 <= v < len(files) and v not in taken:
                    taken.add(v)
                    picks[int(k)] = files[v]
                else:
                    picks[int(k)] = None
        except Exception:   # noqa: BLE001 — no answer: the search order stands
            picks = {}

    def fetch(k_s):
        k, s = k_s
        cands = found.get(k) or []
        session = requests.Session()
        if k in picks:
            return picks[k] is not None and save(k, s, picks[k], session)
        return any(save(k, s, f, session) for f in cands[:3] if f.url not in used)
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(fetch, todo))
    for k, s in todo:
        if not (folder / f"shot_{k}.jpg").exists():
            if s["kind"] == "person" and s.get("label"):   # no photo of them: their name still comes up big
                s.update(kind="text", text=s["label"] + (" · " + s["role"] if s.get("role") else ""))
            else:
                s["kind"] = "face"


# ---------- drawing ----------

def _font(name: str, size: int):
    return ImageFont.truetype(str(FONTS / name), size, layout_engine=ImageFont.Layout.RAQM)


def word_layer(text: str) -> Image.Image:
    """The key word: elegant serif, white, a soft shadow (their lowercase italic, in Arabic)."""
    f = _font("Amiri-Italic.ttf", 104)
    box = f.getbbox(text, direction="rtl", language="ar")
    w, h = box[2] - box[0] + 60, box[3] - box[1] + 60
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((30 - box[0], 30 - box[1]), text, font=f, fill=(0, 0, 0, 255), direction="rtl", language="ar",
                                stroke_width=6, stroke_fill=(0, 0, 0, 255))
    layer = Image.alpha_composite(layer, shadow.filter(ImageFilter.GaussianBlur(14)))   # a soft dark halo: readable on any photo
    ImageDraw.Draw(layer).text((30 - box[0], 30 - box[1]), text, font=f, fill=(250, 248, 240, 255), direction="rtl", language="ar")
    return layer


def label_layer(text: str) -> Image.Image:
    """A name on a yellow tag, slightly tilted (their «Walter Freeman» label)."""
    f = _font("Alexandria-ExtraBold.ttf", 54)
    box = f.getbbox(text, direction="rtl", language="ar")
    w, h = box[2] - box[0] + 56, box[3] - box[1] + 34
    tag = Image.new("RGBA", (w, h), YELLOW + (255,))
    ImageDraw.Draw(tag).text((28 - box[0], 17 - box[1]), text, font=f, fill=(15, 15, 15, 255), direction="rtl", language="ar")
    return tag.rotate(-3, expand=True, resample=Image.BICUBIC)


def archive_look(img: Image.Image) -> Image.Image:
    """Black and white, contrast like a print, a touch of warmth in the shadows."""
    g = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1)
    return ImageOps.colorize(g, black=(14, 13, 12), white=(242, 238, 228), mid=(120, 116, 110))


def cover(img: Image.Image, w: int, h: int) -> Image.Image:
    r = max(w / img.width, h / img.height)
    img = img.resize((max(w, round(img.width * r)), max(h, round(img.height * r))), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


class Film:
    """Grain and vignette laid on every picture frame (precomputed: cheap per frame)."""
    def __init__(self, seed: int = 7):
        rng = np.random.default_rng(seed)
        self.grain = [rng.normal(0, 9, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1).astype(np.int16) for _ in range(6)]
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.vig = np.clip(1.0 - 0.38 * np.clip(d - 0.55, 0, None) ** 1.4, 0.55, 1.0)[..., None].astype(np.float32)

    def apply(self, frame: np.ndarray, i: int) -> np.ndarray:
        x = frame.astype(np.float32) * self.vig + self.grain[i % len(self.grain)]
        return np.clip(x, 0, 255).astype(np.uint8)


def _ease(t: float) -> float:
    return 1 - (1 - min(max(t, 0.0), 1.0)) ** 3


def _desk() -> Image.Image:
    rng = np.random.default_rng(3)
    base = np.full((H, W, 3), (34, 30, 27), np.float32)
    base += rng.normal(0, 6, (H, W, 1))
    base += np.linspace(-14, 10, W)[None, :, None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))


def photo_frames(img: Image.Image, n: int, shot: dict, seed: int):
    """Yield n RGB frames (numpy) for one photo shot."""
    rng = random.Random(seed)
    look = archive_look(img)
    word = word_layer(shot["word"]) if shot.get("word") else None
    label = label_layer(shot["label"]) if shot.get("label") else None
    if shot.get("print"):
        desk = _desk()
        pw = int(W * 0.56)
        pic = look.copy()
        pic.thumbnail((pw, int(H * 0.72)))
        card = Image.new("RGB", (pic.width + 36, pic.height + 36), (236, 232, 222))
        card.paste(pic, (18, 18))
        angle = rng.uniform(-4, 4)
        card = card.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC)
        shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
        shadow.putalpha(card.getchannel("A").point(lambda a: int(a * 0.55)))
        shadow = shadow.filter(ImageFilter.GaussianBlur(16))
        drift = rng.choice([-1, 1]) * 24
    else:
        big = cover(look, int(W * 1.12), int(H * 1.12))
        zin = rng.random() < 0.75
        pan = rng.uniform(-0.02, 0.02)
    for i in range(n):
        t = i / max(1, n - 1)
        if shot.get("print"):
            frame = desk.copy()
            drop = _ease(i / 7.0)                       # lands in ~0.3 s
            x = (W - card.width) // 2 + int(drift * t)
            y = (H - card.height) // 2 + int((1 - drop) * H * 0.55)
            frame.paste(shadow, (x + 14, y + 22), shadow)
            frame.paste(card, (x, y), card)
        else:
            z = 1.0 + 0.07 * (t if zin else 1 - t)     # slow push-in (or pull-out)
            cw, ch = W * 1.12 / z, H * 1.12 / z
            cx = big.width / 2 + pan * big.width * t
            box = (cx - cw / 2, big.height / 2 - ch / 2, cx + cw / 2, big.height / 2 + ch / 2)
            frame = big.transform((W, H), Image.EXTENT, box, Image.BICUBIC)
        if label is not None:
            a = _ease((i - 3) / 5.0)
            if a > 0:
                lay = label.copy()
                lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
                frame.paste(lay, ((W - lay.width) // 2, int(H * 0.70)), lay)
        if word is not None:
            a = _ease((i - 1) / 4.0)
            if a > 0:
                lay = word.copy()
                lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
                frame.paste(lay, ((W - lay.width) // 2, int(H * 0.52 - lay.height / 2 + (1 - a) * 12)), lay)
        yield np.asarray(frame.convert("RGB"))


def encode(frames, out: Path, fps: str, film: Film) -> Path:
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", fps, "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt",
                          "yuv420p", "-r", fps, str(out)], stdin=subprocess.PIPE)
    for i, f in enumerate(frames):
        p.stdin.write(film.apply(f, i).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError(f"encode failed: {out.name}")
    return out


def face_clip(ep: Episode, start: float, dur: float, close: bool, out: Path, fps: str, delogo: str | None) -> Path:
    """His talk, cut from the cleaned video: medium or close (a punch-in on the face hides the jump cut)."""
    try:
        f = json.loads((ep.work / "face.json").read_text(encoding="utf-8"))
        cx, cy = float(f.get("cx", 0.5)), float(f.get("cy", 0.42))
    except (OSError, ValueError):
        cx, cy = 0.5, 0.42
    vf = [delogo] if delogo else []
    if close:
        z = 1.3
        cw, ch = W / z, H / z
        x = min(max(cx * W - cw / 2, 0), W - cw)
        y = min(max(cy * H - ch * 0.42, 0), H - ch)
        vf += [f"scale={W}:{H}", f"crop={cw:.0f}:{ch:.0f}:{x:.0f}:{y:.0f}", f"scale={W}:{H}:flags=lanczos"]
    else:
        vf += [f"scale={W}:{H}"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(ep.clean_video),
                    "-vf", ",".join(vf + ["setsar=1"]), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-r", fps, str(out)], check=True)
    return out


def find_logo(ep: Episode) -> str | None:
    """A camera's burned-in name (DJI «OSMO NANO» top-left) is blurred away: it pulls the eye in every face shot.
    Found as a bright, still patch in the top-left that never changes across the video."""
    import cv2
    cap = cv2.VideoCapture(str(ep.clean_video))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    frames = []
    for k in range(6):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * (k + 0.5) / 6))
        ok, fr = cap.read()
        if ok:
            frames.append(cv2.resize(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), (W, H)).astype(np.float32))
    cap.release()
    if len(frames) < 3:
        return None
    st = np.stack(frames)
    region = st[:, : int(H * 0.35), : int(W * 0.35)]
    mask = ((region.std(axis=0) < 6) & (region.min(axis=0) > 215)).astype(np.uint8)
    # letters of one word sit close together: join them, then keep the biggest short, wide patch (the logo)
    mask = cv2.dilate(mask, np.ones((9, 25), np.uint8))
    n_lab, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    best = None
    for x, y, w, h, area in stats[1:]:
        if 20 <= h <= 120 and w >= 2 * h and (best is None or area > best[4]):
            best = (x, y, w, h, area)
    if best is None:
        return None
    x0, y0, x1, y1 = best[0], best[1], best[0] + best[2], best[1] + best[3]
    grown = True
    while grown:   # the brand and the model name are two words: take the neighbours on the same line too
        grown = False
        for x, y, w, h, area in stats[1:]:
            same_line = min(y1, y + h) - max(y0, y) > 0.5 * min(h, y1 - y0)
            near = x <= x1 + 90 and x + w >= x0 - 90
            if same_line and near and (x < x0 or x + w > x1) and h <= 120:
                x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x + w), max(y1, y + h)
                grown = True
    x0, y0, x1, y1 = x0 - 8, y0 - 6, x1 + 36, y1 + 6   # the last round letter is often softer: a wider margin
    return f"delogo=x={max(1, x0)}:y={max(1, y0)}:w={x1 - x0}:h={y1 - y0}"


# ---------- sound ----------

def mix(ep: Episode, video: Path, shots: list[dict], mood: str, out: Path) -> Path:
    """His voice levelled (no loud or quiet stretches), a music bed under it that ducks while he talks,
    and a sound under each graphic as it lands (paper for a cutting, a hit for a number, a whoosh for photos)."""
    from .composer import compose, write_wav
    from .sfx import sfx_path
    dur = clean_duration(ep)
    music = write_wav(compose(dur + 1.0, mood if mood in ("tension", "dark", "wonder", "sad", "drive") else "tension", 11),
                      ep.work / "archive_music.wav")
    # a sound under every graphic as it lands, and a soft whoosh where a run of photos starts
    events: dict[str, list[float]] = {}
    for k, s in enumerate(shots):
        kind = s["kind"]
        if kind in MOTION or (kind == "photo" and (k == 0 or shots[k - 1]["kind"] != "photo")):
            events.setdefault(SFX.get(kind, "whoosh_soft"), []).append(s["start"])
    inputs = ["-i", str(video), "-i", str(ep.clean_video), "-i", str(music)]
    graph = ["[1:a]highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,"
             "loudnorm=I=-15:TP=-1.5:LRA=7,aresample=48000,asplit=2[v][vk]",
             "[2:a]volume=0.32,aresample=48000[m]",
             "[m][vk]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md]"]
    mixes = ["[v]", "[md]"]
    n_in = 3
    for name, times in events.items():
        try:
            path = sfx_path(name)
        except Exception:   # noqa: BLE001 — a sound that can't be made: the others still play
            continue
        inputs += ["-i", str(path)]
        tags = [f"s{n_in}_{i}" for i in range(len(times))]
        graph.append(f"[{n_in}:a]aresample=48000,volume={0.5 if name.startswith('whoosh') else 0.35},asplit={len(times)}"
                     + "".join(f"[{t}]" for t in tags))
        for tag, t in zip(tags, times):
            ms = max(0, int((t - (0.15 if name.startswith(("whoosh", "swoosh")) else 0.0)) * 1000))
            graph.append(f"[{tag}]adelay={ms}|{ms}[{tag}d]")
            mixes.append(f"[{tag}d]")
        n_in += 1
    graph.append("".join(mixes) + f"amix=inputs={len(mixes)}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(graph), "-map", "0:v",
                    "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-t", f"{dur:.3f}",
                    "-movflags", "+faststart", str(out)], check=True)
    return out


# ---------- the whole thing ----------

def build(ep: Episode, ask, say=print, out: Path | None = None, reuse: bool = False) -> Path:
    """`reuse`: the shot list of the last build (only the drawing changes): fast, and the same pictures."""
    saved = ep.work / "archive_shots.json"
    if reuse and saved.exists():
        plan = json.loads(saved.read_text(encoding="utf-8"))
    else:
        say("🎞️ قالب الأرشيف: أكتب قائمة اللقطات…")
        plan = shot_list(ep, ask)
    shots = plan["shots"]
    say(f"🖼️ أجيب الصور ({sum(s['kind'] in PICTURED for s in shots)})، والموشن جرافك {sum(s['kind'] in MOTION for s in shots)}…")
    from .transcribe import load_words
    words = load_words(ep.clean_words)
    for s in shots:
        s["said"] = " ".join(w.text for w in words if s["start"] - 0.2 <= w.start < s["end"])
    fetch_pictures(ep, shots, ask)
    rate = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", str(ep.clean_video)], capture_output=True, text=True).stdout.strip() or "30"
    fps = eval(rate) if "/" in rate else float(rate)   # noqa: S307 — "24000/1001" from ffprobe
    work = ep.work / "archive"
    work.mkdir(parents=True, exist_ok=True)
    delogo = find_logo(ep)
    say("🎬 أرسم اللقطات…")
    # frame-exact lengths: each shot gets round(end*fps) - round(start*fps) frames, so the pieces add up to the voice
    film = Film()
    pieces, close = [], False

    def render(k_s):
        k, s = k_s
        n = round(s["end"] * fps) - round(s["start"] * fps)
        o = work / f"shot_{k:03d}.mp4"
        if s["kind"] == "photo":
            img = Image.open(ep.assets / "archive" / f"shot_{k}.jpg").convert("RGB")
            return encode(photo_frames(img, n, s, seed=k), o, rate, film)
        if s["kind"] in MOTION:
            from . import motion
            if s["kind"] == "person":
                img = Image.open(ep.assets / "archive" / f"shot_{k}.jpg").convert("RGB")
                frames = motion.person(img, s, n, fps, archive_look)
            else:
                frames = {"headline": motion.headline, "number": motion.number, "map": motion.world_map,
                          "text": motion.big_text}[s["kind"]](s, n, fps)
            return encode(frames, o, rate, film)
        return face_clip(ep, round(s["start"] * fps) / fps, n / fps, s["_close"], o, rate, delogo)
    for k, s in enumerate(shots):   # his face alternates medium / close, so the cut between two takes never jumps
        if s["kind"] == "face":
            s["_close"] = close
            close = not close
    with ThreadPoolExecutor(max_workers=3) as pool:
        pieces = list(pool.map(render, enumerate(shots)))
    listing = work / "concat.txt"
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in pieces), encoding="utf-8")
    silent = work / "video.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy",
                    str(silent)], check=True)
    say("🎵 الصوت: صوتك موزون، موسيقى تحته، ووووش على الصور…")
    final = out or (ep.edit / "archive.mp4")
    mix(ep, silent, shots, plan.get("mood", "tension"), final)
    credits = [json.loads(p.read_text(encoding="utf-8"))["credit"] for p in sorted((ep.assets / "archive").glob("shot_*.json"))]
    (ep.edit / "archive_credits.txt").write_text("\n".join(dict.fromkeys(credits)), encoding="utf-8")
    say(f"✅ جاهز: {final}")
    return final
