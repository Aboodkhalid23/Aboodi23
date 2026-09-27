import json

import pytest

from editor.pipeline.clean import clean, drop_retakes, keep_segments, normalize_ar, remap_words, split_phrases
from editor.pipeline.fetch import fetch
from editor.pipeline.media import probe
from editor.pipeline.paths import Episode
from editor.pipeline.transcribe import Word, load_words, save_words


def phrase(text, start, end):
    toks = text.split()
    step = (end - start) / len(toks)
    return [Word(t, start + i * step, start + (i + 1) * step) for i, t in enumerate(toks)]


def speech(*spans):
    """One 1-second word per second inside each (start, end) span."""
    return [w for n, (a, b) in enumerate(spans)
            for w in phrase(" ".join(f"كلمة{n}{i}" for i in range(int(b - a))), a, b)]


def test_normalize_ar():
    assert normalize_ar("أَنَّ الشَّرِكَةَ") == "ان الشركه"


def test_drop_retakes_keeps_last():
    kept = drop_retakes([phrase("شركة ايفرغراند كانت", 0, 2),
                         phrase("شركة ايفرغراند كانت أكبر شركة", 3, 6)])
    assert len(kept) == 1
    assert kept[0][0].start == 3.0


def test_drop_retakes_ignores_far_repeats():
    kept = drop_retakes([phrase("شركة ايفرغراند كانت", 0, 2),
                         phrase("شركة ايفرغراند كانت أكبر شركة", 100, 103)])
    assert len(kept) == 2


def test_drop_retakes_short_false_start():
    kept = drop_retakes([phrase("شركة", 0, 0.5), phrase("شركة ايفرغراند كانت أكبر", 2, 5)])
    assert [p[0].start for p in kept] == [2]


def test_keep_segments_removes_silence():
    segs = keep_segments(split_phrases(speech((0, 4), (7, 12), (13, 20))), duration=20.0)
    expected = [(0.0, 4.12), (6.88, 12.12), (12.88, 20.0)]
    assert len(segs) == 3
    for (s, e), (xs, xe) in zip(segs, expected):
        assert s == pytest.approx(xs, abs=0.01) and e == pytest.approx(xe, abs=0.01)


def test_remap_words_onto_clean_timeline():
    words = [Word("a", 1.0, 1.5), Word("b", 5.0, 5.5)]
    assert remap_words(words, [(0.9, 1.6), (4.9, 5.6)]) == [Word("a", 0.1, 0.6), Word("b", 0.8, 1.3)]


def test_clean_video_duration_matches_segments(talking_video, tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    fetch(str(talking_video), ep)
    save_words(speech((0, 4), (7, 12), (13, 20)), ep.transcript)
    total = clean(ep)
    assert total == pytest.approx(496 / 30, abs=1e-6)  # frame-snapped 16.48 s
    cuts = json.loads(ep.cuts.read_text())
    assert total == pytest.approx(sum(e - s for s, e in cuts), abs=0.01)
    assert probe(ep.clean_video).duration == pytest.approx(total, abs=0.1)
    assert load_words(ep.clean_words)[-1].end <= total + 0.01


@pytest.mark.slow
def test_clean_video_matches_cuts_with_many_segments(tmp_path):
    """C-1: per-segment frame rounding must not accumulate (100+ segments)."""
    import subprocess
    src = tmp_path / "long.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=30:duration=130",
                    "-f", "lavfi", "-i", "sine=f=440:r=48000:d=130", "-c:v", "libx264", "-preset", "ultrafast",
                    "-c:a", "aac", "-ar", "48000", "-shortest", str(src)], check=True)
    ep = Episode(tmp_path / "ep").ensure()
    fetch(str(src), ep)
    words, t = [], 0.0
    for n in range(110):  # 0.43 s of speech, then 0.74 s pause
        words.append(Word(f"كلمة{n}", round(t, 3), round(t + 0.43, 3)))
        t += 1.17
    save_words(words, ep.transcript)
    total = clean(ep)
    cuts = json.loads(ep.cuts.read_text())
    assert len(cuts) >= 100
    assert total == pytest.approx(sum(e - s for s, e in cuts), abs=1e-6)
    info = probe(ep.clean_video)
    assert abs(info.duration - total) <= 1 / 30
