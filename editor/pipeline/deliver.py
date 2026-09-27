"""Stage 7: make sure the final file is small enough to send in the chat."""
from pathlib import Path

from .media import probe, run_ffmpeg
from .paths import Episode

AUDIO_KBPS = 192
SAFETY = 0.92  # container overhead + encoder overshoot


def prepare_delivery(ep: Episode, max_mb: float | None = None) -> Path:
    """The original file is delivered untouched; re-encode only when a size limit is given."""
    if max_mb is None or ep.final.stat().st_size <= max_mb * 1e6:
        return ep.final
    small = ep.edit / "final_small.mp4"
    seconds = probe(ep.final).duration
    video_kbps = max(300, int(max_mb * 8000 * SAFETY / seconds) - AUDIO_KBPS)
    # One pass, bitrate chosen from the size target (a CRF ladder would re-encode a 30-min file many times).
    run_ffmpeg(["-i", str(ep.final), "-c:v", "libx264", "-preset", "veryfast",
                "-b:v", f"{video_kbps}k", "-maxrate", f"{video_kbps}k", "-bufsize", f"{video_kbps * 2}k",
                "-c:a", "copy", "-movflags", "+faststart", str(small)])
    return small
