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
        assert kwargs["language"] == "ar" and kwargs["word_timestamps"] is True
        seg = NS(words=[NS(word=w, start=s, end=e) for w, s, e in self.words])
        return iter([seg] if self.words else []), NS(language="ar")


def test_transcribe_writes_words(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    ep.source.write_bytes(b"x")
    words = transcribe(ep, model=FakeModel([(" شركة", 0.0, 0.4), (" ايفرغراند", 0.4, 1.0), (" كانت", 1.1, 1.4)]))
    assert words[0] == Word("شركة", 0.0, 0.4)
    assert load_words(ep.transcript) == words
    assert len(words) == 3


def test_transcribe_empty_raises(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    ep.source.write_bytes(b"x")
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
