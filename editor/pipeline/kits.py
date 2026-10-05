"""Free animation kits for the stickers, fetched on demand and cached (owner: collect every free source):
  emoji  Google Noto ANIMATED emoji (Lottie, CC BY 4.0): 🔥 😱 💰 🤯 … move by themselves on screen
  icon   Iconify (200k+ icons): only sets whose licence allows a monetised video (MIT / Apache / ISC / CC0 / CC BY)"""
import json
from pathlib import Path

import requests

CACHE = Path.home() / ".cache" / "aboodi-kits"
HEADERS = {"User-Agent": "Aboodi23-editor/0.1 (github.com/Aboodkhalid23/Aboodi23)"}
ICON_SETS = {"fluent-emoji-flat": "MIT", "fluent-emoji": "MIT", "noto": "Apache-2.0", "twemoji": "CC BY 4.0",
             "mdi": "Apache-2.0", "ph": "MIT", "tabler": "MIT", "lucide": "ISC", "material-symbols": "Apache-2.0",
             "streamline-emojis": "CC BY 4.0", "game-icons": "CC BY 3.0"}


def emoji_code(char: str) -> str:
    """"🔥" → "1f525"; sequences joined by "_" (variation selector dropped), the way Noto names them."""
    return "_".join(f"{ord(c):x}" for c in char if ord(c) != 0xFE0F)


def emoji_lottie(char: str, session=None) -> dict | None:
    code = emoji_code(char)
    f = CACHE / "emoji" / f"{code}.json"
    if f.exists():
        return json.loads(f.read_text())
    try:
        r = (session or requests).get(f"https://fonts.gstatic.com/s/e/notoemoji/latest/{code}/lottie.json",
                                      headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return None
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data))
    return data


def icon_svg(name: str, session=None) -> Path | None:
    """"fluent-emoji-flat:factory" → a cached SVG file (None if the set's licence isn't allowed or it doesn't exist)."""
    if ":" not in name or name.split(":", 1)[0] not in ICON_SETS:
        return None
    prefix, icon = name.split(":", 1)
    f = CACHE / "icons" / f"{prefix}__{icon}.svg"
    if f.exists():
        return f
    try:
        r = (session or requests).get(f"https://api.iconify.design/{prefix}/{icon}.svg", params={"height": 512},
                                      headers=HEADERS, timeout=30)
        r.raise_for_status()
    except requests.RequestException:
        return None
    if not r.text.lstrip().startswith("<svg"):
        return None
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(r.text)
    return f


def prepare_stickers(stickers: list[dict], publish) -> list[dict]:
    """Stickers ready for Remotion: an emoji carries its animation, an icon its published SVG file.
    One that can't be fetched becomes a plain stamp with its text (never a broken frame)."""
    out = []
    for st in stickers or []:
        st = dict(st)
        if st.get("type") == "emoji":
            data = emoji_lottie(st.get("text", ""))
            st = {**st, "data": data} if data else {**st, "type": "burst"}
        elif st.get("type") == "icon":
            svg = icon_svg(st.get("text", ""))
            st = {**st, "src": publish(svg)} if svg else {**st, "type": "stamp", "text": st.get("label", "")}
        out.append(st)
    return out
