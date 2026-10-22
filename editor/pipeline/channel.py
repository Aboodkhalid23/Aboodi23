"""The owner's channel (name, handle, avatar) for the subscribe / TV scenes. Public info only."""
import json
from pathlib import Path

import requests

CHANNEL_FILE = Path(__file__).resolve().parent.parent / "channel.json"


def load_channel() -> dict:
    d = json.loads(CHANNEL_FILE.read_text(encoding="utf-8"))
    return {"name": d["name"], "handle": d.get("handle", "")}


def channel_avatar(cache_dir: Path) -> Path | None:
    """Download the channel picture once per episode; None (initial letter instead) if offline."""
    out = Path(cache_dir) / "channel_avatar.jpg"
    if out.exists():
        return out
    url = json.loads(CHANNEL_FILE.read_text(encoding="utf-8")).get("avatar_url")
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException:
        print("⚠️  ما گدرت أنزّل صورة القناة، أستخدم أول حرف من الاسم")
        return None
    out.write_bytes(resp.content)
    return out


def channel_videos(cache_dir: Path, n: int = 4) -> list[dict]:
    """His latest videos from the channel's public feed (title, views, thumbnail downloaded into cache_dir), for
    the "search" subscribe scene. Empty when offline: the scene then shows the channel alone."""
    import re
    import xml.etree.ElementTree as ET
    out_file = Path(cache_dir) / "channel_videos.json"
    if out_file.exists():
        return json.loads(out_file.read_text(encoding="utf-8"))
    cid = json.loads(CHANNEL_FILE.read_text(encoding="utf-8")).get("id")
    if not cid:
        return []
    try:
        r = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except (requests.RequestException, ET.ParseError):
        return []
    ns = {"a": "http://www.w3.org/2005/Atom", "m": "http://search.yahoo.com/mrss/", "yt": "http://www.youtube.com/xml/schemas/2015"}
    videos = []
    for e in root.findall("a:entry", ns)[:n]:
        vid = e.findtext("yt:videoId", default="", namespaces=ns)
        title = e.findtext("a:title", default="", namespaces=ns)
        stats = e.find("m:group/m:community/m:statistics", ns)
        views = int(stats.get("views")) if stats is not None and stats.get("views", "").isdigit() else None
        thumb = None
        try:
            t = requests.get(f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg", timeout=30)
            t.raise_for_status()
            thumb = Path(cache_dir) / f"yt_{vid}.jpg"
            thumb.write_bytes(t.content)
        except requests.RequestException:
            pass
        videos.append({"title": re.sub(r"\s+", " ", title).strip(), "views": views, "thumb": str(thumb) if thumb else None})
    out_file.write_text(json.dumps(videos, ensure_ascii=False, indent=1), encoding="utf-8")
    return videos
