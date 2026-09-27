"""Stage 6: build final.mp4 — per-beat video clips + one continuous audio track."""
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from .graphics import ensure_bundle, render_face_frame_bg, render_graphic
from .media import MediaError, run_ffmpeg
from .paths import Episode
from .plan import Beat, EditPlan, load_plan
from .styles import Style, load_style

FPS = 30
W, H = 1920, 1080
ZOOM = 0.15          # face zoom: 1.0 <-> 1.15
FOCUS_Y = 0.4        # keep the face (upper part of frame) in view while zooming
FRAME_BOX = (1152, 648, 384, 216)  # face_framed: w, h, x, y (matches FaceFrame.tsx)
ENCODE = ["-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
          "-r", str(FPS), "-video_track_timescale", "15360"]
FIT = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
       f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1")


def source_ranges(start: float, end: float, teaser: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Map a final-timeline span onto spans of the cleaned video (teaser plays first)."""
    out, t = [], 0.0
    for s, e in teaser:
        a, b = max(start, t), min(end, t + (e - s))
        if a < b:
            out.append((s + a - t, s + b - t))
        t += e - s
    a = max(start, t)
    if a < end:
        out.append((a - t, end - t))
    return out


def _face_filter(kind: str, dur: float) -> str:
    if kind in ("face_zoom_in", "face_zoom_out"):
        z0, z1 = (1.0, 1.0 + ZOOM) if kind == "face_zoom_in" else (1.0 + ZOOM, 1.0)
        z = f"({z0}+({z1}-{z0})*t/{dur:.3f})"
        return (f"{FIT},scale=w='trunc({W}*{z}/2)*2':h=-2:eval=frame,"
                f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*{FOCUS_Y}")
    if kind == "face_framed":
        w, h, _, _ = FRAME_BOX
        return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
    return FIT


def _face_clip(ep: Episode, beat: Beat, frames: int, teaser, out: Path, frame_bg: Path | None) -> None:
    ranges = source_ranges(beat.start, beat.end, teaser)
    if not ranges:
        raise MediaError(f"الـ beat ({beat.start}–{beat.end}) برا الفيديو المنظف")
    args, labels = [], ""
    for i, (s, e) in enumerate(ranges):
        args += ["-ss", f"{s:.3f}", "-t", f"{e - s + 0.1:.3f}", "-i", str(ep.clean_video)]
        labels += f"[{i}:v]"
    joined = f"{labels}concat=n={len(ranges)}:v=1:a=0,fps={FPS}" if len(ranges) > 1 else f"[0:v]fps={FPS}"
    graph = f"{joined},setpts=PTS-STARTPTS,{_face_filter(beat.kind, beat.duration)},tpad=stop_mode=clone:stop_duration=1"
    if beat.kind == "face_framed":
        _, _, x, y = FRAME_BOX
        args += ["-loop", "1", "-i", str(frame_bg)]
        graph += f"[face];[{len(ranges)}:v]scale={W}:{H},setsar=1[bg];[bg][face]overlay={x}:{y}"
    run_ffmpeg([*args, "-filter_complex", graph, "-frames:v", str(frames), "-an", *ENCODE, str(out)])


def _graphic_clip(ep: Episode, beat: Beat, i: int, style: Style, frames: int, out: Path, bundle: Path) -> None:
    raw = render_graphic(beat, style, ep.work / f"graphic_{i}.mp4", public_dir=ep.assets, index=i, bundle=bundle)
    run_ffmpeg(["-i", str(raw), "-vf", f"{FIT},fps={FPS},tpad=stop_mode=clone:stop_duration=1",
                "-frames:v", str(frames), "-an", *ENCODE, str(out)])


def _build_audio(ep: Episode, teaser, duration: float, out: Path) -> None:
    args, labels = [], ""
    parts = [*teaser]
    for i, (s, e) in enumerate(parts):
        args += ["-ss", f"{s:.3f}", "-t", f"{e - s:.3f}", "-i", str(ep.clean_video)]
        labels += f"[{i}:a]"
    args += ["-i", str(ep.clean_video)]
    labels += f"[{len(parts)}:a]"
    graph = (f"{labels}concat=n={len(parts) + 1}:v=0:a=1,"
             f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,"
             f"apad,atrim=0:{duration:.4f}")
    run_ffmpeg([*args, "-filter_complex", graph, "-vn", "-c:a", "aac", "-b:a", "192k", str(out)])


def compose(ep: Episode) -> Path:
    plan: EditPlan = load_plan(ep.plan)
    style = load_style(plan.style["primary"])
    teaser = [tuple(t) for t in plan.teaser]
    bundle = ensure_bundle(ep.work / "bundle")
    frame_bg = None
    if any(b.kind == "face_framed" for b in plan.beats):
        frame_bg = ep.work / f"face_frame_{style.name}.png"
        if not frame_bg.exists():
            render_face_frame_bg(style, frame_bg, bundle)

    src_stamp = str(ep.clean_video.stat().st_mtime)
    clips = []
    for i, b in enumerate(plan.beats):
        # Frame-grid boundaries: the sum of clip lengths equals the timeline exactly (no drift).
        frames = round(b.end * FPS) - round(b.start * FPS)
        out = ep.work / f"beat_{i}.mp4"
        stamp = ep.work / f"beat_{i}.hash"
        key = hashlib.sha1(json.dumps([asdict(b), style.name, teaser, src_stamp, frames],
                                      ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if not (out.exists() and stamp.exists() and stamp.read_text() == key):
            if b.kind in ("image", "graphic"):
                _graphic_clip(ep, b, i, style, frames, out, bundle)
            else:
                _face_clip(ep, b, frames, teaser, out, frame_bg)
            stamp.write_text(key)
        clips.append(out)

    listing = ep.work / "concat.txt"
    listing.write_text("".join(f"file '{c.resolve()}'\n" for c in clips), encoding="utf-8")
    video = ep.work / "video.mp4"
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(video)])
    audio = ep.work / "audio.m4a"
    total_frames = round(plan.beats[-1].end * FPS) - round(plan.beats[0].start * FPS)
    _build_audio(ep, teaser, total_frames / FPS, audio)
    run_ffmpeg(["-i", str(video), "-i", str(audio), "-map", "0:v", "-map", "1:a",
                "-c", "copy", "-movflags", "+faststart", str(ep.final)])
    return ep.final
