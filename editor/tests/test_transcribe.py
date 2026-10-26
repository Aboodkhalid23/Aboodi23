import os
from types import SimpleNamespace as NS

import pytest

from editor.pipeline.media import MediaError
from editor.pipeline.paths import Episode
from editor.pipeline.transcribe import Word, load_words, transcribe


class FakeModel:
    """Hears `words` in the first piece of talk it is given (the talk is read piece by piece)."""
    def __init__(self, words):
        self.words, self.calls = words, 0

    def transcribe(self, audio, **kwargs):
        self.kwargs = kwargs
        self.calls += 1
        assert kwargs["language"] == "ar" and kwargs["word_timestamps"] is True
        words = self.words if self.calls == 1 else []
        seg = NS(words=[NS(word=w, start=s, end=e) for w, s, e in words])
        return iter([seg] if words else []), NS(language="ar")


def test_transcribe_writes_words(talking_video, tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    ep.source.write_bytes(talking_video.read_bytes())
    words = transcribe(ep, model=FakeModel([(" شركة", 0.0, 0.4), (" ايفرغراند", 0.4, 1.0), (" كانت", 1.1, 1.4)]))
    assert words[0] == Word("شركة", 0.0, 0.4)
    assert load_words(ep.transcript) == words
    assert len(words) == 3


def test_transcribe_empty_raises(talking_video, tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    ep.source.write_bytes(talking_video.read_bytes())
    with pytest.raises(MediaError) as err:
        transcribe(ep, model=FakeModel([]))
    assert str(err.value) == "الصوت فارغ أو مو واضح"


@pytest.mark.network
@pytest.mark.skipif(os.environ.get("EDITOR_NETWORK") != "1", reason="needs internet")
def test_transcribe_real_model_smoke(talking_video, tmp_path):
    from faster_whisper import WhisperModel  # noqa: F401  (download check)
    ep = Episode(tmp_path / "ep").ensure()
    ep.source.write_bytes(talking_video.read_bytes())
    with pytest.raises(MediaError):  # a pure tone has no speech
        transcribe(ep, model_name="tiny")


def test_transcribe_no_audio_track_raises(talking_video, tmp_path):
    """I-1: a video without an audio stream gives the Arabic message, not a traceback."""
    import subprocess
    ep = Episode(tmp_path / "ep").ensure()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(talking_video), "-an", "-c:v", "copy",
                    str(ep.source)], check=True)
    with pytest.raises(MediaError) as err:
        transcribe(ep, model=FakeModel([("كلمة", 0, 1)]))
    assert str(err.value) == "الصوت فارغ أو مو واضح"


def test_transcribe_passes_prompt_and_hotwords(talking_video, tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    ep.source.write_bytes(talking_video.read_bytes())
    (ep.edit / "vocab.txt").write_text("إيفرغراند\nهوي كا يان\n", encoding="utf-8")
    model = FakeModel([("شركة", 0, 1)])
    transcribe(ep, model=model)
    assert "إيفرغراند" in model.kwargs["hotwords"] and "هوي كا يان" in model.kwargs["hotwords"]
    assert "شلون" in model.kwargs["initial_prompt"]


def test_talk_is_read_piece_by_piece_at_his_pauses():
    """Owner, 2026-10-26: Whisper read 30 s at once and wrote a retake only once, so it was never cut.
    Every half-second pause starts a new piece; short pauses inside a sentence don't."""
    import numpy as np
    from editor.pipeline.transcribe import SR, speech_chunks
    t = np.arange(SR) / SR
    talk = lambda secs: np.tile(0.3 * np.sin(2 * np.pi * 220 * t), int(secs))[: int(secs * SR)]
    gap = lambda secs: np.zeros(int(secs * SR))
    audio = np.concatenate([talk(2), gap(0.2), talk(1), gap(0.9), talk(3), gap(0.6), talk(2)]).astype(np.float32)
    chunks = speech_chunks(audio)
    assert len(chunks) == 3
    assert chunks[0][1] < 3.4 < chunks[1][0] and chunks[1][1] < 7.3 < chunks[2][0]


def test_whisper_credits_heard_in_silence_are_dropped():
    from editor.pipeline.transcribe import _clean_piece
    assert _clean_piece([Word("اشتركوا", 0, 1, 0.3), Word("في", 1, 1.2, 0.3), Word("القناة", 1.2, 2, 0.3)]) == []
    real = [Word("هواوي", 0, 1)]
    assert _clean_piece(real) == real
