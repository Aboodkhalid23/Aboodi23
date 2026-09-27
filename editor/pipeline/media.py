"""ffprobe / ffmpeg helpers shared by every stage."""
import json
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
        duration=float(data["format"]["duration"]),
        width=int(video["width"]),
        height=int(video["height"]),
        fps=_fps(video.get("avg_frame_rate") or video.get("r_frame_rate", "0/1")),
        has_audio=any(s.get("codec_type") == "audio" for s in streams),
        rotation=rotation % 360,
        color_transfer=video.get("color_transfer", ""),
    )


def run_ffmpeg(args: list[str]) -> None:
    proc = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise MediaError(f"فشل ffmpeg: {proc.stderr.strip()[-800:]}")
