"""AI scenes (ai_image / ai_video beats). Python can't reach Higgsfield — Claude can, through its tools.
So: `ai-jobs` lists what to generate → Claude generates and logs the cost → `ai-fetch` downloads the
result into the episode → compose places it."""
import json
from dataclasses import dataclass, asdict
from pathlib import Path

import requests

from .media import MediaError, probe
from .paths import Episode
from .plan import AI_KINDS, load_plan
from .styles import load_style

IMAGE_MODEL, VIDEO_MODEL = "nano_banana", "veo3_1_lite"   # good and cheap: ≈1 credit per image, 6 per 4 s clip
# Looks from the owner's references (style update 1, style د and و): replace the world's suffix for one beat.
AI_LOOKS = {
    "cinematic": ("cinematic film still, dark moody room lit by warm practical lamps and window light, shallow depth of "
                  "field, 35mm, rich shadows, realistic, leave empty space behind the subject for a big title"),
    "caricature_3d": ("3D caricature render, big expressive head, soft clay-like materials, playful, bright studio light, "
                      "clean background with soft clouds, Pixar-like but editorial"),
    "pencil": "detailed graphite pencil sketch on cream paper, hatching, visible pencil strokes, documentary illustration",
    "blueprint": "technical blueprint drawing, white precise lines on deep blue paper, labels and measurements, engineering plan",
}
EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "video/mp4": ".mp4",
       "video/quicktime": ".mov", "video/webm": ".webm"}


@dataclass
class AiJob:
    beat: int
    kind: str
    prompt: str        # full prompt sent to the model (beat prompt + style suffix)
    model: str
    aspect_ratio: str
    duration: int      # seconds of video to ask for (0 for images)
    asset: str         # where ai-fetch saves it
    done: bool


def ledger_file(ep: Episode) -> Path:
    return ep.edit / "ai_ledger.json"


def load_ledger(ep: Episode) -> list[dict]:
    f = ledger_file(ep)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def spent(ep: Episode) -> float:
    return round(sum(float(e.get("credits", 0)) for e in load_ledger(ep)), 3)


def log_spend(ep: Episode, beat: int, model: str, credits: float, job_id: str = "") -> float:
    entries = load_ledger(ep) + [{"beat": beat, "model": model, "credits": credits, "job_id": job_id}]
    ledger_file(ep).write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
    return spent(ep)


def _existing(ep: Episode, i: int) -> Path | None:
    return next(iter(sorted(ep.assets.glob(f"ai_{i}.*"))), None)


def ai_jobs(ep: Episode) -> list[AiJob]:
    plan = load_plan(ep.plan)
    suffix = load_style(plan.style["primary"]).ai_suffix
    jobs = []
    for i, b in enumerate(plan.beats):
        if b.kind not in AI_KINDS:
            continue
        video = b.kind == "ai_video"
        have = _existing(ep, i)
        jobs.append(AiJob(i, b.kind, f"{b.prompt.rstrip('. ')}. {AI_LOOKS.get(b.look or '', suffix)}", VIDEO_MODEL if video else IMAGE_MODEL,
                          "16:9", (4 if b.duration <= 4.5 else 6) if video else 0,
                          str(have or ep.assets / f"ai_{i}.{'mp4' if video else 'png'}"), have is not None))
    (ep.work / "ai_jobs.json").write_text(json.dumps([asdict(j) for j in jobs], ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    return jobs


def ai_fetch(ep: Episode, beat: int, url: str, session=None) -> Path:
    """Download a generated result for `beat` and make sure it really is a picture / video."""
    session = session or requests.Session()
    try:
        resp = session.get(url, timeout=180)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise MediaError(f"ما گدرت أنزّل ناتج الذكاء الاصطناعي: {exc}") from exc
    ctype = resp.headers.get("Content-Type", "").split(";")[0].strip()
    ext = EXT.get(ctype) or Path(url.split("?")[0]).suffix.lower() or ".bin"
    for old in ep.assets.glob(f"ai_{beat}.*"):
        old.unlink()
    out = ep.assets / f"ai_{beat}{ext}"
    out.write_bytes(resp.content)
    try:
        probe(out)
    except MediaError:
        out.unlink()
        raise MediaError(f"الملف الي نزل مو صورة ولا فيديو ({ctype or 'نوع غير معروف'})")
    return out
