"""The edit plan Claude writes, and the rules code enforces on it."""
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

KINDS = ("face", "face_zoom_in", "face_zoom_out", "face_framed", "face_punch", "face_fx",
         "image", "ai_image", "ai_video", "graphic", "entity")
FACE_KINDS = KINDS[:6]
AI_KINDS = ("ai_image", "ai_video")
GRAPHIC_TYPES = ("number", "headline", "quote", "map", "timeline", "chart", "text")
FX_TYPES = ("subscribe", "tv", "none")        # face_fx wrappers; "none" = stickers only
TRANSITIONS = ("zoom", "flash", "whip", "glitch")
STICKERS = ("stamp", "arrow", "burst", "tape", "circle")

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
    caption: str | None = None   # Arabic words for the screen if no image is found
    prompt: str | None = None
    treatment: str | None = None
    graphic: dict | None = None
    sfx: str | None = None
    entity: str | None = None       # id in edit/entities.json (kind "entity")
    fx: str | None = None           # face_fx wrapper: subscribe | tv | none
    stickers: list | None = None    # [{"type": "stamp", "text": "...", "at": 0.5}] on face_fx beats
    transition: str | None = None   # entry effect on this beat: zoom | flash | whip | glitch

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
    chapters: list[dict] = field(default_factory=list)  # [{"t": cleaned-timeline seconds, "title": str}]
    ai_budget: float = 0.0   # Higgsfield credits this episode may spend (edit/ai_ledger.json)

    def chapter_times(self) -> list[float]:
        """Chapter starts on the final timeline: the first covers the teaser, the rest shift by it."""
        return [0.0 if i == 0 else c["t"] + self.teaser_total for i, c in enumerate(self.chapters)]

    @property
    def teaser_total(self) -> float:
        return sum(e - s for s, e in self.teaser)


def load_plan(path: Path) -> EditPlan:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return EditPlan(style=d["style"], style_reason=d.get("style_reason", ""),
                    teaser=[tuple(t) for t in d.get("teaser", [])],
                    beats=[Beat(**b) for b in d["beats"]], shorts=d.get("shorts", []),
                    chapters=d.get("chapters", []), ai_budget=d.get("ai_budget", 0.0))


def save_plan(plan: EditPlan, path: Path) -> None:
    d = asdict(plan)
    d["teaser"] = [list(t) for t in plan.teaser]
    d["beats"] = [{k: v for k, v in b.items() if v is not None} for b in d["beats"]]
    Path(path).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def validate_plan(plan: EditPlan, clean_duration: float, entities: set[str] | None = None,
                  ai_spent: float = 0.0) -> list[str]:
    """`entities`: ids known in entities.json (None = don't check). `ai_spent`: credits in the ledger."""
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
        if b.kind in AI_KINDS and not (b.prompt and b.caption):
            errs.append(f"beat {i}: مشهد الذكاء الاصطناعي لازم بيه prompt (إنگليزي) و caption (عربي)")
        if b.kind == "entity":
            if not b.entity:
                errs.append(f"beat {i}: بطاقة الاسم لازم بيها entity")
            elif entities is not None and b.entity not in entities:
                errs.append(f"beat {i}: '{b.entity}' مو موجود بـ entities.json")
        if b.kind == "face_fx" and b.fx not in FX_TYPES:
            errs.append(f"beat {i}: face_fx لازم fx من {', '.join(FX_TYPES)}")
        for s in b.stickers or []:
            if b.kind != "face_fx" or s.get("type") not in STICKERS:
                errs.append(f"beat {i}: الملصقات بس على face_fx، ونوعها من {', '.join(STICKERS)}")
                break
        if b.transition and b.transition not in TRANSITIONS:
            errs.append(f"beat {i}: transition لازم من {', '.join(TRANSITIONS)}")
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
        if b.kind == "image" and not (b.query and b.caption):
            errs.append(f"beat {i}: صورة لازم بيها query (إنگليزي) و caption (عربي)")
        if b.kind == "graphic" and (not b.graphic or b.graphic.get("type") not in GRAPHIC_TYPES):
            errs.append(f"beat {i}: گرافيك لازم type من {', '.join(GRAPHIC_TYPES)}")
        prev_end = b.end

    if plan.chapters:
        if len(plan.chapters) < 3:
            errs.append("chapter 0: يوتيوب يحتاج 3 فصول أو أكثر")
        if plan.chapters[0]["t"] != 0:
            errs.append("chapter 0: أول فصل لازم يبدي من 0")
        times = plan.chapter_times()
        for i in range(1, len(times)):
            if times[i] - times[i - 1] < 10:
                errs.append(f"chapter {i}: لازم يبعد 10 ثواني أو أكثر عن الي قبله")

    if ai_spent > plan.ai_budget + 1e-9:
        errs.append(f"ai: صرفنا {ai_spent:g} رصيد، والميزانية {plan.ai_budget:g}")

    body = [b for b in beats if b.zone == "body" and b.kind in KINDS]
    body_time = sum(b.duration for b in body)
    if body_time > 0:
        share = sum(b.duration for b in body if b.kind in FACE_KINDS) / body_time
        if not (FACE_SHARE[0] <= share <= FACE_SHARE[1]):
            errs.append(f"beat {beats.index(body[0])}: الوجه {share:.0%} من الجسم، لازم بين 35% و 55%")
    return errs
