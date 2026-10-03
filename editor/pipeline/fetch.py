"""Stage 1: get the raw footage (Drive link or local file) and normalize it."""
import json
import re
import shutil
import time
from pathlib import Path

from .fmt import decide_format, save_format
from .media import MediaError, probe, run_ffmpeg
from .paths import Episode

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".webm"}
HDR_TRANSFERS = {"arib-std-b67", "smpte2084"}
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv")
INTERMEDIATE = ["-c:v", "libx264", "-crf", "14", "-preset", "veryfast"]  # visually lossless working copy
DRIVE_RE = re.compile(r"^https://(drive|docs)\.google\.com/")


_DRIVE_ID = re.compile(r"(?:/d/|[?&]id=)([A-Za-z0-9_-]{20,})")


def _drive_id(url: str) -> str | None:
    m = _DRIVE_ID.search(url)
    return m.group(1) if m else None


def _download_drive(url: str, work: Path) -> Path:
    import gdown

    try:
        if "/folders/" in url:
            files = gdown.download_folder(url=url, output=str(work / "drive"), quiet=True) or []
            videos = [Path(f) for f in files if Path(f).suffix.lower() in VIDEO_EXTS]
            if not videos:
                raise MediaError("الفولدر بدرايف ما بيه فيديو")
            return max(videos, key=lambda p: p.stat().st_size)
        fid = _drive_id(url)
        if not fid:
            raise MediaError("ما گدرت أقرا رابط درايف. دز رابط الملف نفسه (Share ← Copy link)")
        # a folder path keeps the file's own name on Drive (shown to the owner to confirm the episode)
        out = gdown.download(id=fid, output=str(work / "raw_download") + "/", quiet=True, retries=3)
    except MediaError:
        raise
    except Exception as exc:  # gdown raises many types for 403/404
        raise MediaError("ما گدرت أسحب الفيديو. تأكد إن الملف مشارك: أي شخص عنده الرابط") from exc
    if not out:
        raise MediaError("ما گدرت أسحب الفيديو. تأكد إن الملف مشارك: أي شخص عنده الرابط")
    return Path(out)


# Rough bitrate (Mbit/s) of our CRF-14 working copies per canvas height, used for the disk check.
WORK_MBPS = {1080: 30, 1440: 55, 2160: 110}


def _check_disk(ep: Episode, seconds: float, height: int) -> None:
    """source.mp4 + clean.mp4 + beat clips ≈ 3 copies at working bitrate."""
    need = seconds * WORK_MBPS[height] / 8 * 1e6 * 3
    free = shutil.disk_usage(ep.work).free
    if free < need:
        raise MediaError(f"المساحة ما تكفي: الحلقة تحتاج تقريباً {need / 1e9:.0f} گيگا، والموجود {free / 1e9:.0f} گيگا. "
                         "جرّب --max-height 1080 (أسرع وأصغر)")


def fetch(source: str, ep: Episode, max_height: int | None = None) -> Path:
    ep.ensure()
    local = None
    if source.startswith(("http://", "https://")):
        if not DRIVE_RE.match(source):
            raise MediaError("الرابط مو رابط گوگل درايف")
    else:
        local = Path(source)
        if not local.exists():
            raise MediaError(f"الملف {source} مو موجود")
    record = ep.work / "source.json"
    old = json.loads(record.read_text(encoding="utf-8")) if record.exists() else {}
    same = old.get("source") == source or (local is None and old.get("drive_id") and old.get("drive_id") == _drive_id(source))
    if ep.source.exists() and ep.format_file.exists() and same and (
            local is None or ep.source.stat().st_mtime >= local.stat().st_mtime):
        return ep.source  # same footage, already prepared (hours of work at 4K) — reuse it
    if ep.source.exists() and not same:
        print("🔁 هذا رابط جديد: أسحب الفيديو من جديد، وما أستخدم القديم")
        for f in (ep.source, ep.clean_video, ep.format_file, ep.work / "grade.json"):
            f.unlink(missing_ok=True)

    raw = _download_drive(source, ep.work) if local is None else local
    info = probe(raw)
    fmt = decide_format(info, max_height)
    _check_disk(ep, info.duration, fmt.height)
    # ffmpeg auto-rotates on decode. Only scale down to fit the canvas; never re-sample needlessly.
    vf = [f"scale=w='min({fmt.width},iw)':h='min({fmt.height},ih)':force_original_aspect_ratio=decrease"
          ":force_divisible_by=2"]
    if info.color_transfer in HDR_TRANSFERS:
        vf.insert(0, TONEMAP)
    vf += [f"fps={fmt.fps}", "format=yuv420p"]
    partial = ep.work / "source.partial.mp4"
    run_ffmpeg(["-i", str(raw), "-vf", ",".join(vf), *INTERMEDIATE,
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-metadata:s:v", "rotate=0", str(partial)])
    partial.replace(ep.source)
    save_format(ep, fmt)
    record.write_text(json.dumps({
        "source": source, "drive_id": _drive_id(source) if local is None else None, "name": raw.name,
        "raw_size_mb": round(raw.stat().st_size / 1e6), "raw_width": info.width, "raw_height": info.height,
        "raw_fps": info.fps, "duration": round(info.duration, 1), "fetched_at": time.strftime("%Y-%m-%d %H:%M"),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    if local is None:  # the Drive download is a copy we no longer need
        shutil.rmtree(ep.work / "drive", ignore_errors=True)
        shutil.rmtree(ep.work / "raw_download", ignore_errors=True)
        for f in ep.work.glob("raw_download*"):
            f.unlink()
    return ep.source
