"""The edit plan Claude writes, and the rules code enforces on it."""
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .grade import LOOKS

KINDS = ("face", "face_zoom_in", "face_zoom_out", "face_framed", "face_punch", "face_fx", "face_cutout",
         "image", "ai_image", "ai_video", "graphic", "entity", "footage")
FACE_KINDS = KINDS[:7]
AI_KINDS = ("ai_image", "ai_video")
GRAPHIC_TYPES = ("number", "headline", "quote", "map", "timeline", "chart", "text", "custom", "article")
CUSTOM_DIR = Path(__file__).resolve().parent.parent / "remotion" / "src" / "custom"
FX_TYPES = ("subscribe", "tv", "none")        # face_fx wrappers; "none" = stickers only
TRANSITIONS = ("zoom", "flash", "whip", "glitch", "tear", "burn")
STICKERS = ("stamp", "arrow", "burst", "tape", "circle", "scribble_circle", "scribble_arrow", "scribble_underline",
            "censor", "name_tag")
MARKABLE = ("face_fx", "image", "ai_image", "graphic", "entity", "footage")   # beats that can carry stickers

HOOK_SECONDS = 30.0
LIMITS = {"hook": (1.5, 3.0), "body": (4.0, 6.0)}   # hook: quick, but not a flicker
FACE_SHARE = (0.40, 0.65)   # channel-system: presenter on screen ≈57% (46–71%)
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
    grade: str | None = None        # colour look for this beat's footage (overrides the plan's)
    source: str | None = None       # footage: "archive" = old films first (else Commons first)
    title: str | None = None        # cinematic_title / halftone_cutout: the giant word; desk: the stamp
    look: str | None = None         # ai_image / ai_video: a look from ai.AI_LOOKS instead of the world's

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
    grade: str | None = None  # colour look for the whole episode (default: the style's)
    music: list[dict] = field(default_factory=list)  # [{"t": final-timeline s, "prompt": ..., "mood": ...}]
    end_screen: float = 20.0  # seconds of YouTube end screen after the last beat (0 = none; YouTube allows 5–20)

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
                    chapters=d.get("chapters", []), ai_budget=d.get("ai_budget", 0.0),
                    grade=d.get("grade"), music=d.get("music", []), end_screen=d.get("end_screen", 20.0))


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
            if b.kind not in MARKABLE or s.get("type") not in STICKERS:
                errs.append(f"beat {i}: الملصقات على {', '.join(MARKABLE)} بس، ونوعها من {', '.join(STICKERS)}")
                break
        if b.grade and b.grade not in LOOKS:
            errs.append(f"beat {i}: grade لازم من {', '.join(LOOKS)}")
        if b.transition and b.transition not in TRANSITIONS:
            errs.append(f"beat {i}: transition لازم من {', '.join(TRANSITIONS)}")
        if b.look:
            from .ai import AI_LOOKS
            if b.kind not in AI_KINDS or b.look not in AI_LOOKS:
                errs.append(f"beat {i}: look على ai_image و ai_video بس، ومن {', '.join(AI_LOOKS)}")
        if b.treatment in ("cinematic_title", "halftone_cutout") and not (b.title or b.caption):
            errs.append(f"beat {i}: {b.treatment} يحتاج title (الكلمة أو الرقم الضخم)")
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
        if b.kind == "footage" and not (b.query and b.caption):
            errs.append(f"beat {i}: footage لازم بيه query (إنگليزي) و caption (عربي)")
        if b.kind == "image" and not (b.query and b.caption):
            errs.append(f"beat {i}: صورة لازم بيها query (إنگليزي) و caption (عربي)")
        if b.kind == "graphic" and (not b.graphic or b.graphic.get("type") not in GRAPHIC_TYPES):
            errs.append(f"beat {i}: گرافيك لازم type من {', '.join(GRAPHIC_TYPES)}")
        elif b.kind == "graphic" and b.graphic["type"] == "article" and not (
                b.graphic.get("url", "").startswith("http") and b.graphic.get("quote") and b.graphic.get("title")):
            errs.append(f"beat {i}: article لازم بيه url، و quote (الجملة بلغة المقالة)، و title (عربي، بديل إذا الموقع ما فتح)")
        elif b.kind == "graphic" and b.graphic["type"] == "custom" and not (
                b.graphic.get("scene") and (CUSTOM_DIR / f"{b.graphic['scene']}.tsx").exists()):
            errs.append(f"beat {i}: المشهد المخصص '{b.graphic.get('scene')}' مو موجود بـ editor/remotion/src/custom")
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

    for k, sh in enumerate(plan.shorts, 1):
        a, z = float(sh.get("from", -1)), float(sh.get("to", -1))
        if not (0 <= a < z <= total + TOL) or not 15 <= z - a <= 60 or not sh.get("title"):
            errs.append(f"short {k}: لازم from و to داخل الحلقة (15–60 ثانية) و title (هوك عربي قصير)")
    if plan.end_screen and not 5 <= plan.end_screen <= 20:
        errs.append("end_screen: يوتيوب يقبل شاشة النهاية بين 5 و 20 ثانية (أو 0 بدونها)")
    if plan.grade and plan.grade not in LOOKS:
        errs.append(f"grade: لازم من {', '.join(LOOKS)}")
    for k, m in enumerate(plan.music):
        if not (0 <= m.get("t", -1) < total and m.get("prompt")):
            errs.append(f"music {k}: لازم t داخل الفيديو و prompt")
        elif k and m["t"] - plan.music[k - 1]["t"] < 20:
            errs.append(f"music {k}: لازم يبعد 20 ثانية أو أكثر عن الي قبله")
    if plan.music and plan.music[0]["t"] != 0:
        errs.append("music 0: أول موسيقى لازم تبدي من 0")
    if ai_spent > plan.ai_budget + 1e-9:
        errs.append(f"ai: صرفنا {ai_spent:g} رصيد، والميزانية {plan.ai_budget:g}")

    body = [b for b in beats if b.zone == "body" and b.kind in KINDS]
    body_time = sum(b.duration for b in body)
    if body_time > 0:
        share = sum(b.duration for b in body if b.kind in FACE_KINDS) / body_time
        if not (FACE_SHARE[0] <= share <= FACE_SHARE[1]):
            errs.append(f"beat {beats.index(body[0])}: الوجه {share:.0%} من الجسم، لازم بين 40% و 65%")
    return errs
