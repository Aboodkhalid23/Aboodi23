import subprocess

import pytest

from editor.pipeline.fetch import fetch
from editor.pipeline.media import MediaError, probe
from editor.pipeline.paths import Episode


def test_fetch_local_normalizes_to_30fps(talking_video, tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    out = fetch(str(talking_video), ep)
    info = probe(out)
    assert out == ep.source
    assert info.fps == 30
    assert abs(info.duration - 20.0) <= 0.1


def test_fetch_rotated_is_upright(talking_video, tmp_path):
    rotated = tmp_path / "rotated.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-display_rotation", "90",
                    "-i", str(talking_video), "-c", "copy", str(rotated)], check=True)
    assert probe(rotated).rotation != 0
    ep = Episode(tmp_path / "ep").ensure()
    info = probe(fetch(str(rotated), ep))
    assert info.width < info.height
    assert info.height == 1080
    assert info.rotation == 0


def test_fetch_rejects_non_drive_url(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    with pytest.raises(MediaError) as err:
        fetch("https://example.com/a.mp4", ep)
    assert str(err.value) == "الرابط مو رابط گوگل درايف"
