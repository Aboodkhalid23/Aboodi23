"""Copies of the finished episode at the size he picks (owner, 2026-10-25: "أصدّره فول اتش دي أو ٤ك أو ٨ك").

From edit/final.mp4 (one high-quality master) to edit/exports/<label>.mp4, one encode, no watermark ever:
  720 / 1080 / 1440  H.264 High, CRF 16, slow preset (what YouTube recommends, and plays everywhere)
  2160 / 4320        HEVC (hvc1, plays on Apple and YouTube), CRF 18; H.264 when this ffmpeg has no HEVC
Bigger than the master is allowed (YouTube gives bigger uploads a better codec and more bitrate), but it adds no
detail: the app says so.  python -m editor.pipeline.export <episode> <height>
"""
import subprocess
import sys
from pathlib import Path

from .media import probe, run_ffmpeg_progress
from .paths import Episode

SIZES = {720: "٧٢٠", 1080: "فول اتش دي ١٠٨٠", 1440: "٢ك ١٤٤٠", 2160: "٤ك", 4320: "٨ك"}


def _has(encoder: str) -> bool:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    return f" {encoder} " in out


def export_copy(ep: Episode, height: int) -> Path:
    if height not in SIZES:
        raise ValueError("دقة مو معروفة")
    src = ep.final
    if not src.exists():
        raise ValueError("طلّع النسخة الكاملة أول")
    info = probe(src)
    tall = info.height > info.width
    scale = f"scale={height}:-2:flags=lanczos" if tall else f"scale=-2:{height}:flags=lanczos"
    if height >= 2160 and _has("libx265"):
        video = ["-c:v", "libx265", "-preset", "medium", "-crf", "18", "-tag:v", "hvc1", "-x265-params", "log-level=error"]
    else:
        video = ["-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high"]
    out = ep.edit / "exports" / f"{ep.root.name}-{height}p.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg_progress(["-i", str(src), "-vf", f"{scale},setsar=1", *video, "-pix_fmt", "yuv420p",
                         "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-map_metadata", "0", "-map_chapters", "0",
                         "-movflags", "+faststart", str(out)], info.duration)
    return out


if __name__ == "__main__":
    import os
    os.environ.setdefault("ABOODI_PROGRESS", "1")
    ep = Episode(Path(sys.argv[1]))
    h = int(sys.argv[2])
    print(f"📤 أطلّع نسخة {SIZES.get(h, h)}…", flush=True)
    out = export_copy(ep, h)
    print(f"✅ جاهزة: {out.name} ({out.stat().st_size / 1e6:.0f} ميگا)", flush=True)
