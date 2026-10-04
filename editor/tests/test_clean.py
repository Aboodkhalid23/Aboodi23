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
    assert total == pytest.approx(496 / 30, abs=0.07)  # frame-snapped ≈16.5 s (cuts sit on the quiet edge of each sound)
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


def test_drop_retakes_keeps_long_sentences_with_same_opener():
    """I-2: two different long sentences that start alike are both real content."""
    a = phrase("هاي الشركة كانت تبني بيوت بكل مدن الصين وتبيعها قبل ما تخلص", 0, 8)
    b = phrase("هاي الشركة كانت عليها ديون أكثر من ميزانية دول كاملة", 10, 16)
    assert len(drop_retakes([a, b])) == 2


def test_drop_retakes_logs_dropped():
    dropped = []
    drop_retakes([phrase("شركة ايفرغراند كانت", 0, 2), phrase("شركة ايفرغراند كانت أكبر شركة", 3, 6)],
                 dropped=dropped)
    assert [" ".join(w.text for w in p) for p in dropped] == ["شركة ايفرغراند كانت"]


def test_clean_with_script_drops_retake_then_corrects(talking_video, tmp_path):
    """C1/I2: retakes are decided on heard words; the script only fixes the kept take's text."""
    ep = Episode(tmp_path / "ep").ensure()
    fetch(str(talking_video), ep)
    save_words(phrase("شركه ايفر غراند كانت", 0, 2) + phrase("شركه ايفر غراند كانت اكبر شركه", 4, 9), ep.transcript)
    script = tmp_path / "04-script.md"
    script.write_text("شركة إيفرغراند كانت أكبر شركة", encoding="utf-8")
    clean(ep, script=script)
    cuts = json.loads(ep.cuts.read_text())
    assert cuts[0][0] >= 3.8
    assert [w.text for w in load_words(ep.clean_words)] == ["شركة", "إيفرغراند", "كانت", "أكبر", "شركة"]
    assert json.loads((ep.work / "align.json").read_text())["ratio"] == 1.0


# ---------- the new cut (owner never says which take was right) ----------

def said(*parts):
    """Phrases with 1.2 s pauses between them: ("text", seconds) pairs."""
    out, t = [], 0.0
    for text, secs in parts:
        out += phrase(text, t, t + secs)
        t += secs + 1.2
    return out


def kept_text(words, **kw):
    from editor.pipeline.clean import decide
    kept, removed = decide(words, **kw)
    return " ".join(w.text for w in kept), removed


def test_retake_spelt_differently_by_the_transcript_still_goes():
    text, removed = kept_text(said(("هسه راح نحجي عن الشركه", 2), ("هسة راح نحچي عن الشركة الصينية الكبيرة", 3)))
    assert text == "هسة راح نحچي عن الشركة الصينية الكبيرة" and removed[0][1] == "إعادة"


def test_a_wrong_continuation_goes_with_its_attempt():
    text, _ = kept_text(said(("الشركة بدت تخسر", 1.5), ("بالسنة الي بعدها طلعت", 1.5),
                             ("الشركة بدت تخسر فلوس هواية بالسنة الثانية", 3), ("وبعدين انهارت", 1)))
    assert text == "الشركة بدت تخسر فلوس هواية بالسنة الثانية وبعدين انهارت"


def test_no_no_let_me_redo_it():
    text, removed = kept_text(said(("هاي اكبر شركة بامريكا", 2), ("لا لا خلي اعيد", 1), ("هاي اكبر شركة بالصين", 2)))
    assert text == "هاي اكبر شركة بالصين"
    assert {why for _, why in removed} >= {"إشارة غلط"}


def test_restart_inside_one_breath_and_stutters():
    text, _ = kept_text(said(("راح نحچي اليوم راح نحچي اليوم عن قصة غريبة", 4)))
    assert text == "راح نحچي اليوم عن قصة غريبة"
    text, _ = kept_text(said(("و و الشر الشركة كانت كبيرة", 3)))
    assert text == "و الشركة كانت كبيرة"


def test_real_repetition_and_different_sentences_stay():
    text, removed = kept_text(said(("شوية شوية صارت اكبر شركة", 3), ("هاي الشركة كانت تبني بيوت بكل مدن الصين", 4),
                                   ("هاي الشركة كانت عليها ديون كبيرة كلش", 4)))
    assert removed == [] and text.startswith("شوية شوية")


def test_owner_overrides_win():
    words = said(("هسه راح نحجي عن الشركه", 2), ("هسة راح نحچي عن الشركة الصينية الكبيرة", 3))
    text, _ = kept_text(words, overrides={"keep": [[0, 2.1]], "drop": [[5.5, 9.0]]})
    assert text.startswith("هسه راح نحجي عن الشركه") and "الكبيرة" not in text


def test_cut_follows_the_real_sound_not_the_transcript():
    """Whisper ended the word at 1.0 s but the voice goes on to 1.25 s: the cut waits for the silence."""
    import numpy as np
    from editor.pipeline.clean import HOP, refine
    env = np.full(400, 0.001, np.float32)
    env[50:125] = 0.3                      # voice 0.5–1.25 s
    env[300:350] = 0.3                     # next phrase 3.0–3.5 s
    words = [Word("كلمة", 0.5, 1.0), Word("ثانية", 3.0, 3.5)]
    segs = refine([(0.38, 1.12), (2.88, 3.62)], env, words)
    assert segs[0][1] >= 1.25 + 0.05 and segs[0][1] < 3.0 and segs[1][0] < 3.0


def test_parallel_phrases_are_how_he_talks_not_a_restart():
    text, removed = kept_text(said(("تشتغل شوكت متريد وتطفى شوكت متريد مثل مفتاح الكهرباء", 5)))
    assert removed == [] and text.startswith("تشتغل شوكت متريد وتطفى")


def test_two_things_side_by_side_are_not_a_restart():
    text, removed = kept_text(said(("تقدر تميز بين صورة القطة وصورة الكلب بسهولة", 4)))
    assert removed == []
