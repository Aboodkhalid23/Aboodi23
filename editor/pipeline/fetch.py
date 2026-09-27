"""Stage 1: get the raw footage (Drive link or local file) and normalize it."""
import re
import shutil
from pathlib import Path

from .fmt import decide_format, save_format
from .media import MediaError, probe, run_ffmpeg
from .paths import Episode

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".webm"}
HDR_TRANSFERS = {"arib-std-b67", "smpte2084"}
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv")
INTERMEDIATE = ["-c:v", "libx264", "-crf", "10", "-preset", "veryfast"]  # near-lossless working copy
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

    if ep.source.exists() and ep.source.stat().st_mtime >= raw.stat().st_mtime and ep.format_file.exists():
        return ep.source
    info = probe(raw)
    fmt = decide_format(info)
    # ffmpeg auto-rotates on decode. Only scale down to fit the canvas; never re-sample needlessly.
    vf = [f"scale=w='min({fmt.width},iw)':h='min({fmt.height},ih)':force_original_aspect_ratio=decrease"
          ":force_divisible_by=2"]
    if info.color_transfer in HDR_TRANSFERS:
        vf.insert(0, TONEMAP)
    vf += [f"fps={fmt.fps}", "format=yuv420p"]
    run_ffmpeg(["-i", str(raw), "-vf", ",".join(vf), *INTERMEDIATE,
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-metadata:s:v", "rotate=0", str(ep.source)])
    save_format(ep, fmt)
    return ep.source
