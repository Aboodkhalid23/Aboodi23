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
