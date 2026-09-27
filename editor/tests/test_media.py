import pytest

from editor.pipeline.media import MediaError, probe, run_ffmpeg


def test_probe_fixture(talking_video):
    info = probe(talking_video)
    assert abs(info.duration - 20.0) <= 0.1
    assert (info.width, info.height) == (1280, 720)
    assert info.fps == 25
    assert info.has_audio is True
    assert info.rotation == 0


def test_run_ffmpeg_error_is_arabic(tmp_path):
    with pytest.raises(MediaError) as err:
        run_ffmpeg(["-i", str(tmp_path / "missing.mp4"), str(tmp_path / "out.mp4")])
    assert "ffmpeg" in str(err.value)
    assert "فشل" in str(err.value)
