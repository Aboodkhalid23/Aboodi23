"""Where real pictures and footage come from. Wikimedia alone is thin, so every search asks several
libraries and keeps the best match. Only sources whose licence allows a monetised video:

  pictures  Wikimedia Commons, Openverse (Flickr and museum photos under CC BY / CC0 / public domain),
            Library of Congress (historic photos), NASA, and — with a free key — Pexels and Pixabay
  footage   Pexels and Pixabay videos (free key), archive.org public-domain films (Prelinger, FedFlix,
            NASA…), NASA videos, Wikimedia Commons videos

`source` on a beat steers the order: "archive" (history: old photos and films first), "stock" (modern
everyday scenes: Pexels / Pixabay first), or nothing (named people, places and events: encyclopaedic
sources first). Keys come from the environment only (PEXELS_API_KEY, PIXABAY_API_KEY), never the repo."""
import os
import re
from dataclasses import dataclass

import requests

HEADERS = {"User-Agent": "Aboodi23-editor/0.1 (github.com/Aboodkhalid23/Aboodi23)"}
MIN_IMAGE_WIDTH = 1000
MIN_VIDEO_WIDTH = 640
OLD = re.compile(r"\b(1[0-8]\d\d|19[0-8]\d)s?\b|\b(history|historic|vintage|archive|old|ancient|war|empire|ottoman)\b", re.I)


@dataclass
class Found:
    provider: str
    title: str
    url: str
    width: int
    height: int
    license: str
    artist: str
    page: str
    words: str = ""          # title + tags, for matching the query
    duration: float = 0.0    # videos

    @property
    def credit(self) -> str:
        return f"{self.title} — {self.artist or self.provider} — {self.license} — {self.page}"


def _words(*parts) -> str:
    out = []
    for p in parts:
        out += p if isinstance(p, list) else [str(p or "")]
    return " ".join(out)[:2000]


def _json(session, url, **params):
    r = session.get(url, params=params, headers=HEADERS, timeout=45)
    r.raise_for_status()
    return r.json()


# ---------- pictures ----------

def commons_images(q, session):
    from .wikimedia import search_commons
    return [Found("Wikimedia Commons", c.title, c.url, c.width, c.height, c.license, c.artist, c.page_url, c.title)
            for c in search_commons(q, session=session)]


def openverse_images(q, session):
    d = _json(session, "https://api.openverse.org/v1/images/", q=q, page_size=12, license_type="commercial,modification",
              size="large", mature="false")
    out = []
    for r in d.get("results", []):
        lic = f"CC {r.get('license', '').upper()} {r.get('license_version') or ''}".strip()
        if r.get("license") in ("cc0", "pdm"):
            lic = "Public domain" if r["license"] == "pdm" else "CC0"
        words = " ".join([r.get("title") or ""] + [t.get("name", "") for t in r.get("tags") or []])
        out.append(Found("Openverse/" + (r.get("source") or "?"), r.get("title") or q, r["url"], r.get("width") or 0,
                         r.get("height") or 0, lic, r.get("creator") or "", r.get("foreign_landing_url") or "", words))
    return out


def loc_images(q, session):
    """Library of Congress photos. The rights line is checked on the item page when one is picked."""
    d = _json(session, "https://www.loc.gov/photos/", q=q, fo="json", c=12)
    out = []
    for r in d.get("results", []):
        best = None
        for u in r.get("image_url") or []:
            m = re.search(r"#h=(\d+)&w=(\d+)", u)
            if m and u.split("#")[0].endswith(".jpg") and (best is None or int(m.group(2)) > best[2]):
                best = (u.split("#")[0], int(m.group(1)), int(m.group(2)))
        if best:
            out.append(Found("Library of Congress", r.get("title") or q, best[0], best[2], best[1],
                             "No known restrictions (Library of Congress)", "Library of Congress", r.get("url") or "",
                             f"{r.get('title') or ''} {' '.join(r.get('subject') or [])}"))
    return out


def loc_rights_ok(found: Found, session) -> bool:
    try:
        item = _json(session, found.page, fo="json").get("item", {})
    except (requests.RequestException, ValueError):
        return False
    rights = " ".join(item.get("rights_advisory") or []) + " " + " ".join(item.get("rights") or [])
    return bool(re.search(r"no known restrictions|public domain|no known copyright", rights, re.I))


def nasa_images(q, session):
    d = _json(session, "https://images-api.nasa.gov/search", q=q, media_type="image")
    out = []
    for it in d.get("collection", {}).get("items", [])[:12]:
        meta = (it.get("data") or [{}])[0]
        nid = meta.get("nasa_id", "")
        url = f"https://images-assets.nasa.gov/image/{nid}/{nid}~orig.jpg"
        out.append(Found("NASA", meta.get("title") or q, url, 1920, 1080, "NASA media (not copyrighted)",
                         meta.get("center") or "NASA", f"https://images.nasa.gov/details/{nid}",
                         f"{meta.get('title', '')} {' '.join(meta.get('keywords') or [])}"))
    return out


def pexels_images(q, session):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return []
    r = session.get("https://api.pexels.com/v1/search", params={"query": q, "per_page": 12, "orientation": "landscape"},
                    headers={**HEADERS, "Authorization": key}, timeout=45)
    r.raise_for_status()
    return [Found("Pexels", p.get("alt") or q, p["src"]["large2x"], p["width"], p["height"], "Pexels License",
                  p.get("photographer") or "", p.get("url") or "", p.get("alt") or "") for p in r.json().get("photos", [])]


def pixabay_images(q, session):
    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        return []
    d = _json(session, "https://pixabay.com/api/", key=key, q=q, image_type="photo", orientation="horizontal",
              per_page=12, safesearch="true")
    return [Found("Pixabay", h.get("tags") or q, h.get("largeImageURL") or h["webformatURL"], h["imageWidth"],
                  h["imageHeight"], "Pixabay Content License", h.get("user") or "", h.get("pageURL") or "",
                  h.get("tags") or "") for h in d.get("hits", [])]


# ---------- footage ----------

def pexels_videos(q, session):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return []
    r = session.get("https://api.pexels.com/videos/search", params={"query": q, "per_page": 10, "orientation": "landscape"},
                    headers={**HEADERS, "Authorization": key}, timeout=45)
    r.raise_for_status()
    out = []
    for v in r.json().get("videos", []):
        files = sorted([f for f in v.get("video_files", []) if (f.get("width") or 0) <= 1920 and f.get("file_type") == "video/mp4"],
                       key=lambda f: -(f.get("width") or 0))
        if files:
            slug = (v.get("url") or "").rstrip("/").split("/")[-1].replace("-", " ")
            out.append(Found("Pexels", slug or q, files[0]["link"], files[0]["width"], files[0]["height"], "Pexels License",
                             (v.get("user") or {}).get("name", ""), v.get("url") or "", slug, float(v.get("duration") or 0)))
    return out


def pixabay_videos(q, session):
    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        return []
    d = _json(session, "https://pixabay.com/api/videos/", key=key, q=q, per_page=10, safesearch="true")
    out = []
    for h in d.get("hits", []):
        v = (h.get("videos") or {}).get("large") or (h.get("videos") or {}).get("medium") or {}
        if v.get("url"):
            out.append(Found("Pixabay", h.get("tags") or q, v["url"], v.get("width") or 0, v.get("height") or 0,
                             "Pixabay Content License", h.get("user") or "", h.get("pageURL") or "", h.get("tags") or "",
                             float(h.get("duration") or 0)))
    return out


_LIC = ["http://creativecommons.org/publicdomain/zero/1.0/", "http://creativecommons.org/publicdomain/mark/1.0/"] + \
    [f"http://creativecommons.org/licenses/by/{v}/" for v in ("2.0", "2.5", "3.0", "4.0")]
# (archive.org's search breaks on wildcards in licenseurl: exact licence links only)
ARCHIVE_FREE = "collection:(prelinger OR fedflix OR nasa) OR licenseurl:(" + " OR ".join(f'"{u}"' for u in _LIC) + ")"


def archive_videos(q, session, max_bytes: float = 600e6):
    """Public-domain and CC BY films on archive.org (old newsreels, government and educational films)."""
    d = _json(session, "https://archive.org/advancedsearch.php", q=f"({q}) AND mediatype:movies AND ({ARCHIVE_FREE})",
              **{"fl[]": ["identifier", "title", "subject", "description"], "sort[]": "downloads desc"}, rows=8, output="json")
    out = []
    for doc in d.get("response", {}).get("docs", []):
        ident = doc["identifier"]
        try:
            meta = _json(session, f"https://archive.org/metadata/{ident}")
        except (requests.RequestException, ValueError):
            continue
        lic = (meta.get("metadata", {}).get("licenseurl") or "public domain").lower()
        if any(p in lic.split("/") for p in ("by-nc", "by-nd", "by-nc-sa", "by-nc-nd", "nc", "nd")):
            continue
        mp4 = next((f for f in meta.get("files", []) if f.get("name", "").endswith(".mp4")
                    and f.get("format") in ("h.264", "MPEG4", "h.264 IA") and float(f.get("size", 0)) < max_bytes), None)
        if mp4:
            title = doc.get("title") or ident
            out.append(Found("Internet Archive", title, f"https://archive.org/download/{ident}/{mp4['name']}",
                             int(mp4.get("width") or 640), int(mp4.get("height") or 480),
                             "Public domain" if "creativecommons" not in lic else lic, "Internet Archive",
                             f"https://archive.org/details/{ident}", _words(title, doc.get("subject"), doc.get("description")),
                             float(mp4.get("length") or 0)))
    return out


def nasa_videos(q, session):
    d = _json(session, "https://images-api.nasa.gov/search", q=q, media_type="video")
    out = []
    for it in d.get("collection", {}).get("items", [])[:5]:
        meta = (it.get("data") or [{}])[0]
        try:
            files = session.get(it["href"], headers=HEADERS, timeout=45).json()
        except (requests.RequestException, ValueError):
            continue
        mp4 = next((f for tag in ("~large.mp4", "~medium.mp4", "~orig.mp4") for f in files if f.endswith(tag)), None)
        if mp4:
            out.append(Found("NASA", meta.get("title") or q, mp4.replace("http://", "https://"), 1280, 720,
                             "NASA media (not copyrighted)", "NASA", f"https://images.nasa.gov/details/{meta.get('nasa_id', '')}",
                             f"{meta.get('title', '')} {' '.join(meta.get('keywords') or [])}"))
    return out


def commons_videos(q, session):
    from .footage import search_commons_video
    return [Found("Wikimedia Commons", c.title, c.url, MIN_VIDEO_WIDTH, 360, c.license, c.artist, c.page, c.title, c.duration)
            for c in search_commons_video(q, session)]


# ---------- choosing ----------

IMAGE_ORDER = {
    "auto": (commons_images, openverse_images, pexels_images, pixabay_images, loc_images, nasa_images),
    "archive": (loc_images, commons_images, openverse_images, nasa_images),
    "stock": (pexels_images, pixabay_images, openverse_images, commons_images),
}
VIDEO_ORDER = {
    "auto": (pexels_videos, pixabay_videos, commons_videos, archive_videos, nasa_videos),
    "archive": (archive_videos, commons_videos, nasa_videos),
    "stock": (pexels_videos, pixabay_videos, archive_videos, commons_videos),
}


def guess_source(query: str, source: str | None) -> str:
    if source in IMAGE_ORDER:
        return source
    return "archive" if OLD.search(query or "") else "auto"


def relevance(query: str, words: str) -> float:
    """Share of the query's words found in the result's title / tags."""
    q = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2] or re.findall(r"[a-z0-9]+", query.lower())
    have = set(re.findall(r"[a-z0-9]+", words.lower()))
    return sum(any(h.startswith(w) or w.startswith(h) and len(h) > 3 for h in have) for w in q) / max(1, len(q))


def find(query: str, kind: str = "image", source: str | None = None, session=None, used=frozenset(),
         errors: list | None = None) -> list[Found]:
    """Candidates from every library for `query`, best first: on-topic matches first, then the
    preferred libraries for this kind of beat, then bigger files. Failing libraries are skipped."""
    session = session or requests.Session()
    order = (IMAGE_ORDER if kind == "image" else VIDEO_ORDER)[guess_source(query, source)]
    min_w = MIN_IMAGE_WIDTH if kind == "image" else MIN_VIDEO_WIDTH
    scored = []
    for rank, search in enumerate(order):
        try:
            results = search(query, session)
            plain = re.sub(r"\b\d{3,4}s?\b", " ", query).strip()
            if not results and plain != query and plain:   # catalogues often miss "1950s": try without dates
                results = search(plain, session)
        except (requests.RequestException, ValueError, KeyError, AttributeError, TypeError) as exc:
            if errors is not None:
                errors.append(f"{search.__name__}: {str(exc)[:120]}")
            continue
        for pos, f in enumerate(results):
            if f.url in used or f.width < min_w:
                continue
            rel = relevance(query, f.words or f.title)
            # nothing in common with the query in the title / tags: only if nothing better exists
            score = rel * 3 - (2 if rel == 0 else 0) - rank * 0.35 - pos * 0.04 + min(f.width, 3000) / 6000
            scored.append((score, f))
    return [f for _, f in sorted(scored, key=lambda s: -s[0])]


def download(f: Found, session) -> bytes:
    """The file's bytes (Wikimedia's polite retry on rate limits); raises requests errors."""
    if f.provider == "Wikimedia Commons" or "wikimedia.org" in f.url:   # also Openverse results hosted there
        from .wikimedia import _get
        return _get(session, f.url).content
    r = session.get(f.url, headers=HEADERS, timeout=90)
    r.raise_for_status()
    return r.content
