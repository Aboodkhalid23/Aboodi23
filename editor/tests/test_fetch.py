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


def synth(path, size="3840x2160", rate=30, dur=2, extra=()):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=size={size}:rate={rate}:duration={dur}",
                    "-f", "lavfi", "-i", f"sine=f=440:r=48000:d={dur}", "-c:v", "libx264", "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p", *extra, "-c:a", "aac", "-shortest", str(path)], check=True)
    return path


def test_decide_format_tiers():
    from editor.pipeline.fmt import Format, decide_format
    from editor.pipeline.media import MediaInfo
    mk = lambda w, h, fps: MediaInfo(10, w, h, fps, True, 0)
    assert decide_format(mk(3840, 2160, 30)) == Format(3840, 2160, 30)
    assert decide_format(mk(2560, 1440, 25)) == Format(2560, 1440, 30)
    assert decide_format(mk(1280, 720, 59.94)) == Format(1920, 1080, 60)
    assert decide_format(mk(1080, 1920, 30)) == Format(1920, 1080, 30)  # portrait → 1080 canvas


def test_fetch_keeps_4k(tmp_path):
    from editor.pipeline.fmt import load_format, Format
    ep = Episode(tmp_path / "ep").ensure()
    info = probe(fetch(str(synth(tmp_path / "4k.mp4")), ep))
    assert (info.width, info.height, info.fps) == (3840, 2160, 30)
    assert load_format(ep) == Format(3840, 2160, 30)


def test_fetch_60fps_stays_60(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    info = probe(fetch(str(synth(tmp_path / "60.mp4", size="1280x720", rate=60)), ep))
    assert info.fps == 60


def test_fetch_tonemaps_hdr(tmp_path):
    hdr = synth(tmp_path / "hdr.mp4", size="1280x720", extra=["-color_primaries", "bt2020", "-color_trc", "arib-std-b67",
                                                              "-colorspace", "bt2020nc"])
    ep = Episode(tmp_path / "ep").ensure()
    out = fetch(str(hdr), ep)
    trc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=color_transfer",
                          "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip()
    assert trc == "bt709"


def test_fetch_refuses_when_disk_is_too_small(talking_video, tmp_path, monkeypatch):
    """I4: stop early with an Arabic message instead of filling the disk for hours."""
    import shutil
    from collections import namedtuple
    Usage = namedtuple("Usage", "total used free")
    monkeypatch.setattr(shutil, "disk_usage", lambda p: Usage(10**9, 10**9, 10**6))
    ep = Episode(tmp_path / "ep").ensure()
    with pytest.raises(MediaError) as err:
        fetch(str(talking_video), ep)
    assert "مساحة" in str(err.value)


def test_fetch_removes_raw_copy(talking_video, tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    fetch(str(talking_video), ep)
    assert not list(ep.work.glob("raw*"))


def test_drive_file_id_from_share_links():
    """gdown 6 dropped fuzzy URL parsing, so we extract the file id ourselves."""
    from editor.pipeline.fetch import _drive_id
    fid = "1GL6NmrF47tWB08lc4vPwaxQ0-L4uhupk"
    assert _drive_id(f"https://drive.google.com/file/d/{fid}/view?usp=drivesdk") == fid
    assert _drive_id(f"https://drive.google.com/open?id={fid}") == fid
    assert _drive_id(f"https://drive.google.com/uc?export=download&id={fid}") == fid
