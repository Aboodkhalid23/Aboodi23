"""Real photos of the people and companies named in the script (Wikidata → Wikimedia Commons).

Claude reads the script and writes edit/entities.json:
  [{"id": "musk", "name": "إيلون ماسك", "en": "Elon Musk", "kind": "person", "role": "مؤسس تسلا",
    "qid": "Q317521" (optional: skips the search), "heard": ["ايلون موسك"] (optional: how he may say it)}]
"""
import json
import re
from pathlib import Path
from urllib.parse import quote

import requests

from .paths import Episode
from .wikimedia import HEADERS, _get, _strip_html, license_ok

WIKIDATA = "https://www.wikidata.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
FILEPATH = "https://commons.wikimedia.org/wiki/Special:FilePath/{}?width=1600"
KINDS = ("person", "company")
# person: photo (P18). company: logo (P154), then any image (P18).
PROPS = {"person": ("P18",), "company": ("P154", "P18")}


def entities_file(ep: Episode) -> Path:
    return ep.edit / "entities.json"


def load_entities(ep: Episode) -> dict[str, dict]:
    f = entities_file(ep)
    if not f.exists():
        return {}
    return {e["id"]: e for e in json.loads(f.read_text(encoding="utf-8"))}


def entity_image(ep: Episode, entity_id: str | None) -> Path | None:
    if not entity_id:
        return None
    return next(iter(sorted(ep.assets.glob(f"entity_{entity_id}.*"))), None)


def find_qid(name_en: str, session) -> str | None:
    resp = _get(session, WIKIDATA, params={"action": "wbsearchentities", "search": name_en, "language": "en",
                                            "type": "item", "limit": 1, "format": "json"})
    hits = resp.json().get("search", [])
    return hits[0]["id"] if hits else None


def image_file(qid: str, kind: str, session) -> str | None:
    """Commons file name of the entity's photo / logo, or None."""
    resp = _get(session, WIKIDATA, params={"action": "wbgetclaims", "entity": qid, "format": "json"})
    claims = resp.json().get("claims", {})
    for prop in PROPS[kind]:
        for c in claims.get(prop, []):
            value = c.get("mainsnak", {}).get("datavalue", {}).get("value")
            if isinstance(value, str) and value:
                return value
    return None


def file_license(title: str, session) -> tuple[str, str, str]:
    """(licence, artist, page url) of a Commons file."""
    resp = _get(session, COMMONS, params={"action": "query", "titles": f"File:{title}", "prop": "imageinfo",
                                          "iiprop": "extmetadata|url", "format": "json"})
    page = next(iter(resp.json().get("query", {}).get("pages", {}).values()), {})
    info = (page.get("imageinfo") or [{}])[0]
    meta = info.get("extmetadata", {})
    return (meta.get("LicenseShortName", {}).get("value", ""), _strip_html(meta.get("Artist", {}).get("value", "")),
            info.get("descriptionurl", ""))


def _ext(resp, url: str) -> str:
    ctype = resp.headers.get("Content-Type", "")
    for mime, ext in (("png", ".png"), ("jpeg", ".jpg"), ("webp", ".webp"), ("gif", ".gif")):
        if mime in ctype:
            return ext
    return Path(url.split("?")[0]).suffix.lower() or ".jpg"


def fetch_entities(ep: Episode, session=None) -> tuple[list[str], list[str]]:
    """Download one picture per entity to assets/entity_<id>.<ext>. Returns (found ids, missing messages).
    Same licence rule as every other image; plain-text company logos are public domain on Commons."""
    session = session or requests.Session()
    ents = load_entities(ep)
    cfile = ep.work / "entity_credits.json"
    known = json.loads(cfile.read_text(encoding="utf-8")) if cfile.exists() else {}
    known = known if isinstance(known, dict) else {}
    found, missing, credits = [], [], {}
    for eid, e in ents.items():
        kind = e.get("kind", "person")
        if kind not in KINDS:
            missing.append(f"{e.get('name', eid)}: kind لازم person أو company")
            continue
        if entity_image(ep, eid):
            found.append(eid)
            if eid in known:
                credits[eid] = known[eid]
            continue
        try:
            qid = e.get("qid") or find_qid(e["en"], session)
            title = image_file(qid, kind, session) if qid else None
            lic = file_license(title, session) if title else ("", "", "")
            if title and license_ok(lic[0]):
                url = FILEPATH.format(quote(title.replace(" ", "_")))
                resp = _get(session, url)
                content, ext = resp.content, _ext(resp, url)
            else:   # no free portrait on Wikidata: every photo library, the full name must match
                from .sources import download, find, relevance
                hit = next((f for f in find(e["en"], "image", None, session) if relevance(e["en"], f.words or f.title) >= 0.99), None)
                if not hit:
                    missing.append(f"{e.get('name', eid)} ({e['en']}): ما لگيت صورة حرة. حط qid من wikidata.org")
                    continue
                title, lic = hit.title.removeprefix("File:"), (hit.license, hit.artist, hit.page)
                content = download(hit, session)
                ext = Path(hit.url.split("?")[0]).suffix.lower()
                ext = ext if ext in (".jpg", ".jpeg", ".png", ".webp") else ".jpg"
            (ep.assets / f"entity_{eid}{ext}").write_bytes(content)
        except requests.RequestException as exc:
            missing.append(f"{e.get('name', eid)}: مشكلة شبكة ({exc})")
            continue
        found.append(eid)
        credits[eid] = f"{title} — {lic[1]} — {lic[0]} — {lic[2]}"
    cfile.write_text(json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")
    return found, missing


def entity_vocab(ep: Episode) -> list[str]:
    """Names to give Whisper as hot words: Arabic spelling and the English name."""
    words = []
    for e in load_entities(ep).values():
        words += [e.get("name", ""), e.get("en", "")]
    return [w for w in words if w]


def entity_tokens(ep: Episode) -> set[str]:
    """Normalised single words of every entity name (for the script alignment)."""
    from .clean import normalize_ar
    out = set()
    for e in load_entities(ep).values():
        for w in re.split(r"\s+", e.get("name", "")):
            if len(w) > 1:
                out.add(normalize_ar(w))
    return out
