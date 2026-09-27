"""Stage 3: drop silences and retakes; build the cleaned video."""
import json
import re

from .media import probe, run_ffmpeg
from .paths import Episode
from .transcribe import Word, load_words, save_words

_TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_PUNCT = re.compile(r"[^\w\s]")
_TRANS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"})


def normalize_ar(text: str) -> str:
    text = _TASHKEEL.sub("", text).translate(_TRANS)
    text = _PUNCT.sub("", text).lower()
    return " ".join(text.split())


def split_phrases(words: list[Word], pause: float = 0.7) -> list[list[Word]]:
    phrases: list[list[Word]] = []
    for w in words:
        if phrases and w.start - phrases[-1][-1].end <= pause:
            phrases[-1].append(w)
        else:
            phrases.append([w])
    return phrases


def _key(p: list[Word], n: int) -> list[str]:
    return [normalize_ar(w.text) for w in p[:n]]


def drop_retakes(phrases: list[list[Word]], window: float = 30.0, match: int = 3) -> list[list[Word]]:
    kept = []
    for i, a in enumerate(phrases):
        retaken = False
        for b in phrases[i + 1:]:
            if b[0].start - a[-1].end > window:
                break
            ka, kb = _key(a, match), _key(b, match)
            if (len(a) >= match and ka == kb) or (len(a) < match and kb[:len(ka)] == ka):
                retaken = True
                break
        if not retaken:
            kept.append(a)
    return kept


def keep_segments(phrases: list[list[Word]], pad: float = 0.12, merge_gap: float = 0.25,
                  duration: float | None = None) -> list[tuple[float, float]]:
    segs: list[tuple[float, float]] = []
    for p in phrases:
        s, e = max(0.0, p[0].start - pad), p[-1].end + pad
        if duration is not None:
            e = min(e, duration)
        if segs and s - segs[-1][1] < merge_gap:
            segs[-1] = (segs[-1][0], max(e, segs[-1][1]))
        else:
            segs.append((s, e))
    return [(round(s, 3), round(e, 3)) for s, e in segs]


def remap_words(words: list[Word], segments: list[tuple[float, float]]) -> list[Word]:
    out, offset = [], 0.0
    for s, e in segments:
        for w in words:
            if s <= (w.start + w.end) / 2 < e:
                out.append(Word(w.text, round(offset + max(w.start, s) - s, 3),
                                round(offset + min(w.end, e) - s, 3)))
        offset += e - s
    return out


FPS = 30                   # fetch() normalizes to 30 fps / 48 kHz
SAMPLES_PER_FRAME = 48000 // FPS


def snap_to_frames(segments: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Cut on frame boundaries so video and audio pieces are exactly the same length."""
    out = []
    for s, e in segments:
        f0, f1 = round(s * FPS), round(e * FPS)
        if f1 > f0:
            out.append((f0 / FPS, f1 / FPS))
    return out


def clean(ep: Episode) -> float:
    words = load_words(ep.transcript)
    duration = probe(ep.source).duration
    segs = snap_to_frames(keep_segments(drop_retakes(split_phrases(words)), duration=duration))
    ep.cuts.write_text(json.dumps(segs), encoding="utf-8")
    save_words(remap_words(words, segs), ep.clean_words)

    parts, labels = [], []
    for i, (s, e) in enumerate(segs):
        f0, f1 = round(s * FPS), round(e * FPS)
        parts.append(f"[0:v]trim=start_frame={f0}:end_frame={f1},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim=start_sample={f0 * SAMPLES_PER_FRAME}:end_sample={f1 * SAMPLES_PER_FRAME},"
                     f"asetpts=PTS-STARTPTS[a{i}];")
        labels.append(f"[v{i}][a{i}]")
    graph = "".join(parts) + "".join(labels) + f"concat=n={len(segs)}:v=1:a=1[v][a]"
    script = ep.work / "clean_filter.txt"
    script.write_text(graph, encoding="utf-8")
    run_ffmpeg(["-i", str(ep.source), "-filter_complex_script", str(script),
                "-map", "[v]", "-map", "[a]", "-r", "30", "-c:v", "libx264", "-crf", "18",
                "-preset", "fast", "-c:a", "aac", "-b:a", "192k", str(ep.clean_video)])
    return sum(e - s for s, e in segs)
