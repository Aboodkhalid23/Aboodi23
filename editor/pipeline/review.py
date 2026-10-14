"""`review`: the senior editor's look at an episode before the owner sees it (editor-mind skill).

Reads the plan (and the finished file when there is one) and answers the questions an experienced editor asks:
where would a viewer leave (his face alone too long, nothing new on screen), is the hook busy enough, are the
moves varied, did a moment that deserved a paper beside him get one, how many pictures were not found, how is
the sound, where did the time go. Writes edit/work/review.txt (Arabic, with a score out of 100 and what to fix
first) and adds one line of numbers to editor/learning/history.jsonl, so later episodes can be compared and the
editor can see whether it is getting better."""
import json
import re
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

from .paths import Episode
from .plan import FACE_KINDS, HOOK_SECONDS, load_plan

HISTORY = Path(__file__).resolve().parents[1] / "learning" / "history.jsonl"
PLAIN_FACE = {"face", "face_zoom_in", "face_zoom_out", "face_framed", "face_punch"}
DULL_FACE = 8.0      # his face alone for longer than this: viewers start to drift
DULL_STILL = 6.2     # one scene with nothing new for longer than this


def _ts(t: float) -> str:
    m, s = divmod(int(t), 60)
    return f"{m}:{s:02d}"


def dull_zones(beats) -> list[tuple[float, float, str]]:
    out, a = [], None
    for b in beats:
        if b.kind in PLAIN_FACE:
            a = b.start if a is None else a
            continue
        if a is not None and b.start - a > DULL_FACE:
            out.append((a, b.start, "وجهك بس"))
        a = None
    if a is not None and beats and beats[-1].end - a > DULL_FACE:
        out.append((a, beats[-1].end, "وجهك بس"))
    out += [(b.start, b.end, "ما اكو شي جديد") for b in beats
            if b.end - b.start > DULL_STILL and b.kind not in ("face_paper", "graphic")]
    return sorted(out)


def missed_papers(ep: Episode, plan) -> list[str]:
    """Moments the brief pointed at for a paper beside him (news, report, quote, number) that are still just his
    face on screen."""
    if not ep.plan_input.exists():
        return []
    out = []
    for line in ep.plan_input.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\[(\d+):(\d+(?:\.\d+)?)\] face_paper (\w+): (.*)", line)
        if not m:
            continue
        t = int(m[1]) * 60 + float(m[2]) + plan.teaser_total
        b = next((b for b in plan.beats if b.start <= t < b.end), None)
        if b is not None and b.kind in PLAIN_FACE:
            out.append(f"{_ts(t)} ({m[3]}): {m[4][:60]}")
    return out


def _loudness(video: Path) -> tuple[float | None, float | None]:
    from .qa import _loudness as measure
    return measure(video)


def review(ep: Episode, record: bool = True) -> dict:
    plan = load_plan(ep.plan)
    beats = plan.beats
    total = beats[-1].end if beats else 0.0
    body = [b for b in beats if b.zone == "body"]
    hook = [b for b in beats if b.start < HOOK_SECONDS]
    kinds = Counter(b.kind for b in beats)
    issues: list[tuple[int, str]] = []   # (weight, text) — the heavier, the more it costs viewers

    from .plan import validate_plan
    clean = sum(e - s for s, e in json.loads(ep.cuts.read_text(encoding="utf-8"))) if ep.cuts.exists() else None
    for e in (validate_plan(plan, clean) if clean is not None else [])[:5]:
        issues.append((5, f"قاعدة مكسورة: {e}"))
    zones = dull_zones(beats)
    for a, z, why in zones[:8]:
        issues.append((6, f"{_ts(a)}–{_ts(z)}: {why} {z - a:.0f} ث، حط ورقة يمّه (face_paper) أو صورة أو حركة وجه"))
    changes = len(hook)
    if hook and changes < HOOK_SECONDS / 3.5:
        issues.append((8, f"الهوك هادي: {changes} تغيير بأول 30 ث (الأحسن 9 أو أكثر)"))
    if beats and beats[0].kind in PLAIN_FACE and beats[0].kind == "face":
        issues.append((4, "أول لقطة وجه ثابت: أول 15 فريم لازم بيها حركة (تقريب أو صورة أو رقم)"))
    face_share = (sum((b.end - b.start) * (0.5 if b.kind == "face_paper" else 1)
                      for b in body if b.kind in FACE_KINDS or b.kind == "face_paper")
                  / max(1e-6, sum(b.end - b.start for b in body))) if body else 0
    trans = sum(1 for b in beats if b.transition)
    per10 = trans / max(1.0, total / 600)
    if per10 > 8:
        issues.append((3, f"انتقالات هواية: {trans} (تقريباً {per10:.0f} بكل 10 دقايق، الأحسن 6 أو أقل)"))
    sfx = sum(1 for b in beats if b.sfx)
    if sfx > max(8, total / 60):
        issues.append((2, f"مؤثرات صوتية كثيرة: {sfx} (الصنعة: قليلة ومربوطة بشي يبين)"))
    run, worst = 1, (1, "")
    for a, b in zip(beats, beats[1:]):
        fam = lambda k: "face" if k in PLAIN_FACE else k
        run = run + 1 if fam(a.kind) == fam(b.kind) else 1
        if run > worst[0]:
            worst = (run, f"{_ts(b.start)}")
    if worst[0] >= 3:
        issues.append((4, f"نفس العائلة {worst[0]} مرات ورا بعض عند {worst[1]} (نوّع: ورقة، صورة، رقم، أرشيف)"))
    missed = missed_papers(ep, plan)
    for m in missed[:6]:
        issues.append((3, f"لحظة تستاهل ورقة يمّه وهي وجه بس: {m}"))
    fallbacks = json.loads(ep.fallbacks.read_text(encoding="utf-8")) if ep.fallbacks.exists() else []
    if fallbacks:
        issues.append((3, f"{len(fallbacks)} صورة ما انلگت وصارت كتابة: جرّب query أقصر أو source ثاني"))
    if "face_paper" not in kinds and total > 120:
        issues.append((4, "ولا مشهد أوراق يمّه بالحلقة: هذا ستايل القناة الجديد"))

    video = next((p for p in (ep.final, ep.edit / "preview.mp4") if p.exists()), None)
    lufs = peak = None
    if video is not None:
        lufs, peak = _loudness(video)
        if lufs is not None and not -16 <= lufs <= -12:
            issues.append((5, f"علو الصوت {lufs:.1f} (يوتيوب يحب −14)"))
        if peak is not None and peak > -1:
            issues.append((5, f"ذروة الصوت {peak:.1f} تقطّع (لازم −1 أو أقل)"))

    timings = ep.work / "timings.json"
    slow = []
    if timings.exists():
        t = json.loads(timings.read_text(encoding="utf-8"))
        slow = sorted(t.items(), key=lambda kv: -kv[1])[:3]

    score = max(0, 100 - sum(w for w, _ in issues))
    issues.sort(key=lambda x: -x[0])
    lines = [f"مراجعة المونتير الخبير: {score}/100", f"المدة {_ts(total)} | {len(beats)} مشهد | الوجه {face_share:.0%} من الجسم"
             f" | انتقالات {trans} | مؤثرات {sfx} | أوراق يمّه {kinds.get('face_paper', 0)}"]
    if lufs is not None:
        lines.append(f"الصوت {lufs:.1f} LUFS، ذروة {peak:.1f}")
    lines += ["", "صلّح أول (الأثقل فوگ):"] + [f"- {t}" for _, t in issues] if issues else ["", "✅ ما لگيت شي يحتاج تصليح"]
    if slow:
        lines += ["", "وين راح الوقت: " + "، ".join(f"{k} {v / 60:.1f} د" for k, v in slow)]
    (ep.work / "review.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = {"episode": ep.root.name, "date": date.today().isoformat(), "score": score, "minutes": round(total / 60, 1),
              "beats": len(beats), "face_share": round(face_share, 2), "dull": len(zones), "hook_changes": changes,
              "papers": kinds.get("face_paper", 0), "fallbacks": len(fallbacks), "lufs": lufs,
              "slowest": slow[0][0] if slow else None, "issues": [t for _, t in issues]}
    if record:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        old = [json.loads(x) for x in HISTORY.read_text(encoding="utf-8").splitlines()] if HISTORY.exists() else []
        old = [o for o in old if o.get("episode") != result["episode"]]   # one line per episode, latest review
        HISTORY.write_text("".join(json.dumps({k: v for k, v in o.items() if k != "issues"}, ensure_ascii=False) + "\n"
                                   for o in old + [result]), encoding="utf-8")
    return result


def trend(n: int = 5) -> str:
    """The last episodes' scores, oldest first: is the editor improving?"""
    if not HISTORY.exists():
        return ""
    rows = [json.loads(x) for x in HISTORY.read_text(encoding="utf-8").splitlines() if x.strip()][-n:]
    return " ← ".join(f"{r['episode']} {r['score']}" for r in rows)
