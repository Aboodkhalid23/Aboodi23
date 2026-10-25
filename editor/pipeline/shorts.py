"""Shorts: 9:16 clips cut from the finished episode. Face shots are cropped around the face; graphics sit
in the middle over a blurred copy of themselves; the hook title stays on top. No speech captions
(owner's rule)."""
import subprocess
from pathlib import Path

from .channel import load_channel
from .graphics import RenderJob, _style_props, ensure_bundle, render_batch
from .media import MediaError, probe, run_ffmpeg
from .paths import Episode
from .plan import FACE_KINDS, load_plan
from .styles import load_style

W, H = 1080, 1920
LIMITS = (15.0, 90.0)     # TikTok and Reels take more than a minute; the main YouTube short stays under one
MAIN_MAX = 59.0
REELS_PACK = 6            # owner, 2026-10-25: one main short (YouTube, < 1 min) + 5 clips (TikTok, Instagram)


def transcript_lines(ep: Episode, gap: float = 0.6) -> list[str]:
    """The episode's speech as lines with their times on the FINAL timeline ("[12.3–18.9] words"), for picking reels."""
    from .transcribe import load_words
    plan = load_plan(ep.plan)
    words = load_words(ep.clean_words) if ep.clean_words.exists() else []
    off, lines, cur = plan.teaser_total, [], []
    for w in words:
        if cur and (w.start - cur[-1].end > gap or len(cur) > 28):
            lines.append(cur)
            cur = []
        cur.append(w)
    if cur:
        lines.append(cur)
    return [f"[{ln[0].start + off:.1f}–{ln[-1].end + off:.1f}] " + " ".join(x.text for x in ln) for ln in lines]


def _master(ep: Episode) -> Path:
    """The finished episode without burned captions or the opening (shorts get their own tall captions)."""
    clean = ep.work / "post" / "master_clean.mp4"
    if clean.exists() and ep.final.exists() and clean.stat().st_mtime >= ep.final.stat().st_mtime - 3600:
        return clean
    return ep.final if ep.final.exists() else ep.edit / "preview.mp4"


def _caption_filter(ep: Episode, start: float, end: float, work: Path) -> str:
    """Reels-style captions for the tall clip when he turned captions on (empty otherwise)."""
    from .options import FONTS, captions_ass, load_options
    from .transcribe import load_words
    opts = load_options(ep)["captions"]
    if not opts["on"] or not ep.clean_words.exists():
        return ""
    off = load_plan(ep.plan).teaser_total
    words = [(w.text, w.start, w.end) for w in load_words(ep.clean_words) if start - off <= w.start and w.end <= end - off]
    ass = work / "captions.ass"
    ass.write_text(captions_ass(words, off - start, W, H, opts["style"], min(opts["words"], 3), until=end - start), encoding="utf-8")
    return f",ass=filename='{ass}':fontsdir='{FONTS}':shaping=complex"


def _pieces(beats, start: float, end: float):
    """(from, to, is_face) pieces of the final timeline between start and end."""
    out = []
    for b in beats:
        a, z = max(start, b.start), min(end, b.end)
        if z - a > 0.02:
            out.append((a, z, b.kind in FACE_KINDS and b.kind not in ("face_fx", "face_cutout", "face_framed")))
    return out


def _face_x(ep: Episode, canvas_w: int, canvas_h: int) -> float:
    """Face centre across the finished frame (0–1); the middle if unknown."""
    from .face import face_info
    f = face_info(ep)
    if not f:
        return 0.5
    info = probe(ep.clean_video)
    scale = min(canvas_w / info.width, canvas_h / info.height)
    w = info.width * scale / canvas_w
    return (1 - w) / 2 + f["cx"] * w


def make_short(ep: Episode, n: int, start: float, end: float, title: str, fps: int) -> Path:
    plan = load_plan(ep.plan)
    final = _master(ep)
    info = probe(final)
    work = ep.work / f"short_{n}"
    work.mkdir(parents=True, exist_ok=True)
    fx = _face_x(ep, info.width, info.height)
    cw = round(info.height * 9 / 16 / 2) * 2                       # 9:16 crop width on the episode frame
    cx = min(max(round(fx * info.width - cw / 2), 0), info.width - cw)
    crop_face = f"crop={cw}:{info.height}:{cx}:0,scale={W}:{H}:flags=lanczos"
    middle = (f"split=2[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"boxblur=20:2,eq=brightness=-0.12[bg];[b]scale={W}:-2[fg];[bg][fg]overlay=0:(H-h)/2")
    segs = []
    for k, (a, z, face) in enumerate(_pieces(plan.beats, start, end)):
        seg = work / f"seg_{k}.mp4"
        frames = round(z * fps) - round(a * fps)
        if frames < 1:
            continue
        run_ffmpeg(["-ss", f"{a:.3f}", "-i", str(final), "-frames:v", str(frames), "-filter_complex",
                    f"[0:v]{crop_face if face else middle},setsar=1,fps={fps}", "-an", "-c:v", "libx264", "-crf", "13",
                    "-preset", "medium", "-pix_fmt", "yuv420p", "-video_track_timescale", "15360", str(seg)])
        segs.append(seg)
    if not segs:
        raise MediaError(f"الشورت {n}: ما بيه مشاهد بين {start} و {end}")
    listing = work / "concat.txt"
    listing.write_text("".join(f"file '{s.resolve()}'\n" for s in segs), encoding="utf-8")
    style = load_style(plan.style["primary"])
    bundle = ensure_bundle(ep.work / "bundle")
    overlay = RenderJob("short-title", {"style": _style_props(style), "durationSec": 1, "title": title,
                                        "handle": load_channel().get("handle", "")}, work / "title.png", 1.0, still=True)
    render_batch([overlay], bundle)
    out = ep.edit / "shorts" / f"{n:02d}-{_safe_name(title) or 'ريل'}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    for old in out.parent.glob(f"{n:02d}-*.mp4"):
        old.unlink()
    dur = end - start
    caps = _caption_filter(ep, start, end, work)
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(overlay.out), "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
                "-i", str(final), "-filter_complex",
                f"[0:v][1:v]overlay=0:0{caps},format=yuv420p[v];[2:a]afade=t=in:d=0.15,afade=t=out:st={max(0, dur - 0.4):.3f}:d=0.4[a]",
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-c:a", "aac", "-b:a", "320k",
                "-t", f"{dur:.3f}", "-movflags", "+faststart", str(out)])
    return out


def _safe_name(title: str) -> str:
    import re
    return re.sub(r"[^\w\s\-]", "", title or "").strip().replace(" ", "-")[:40]


def make_shorts(ep: Episode) -> list[Path]:
    plan = load_plan(ep.plan)
    final = _master(ep)
    if not final.exists():
        raise MediaError("الشورتس تنقص من الحلقة الجاهزة: سوّ render أول")
    fps = round(probe(final).fps)
    return [make_short(ep, n, float(s["from"]), float(s["to"]), s.get("title", ""), fps)
            for n, s in enumerate(plan.shorts, 1)]
