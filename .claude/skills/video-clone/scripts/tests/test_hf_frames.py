"""hf_frames takes frames from a silent mirror of the build: same files, no <audio> elements."""
import os
from pathlib import Path

import hf_frames


def test_silent_mirror_drops_audio_only(tmp_path, monkeypatch):
    build = tmp_path / "build"
    (build / "compositions").mkdir(parents=True)
    (build / "assets").mkdir()
    (build / "node_modules").mkdir()
    (build / "index.html").write_text(
        '<div id="root"><div id="S1"></div>\n  <audio id="music" src="assets/mix.m4a" data-start="0"></audio>\n'
        '<AUDIO src="b.mp3">\n<audiogram-note></div>', encoding="utf-8")
    (build / "compositions" / "S1.html").write_text('<template><audio src="sfx.wav"></audio><video src="v.mp4"></video></template>', encoding="utf-8")
    (build / "assets" / "kit.js").write_text("window.kit = 1;", encoding="utf-8")
    (build / "node_modules" / "big.js").write_text("x", encoding="utf-8")
    monkeypatch.setattr(hf_frames, "CACHE", str(tmp_path / "cache"))

    m = hf_frames.silent_mirror(str(build), "k1")
    index = (Path(m) / "index.html").read_text(encoding="utf-8")
    assert "<audio" not in index.lower().replace("<audiogram", "")
    assert '<div id="S1">' in index and "<audiogram-note>" in index          # only audio elements go
    s1 = (Path(m) / "compositions" / "S1.html").read_text(encoding="utf-8")
    assert "<audio" not in s1 and '<video src="v.mp4">' in s1                # video frames are pictures: kept
    assert (Path(m) / "assets" / "kit.js").read_text(encoding="utf-8") == "window.kit = 1;"
    assert not os.path.exists(os.path.join(m, "node_modules"))
    assert hf_frames.silent_mirror(str(build), "k1") == m                    # made once per build content


def test_times_snap_to_the_frame_the_film_shows(tmp_path):
    ft = hf_frames.frame_time
    assert abs(ft(19.75, 30) - 592 / 30) < 1e-4          # between frames → the frame on screen at that moment
    assert ft(19.733, 30) == ft(19.75, 30)                 # a 3-decimal frame time is that frame, not the one before
    assert ft(19.767, 30) > ft(19.75, 30)
    assert ft(19.733, 30) >= 592 / 30                      # never seeks just before the frame starts
    (tmp_path / "build").mkdir()
    (tmp_path / "plan.json").write_text('{"format": {"fps": 24}}', encoding="utf-8")
    assert hf_frames.film_fps(str(tmp_path / "build")) == 24
