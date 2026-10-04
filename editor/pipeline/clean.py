"""Stage 3: the cut. Keeps the good take of everything the owner says and throws away the rest, with no
help from him (owner's rule: he never says which take was right).

What goes, in this order:
  1. mistake cues   a short phrase like "لا لا، خلي أعيد" / "غلط" / "من جديد" — it and the attempt before it
  2. retakes        a phrase that a later phrase restarts (fuzzy: the transcript may spell the two takes a little
                    differently, or he adds / drops a word); everything from the failed attempt up to the
                    restart goes, so a wrong continuation never survives. The LAST take is kept.
  3. restarts       inside one breath: "راح نحچي عن... راح نحچي عن قصة" → the first "راح نحچي عن"
  4. stutters       "ال ال الشركة", a cut-off word followed by the full word
  5. fillers        long "اممم / ااا" sounds
  6. silences       every pause longer than MAX_GAP; a short natural breath is kept at each cut

Every cut point is then moved to the quietest spot of the real sound next to it (Whisper's word times can be
off by a tenth of a second: cutting on them clips word endings), each piece gets an 8 ms fade (no clicks),
and the cuts land on frame boundaries. edit/work/cut_report.txt lists everything removed and why;
edit/cuts_override.json ({"keep": [[s, e]], "drop": [[s, e]]}, source seconds) overrides any decision."""
import json
import re
import subprocess
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np

from .fmt import load_format
from .media import probe, run_ffmpeg
from .paths import Episode
from .transcribe import Word, load_words, save_words

_TASHKEEL = re.compile("[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")   # harakat, tatweel
_PUNCT = re.compile(r"[^\w\s]")
_TRANS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "گ": "ك", "چ": "ج", "ڤ": "ف", "پ": "ب"})

PHRASE_PAUSE = 0.7     # s: a longer pause starts a new phrase (unit for retakes)
MAX_GAP = 0.45         # s: a longer pause inside the talk is cut out
PAD = 0.12             # s: breath kept on each side of a cut (when the sound allows)
RETAKE_WINDOW = 30.0   # s: how far ahead a restart can come
SPAN_LIMIT = 12.0      # s: at most this much between a failed attempt and its restart is dropped with it
FILLERS = {"اه", "ااه", "اااه", "ام", "امم", "اممم", "مم", "ممم", "اا", "ااا", "اهه", "همم", "هممم", "اوم", "ايي"}
CUE_STRONG = {"اعيد", "اعيدها", "نعيد", "نعيدها", "غلط", "ستوب", "استوب", "كت", "جديد", "لحظه", "سوري"}
CUE_WORDS = CUE_STRONG | {"لا", "خلي", "خليني", "من", "مره", "ثانيه", "اوكي", "اوك", "عفوا", "ماكو", "شي", "يعني"}


def normalize_ar(text: str) -> str:
    text = _TASHKEEL.sub("", text).translate(_TRANS)
    text = _PUNCT.sub("", text).lower()
    return " ".join(text.split())


def split_phrases(words: list[Word], pause: float = PHRASE_PAUSE) -> list[list[Word]]:
    phrases: list[list[Word]] = []
    for w in words:
        if phrases and w.start - phrases[-1][-1].end <= pause:
            phrases[-1].append(w)
        else:
            phrases.append([w])
    return phrases


def same(a: str, b: str) -> bool:
    """Two heard words are the same word: equal, nearly equal spelling, or one cut off from the other."""
    if a == b:
        return True
    if len(a) < 3 or len(b) < 3 or any(c.isdigit() for c in a + b):   # numbers must match exactly
        return False
    if a.startswith(b) or b.startswith(a):
        return min(len(a), len(b)) >= 3
    return SequenceMatcher(None, a, b).ratio() >= 0.75


def _tokens(p: list[Word]) -> list[str]:
    return [t for t in (normalize_ar(w.text) for w in p) if t and t not in FILLERS]


def _matched(ta: list[str], tb: list[str]) -> tuple[int, int]:
    """(words of `ta` found in order inside `tb`, position in `tb` of the first match) — fuzzy LCS."""
    n, m = len(ta), len(tb)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            dp[i][j] = dp[i + 1][j + 1] + 1 if same(ta[i], tb[j]) else max(dp[i + 1][j], dp[i][j + 1])
    first = next((j for j in range(m) if same(ta[0], tb[j])), m) if n else m
    return dp[0][0], first


def _is_retake(a: list[Word], b: list[Word], match: int = 3, max_retake: float = 6.0, overlap: float = 0.6) -> bool:
    """B starts again what A started: A's opening is near B's opening and most of A is said again in B."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return False
    if len(ta) < match:     # a false start: a word or two, then the full sentence
        got, first = _matched(ta, tb[:len(ta) + 1])
        return got == len(ta) and first == 0 and b[0].start - a[-1].end <= 5.0
    got, first = _matched(ta, tb[:len(ta) + 4])
    if first > 2 or got < min(match, len(ta)):
        return False
    cover = got / len(ta)
    return cover >= 0.75 or (cover >= overlap and a[-1].end - a[0].start <= max_retake)


def _is_cue(p: list[Word]) -> bool:
    """"لا لا، خلي أعيدها" — a short phrase that only says the last attempt was wrong."""
    toks = [normalize_ar(w.text) for w in p]
    toks = [t for t in toks if t]
    if not toks or len(toks) > 5:
        return False
    strong = any(t in CUE_STRONG for t in toks) or "لا لا" in " ".join(toks)
    return strong and sum(t in CUE_WORDS for t in toks) / len(toks) >= 0.6


def drop_retakes(phrases: list[list[Word]], window: float = RETAKE_WINDOW, match: int = 3,
                 max_retake: float = 6.0, overlap: float = 0.6,
                 dropped: list | None = None, reasons: dict | None = None) -> list[list[Word]]:
    """Phrases that survive. `dropped` collects the rest; `reasons[id(phrase)]` says why."""
    gone: dict[int, str] = {}
    for i, a in enumerate(phrases):
        if _is_cue(a):
            gone[i] = "إشارة غلط"
            if i > 0 and a[0].start - phrases[i - 1][-1].end <= 10.0:
                gone.setdefault(i - 1, "قبل إشارة الغلط")
            continue
        if not _tokens(a):
            gone[i] = "حشو"
            continue
        for j in range(i + 1, len(phrases)):
            b = phrases[j]
            if b[0].start - a[-1].end > window:
                break
            if _is_retake(a, b, match, max_retake, overlap):
                gone.setdefault(i, "إعادة")
                # the whole failed attempt goes: what he said between the try and the restart
                if b[0].start - a[0].start <= SPAN_LIMIT:
                    for k in range(i + 1, j):
                        gone.setdefault(k, "إعادة (تكملة غلط)")
                break
    kept = []
    for i, p in enumerate(phrases):
        if i in gone:
            if dropped is not None:
                dropped.append(p)
            if reasons is not None:
                reasons[id(p)] = gone[i]
        else:
            kept.append(p)
    return kept


def trim_phrase(p: list[Word], removed: list | None = None) -> list[Word]:
    """Inside one breath: restarts ("راح نحچي عن راح نحچي عن قصة"), stutters ("ال ال"), cut-off words, long fillers."""
    words = list(p)
    changed = True
    while changed:
        changed = False
        t = [normalize_ar(w.text) for w in words]
        for i in range(len(words) - 1):
            cut = None
            if t[i] in FILLERS and words[i].end - words[i].start >= 0.2:
                cut = (i, i + 1, "حشو")
            elif t[i] and t[i + 1].startswith(t[i]) and t[i] != t[i + 1] and len(t[i]) >= 3 \
                    and words[i].end - words[i].start < 0.6:     # ("لا، لازم" is not a cut-off word: 3 letters at least)
                cut = (i, i + 1, "كلمة مقطوعة")
            elif t[i] == t[i + 1] and len(t[i]) <= 2:
                cut = (i, i + 1, "تأتأة")
            else:
                for j in range(i + 2, min(len(words) - 1, i + 7)):
                    span = j - i
                    # a restart repeats the WHOLE abandoned piece (its last word may be cut off);
                    # "تشتغل شوكت متريد وتطفى شوكت متريد" repeats only part of it: that is how he talks
                    if t[i] and len(t[i] + t[i + 1]) >= 5 and j + span - 1 <= len(t) and \
                            all(same(t[i + k], t[j + k]) for k in range(span - 1)) and \
                            (same(t[j - 1], t[j + span - 1]) or t[j + span - 1].startswith(t[j - 1])):
                        cut = (i, j, "بدأ الجملة من جديد")
                        break
            if cut:
                a, b, why = cut
                if removed is not None:
                    removed.append((words[a:b], why))
                words = words[:a] + words[b:]
                changed = True
                break
    return words


def keep_segments(phrases: list[list[Word]], pad: float = PAD, merge_gap: float = 0.25,
                  duration: float | None = None, max_gap: float = MAX_GAP) -> list[tuple[float, float]]:
    """Source ranges to keep: one per stretch of talk without a long pause. A word removed from inside a
    phrase splits it too, and no range's breath reaches into a removed word."""
    runs: list[list[Word]] = []
    for w in (w for p in phrases for w in p):
        if runs and w.start - runs[-1][-1].end <= max_gap and _adjacent(runs[-1][-1], w):
            runs[-1].append(w)
        else:
            runs.append([w])
    segs: list[tuple[float, float]] = []
    joinable = []
    for r in runs:
        lo, hi = _neighbours(r[0], r[-1])
        s, e = max(0.0, lo, r[0].start - pad), min(hi, r[-1].end + pad)
        if duration is not None:
            e = min(e, duration)
        if segs and s - segs[-1][1] < merge_gap and joinable[-1] is r[0]:
            segs[-1] = (segs[-1][0], max(e, segs[-1][1]))
        else:
            segs.append((s, e))
        joinable.append(_next_word(r[-1]))
    return [(round(s, 3), round(e, 3)) for s, e in segs]


_ALL: list[Word] = []          # the full transcript of the current clean (set by decide)
_ORDER: dict[int, int] = {}    # id(word) -> its index in _ALL


def _adjacent(a: Word, b: Word) -> bool:
    ia, ib = _ORDER.get(id(a)), _ORDER.get(id(b))
    return ia is None or ib is None or ib == ia + 1


def _next_word(w: Word):
    i = _ORDER.get(id(w))
    return _ALL[i + 1] if i is not None and i + 1 < len(_ALL) else None


def _neighbours(first: Word, last: Word) -> tuple[float, float]:
    """End of the transcript word before `first`, start of the one after `last` (removed words included)."""
    i, j = _ORDER.get(id(first)), _ORDER.get(id(last))
    lo = _ALL[i - 1].end + 0.02 if i else 0.0
    hi = _ALL[j + 1].start - 0.02 if j is not None and j + 1 < len(_ALL) else float("inf")
    return lo, hi


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


# ---------- the real sound ----------

HOP = 0.01   # s per loudness value


def loudness(path: Path) -> np.ndarray:
    """RMS of the sound every 10 ms (mono, 16 kHz)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    n = len(x) // 160
    return np.sqrt((x[: n * 160].reshape(n, 160) ** 2).mean(axis=1)) if n else np.zeros(1, np.float32)


def refine(segs: list[tuple[float, float]], env: np.ndarray, words: list[Word],
           pad: float = PAD) -> list[tuple[float, float]]:
    """Move each cut to where the sound really is quiet: the end goes past the word's real tail (Whisper
    often ends words early), the start before its real onset; never into a neighbouring word."""
    if len(env) < 10:
        return segs
    floor, peak = float(np.percentile(env, 10)), float(np.percentile(env, 95))
    quiet = max(floor * 3, peak * 0.04, 1e-4)
    times = sorted((w.start, w.end) for w in words)

    def neighbour_bounds(s, e):
        before = max((we for ws, we in times if we <= s + pad + 0.01), default=0.0)
        after = min((ws for ws, we in times if ws >= e - pad - 0.01), default=len(env) * HOP)
        return before, after

    out = []
    for s, e in segs:
        lo, hi = neighbour_bounds(s, e)
        speech_s, speech_e = s + pad, e - pad
        # start: last quiet spot before the onset (≤ 0.15 s back: Whisper's onsets are close), then a short breath
        i = int(speech_s / HOP)
        j = i
        while j > 0 and (i - j) * HOP < 0.15 and env[j] > quiet:
            j -= 1
        start = max(lo + 0.02, min(s, j * HOP - 0.04))
        # end: first quiet spot after the word's end (≤ 0.35 s on), then a short breath
        i = int(speech_e / HOP)
        j = min(i, len(env) - 1)
        while j < len(env) - 1 and (j - i) * HOP < 0.35 and env[j] > quiet:
            j += 1
        end = min(hi - 0.02, max(e, j * HOP + 0.06))
        if out and start <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], end))
        elif end > start:
            out.append((round(start, 3), round(end, 3)))
    return out


# ---------- the whole stage ----------

def decide(words: list[Word], overrides: dict | None = None) -> tuple[list[Word], list[tuple[list[Word], str]]]:
    """(words kept, [(words removed, why)]) for the full transcript."""
    _ALL[:] = words
    _ORDER.clear()
    _ORDER.update({id(w): i for i, w in enumerate(words)})
    removed: list[tuple[list[Word], str]] = []
    dropped, reasons = [], {}
    kept_phrases = drop_retakes(split_phrases(words), dropped=dropped, reasons=reasons)
    removed += [(p, reasons.get(id(p), "إعادة")) for p in dropped]
    kept = [w for p in kept_phrases for w in trim_phrase(p, removed)]
    overrides = overrides or {}
    for s, e in overrides.get("drop", []):
        out = [w for w in kept if s <= (w.start + w.end) / 2 < e]
        if out:
            removed.append((out, "حذف يدوي"))
        kept = [w for w in kept if not s <= (w.start + w.end) / 2 < e]
    for s, e in overrides.get("keep", []):
        back = [w for w in words if s <= (w.start + w.end) / 2 < e and w not in kept]
        kept = sorted(kept + back, key=lambda w: w.start)
    return kept, removed


def unheard(env: np.ndarray, words: list[Word], min_len: float = 0.8) -> list[tuple[float, float]]:
    """Stretches of clear sound that no transcribed word covers (speech Whisper may have missed: it is cut
    with the silences, so the report lists it for a human look)."""
    if len(env) < 10:
        return []
    loud = env > max(float(np.percentile(env, 10)) * 4, float(np.percentile(env, 95)) * 0.15)
    covered = np.zeros(len(env), bool)
    for w in words:
        covered[max(0, int((w.start - 0.25) / HOP)): int((w.end + 0.25) / HOP)] = True
    out, start = [], None
    for i, v in enumerate(loud & ~covered):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if (i - start) * HOP >= min_len:
                out.append((round(start * HOP, 2), round(i * HOP, 2)))
            start = None
    return out


def _report(ep: Episode, removed, duration: float, kept_secs: float, missed=()) -> None:
    lines = [f"الطول الخام: {duration:.1f} ث  ←  بعد القص: {kept_secs:.1f} ث  (انشال {duration - kept_secs:.1f} ث)", ""]
    if missed:
        lines += ["⚠️ صوت واضح ما انكتب بالتفريغ (انشال ويه السكتات، راجعه إذا كلام مهم):"]
        lines += [f"{s:8.2f}–{e:8.2f}" for s, e in missed] + [""]
    for ws, why in sorted(removed, key=lambda r: r[0][0].start):
        lines.append(f"{ws[0].start:8.2f}–{ws[-1].end:8.2f}  {why:<18}  {' '.join(w.text for w in ws)}")
    (ep.work / "cut_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def clean(ep: Episode, script: Path | None = None) -> float:
    words = load_words(ep.transcript)
    duration = probe(ep.source).duration
    override_file = ep.edit / "cuts_override.json"
    overrides = json.loads(override_file.read_text(encoding="utf-8")) if override_file.exists() else {}
    kept_words, removed = decide(words, overrides)
    (ep.work / "retakes.json").write_text(json.dumps(
        [{"start": ws[0].start, "end": ws[-1].end, "why": why, "text": " ".join(w.text for w in ws)}
         for ws, why in removed], ensure_ascii=False, indent=1), encoding="utf-8")
    fps = load_format(ep).fps  # fetch() normalized to this fps and 48 kHz audio
    spf = 48000 // fps
    segs = keep_segments([kept_words], duration=duration)
    env = loudness(ep.source)
    segs = refine(segs, env, words)
    segs = snap_to_frames([(s, min(e, duration)) for s, e in segs], fps)
    ep.cuts.write_text(json.dumps(segs), encoding="utf-8")
    if script:  # Iraqi dialect: correct the words we keep from the script the owner read
        from .align import align_to_script
        kept_words = align_to_script(ep, kept_words, script)
    save_words(remap_words(kept_words, segs), ep.clean_words)
    kept_secs = sum(e - s for s, e in segs)
    _report(ep, removed, duration, kept_secs, unheard(env, words))

    parts, labels = [], []
    for i, (s, e) in enumerate(segs):
        f0, f1 = round(s * fps), round(e * fps)
        d = (f1 - f0) / fps
        fade = min(0.008, d / 4)
        parts.append(f"[0:v]trim=start_frame={f0}:end_frame={f1},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim=start_sample={f0 * spf}:end_sample={f1 * spf},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d={fade:.4f},afade=t=out:st={d - fade:.4f}:d={fade:.4f}[a{i}];")
        labels.append(f"[v{i}][a{i}]")
    graph = "".join(parts) + "".join(labels) + f"concat=n={len(segs)}:v=1:a=1[v][a]"
    gfile = ep.work / "clean_filter.txt"
    gfile.write_text(graph, encoding="utf-8")
    run_ffmpeg(["-i", str(ep.source), "-filter_complex_script", str(gfile),
                "-map", "[v]", "-map", "[a]", "-r", str(fps), "-c:v", "libx264", "-crf", "12",
                "-preset", "veryfast", "-c:a", "pcm_s16le" if ep.clean_video.suffix == ".mov" else "aac",
                "-b:a", "320k", str(ep.clean_video)])
    return kept_secs
