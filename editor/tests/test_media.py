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


def test_quiet_mode_halves_the_jobs_running_together(monkeypatch):
    from editor.pipeline import media
    monkeypatch.setenv("URU_COOL", "1")
    assert media.cool() and media.workers(4) == 2 and media.workers(3) == 1 and media.workers(1) == 1
    monkeypatch.setenv("URU_COOL", "0")
    assert not media.cool() and media.workers(4) == 4
    monkeypatch.delenv("URU_COOL")
    assert media.cool() == media.fanless()      # «تلقائي»: on by itself only on a Mac with no fan
