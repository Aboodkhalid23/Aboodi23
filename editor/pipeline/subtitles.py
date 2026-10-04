"""Subtitle file for YouTube (uploaded separately, never burned into the picture — owner's rule).
Text comes from the script-corrected words, timed on the final timeline (teaser first)."""
from pathlib import Path

from .clean import split_phrases
from .paths import Episode
from .plan import load_plan
from .transcribe import Word, load_words

MAX_CHARS = 42      # one comfortable line on a phone
MAX_SECONDS = 5.0


def _srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def cues(words: list[Word]) -> list[tuple[float, float, str]]:
    out = []
    for phrase in split_phrases(words):
        line: list[Word] = []
        for w in phrase:
            text = " ".join(x.text for x in [*line, w])
            if line and (len(text) > MAX_CHARS or w.end - line[0].start > MAX_SECONDS):
                out.append((line[0].start, line[-1].end, " ".join(x.text for x in line)))
                line = []
            line.append(w)
        if line:
            out.append((line[0].start, line[-1].end, " ".join(x.text for x in line)))
    return out


def on_final_timeline(words: list[Word], teaser: list[tuple[float, float]]) -> list[list[Word]]:
    """Pieces in play order: each teaser shot (its words repeat there), then the whole cleaned video.
    Kept apart so a line never joins the end of one shot to the start of the next."""
    pieces, t = [], 0.0
    for s, e in teaser:
        pieces.append([Word(w.text, t + max(w.start, s) - s, t + min(w.end, e) - s)
                       for w in words if w.end > s and w.start < e])
        t += e - s
    return pieces + [[Word(w.text, w.start + t, w.end + t) for w in words]]


def write_srt(ep: Episode, lang: str = "ar") -> Path:
    plan = load_plan(ep.plan)
    pieces = on_final_timeline(load_words(ep.clean_words), [tuple(x) for x in plan.teaser])
    lines = []
    for n, (a, b, text) in enumerate((c for piece in pieces for c in cues(piece)), 1):
        lines += [str(n), f"{_srt_time(a)} --> {_srt_time(max(b, a + 0.4))}", text, ""]
    out = ep.edit / f"subtitles.{lang}.srt"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
