import os
from types import SimpleNamespace as NS

import pytest

from editor.pipeline.media import MediaError
from editor.pipeline.paths import Episode
from editor.pipeline.transcribe import Word, load_words, transcribe


class FakeModel:
    def __init__(self, words):
        self.words = words

    def transcribe(self, audio, **kwargs):
        self.kwargs = kwargs
        assert kwargs["language"] == "ar" and kwargs["word_timestamps"] is True
        seg = NS(words=[NS(word=w, start=s, end=e) for w, s, e in self.words])
        return iter([seg] if self.words else []), NS(language="ar")


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
