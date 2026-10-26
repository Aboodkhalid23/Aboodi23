"""ffprobe / ffmpeg helpers shared by every stage."""
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


class MediaError(Exception):
    """Error with an Arabic message meant for the channel owner."""


@dataclass
class MediaInfo:
    duration: float
    width: int
    height: int
    fps: float
    has_audio: bool
    rotation: int
    color_transfer: str = ""


def _fps(rate: str) -> float:
    num, _, den = rate.partition("/")
    value = float(num) / float(den or 1) if float(den or 1) else 0.0
    return round(value, 3)


def probe(path: Path) -> MediaInfo:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise MediaError(f"فشل فحص الملف {path} (ffprobe): {proc.stderr.strip()}")
    data = json.loads(proc.stdout)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise MediaError(f"الملف {path} ما بيه فيديو")
    rotation = 0
    for side in video.get("side_data_list", []):
        if "rotation" in side:
            rotation = int(side["rotation"])
    if not rotation and "rotate" in video.get("tags", {}):
        rotation = int(video["tags"]["rotate"])
    return MediaInfo(
        duration=float(data["format"].get("duration") or 0.0),  # stills have none
        width=int(video["width"]),
        height=int(video["height"]),
        fps=_fps(video.get("avg_frame_rate") or video.get("r_frame_rate", "0/1")),
        has_audio=any(s.get("codec_type") == "audio" for s in streams),
        rotation=rotation % 360,
        color_transfer=video.get("color_transfer", ""),
    )


_FFMPEG_VERSION: tuple[int, int] | None = None


def ffmpeg_version() -> tuple[int, int]:
    """(major, minor) of the ffmpeg on the PATH; a git snapshot ("N-12345") counts as the newest."""
    global _FFMPEG_VERSION
    if _FFMPEG_VERSION is None:
        out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout
        m = re.search(r"ffmpeg version n?(\d+)\.(\d+)", out)
        _FFMPEG_VERSION = (int(m.group(1)), int(m.group(2))) if m else (99, 0)
    return _FFMPEG_VERSION


def filter_script(path: Path) -> list[str]:
    """Arguments that read a filter graph from a file: ffmpeg 7.1 added "-/filter_complex <file>" and 8 dropped
    "-filter_complex_script" (the Mac app ships ffmpeg 9; the cloud has 6)."""
    return ["-/filter_complex", str(path)] if ffmpeg_version() >= (7, 1) else ["-filter_complex_script", str(path)]


def run_ffmpeg_progress(args: list[str], duration: float) -> None:
    """run_ffmpeg that also tells the Mac app how far it is ("@@ 42"), when ABOODI_PROGRESS is set."""
    import os
    if not os.environ.get("ABOODI_PROGRESS") or duration <= 0:
        return run_ffmpeg(args)
    proc = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostats", "-progress", "pipe:1", *args],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    last = -1
    for line in proc.stdout:
        if line.startswith("out_time_us=") and line.strip()[12:].isdigit():
            pct = min(99, int(int(line.strip()[12:]) / 1e6 / duration * 100))
            if pct > last:
                print(f"@@ {pct}", flush=True)
                last = pct
    err = proc.stderr.read()
    if proc.wait() != 0:
        raise MediaError(f"فشل ffmpeg: {err.strip()[-800:]}")


def _videotoolbox() -> bool:
    """The Mac's own video chip (owner, 2026-10-26: "أريد سرعة"): encodes many times faster than the CPU, so preparing,
    cutting and building stop waiting on x264. Off with ABOODI_NO_HW=1, and never off a Mac."""
    import os
    import sys
    if sys.platform != "darwin" or os.environ.get("ABOODI_NO_HW"):
        return False
    try:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True, timeout=20).stdout
        if "h264_videotoolbox" not in out:
            return False
        test = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=320x240:d=0.2", "-c:v",
                               "h264_videotoolbox", "-b:v", "1M", "-f", "null", "-"], capture_output=True, timeout=30)
        return test.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


HW = _videotoolbox()
# working copies (source.mp4, clean.mp4, beat clips): visually lossless; on the Mac the video chip at a high bitrate
WORK = (["-c:v", "h264_videotoolbox", "-b:v", "70M", "-maxrate", "110M", "-bufsize", "140M", "-allow_sw", "1", "-pix_fmt", "yuv420p"]
        if HW else ["-c:v", "libx264", "-crf", "12", "-preset", "veryfast", "-pix_fmt", "yuv420p"])
# the app's light copy for playing and scrubbing (720p, a keyframe every 12 frames, index first)
PROXY = ([*(["-c:v", "h264_videotoolbox", "-b:v", "5M", "-allow_sw", "1"] if HW else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "27"]),
          "-g", "12", "-keyint_min", "12", "-sc_threshold", "0",
          "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "96k"])


def run_ffmpeg(args: list[str]) -> None:
    proc = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise MediaError(f"فشل ffmpeg: {proc.stderr.strip()[-800:]}")
