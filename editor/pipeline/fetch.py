"""Stage 1: get the raw footage (Drive link or local file) and normalize it."""
import re
import shutil
from pathlib import Path

from .media import MediaError, run_ffmpeg
from .paths import Episode

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".webm"}
DRIVE_RE = re.compile(r"^https://(drive|docs)\.google\.com/")


def _download_drive(url: str, work: Path) -> Path:
    import gdown

    try:
        if "/folders/" in url:
            files = gdown.download_folder(url=url, output=str(work / "drive"), quiet=True) or []
            videos = [Path(f) for f in files if Path(f).suffix.lower() in VIDEO_EXTS]
            if not videos:
                raise MediaError("الفولدر بدرايف ما بيه فيديو")
            return max(videos, key=lambda p: p.stat().st_size)
        out = gdown.download(url=url, output=str(work / "raw_download"), quiet=True, fuzzy=True)
    except MediaError:
        raise
    except Exception as exc:  # gdown raises many types for 403/404
        raise MediaError("ما گدرت أسحب الفيديو. تأكد إن الملف مشارك: أي شخص عنده الرابط") from exc
    if not out:
        raise MediaError("ما گدرت أسحب الفيديو. تأكد إن الملف مشارك: أي شخص عنده الرابط")
    return Path(out)


def fetch(source: str, ep: Episode) -> Path:
    ep.ensure()
    if source.startswith(("http://", "https://")):
        if not DRIVE_RE.match(source):
            raise MediaError("الرابط مو رابط گوگل درايف")
        raw = _download_drive(source, ep.work)
    else:
        local = Path(source)
        if not local.exists():
            raise MediaError(f"الملف {source} مو موجود")
        raw = ep.work / f"raw{local.suffix.lower()}"
        if local.resolve() != raw.resolve():
            shutil.copyfile(local, raw)

    if ep.source.exists() and ep.source.stat().st_mtime >= raw.stat().st_mtime:
        return ep.source
    # ffmpeg auto-rotates on decode; scale only down into a 1920x1080 box.
    vf = ("scale=w='min(1920,iw)':h='min(1080,ih)':force_original_aspect_ratio=decrease"
          ":force_divisible_by=2,fps=30,format=yuv420p")
    run_ffmpeg(["-i", str(raw), "-vf", vf, "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
                "-metadata:s:v", "rotate=0", str(ep.source)])
    return ep.source
