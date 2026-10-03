"""Stage 2: speech → words with timestamps (faster-whisper, CPU)."""
import json
from dataclasses import dataclass
from pathlib import Path

from .media import MediaError, probe
from .paths import Episode


@dataclass
class Word:
    text: str
    start: float
    end: float


def save_words(words: list[Word], path: Path) -> None:
    data = [{"t": w.text, "s": round(w.start, 3), "e": round(w.end, 3)} for w in words]
    Path(path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def load_words(path: Path) -> list[Word]:
    return [Word(d["t"], d["s"], d["e"]) for d in json.loads(Path(path).read_text(encoding="utf-8"))]


IRAQI_PROMPT = "هلا بيكم، اليوم راح نحچي عن قصة غريبة. شلون صار هيچ؟ خلي نشوف شنو الي صار بالضبط."


def hotwords(ep: Episode) -> str | None:
    """Words Whisper should expect: edit/vocab.txt plus every name in edit/entities.json."""
    from .entities import entity_vocab
    vocab = ep.edit / "vocab.txt"
    words = vocab.read_text(encoding="utf-8").split() if vocab.exists() else []
    words += entity_vocab(ep)
    return " ".join(dict.fromkeys(w for w in words if w)) or None


def transcribe(ep: Episode, model_name: str = "large-v3", model=None) -> list[Word]:
    if not probe(ep.source).has_audio:
        raise MediaError("الصوت فارغ أو مو واضح")
    if model is None:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(
        str(ep.source), language="ar", word_timestamps=True, vad_filter=True,
        initial_prompt=IRAQI_PROMPT, hotwords=hotwords(ep), beam_size=5,
        condition_on_previous_text=False,  # long talks: stops Whisper repeating / inventing lines
    )
    words = [
        Word(w.word.strip(), float(w.start), float(w.end))
        for seg in segments for w in (seg.words or []) if w.word.strip()
    ]
    if not words:
        raise MediaError("الصوت فارغ أو مو واضح")
    save_words(words, ep.transcript)
    return words
