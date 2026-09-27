"""Stage 7: make sure the final file is small enough to send in the chat."""
from pathlib import Path

from .media import run_ffmpeg
from .paths import Episode


def prepare_delivery(ep: Episode, max_mb: float = 1024) -> Path:
    if ep.final.stat().st_size <= max_mb * 1e6:
        return ep.final
    small = ep.edit / "final_small.mp4"
    for crf in range(23, 33, 3):
        run_ffmpeg(["-i", str(ep.final), "-c:v", "libx264", "-crf", str(crf), "-preset", "medium",
                    "-c:a", "copy", "-movflags", "+faststart", str(small)])
        if small.stat().st_size <= max_mb * 1e6:
            break
    return small
