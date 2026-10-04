"""Real moving footage, free to use: Wikimedia Commons videos (free licences) and the Prelinger Archives
on archive.org (old films, public domain). A `footage` beat gets a clip cut to its length into
assets/footage_<i>.mp4; if nothing is found it falls back to its caption card."""
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import requests

from .media import MediaError, probe
from .paths import Episode
from .plan import EditPlan
from .wikimedia import API, HEADERS, _strip_html, license_ok

ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"
MAX_DOWNLOAD = 600e6       # bytes: skip films larger than this
MIN_WIDTH = 480


@dataclass
class Clip:
    title: str
    url: str
    duration: float
    license: str
    artist: str
    page: str


def search_commons_video(query: str, session) -> list[Clip]:
    params = {"action": "query", "generator": "search", "gsrsearch": f"{query} filetype:video", "gsrnamespace": 6,
              "gsrlimit": 8, "prop": "imageinfo", "iiprop": "url|size|extmetadata", "format": "json"}
    resp = session.get(API, params=params, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    out = []
    for p in sorted(((resp.json().get("query") or {}).get("pages") or {}).values(), key=lambda p: p.get("index", 0)):
        info = (p.get("imageinfo") or [{}])[0]
        lic = info.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
        if info.get("width", 0) < MIN_WIDTH or not license_ok(lic) or not info.get("duration"):
            continue
        out.append(Clip(p["title"], info["url"], float(info["duration"]), lic,
                        _strip_html(info.get("extmetadata", {}).get("Artist", {}).get("value", "")),
                        info.get("descriptionurl", "")))
    return out


def search_prelinger(query: str, session) -> list[Clip]:
    """Old films from the Prelinger Archives (public domain)."""
    resp = session.get(ARCHIVE_SEARCH, params={"q": f"collection:prelinger AND ({query})", "fl[]": ["identifier", "title"],
                                               "rows": 6, "output": "json"}, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    out = []
    for doc in resp.json().get("response", {}).get("docs", []):
        ident = doc["identifier"]
        meta = session.get(f"https://archive.org/metadata/{ident}", headers=HEADERS, timeout=60).json()
        lic = (meta.get("metadata", {}).get("licenseurl") or "public domain").lower()
        if "nc" in lic.split("/") or "nd" in lic.split("/"):
            continue
        mp4 = next((f for f in meta.get("files", []) if f.get("format") == "h.264" and f["name"].endswith(".mp4")
                    and float(f.get("size", 0)) < MAX_DOWNLOAD), None)
        if mp4:
            out.append(Clip(doc.get("title", ident), f"https://archive.org/download/{ident}/{mp4['name']}",
                            float(mp4.get("length") or 0), "Public domain (Prelinger Archives)", "Prelinger Archives",
                            f"https://archive.org/details/{ident}"))
    return out


def _download(url: str, cache: Path, session) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    out = cache / (hashlib.sha1(url.encode()).hexdigest()[:16] + Path(url.split("?")[0]).suffix)
    if out.exists():
        return out
    with session.get(url, headers=HEADERS, stream=True, timeout=120) as r:
        r.raise_for_status()
        part = out.with_suffix(".part")
        with open(part, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        part.rename(out)
    return out


def cut(src: Path, seconds: float, out: Path) -> Path:
    """A piece from about a third of the way in (skips titles), at most 1080p, no sound."""
    dur = probe(src).duration
    start = max(0.0, (dur - seconds) * 0.35) if dur > seconds else 0.0
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.2f}", "-t", f"{seconds + 0.5:.2f}", "-i", str(src),
                    "-vf", "scale='min(1920,iw)':-2", "-an", "-c:v", "libx264", "-crf", "16", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def collect_footage(plan: EditPlan, ep: Episode, session=None) -> tuple[list[dict], list[str]]:
    """Returns (fallbacks, credits). `source: "archive"` searches the old-film archive first."""
    session = session or requests.Session()
    fallbacks, credits, used = [], [], set()
    for i, b in enumerate(plan.beats):
        if b.kind != "footage":
            continue
        out = ep.assets / f"footage_{i}.mp4"
        meta = out.with_suffix(".json")
        if out.exists() and meta.exists() and json.loads(meta.read_text())["query"] == b.query:
            credits.append(json.loads(meta.read_text())["credit"])
            continue
        order = (search_prelinger, search_commons_video) if b.source == "archive" else (search_commons_video, search_prelinger)
        got, reason = None, "no free footage"
        for search in order:
            try:
                clips = [c for c in search(b.query, session) if c.url not in used]
            except (requests.RequestException, ValueError) as exc:
                reason = f"network: {exc}"
                continue
            for c in clips[:3]:
                try:
                    cut(_download(c.url, ep.work / "footage_cache", session), b.duration, out)
                except (requests.RequestException, subprocess.CalledProcessError, MediaError) as exc:
                    reason = f"download: {exc}"
                    continue
                got = c
                break
            if got:
                break
        if got is None:
            fallbacks.append({"beat": i, "query": b.query, "reason": reason[:200]})
            b.kind, b.graphic = "graphic", {"type": "text", "text": b.caption or b.query}
            continue
        used.add(got.url)
        credit = f"{got.title} — {got.artist} — {got.license} — {got.page}"
        meta.write_text(json.dumps({"query": b.query, "credit": credit}, ensure_ascii=False), encoding="utf-8")
        credits.append(credit)
    return fallbacks, credits
