import json
import subprocess

import pytest

from editor.pipeline.clean import clean
from editor.pipeline.compose import compose
from editor.pipeline.fetch import fetch
from editor.pipeline.media import probe
from editor.pipeline.paths import Episode
from editor.pipeline.plan import Beat, EditPlan, save_plan
from editor.pipeline.transcribe import save_words

from .test_clean import speech


def stream_durations(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    return {s["codec_type"]: float(s["duration"]) for s in json.loads(out)["streams"]}


def corner_rgb(path, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1",
                          "-vf", "crop=200:200:20:20,scale=1:1:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return tuple(raw[:3])


@pytest.fixture(scope="module")
def composed(tmp_path_factory):
    from .conftest import make_talking_video
    tmp = tmp_path_factory.mktemp("compose")
    ep = Episode(tmp / "ep").ensure()
    fetch(str(make_talking_video(tmp / "talking.mp4")), ep)
    save_words(speech((0, 4), (7, 12), (13, 20)), ep.transcript)
    clean_dur = clean(ep)
    total = 4.0 + clean_dur
    beats = [Beat(0, 4, "hook", "face"), Beat(4, 8, "hook", "face_zoom_in"),
             Beat(8, 11, "hook", "graphic", graphic={"type": "text", "text": "شركة"}),
             Beat(11, 15, "hook", "face_zoom_out"), Beat(15, round(total, 3), "hook", "face_framed")]
    save_plan(EditPlan({"primary": "vox", "sections": []}, "", [(2.0, 4.0), (9.0, 11.0)], beats), ep.plan)
    compose(ep)
    return ep, total


@pytest.mark.slow
def test_final_duration(composed):
    ep, total = composed
    assert probe(ep.final).duration == pytest.approx(total, abs=0.1)


@pytest.mark.slow
def test_av_in_sync(composed):
    ep, _ = composed
    d = stream_durations(ep.final)
    assert abs(d["video"] - d["audio"]) <= 0.1


@pytest.mark.slow
def test_output_format(composed):
    info = probe(composed[0].final)
    assert (info.width, info.height, info.fps) == (1920, 1080, 30)


@pytest.mark.slow
def test_graphic_beat_visible(composed):
    r, g, b = corner_rgb(composed[0].final, 9.5)
    for got, want in zip((r, g, b), (0xF2, 0xEB, 0xDD)):
        assert abs(got - want) <= 25


@pytest.mark.slow
def test_rerun_uses_cache(composed):
    ep, _ = composed
    clips = sorted(ep.work.glob("beat_*.mp4"))
    before = {p: p.stat().st_mtime for p in clips}
    compose(ep)
    assert len(clips) == 5
    assert {p: p.stat().st_mtime for p in clips} == before


def test_source_ranges_teaser_then_body():
    from editor.pipeline.compose import source_ranges
    teaser = [(2.0, 4.0), (9.0, 11.0)]
    assert source_ranges(0, 4, teaser) == [(2.0, 4.0), (9.0, 11.0)]
    assert source_ranges(3, 6, teaser) == [(10.0, 11.0), (0.0, 2.0)]


def test_beat_outside_clean_video_raises(tmp_path):
    from editor.pipeline.compose import _face_clip
    from editor.pipeline.media import MediaError
    with pytest.raises(MediaError):
        _face_clip(Episode(tmp_path), Beat(5, 5, "body", "face"), 0, [], tmp_path / "x.mp4", None)
