"""Stage 5: free, properly licensed images: Wikimedia Commons search here, and every other library in sources.py."""
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from .paths import Episode
from .plan import EditPlan, save_plan
from .styles import load_style
from .vary import assign_variety

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "Aboodi23-editor/0.1 (github.com/Aboodkhalid23/Aboodi23)"}
MIN_WIDTH = 1280
DRAWING_WORDS = ("diagram", "chart", "graph", "schema", "example", "logo", "icon", "map", "plot", "svg")
RETRIES = 4


def _get(session, url, **kw):
    """GET that honours Wikimedia's 429 Retry-After (shared cloud IPs hit the anonymous limit)."""
    for attempt in range(RETRIES):
        resp = session.get(url, headers=HEADERS, timeout=60, **kw)
        if resp.status_code != 429:
            resp.raise_for_status()
            return resp
        time.sleep(min(60, int(resp.headers.get("Retry-After", 5 * (attempt + 1)))))
    resp.raise_for_status()
    return resp


@dataclass
class CommonsImage:
    title: str
    url: str
    width: int
    height: int
    license: str
    artist: str
    page_url: str


def license_ok(name: str) -> bool:
    n = name.lower().strip()
    if n.startswith("cc0") or "public domain" in n or n.startswith("pd"):
        return True
    return n.startswith("cc by") and "nc" not in n and "nd" not in n


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def search_commons(query: str, limit: int = 8, session=None) -> list[CommonsImage]:
    session = session or requests.Session()
    params = {"action": "query", "generator": "search", "gsrsearch": query, "gsrnamespace": 6,
              "gsrlimit": limit, "prop": "imageinfo", "iiprop": "url|size|extmetadata",
              "iiurlwidth": 1920, "format": "json"}
    resp = _get(session, API, params=params)
    pages = (resp.json().get("query") or {}).get("pages", {})
    out = []
    for p in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        lic = meta.get("LicenseShortName", {}).get("value", "")
        if info.get("width", 0) < MIN_WIDTH or not license_ok(lic):
            continue
        out.append(CommonsImage(p["title"], info.get("thumburl") or info["url"], info["width"],
                                info["height"], lic, _strip_html(meta.get("Artist", {}).get("value", "")),
                                info.get("descriptionurl", "")))
    # Real photographs first: drawings, charts and logos only when nothing else fits (or when asked for)
    q = query.lower()
    def drawing(img: CommonsImage) -> bool:
        t = img.title.lower()
        return not t.endswith((".jpg", ".jpeg")) or any(w in t and w not in q for w in DRAWING_WORDS)
    return sorted(out, key=drawing)


def _has_people(path: Path) -> bool:
    from .masks import person_cutout
    cut = person_cutout(path, path.with_name(path.stem + "_people_check.png"))
    if cut:
        cut.unlink(missing_ok=True)
    return cut is not None


def collect_images(plan: EditPlan, ep: Episode, session=None) -> EditPlan:
    """Download one image per `image` beat to assets/img_<beat index>.<ext> from the best of all the
    libraries (sources.find); fall back to text."""
    from .sources import download, find, loc_rights_ok
    session = session or requests.Session()
    style = load_style(plan.style["primary"])
    used, fallbacks, credits = set(), [], []
    for i, b in enumerate(plan.beats):
        if b.kind != "image" and not (b.kind == "face_cutout" and b.query):
            continue
        img, errors = None, []
        candidates = find(b.query, "image", b.source, session, used, errors)
        reason = "no free image" + (f" ({'; '.join(errors)})" if errors else "")
        for c in candidates[:8 if b.treatment == 'scene' else 4]:  # one file refusing to download (rate limit) shouldn't lose the beat
            if c.provider == "Library of Congress" and not loc_rights_ok(c, session):
                continue
            try:
                data = download(c, session)
            except requests.RequestException as exc:
                reason = f"network: {exc}"
                continue
            ext = Path(c.url.split("?")[0]).suffix.lower()
            dest = ep.assets / f"img_{i}{ext if ext in ('.jpg', '.jpeg', '.png', '.webp') else '.jpg'}"
            dest.write_bytes(data)
            if b.kind == "face_cutout" and b.treatment == "scene" and _has_people(dest):
                dest.unlink()                 # he is moved INTO this place: it must be empty of other people
                reason = "every picture of the place had people in it"
                continue
            img = c
            break
        if img is None and b.kind == "face_cutout":   # the cut-out simply shows its caption instead
            continue
        if img is None and b.prompt:      # no real picture exists: generate it (owner's rule: AI only then)
            fallbacks.append({"beat": i, "query": b.query, "reason": reason[:300], "now": "ai_image"})
            b.kind = "ai_image"
            continue
        if img is None:
            fallbacks.append({"beat": i, "query": b.query, "reason": reason[:300]})
            b.kind, b.graphic = "graphic", {"type": "text", "text": b.caption or b.query}
            continue
        used.add(img.url)
        credits.append(img.credit)
    from .articles import collect_articles
    from .footage import collect_footage
    fallbacks += collect_articles(plan, ep)
    fb, footage_credits = collect_footage(plan, ep, session)
    fallbacks += fb
    credits += footage_credits
    assign_variety(plan, style)
    ep.fallbacks.write_text(json.dumps(fallbacks, ensure_ascii=False, indent=1), encoding="utf-8")
    ent = ep.work / "entity_credits.json"
    credits += list(json.loads(ent.read_text(encoding="utf-8")).values()) if ent.exists() else []
    mus = ep.work / "music_credits.json"
    credits += [c["credit"] for c in json.loads(mus.read_text(encoding="utf-8")).values()] if mus.exists() else []
    ep.credits.write_text("\n".join(credits) + ("\n" if credits else ""), encoding="utf-8")
    save_plan(plan, ep.plan)
    return plan
