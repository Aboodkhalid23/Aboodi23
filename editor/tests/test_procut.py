"""The professional cut (owner, 2026-10-30: "مثل أدوبي بريمير"): speech found by a model, every take read on its own,
words on the edges the sound shows, and pauses cut with a breath left."""
from types import SimpleNamespace as NS

import numpy as np

from editor.pipeline import transcribe as tr
from editor.pipeline import wordtimes
from editor.pipeline.clean import HEAD_SHARE, HOP, drop_silences
from editor.pipeline.paths import Episode
from editor.pipeline.transcribe import SR, Word


def test_silence_is_no_speech_and_tones_fall_back_to_loudness():
    from editor.pipeline.vad import islands
    assert islands(np.zeros(SR * 3, np.float32)) == []
    t = np.arange(SR * 3) / SR
    assert islands((0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)) is None   # loud, not talk: caller decides


def test_noise_does_not_hide_a_pause_when_the_model_says_no_talk():
    """A fan keeps the loudness up all through a 2 s pause; the speech map shows the pause, so it goes."""
    env = np.full(700, 0.005, np.float32)             # 7 s: quiet room
    env[100:300] = env[500:700] = 0.2                 # he talks 1–3 s and 5–7 s
    env[300:500] = 0.06                               # a fan between
    talk = env > 0.1
    assert drop_silences([(1.0, 7.0)], env) == [(1.0, 7.0)]          # loudness alone: nothing to cut
    segs = drop_silences([(1.0, 7.0)], env, speech=talk)
    assert len(segs) == 2
    assert segs[0][1] == round(3.0 + 0.12, 3) and segs[1][0] == round(5.0 - 0.12 * HEAD_SHARE, 3)
    assert 0.18 <= (segs[0][1] - 3.0) + (5.0 - segs[1][0]) <= 0.22    # ~0.2 s of breath left in all


def test_letters_follow_the_models_alphabet():
    vocab = {c: i for i, c in enumerate("|ءاأبتمهيك")}
    assert wordtimes.letters("أمّه", vocab) == [vocab["ا"], vocab["م"], vocab["ه"]]
    assert wordtimes.letters("گاع", vocab) == [vocab["ك"], vocab["ا"]]      # ع is not in this alphabet
    assert wordtimes.letters("2026", vocab) == []


def _logp(T, V, peaks):
    """Log-probabilities where the blank (0) wins every frame except `peaks` {frame: token}."""
    x = np.full((T, V), -8.0)
    x[:, 0] = -0.01
    for f, tok in peaks.items():
        x[f, 0], x[f, tok] = -8.0, -0.01
    return x


def test_forced_alignment_puts_each_letter_on_its_frame():
    spans = wordtimes.viterbi(_logp(20, 4, {3: 1, 4: 1, 9: 2, 15: 3}), [1, 2, 3], blank=0)
    assert spans == [(3, 5), (9, 10), (15, 16)]
    assert wordtimes.viterbi(_logp(10, 4, {2: 1, 5: 1}), [1, 1], blank=0) == [(2, 3), (5, 6)]   # a doubled letter
    assert wordtimes.viterbi(_logp(2, 4, {}), [1, 2, 3], blank=0) is None                     # can't fit


class _Sess:
    """Stands in for the speech model: 50 frames a second, letters where `peaks` says."""
    def __init__(self, peaks_at):
        self.peaks_at = peaks_at

    def get_inputs(self):
        return [NS(name="input_values")]

    def run(self, _, feeds):
        n = feeds["input_values"].shape[1]
        T = n // 320
        return [_logp(T, 5, self.peaks_at(T))[None]]


def test_a_word_whisper_stretched_over_a_pause_gets_its_real_edges(monkeypatch):
    """Whisper: "لكن" 0.0–4.5 s over a long pause; the letters say it is said at 0.4–0.6 s."""
    vocab = {"|": 4, "<pad>": 0, "ل": 1, "ك": 2, "ن": 3}
    # the stretch 0.2–1.0 s is aligned with 0.1 s of sound around it: frame 0 = 0.1 s
    monkeypatch.setattr(wordtimes, "_load", lambda: (_Sess(lambda T: {15: 1, 20: 2, 24: 3}), vocab))
    audio = np.random.default_rng(0).normal(0, 0.1, SR * 5).astype(np.float32)
    out = wordtimes.refine_times(audio, [Word("لكن", 0.0, 4.5)], spans=[(0.2, 1.0)])
    assert abs(out[0].start - 0.4) < 0.03 and abs(out[0].end - (0.1 + 28 * 0.02)) < 0.03


def test_text_that_doesnt_fit_the_sound_keeps_whispers_times(monkeypatch):
    vocab = {"|": 4, "<pad>": 0, "ل": 1, "ك": 2, "ن": 3}
    monkeypatch.setattr(wordtimes, "_load", lambda: (_Sess(lambda T: {}), vocab))    # the model hears no letters
    audio = np.zeros(SR * 2, np.float32)
    w = [Word("لكن", 0.3, 0.9)]
    assert wordtimes.refine_times(audio, w, spans=[(0.2, 1.0)]) == w


def test_verbatim_reads_every_stretch_of_talk_alone(talking_video, tmp_path, monkeypatch):
    """Owner, 2026-10-30: a take Whisper heard twice in one window was written once, so the wrong one stayed."""
    ep = Episode(tmp_path / "ep").ensure()
    ep.source.write_bytes(talking_video.read_bytes())      # tone 0–4, 7–12, 13–20 s
    calls = []

    def read(piece, example):
        if example is not None:
            calls.append(len(piece) / SR)
        return []
    tr._run_chunks(ep, read, verbatim=False)
    windows = len(calls)
    calls.clear()
    tr._run_chunks(ep, read, verbatim=True)
    assert len(calls) > windows and max(calls) <= tr.CHUNK_MAX + 0.5


def test_verbatim_is_on_with_the_macs_chip_or_when_asked(monkeypatch):
    monkeypatch.delenv("ABOODI_VERBATIM", raising=False)
    monkeypatch.setattr(tr, "mlx_ready", lambda: True)
    assert tr.verbatim_wanted()
    monkeypatch.setenv("ABOODI_VERBATIM", "0")
    assert not tr.verbatim_wanted()
    monkeypatch.setattr(tr, "mlx_ready", lambda: False)
    monkeypatch.setenv("ABOODI_VERBATIM", "1")
    assert tr.verbatim_wanted()


def test_a_breath_read_alone_gives_no_guessed_words(talking_video, tmp_path, monkeypatch):
    ep = Episode(tmp_path / "ep").ensure()
    ep.source.write_bytes(talking_video.read_bytes())

    def read(piece, example):
        if example is None:
            return []
        return [NS(words=[NS(word=" شكرا", start=0.0, end=0.2, probability=0.2)])]
    monkeypatch.setattr(tr, "speech_chunks", lambda audio, **k: [(1.0, 1.4)])
    assert tr._run_chunks(ep, read, verbatim=True) == []
