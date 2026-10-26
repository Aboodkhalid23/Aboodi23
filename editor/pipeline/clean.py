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
from functools import lru_cache
from pathlib import Path

import numpy as np

from .fmt import load_format
from .media import HWDEC, PROXY, WORK, filter_script, probe, run_ffmpeg
from .paths import Episode
from .transcribe import Word, load_words, save_words

_TASHKEEL = re.compile("[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")   # harakat, tatweel
_PUNCT = re.compile(r"[^\w\s]")
_TRANS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "گ": "ك", "چ": "ج", "ڤ": "ف", "پ": "ب"})

PHRASE_PAUSE = 0.7     # s: a longer pause starts a new phrase (unit for retakes)
MAX_GAP = 0.45         # s: a longer pause inside the talk is cut out
PAD = 0.12             # s: breath kept on each side of a cut (when the sound allows)
RETAKE_WINDOW = 30.0   # s: how far ahead a restart can come
PUNCH = 1.08          # after a removed retake the picture steps in (or back out) by this much: the jump reads as a
JUMP = 0.9            # deliberate second camera, not a hole. JUMP: seconds removed that make a cut "visible"
SEEN_JUMP = 9.0       # mean change (0–255) of a tiny grey frame across a cut that the eye reads as a "jump"
MIN_REFRAME = 1.5     # s: never change the framing again sooner than this (it would feel busy)
SPAN_LIMIT = 12.0      # s: at most this much between a failed attempt and its restart is dropped with it
FILLERS = {"اه", "ااه", "اااه", "ام", "امم", "اممم", "مم", "ممم", "اا", "ااا", "اهه", "همم", "هممم", "اوم", "ايي"}
# Short words Iraqis double on purpose ("لا لا"، "اي اي"، "يا يا"): emphasis, not a stutter — said without a gap
EMPHATIC = {"لا", "اي", "يا", "بس", "هي", "هو", "اه"}
# "I got it wrong, again" in every dialect (owner, 2026-10-26): Iraqi, Gulf, Levantine, Egyptian and formal Arabic
CUE_STRONG = {"اعيد", "اعيدها", "اعيده", "نعيد", "نعيدها", "عيدها", "بعيد", "بعيدها", "هعيد", "هعيدها", "غلط", "غلطت",
              "خطا", "ستوب", "استوب", "كت", "كات", "جديد", "لحظه", "سوري", "معليش", "معلش", "عذرا", "اسف", "اسفه"}
CUE_WORDS = CUE_STRONG | {"لا", "خلي", "خليني", "خلني", "خلينا", "دعني", "دعوني", "من", "مره", "ثانيه", "تانيه", "ثاني",
                          "تاني", "اوكي", "اوك", "عفوا", "ماكو", "مو", "مب", "مش", "شي", "اشي", "يعني", "كذا", "هيك",
                          "كده", "البدايه", "الاول", "طيب", "يلا", "ثواني"}


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


@lru_cache(maxsize=300_000)
def same(a: str, b: str) -> bool:
    """Two heard words are the same word: equal, nearly equal spelling, or one cut off from the other.
    Remembered: an hour of talk asks the same pairs again and again (that made the cut slow)."""
    if a == b:
        return True
    if len(a) < 3 or len(b) < 3 or any(c.isdigit() for c in a + b):   # numbers must match exactly
        return False
    if a.startswith(b) or b.startswith(a):
        return min(len(a), len(b)) >= 3
    if 2 * min(len(a), len(b)) < 0.75 * (len(a) + len(b)):   # too different in length to ever reach 0.75
        return False
    m = SequenceMatcher(None, a, b)
    return m.quick_ratio() >= 0.75 and m.ratio() >= 0.75


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
            elif t[i] == t[i + 1] and len(t[i]) <= 2 and not (
                    t[i] in EMPHATIC and words[i + 1].start - words[i].end < 0.15):
                cut = (i, i + 1, "تأتأة")
            else:
                for j in range(i + 2, min(len(words) - 1, i + 7)):
                    span = j - i
                    # a restart repeats the WHOLE abandoned piece (its last word may be cut off);
                    # "تشتغل شوكت متريد وتطفى شوكت متريد" repeats only part of it: that is how he talks
                    if t[i] and len(t[i] + t[i + 1]) >= 5 and j + span - 1 < len(t) and \
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


RESTART_WORDS = 15      # the second try starts at most this many words after the first
RESTART_SECS = 12.0


def drop_restarts(words: list[Word], removed: list | None = None) -> list[Word]:
    """He starts a sentence, goes wrong, and says it again from the top without stopping (owner, 2026-10-26:
    "يوم من الايام كان اكو رجل يوم من الايام عاش رجل…"). The first try goes, from its opening words up to where
    the same opening is said again. Works on the whole talk, so pauses that split phrases don't hide it.
    An opening of three words is enough anywhere; two words only at the start of a sentence (after a breath)."""
    words = list(words)
    t = [normalize_ar(w.text) for w in words]
    i = 0
    while i < len(words) - 3:
        if not t[i] or t[i] in FILLERS:
            i += 1
            continue
        starts = i == 0 or words[i].start - words[i - 1].end >= 0.3
        cut = None
        for j in range(i + 2, min(len(words) - 1, i + RESTART_WORDS + 1)):
            if words[j].start - words[i].start > RESTART_SECS:
                break
            n = 0
            while j + n < len(words) and i + n < j and t[i + n] and same(t[i + n], t[j + n]):
                n += 1
            long_enough = n >= 3 or (n == 2 and starts and len(t[i] + t[i + 1]) >= 7 and j - i <= 8)
            # after a real stop, a long first try is a sentence of its own that starts alike
            # ("هاي الشركة كانت تبني… / هاي الشركة كانت عليها ديون…"): the phrase rules judge those
            stopped = words[j].start - words[j - 1].end >= 0.5
            if long_enough and j + n < len(words) and not (stopped and j - i - n > 3):
                cut = j
                break
        if cut is None:
            i += 1
            continue
        if removed is not None:
            removed.append((words[i:cut], "بدأ الجملة من جديد"))
        del words[i:cut], t[i:cut]      # stay at i: a third take may follow the second
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
                                round(offset + min(w.end, e) - s, 3), w.p))
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
    kept = drop_restarts(kept, removed)
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


def seen_jumps(video: Path, segs: list[tuple[float, float]], fps: int) -> set[int]:
    """Cuts where his picture visibly jumps (head moved, leaned, hands): the last frame before the cut against the
    first after it, on the app's light copy (one fast decode). Owner, 2026-10-25: "قص احترافي… ما يبين مقصص".
    A pro hides these by changing the framing on the cut (a second-camera feel); a still head needs nothing."""
    if not video.exists() or len(segs) < 2:
        return set()
    want = {}
    for i in range(1, len(segs)):
        want[max(0, round(segs[i - 1][1] * fps) - 1)] = (i, 0)
        want[round(segs[i][0] * fps)] = (i, 1)
    expr = "+".join(f"eq(n\\,{n})" for n in sorted(want))
    script = video.with_name("jump_select.txt")
    script.write_text(f"select={expr},scale=64:36,format=gray", encoding="utf-8")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-filter_script:v", str(script), "-vsync", "0",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8)
    k = len(frames) // (64 * 36)
    if k != len(want):
        return set()
    frames = frames[: k * 64 * 36].reshape(k, 36, 64).astype(np.int16)
    got = {}
    for (n, (i, side)), f in zip(sorted(want.items()), frames):
        got.setdefault(i, [None, None])[side] = f
    return {i for i, (a, b) in got.items() if a is not None and b is not None and float(np.abs(a - b).mean()) > SEEN_JUMP}


def _punch_filter(ep: Episode) -> str:
    """Crop PUNCH× around his face and scale back: the closer framing used after a removed retake."""
    info = probe(ep.source)
    w, h = info.width, info.height
    try:   # on the raw footage (face.json is made later, from the cleaned video)
        from .face import locate_face
        f = locate_face(ep.source, info.duration) or {}
    except Exception:   # no face found: centre, a little above the middle (where faces sit)
        f = {}
    cx, cy = f.get("cx", 0.5), f.get("cy", 0.42)
    cw, ch = round(w / PUNCH / 2) * 2, round(h / PUNCH / 2) * 2
    x = min(max(0, round(cx * w - cw / 2)), w - cw)
    y = min(max(0, round(cy * h - ch / 2)), h - ch)
    return f",crop={cw}:{ch}:{x}:{y},scale={w}:{h}:flags=lanczos,setsar=1"


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
    from .options import pace_gaps
    gaps = pace_gaps(ep)   # the assistant sets the rhythm (the app's option): how much of each pause stays
    segs = keep_segments([kept_words], duration=duration, **({"max_gap": gaps[0], "pad": gaps[1]} if gaps else {}))
    env = loudness(ep.source)
    segs = refine(segs, env, words, **({"pad": gaps[1]} if gaps else {}))
    segs = snap_to_frames([(s, min(e, duration)) for s, e in segs], fps)
    ep.cuts.write_text(json.dumps(segs), encoding="utf-8")
    if script:  # Iraqi dialect: correct the words we keep from the script the owner read
        from .align import align_to_script
        kept_words = align_to_script(ep, kept_words, script)
    save_words(remap_words(kept_words, segs), ep.clean_words)
    kept_secs = sum(e - s for s, e in segs)
    _report(ep, removed, duration, kept_secs, unheard(env, words))

    zoomed, punch = False, _punch_filter(ep)
    try:
        seen = seen_jumps(ep.work / "app" / "proxy_source.mp4", segs, fps)
    except Exception:   # the check is a nicety: the old rule alone still cuts well
        seen = set()
    last_reframe, t_out = -99.0, 0.0
    pieces = []      # (first frame, last frame, zoomed, fade) of every kept stretch
    for i, (s, e) in enumerate(segs):
        f0, f1 = round(s * fps), round(e * fps)
        d = (f1 - f0) / fps
        jump = i > 0 and s - segs[i - 1][1] >= JUMP
        if jump or (i in seen and t_out - last_reframe >= MIN_REFRAME):
            # a retake was removed, or his picture visibly moved: change the framing so the cut reads as a camera change
            zoomed = not zoomed
            last_reframe = t_out
        t_out += d
        # the sound: a slightly longer fade on the big cuts, so no click and no sudden breath
        fade = min(0.025 if jump or (i + 1 < len(segs) and segs[i + 1][0] - e >= JUMP) else 0.012, d / 4)
        pieces.append((f0, f1, zoomed, fade))
    if len(pieces) > CHUNK:
        try:
            _encode_in_chunks(ep, pieces, fps, spf, punch)
            return kept_secs
        except Exception:   # noqa: BLE001 — the one-pass way below always works, only slower
            pass
    graph = _cut_graph(pieces, fps, spf, punch, 0) + "[v0]split=2[v][vp];[vp]scale=-2:720[pv];[a0]asplit=2[a][pa]"
    gfile = ep.work / "clean_filter.txt"
    gfile.write_text(graph, encoding="utf-8")
    run_ffmpeg([*HWDEC, "-i", str(ep.source), *filter_script(gfile),
                "-map", "[v]", "-map", "[a]", "-r", str(fps), *WORK, "-c:a", "pcm_s16le" if ep.clean_video.suffix == ".mov" else "aac",
                "-b:a", "320k", str(ep.clean_video),
                "-map", "[pv]", "-map", "[pa]", "-r", str(fps), *PROXY, str(_proxy(ep))])
    return kept_secs


CHUNK = 60      # kept stretches per piece: an hour of talk is ~1000 stretches, cut as ~17 pieces at the same time


def _cut_graph(pieces: list, fps: int, spf: int, punch: str, base: int) -> str:
    """Trim every kept stretch out of one input (frames counted from `base`) and join them as [v0][a0]."""
    parts, labels = [], []
    for i, (f0, f1, zoomed, fade) in enumerate(pieces):
        d = (f1 - f0) / fps
        a0, a1 = f0 - base, f1 - base
        parts.append(f"[0:v]trim=start_frame={a0}:end_frame={a1},setpts=PTS-STARTPTS{punch if zoomed else ''}[v{i}];"
                     f"[0:a]atrim=start_sample={a0 * spf}:end_sample={a1 * spf},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d={fade:.4f},afade=t=out:st={d - fade:.4f}:d={fade:.4f}[a{i}];")
        labels.append(f"[v{i}][a{i}]")
    return "".join(parts) + "".join(labels) + f"concat=n={len(pieces)}:v=1:a=1[v0][a0];"


def _encode_in_chunks(ep: Episode, pieces: list, fps: int, spf: int, punch: str) -> None:
    """Long videos: every filter branch sees every frame of its input, so one graph with 1000 stretches crawls.
    Here each piece of ~60 stretches reads only its own part of the source (a fast seek) and the pieces are made
    at the same time, then joined without re-encoding. The sound stays uncompressed until the join, so no gap."""
    import os
    from concurrent.futures import ThreadPoolExecutor
    tmp = ep.work / "cut_chunks"
    tmp.mkdir(parents=True, exist_ok=True)
    groups = [pieces[i:i + CHUNK] for i in range(0, len(pieces), CHUNK)]

    def one(k):
        g = groups[k]
        base = g[0][0]
        gfile = tmp / f"g{k}.txt"
        gfile.write_text(_cut_graph(g, fps, spf, punch, base) + "[v0]split=2[v][vp];[vp]scale=-2:720[pv];[a0]asplit=2[a][pa]",
                         encoding="utf-8")
        span = (g[-1][1] - base) / fps + 1.0
        proxy_v = [x for x in PROXY if x not in ("-movflags", "+faststart")]
        proxy_v = proxy_v[:proxy_v.index("-c:a")] if "-c:a" in proxy_v else proxy_v
        run_ffmpeg([*HWDEC, "-ss", f"{base / fps:.6f}", "-t", f"{span:.3f}", "-i", str(ep.source), *filter_script(gfile),
                    "-map", "[v]", "-map", "[a]", "-r", str(fps), *WORK, "-c:a", "pcm_s16le", str(tmp / f"c{k}.mov"),
                    "-map", "[pv]", "-map", "[pa]", "-r", str(fps), *proxy_v, "-c:a", "pcm_s16le", str(tmp / f"p{k}.mov")])

    workers = max(2, min(4, (os.cpu_count() or 4) // 3))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, range(len(groups))))
    for prefix, out, audio in (("c", ep.clean_video, ["-c:a", "pcm_s16le"] if ep.clean_video.suffix == ".mov"
                                else ["-c:a", "aac", "-b:a", "320k"]),
                               ("p", _proxy(ep), ["-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart"])):
        lst = tmp / f"{prefix}.txt"
        lst.write_text("".join(f"file '{tmp / f'{prefix}{k}.mov'}'\n" for k in range(len(groups))), encoding="utf-8")
        run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "copy", *audio, str(out)])
    for f in tmp.iterdir():
        f.unlink(missing_ok=True)


def _proxy(ep: Episode) -> Path:
    """The app's light copy of the cut video (same pass)."""
    p = ep.work / "app" / "proxy_clean.mp4"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
