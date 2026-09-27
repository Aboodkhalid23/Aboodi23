"""The edit plan Claude writes, and the rules code enforces on it."""
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

KINDS = ("face", "face_zoom_in", "face_zoom_out", "face_framed",
         "image", "ai_image", "ai_video", "graphic")
FACE_KINDS = KINDS[:4]
AI_KINDS = ("ai_image", "ai_video")
GRAPHIC_TYPES = ("number", "headline", "quote", "map", "timeline", "chart", "text")

HOOK_SECONDS = 30.0
LIMITS = {"hook": (1.5, 2.5), "body": (4.0, 6.0)}
FACE_SHARE = (0.35, 0.55)
TOL = 0.05


@dataclass
class Beat:
    start: float
    end: float
    zone: str
    kind: str
    query: str | None = None
    prompt: str | None = None
    treatment: str | None = None
    graphic: dict | None = None
    sfx: str | None = None

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class EditPlan:
    style: dict
    style_reason: str
    teaser: list[tuple[float, float]]
    beats: list[Beat]
    shorts: list = field(default_factory=list)

    @property
    def teaser_total(self) -> float:
        return sum(e - s for s, e in self.teaser)


def load_plan(path: Path) -> EditPlan:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return EditPlan(style=d["style"], style_reason=d.get("style_reason", ""),
                    teaser=[tuple(t) for t in d.get("teaser", [])],
                    beats=[Beat(**b) for b in d["beats"]], shorts=d.get("shorts", []))


def save_plan(plan: EditPlan, path: Path) -> None:
    d = asdict(plan)
    d["teaser"] = [list(t) for t in plan.teaser]
    d["beats"] = [{k: v for k, v in b.items() if v is not None} for b in d["beats"]]
    Path(path).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def validate_plan(plan: EditPlan, clean_duration: float) -> list[str]:
    errs: list[str] = []
    for i, (s, e) in enumerate(plan.teaser):
        if not (0 <= s < e <= clean_duration + TOL):
            errs.append(f"teaser {i}: لازم يكون داخل الفيديو المنظف (0–{clean_duration:.2f})")
        elif not (1.5 - TOL <= e - s <= 2.5 + TOL):
            errs.append(f"teaser {i}: طوله لازم بين 1.5 و 2.5 ثانية")
    total = plan.teaser_total + clean_duration
    beats = plan.beats
    if not beats:
        return errs + ["beat 0: الخطة ما بيها beats"]

    prev_end = 0.0
    for i, b in enumerate(beats):
        last = i == len(beats) - 1
        if b.kind not in KINDS:
            errs.append(f"beat {i}: نوع غير معروف '{b.kind}'")
            prev_end = b.end
            continue
        if b.kind in AI_KINDS:
            errs.append(f"beat {i}: الذكاء الاصطناعي مو مفعّل بعد (الجزء 2)")
        if b.start > prev_end + TOL:
            errs.append(f"beat {i}: فراغ قبله ({prev_end:.2f}–{b.start:.2f})")
        elif b.start < prev_end - TOL:
            errs.append(f"beat {i}: متداخل ويه الي قبله ({b.start:.2f} < {prev_end:.2f})")
        if b.end > total + TOL:
            errs.append(f"beat {i}: يعبر نهاية الفيديو ({b.end:.2f} > {total:.2f})")
        elif last and b.end < total - TOL:
            errs.append(f"beat {i}: الخطة تخلص قبل نهاية الفيديو ({b.end:.2f} < {total:.2f})")
        zone = "hook" if b.start < HOOK_SECONDS - TOL else "body"
        if b.zone != zone:
            errs.append(f"beat {i}: المنطقة لازم تكون {zone}")
        lo, hi = LIMITS[zone]
        if last:
            lo = min(lo, 1.5)  # the final beat absorbs whatever time is left
        if not (lo - TOL <= b.duration <= hi + TOL):
            errs.append(f"beat {i}: طوله {b.duration:.2f} ثانية، لازم بين {lo:g} و {hi:g}")
        if i and beats[i - 1].kind == b.kind:
            errs.append(f"beat {i}: نفس نوع الي قبله ({b.kind})")
        if b.kind == "image" and not b.query:
            errs.append(f"beat {i}: صورة بدون query")
        if b.kind == "graphic" and (not b.graphic or b.graphic.get("type") not in GRAPHIC_TYPES):
            errs.append(f"beat {i}: گرافيك لازم type من {', '.join(GRAPHIC_TYPES)}")
        prev_end = b.end

    body = [b for b in beats if b.zone == "body" and b.kind in KINDS]
    body_time = sum(b.duration for b in body)
    if body_time > 0:
        share = sum(b.duration for b in body if b.kind in FACE_KINDS) / body_time
        if not (FACE_SHARE[0] <= share <= FACE_SHARE[1]):
            errs.append(f"beat {beats.index(body[0])}: الوجه {share:.0%} من الجسم، لازم بين 35% و 55%")
    return errs
