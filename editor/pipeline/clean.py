"""Stage 3: drop silences and retakes; build the cleaned video."""
import json
import re
from pathlib import Path

from .fmt import load_format
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


def _is_retake(a: list[Word], b: list[Word], match: int, max_retake: float, overlap: float) -> bool:
    """B restarts A: same opening, and A is either short or mostly repeated inside B."""
    ka, kb = _key(a, len(a)), _key(b, len(b))
    if len(a) < match:
        return kb[:len(ka)] == ka and b[0].start - a[-1].end <= 5.0
    if ka[:match] != kb[:match]:
        return False
    shared = sum(1 for x, y in zip(ka, kb) if x == y)
    return a[-1].end - a[0].start <= max_retake or shared / len(ka) >= overlap


def drop_retakes(phrases: list[list[Word]], window: float = 30.0, match: int = 3,
                 max_retake: float = 6.0, overlap: float = 0.6,
                 dropped: list | None = None) -> list[list[Word]]:
    kept = []
    for i, a in enumerate(phrases):
        later = [b for b in phrases[i + 1:] if b[0].start - a[-1].end <= window]
        if any(_is_retake(a, b, match, max_retake, overlap) for b in later):
            if dropped is not None:
                dropped.append(a)
        else:
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


def snap_to_frames(segments: list[tuple[float, float]], fps: int = 30) -> list[tuple[float, float]]:
    """Cut on frame boundaries so video and audio pieces are exactly the same length."""
    out = []
    for s, e in segments:
        f0, f1 = round(s * fps), round(e * fps)
        if f1 > f0:
            out.append((f0 / fps, f1 / fps))
    return out


def clean(ep: Episode, script: Path | None = None) -> float:
    words = load_words(ep.transcript)
    duration = probe(ep.source).duration
    dropped: list = []
    kept = drop_retakes(split_phrases(words), dropped=dropped)
    (ep.work / "retakes.json").write_text(json.dumps(
        [{"start": p[0].start, "end": p[-1].end, "text": " ".join(w.text for w in p)} for p in dropped],
        ensure_ascii=False, indent=1), encoding="utf-8")
    fps = load_format(ep).fps  # fetch() normalized to this fps and 48 kHz audio
    spf = 48000 // fps
    segs = snap_to_frames(keep_segments(kept, duration=duration), fps)
    ep.cuts.write_text(json.dumps(segs), encoding="utf-8")
    kept_words = [w for p in kept for w in p]
    if script:  # Iraqi dialect: correct the words we keep from the script the owner read
        from .align import align_to_script
        kept_words = align_to_script(ep, kept_words, script)
    save_words(remap_words(kept_words, segs), ep.clean_words)

    parts, labels = [], []
    for i, (s, e) in enumerate(segs):
        f0, f1 = round(s * fps), round(e * fps)
        parts.append(f"[0:v]trim=start_frame={f0}:end_frame={f1},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim=start_sample={f0 * spf}:end_sample={f1 * spf},"
                     f"asetpts=PTS-STARTPTS[a{i}];")
        labels.append(f"[v{i}][a{i}]")
    graph = "".join(parts) + "".join(labels) + f"concat=n={len(segs)}:v=1:a=1[v][a]"
    script = ep.work / "clean_filter.txt"
    script.write_text(graph, encoding="utf-8")
    run_ffmpeg(["-i", str(ep.source), "-filter_complex_script", str(script),
                "-map", "[v]", "-map", "[a]", "-r", str(fps), "-c:v", "libx264", "-crf", "14",
                "-preset", "veryfast", "-c:a", "aac", "-b:a", "192k", str(ep.clean_video)])
    return sum(e - s for s, e in segs)
