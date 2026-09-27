import subprocess
from pathlib import Path

import pytest


def make_talking_video(path: Path) -> Path:
    """20 s test video: tone 0-4, silence 4-7, tone 7-12, silence 12-13, tone 13-20."""
    tone = "sin(2*PI*1000*t)*0.3*(between(t,0,4)+between(t,7,12)+between(t,13,20))"
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=25:duration=20",
         "-f", "lavfi", "-i", f"aevalsrc='{tone}':s=48000:d=20",
         "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", str(path)],
        check=True,
    )
    return path


@pytest.fixture
def talking_video(tmp_path) -> Path:
    return make_talking_video(tmp_path / "talking.mp4")
