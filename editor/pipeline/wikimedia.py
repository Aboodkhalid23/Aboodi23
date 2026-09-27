"""Stage 5: free, properly licensed images from Wikimedia Commons."""
import json
import re
from dataclasses import dataclass
from pathlib import Path

import requests

from .paths import Episode
from .plan import EditPlan, save_plan
from .styles import load_style

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "Aboodi23-editor/0.1 (github.com/Aboodkhalid23/Aboodi23)"}
MIN_WIDTH = 1280


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
    resp = session.get(API, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
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
    return out


def collect_images(plan: EditPlan, ep: Episode, session=None) -> EditPlan:
    """Download one image per `image` beat to assets/img_<beat index>.<ext>; fall back to text."""
    session = session or requests.Session()
    treatment = load_style(plan.style["primary"]).image_treatment
    used, fallbacks, credits = set(), [], []
    for i, b in enumerate(plan.beats):
        if b.kind != "image":
            continue
        try:
            img = next((c for c in search_commons(b.query, session=session) if c.title not in used), None)
            if img:
                ext = Path(img.url.split("?")[0]).suffix.lower() or ".jpg"
                data = session.get(img.url, headers=HEADERS, timeout=60)
                data.raise_for_status()
                (ep.assets / f"img_{i}{ext}").write_bytes(data.content)
        except requests.RequestException as exc:
            img, reason = None, f"network: {exc}"
        else:
            reason = "no free image"
        if img is None:
            fallbacks.append({"beat": i, "query": b.query, "reason": reason})
            b.kind, b.graphic = "graphic", {"type": "text", "text": b.query}
            continue
        used.add(img.title)
        b.treatment = b.treatment or treatment
        credits.append(f"{img.title} — {img.artist} — {img.license} — {img.page_url}")
    ep.fallbacks.write_text(json.dumps(fallbacks, ensure_ascii=False, indent=1), encoding="utf-8")
    ep.credits.write_text("\n".join(credits) + ("\n" if credits else ""), encoding="utf-8")
    save_plan(plan, ep.plan)
    return plan
