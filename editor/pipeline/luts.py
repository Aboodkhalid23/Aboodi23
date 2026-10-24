"""Colour cubes for the Mac app's looks (owner, 2026-10-24: "كامرتي سوني، راح أصور بدون ألوان وأضيف ألوان جاهزة
أو قوية").

A look is baked into one 3D LUT (.cube): the camera conversion first (Sony S-Log3 / S-Gamut3.Cine → normal
display colours, from Sony's published formulas), then the look's colour filters, mixed with the converted
picture by the owner's "strength" (0–1). One lut3d filter then does it all in the render, so the strength
works for every look, and the app's thumbnails show exactly what the render will do.
Filters that look at neighbouring pixels (grain, vignette, denoise, sharpening) cannot live in a cube: they are
returned apart and run after it.
"""
import hashlib
import re
import subprocess
from pathlib import Path

import numpy as np

SIZE = 33
SPATIAL = {"noise", "vignette", "hqdn3d", "unsharp", "gblur", "boxblur", "smartblur", "deband"}
# S-Gamut3.Cine → BT.709 primaries (linear light); each row sums to 1, so white stays white
SGAMUT3CINE_TO_709 = np.array([[1.6269474, -0.5401385, -0.0868089],
                               [-0.1785155, 1.4179409, -0.2394254],
                               [0.0444361, -0.1959199, 1.1514838]])
SOURCES = {"rec709": "عادي", "slog3": "سوني لوگ ٣"}


def split_chain(chain: str) -> tuple[str, str]:
    """(colour-only filters, neighbourhood filters) of an ffmpeg chain; quotes keep their commas."""
    parts = re.findall(r"(?:[^,']|'[^']*')+", chain or "")
    pix = [p for p in parts if p.split("=")[0].strip() not in SPATIAL and p.strip()]
    spatial = [p for p in parts if p.split("=")[0].strip() in SPATIAL]
    return ",".join(pix), ",".join(spatial)


def slog3_to_display(rgb: np.ndarray) -> np.ndarray:
    """Sony S-Log3/S-Gamut3.Cine (as ffmpeg hands it over: full-range RGB 0–1 from legal-range video) →
    display RGB. Sony's S-Log3 decode, the gamut matrix, a filmic tone curve (soft highlights, mid grey ≈ 0.5),
    then the display gamma."""
    code = (rgb * 876 + 64) / 1023                     # back to 10-bit legal code values / 1023
    lin = np.where(code >= 171.2102946929 / 1023,
                   10 ** ((code * 1023 - 420) / 261.5) * (0.18 + 0.01) - 0.01,
                   (code * 1023 - 95) * 0.01125 / (171.2102946929 - 95))
    lin = np.clip(lin, 0, None) @ SGAMUT3CINE_TO_709.T
    x = np.clip(lin, 0, None) * 0.8
    tone = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)   # filmic shoulder (ACES-like, fitted)
    return np.clip(tone, 0, 1) ** (1 / 2.4)


CONVERT = {"rec709": lambda g: g, "slog3": slog3_to_display}


def _grid(size: int = SIZE) -> np.ndarray:
    """Every lattice point, red changing fastest (the .cube order), as (size³, 3)."""
    i = np.arange(size ** 3)
    return np.stack([i % size, (i // size) % size, i // (size * size)], axis=1) / (size - 1)


def _through_ffmpeg(rgb: np.ndarray, chain: str) -> np.ndarray:
    """Run a colour-only chain over a list of colours (as one small 16-bit picture)."""
    n = len(rgb)
    w = SIZE * SIZE
    h = -(-n // w)
    img = np.zeros((h * w, 3), np.uint16)
    img[:n] = np.round(np.clip(rgb, 0, 1) * 65535)
    out = subprocess.run(["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb48le", "-s", f"{w}x{h}", "-i", "-",
                          "-vf", f"{chain},format=rgb48le", "-f", "rawvideo", "-"],
                         input=img.tobytes(), capture_output=True)
    if out.returncode != 0 or len(out.stdout) < n * 6:
        raise RuntimeError("ffmpeg could not run the look: " + out.stderr.decode()[-300:])
    return np.frombuffer(out.stdout, np.uint16).reshape(-1, 3)[:n] / 65535


def bake(out_dir: Path, source: str = "rec709", look_chain: str = "", strength: float = 1.0,
         user_lut: Path | None = None) -> Path:
    """The .cube for this camera + look + strength (cached by its recipe)."""
    strength = max(0.0, min(1.0, float(strength)))
    chain = f"lut3d=file='{user_lut}'" if user_lut else look_chain
    key = hashlib.sha1(f"{source}|{chain}|{strength:.3f}|{user_lut and Path(user_lut).stat().st_mtime}".encode()).hexdigest()[:12]
    out = Path(out_dir) / f"look_{key}.cube"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    base = CONVERT.get(source, CONVERT["rec709"])(_grid())
    graded = _through_ffmpeg(base, chain) if chain and strength > 0 else base
    mix = base + (graded - base) * strength
    lines = [f"LUT_3D_SIZE {SIZE}", "DOMAIN_MIN 0 0 0", "DOMAIN_MAX 1 1 1"]
    lines += [f"{r:.6f} {g:.6f} {b:.6f}" for r, g, b in np.clip(mix, 0, 1)]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
