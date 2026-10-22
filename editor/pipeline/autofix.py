"""`autofix`: repairs the mechanical mistakes of an edit plan by itself, so a plan never stops the render for a
gap, a beat that is too long or two faces in a row. Judgement calls (which picture, which story beat) are left
to Claude: those are reported, not guessed.

Fixes, in order: gaps and overlaps are closed; zones follow the clock; the last beat reaches the end; beats that
are too long are split on a pause between words (the second half becomes a face move, so the screen changes);
beats that are too short are folded into a neighbour; two face beats of the same kind in a row get different
face moves."""
import json
from dataclasses import replace
from pathlib import Path

from .plan import FACE_KINDS, HOOK_SECONDS, LIMITS, PAPER_LIMITS, TOL, EditPlan

FACE_CYCLE = ("face", "face_zoom_in", "face_punch", "face_zoom_out")


def _limits(b):
    return (PAPER_LIMITS if b.kind == "face_paper" else LIMITS)["hook" if b.start < HOOK_SECONDS - TOL else "body"]


def _pauses(words_file: Path | None, offset: float) -> list[float]:
    """Moments between two words (plan timeline): the cleanest places to cut a beat in two."""
    if not words_file or not Path(words_file).exists():
        return []
    words = json.loads(Path(words_file).read_text(encoding="utf-8"))
    return [round((a["e"] + b["s"]) / 2 + offset, 2) for a, b in zip(words, words[1:])]


def _other_face(*avoid: str) -> str:
    return next(k for k in FACE_CYCLE if k not in avoid)


def moments(plan: EditPlan, words_file: Path | None) -> list[str]:
    """His own moments get their look by themselves: asking to subscribe → the channel and the subscribe button
    (face_fx subscribe); an aside (joke, side fact) → kept, with a "على الهامش" tape (face_fx none)."""
    from .brief import _chunks, find_asides, find_moments
    from .clean import split_phrases
    from .transcribe import load_words
    if not words_file or not Path(words_file).exists():
        return []
    words = load_words(words_file)
    off = plan.teaser_total
    fixes = []

    def beat_at(t):
        return next((i for i, b in enumerate(plan.beats) if b.start <= t + off < b.end), None)

    def lonely(i):   # two face_fx in a row break the variety rule
        return all(plan.beats[j].kind != "face_fx" for j in (i - 1, i + 1) if 0 <= j < len(plan.beats))
    for line in find_moments(list(_chunks(split_phrases(words)))):
        if " face_fx subscribe:" not in line:
            continue
        m, sec = line[1:line.index("]")].split(":")
        i = beat_at(int(m) * 60 + float(sec))
        if i is None:
            continue
        b = plan.beats[i]
        near = any(x.kind == "face_fx" and x.fx in ("subscribe", "search") and abs(x.start - b.start) < 8 for x in plan.beats)
        if not near and b.kind in FACE_KINDS and b.kind != "face_cutout" and b.end - b.start >= 3.5 and lonely(i):
            # long enough: his channel is searched on a YouTube page with his real videos; else the short card
            b.kind, b.fx, b.stickers = "face_fx", "search" if b.end - b.start >= 4.5 else "subscribe", None
            fixes.append(f"beat {i}: يطلب الاشتراك هنا، حطيت " + ("صفحة البحث بقناته وفيديواته" if b.fx == "search" else "القناة وزر الاشتراك"))
    for a, _z, _t in find_asides(split_phrases(words)):
        i = beat_at(a)
        if i is None:
            continue
        b = plan.beats[i]
        if b.kind in FACE_KINDS and b.kind not in ("face_fx", "face_cutout") and not b.stickers and lonely(i):
            b.kind, b.fx = "face_fx", "none"
            b.stickers = [{"type": "tape", "text": "على الهامش", "at": round(min(b.end - b.start - 0.5, max(0.2, a + off - b.start)), 2)}]
            fixes.append(f"beat {i}: سالفة جانبية، بقت ويه شريط «على الهامش»")
    return fixes


def repair(plan: EditPlan, clean_duration: float, words_file: Path | None = None) -> list[str]:
    total = round(plan.teaser_total + clean_duration, 3)
    pauses = _pauses(words_file, plan.teaser_total)
    fixes: list[str] = []
    beats = sorted(plan.beats, key=lambda b: b.start)
    for _ in range(6):   # each pass can create work for the next (a split makes two beats); settles fast
        changed = False
        if beats and abs(beats[0].start) > 1e-6:
            beats[0].start = 0.0
            fixes.append("beat 0: صار يبدي من 0")
            changed = True
        for i in range(1, len(beats)):
            if abs(beats[i].start - beats[i - 1].end) > 1e-6:
                fixes.append(f"beat {i}: {'سدّيت فراغ' if beats[i].start > beats[i - 1].end else 'شلت تداخل'} "
                             f"({beats[i - 1].end:.2f} → {beats[i].start:.2f})")
                beats[i].start = beats[i - 1].end
                changed = True
        if beats and abs(beats[-1].end - total) > TOL:
            fixes.append(f"beat {len(beats) - 1}: نهايته صارت نهاية الفيديو ({total:.2f})")
            beats[-1].end = total
            changed = True
        beats = [b for b in beats if b.end - b.start > 0.05]

        out = []
        for i, b in enumerate(beats):
            lo, hi = _limits(b)
            last = i == len(beats) - 1
            if b.end - b.start > hi + TOL:
                mid = (b.start + b.end) / 2
                ok = [p for p in pauses if b.start + lo <= p <= b.end - lo]
                cut = round(min(ok, key=lambda p: abs(p - mid)) if ok else mid, 2)
                nxt = beats[i + 1].kind if i + 1 < len(beats) else ""
                second = _other_face(b.kind, nxt)
                tail = replace(b, start=cut, kind=second, query=None, caption=None, prompt=None, treatment=None,
                               graphic=None, papers=None, stickers=None, transition=None, sfx=None, pick=None,
                               entity=None, title=None, look=None, animate=None, fx=None, source=None)
                fixes.append(f"beat {i}: طويل ({b.end - b.start:.1f} ث)، قسمته على وقفة بالكلام ({cut:.2f})")
                b.end = cut
                if b.papers:   # papers that would now land after the scene ends move to... nowhere: drop them
                    b.papers = [p for p in b.papers if float(p.get("at", 0)) <= cut - b.start - 0.8] or b.papers[:1]
                out += [b, tail]
                changed = True
                continue
            if b.end - b.start < lo - TOL and not last and out:
                prev = out[-1]
                if prev.end - prev.start + (b.end - b.start) <= _limits(prev)[1] + TOL:
                    fixes.append(f"beat {i}: قصير ({b.end - b.start:.1f} ث)، ضميته للي قبله")
                    prev.end = b.end
                    changed = True
                    continue
            out.append(b)
        beats = out

        for i in range(1, len(beats)):
            a, b = beats[i - 1], beats[i]
            if a.kind == b.kind and b.kind in FACE_KINDS and b.kind not in ("face_fx", "face_cutout"):
                nxt = beats[i + 1].kind if i + 1 < len(beats) else ""
                b.kind = _other_face(a.kind, nxt)
                fixes.append(f"beat {i}: نفس حركة الوجه الي قبله، بدلتها لـ {b.kind}")
                changed = True
        for b in beats:
            zone = "hook" if b.start < HOOK_SECONDS - TOL else "body"
            if b.zone != zone:
                b.zone = zone
                changed = True
        if not changed:
            break
    plan.beats = beats
    fixes += moments(plan, words_file)
    return fixes
