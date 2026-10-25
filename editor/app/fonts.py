"""The app's font library (owner, 2026-10-25): free fonts in two drawers, Arabic and Latin, downloaded on demand from
Google Fonts (all open licences), plus fonts he buys and adds himself. Kept in $MONTIER_HOME/fonts so updates never
lose them. The captions use the chosen ones (libass reads them from one folder per build)."""
import re
import shutil
import urllib.parse
from pathlib import Path

import requests

ARABIC = ["Cairo", "Tajawal", "Almarai", "Changa", "Lalezar", "Reem Kufi", "El Messiri", "Rakkas", "Amiri", "Aref Ruqaa",
          "Noto Kufi Arabic", "Noto Naskh Arabic", "Noto Sans Arabic", "IBM Plex Sans Arabic", "Readex Pro", "Alexandria",
          "Baloo Bhaijaan 2", "Markazi Text", "Mada", "Harmattan", "Lateef", "Scheherazade New", "Marhey", "Vibes", "Blaka",
          "Kufam", "Zain", "Lemonada", "Jomhuria", "Mirza", "Katibeh", "Gulzar", "Badeen Display", "Qahiri", "Rubik",
          "Noto Nastaliq Urdu", "Handjet", "Beiruti", "Playpen Sans Arabic", "Kalam"]
LATIN = ["Inter", "Montserrat", "Poppins", "Bebas Neue", "Anton", "Oswald", "Archivo Black", "Space Grotesk", "Syne",
         "Unbounded", "League Spartan", "Manrope", "Sora", "Outfit", "Plus Jakarta Sans", "Barlow Condensed", "Teko",
         "Big Shoulders Display", "Roboto Condensed", "Playfair Display", "DM Serif Display", "Instrument Serif", "Fraunces",
         "Cormorant Garamond", "EB Garamond", "Libre Baskerville", "Cinzel", "Abril Fatface", "Caveat", "Permanent Marker",
         "Bangers", "Righteous", "Lobster", "Space Mono", "JetBrains Mono", "Special Elite", "Courier Prime", "Rubik Mono One",
         "Black Ops One", "Monoton"]
EXT = (".ttf", ".otf")


def folder(home: Path) -> Path:
    f = home / "fonts"
    f.mkdir(parents=True, exist_ok=True)
    return f


def _family(path: Path) -> str:
    try:
        from PIL import ImageFont
        return ImageFont.truetype(str(path), 20).getname()[0]
    except Exception:
        return path.stem.split("-")[0]


def installed(home: Path) -> dict:
    """{family: file name} of every font he has (downloaded or his own)."""
    out = {}
    for f in sorted(folder(home).iterdir()):
        if f.suffix.lower() in EXT:
            out.setdefault(_family(f), f.name)
    return out


def catalog(home: Path) -> dict:
    have = installed(home)
    own = [k for k in have if k not in ARABIC and k not in LATIN]
    return {"arabic": [{"family": n, "have": n in have} for n in ARABIC],
            "latin": [{"family": n, "have": n in have} for n in LATIN],
            "own": [{"family": n, "file": have[n]} for n in own]}


def download(home: Path, family: str, session=None) -> dict:
    if family not in ARABIC + LATIN:
        raise ValueError("هذا الخط مو بالمكتبة")
    s = session or requests
    weight = "" if family in ("Lalezar", "Rakkas", "Bebas Neue", "Anton", "Archivo Black", "Bangers", "Righteous", "Lobster",
                              "Abril Fatface", "Permanent Marker", "Special Elite", "Rubik Mono One", "Black Ops One", "Monoton",
                              "Jomhuria", "Katibeh", "Mirza", "Lateef", "Gulzar", "Vibes", "Blaka", "Badeen Display", "Qahiri") else ":wght@700"
    css = s.get("https://fonts.googleapis.com/css2?family=" + urllib.parse.quote(family) + weight,
                headers={"User-Agent": "Mozilla/4.0"}, timeout=30)
    if css.status_code != 200 and weight:
        css = s.get("https://fonts.googleapis.com/css2?family=" + urllib.parse.quote(family), headers={"User-Agent": "Mozilla/4.0"}, timeout=30)
    urls = re.findall(r"url\((https://[^)]+\.(?:ttf|otf))\)", css.text)
    if not urls:
        raise ValueError("ما گدرت أنزّل الخط، تأكد من النت")
    data = s.get(urls[0], timeout=60).content
    dest = folder(home) / (family.replace(" ", "") + Path(urls[0]).suffix)
    dest.write_bytes(data)
    return catalog(home)


def add_own(home: Path, name: str, data: bytes) -> dict:
    """A font he bought: saved as it is (licence is his)."""
    name = Path(name).name
    if Path(name).suffix.lower() not in EXT or name.startswith("."):
        raise ValueError("الخط لازم ملف ttf أو otf")
    dest = folder(home) / name
    dest.write_bytes(data)
    try:
        _family(dest)
    except Exception:
        dest.unlink()
        raise ValueError("هذا الملف مو خط")
    return catalog(home)


def remove(home: Path, family: str) -> dict:
    f = installed(home).get(family)
    if f:
        (folder(home) / f).unlink(missing_ok=True)
    return catalog(home)


def caption_fonts_dir(home: Path, work: Path, families: list[str]) -> Path:
    """One folder for libass: our Vazirmatn plus the fonts the captions ask for."""
    out = work / "fonts"
    out.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve().parents[1] / "fonts"
    for f in src.glob("*.ttf"):
        shutil.copyfile(f, out / f.name)
    have = installed(home)
    for fam in families:
        if fam in have:
            shutil.copyfile(folder(home) / have[fam], out / have[fam])
    return out
