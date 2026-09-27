"""Stage 6: build final.mp4 (or preview.mp4) — per-beat video clips + one continuous audio track."""
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .fmt import load_format
from .graphics import ensure_bundle, render_face_frame_bg, render_graphic
from .media import MediaError, run_ffmpeg
from .paths import Episode
from .plan import Beat, load_plan
from .styles import Style, load_style

ZOOM = 0.15          # face zoom: 1.0 <-> 1.15
FOCUS_Y = 0.4        # keep the face (upper part of frame) in view while zooming
FRAME = 0.6          # face_framed: face box is 60% of the canvas, centred (matches FaceFrame.tsx)


@dataclass
class Canvas:
    width: int
    height: int
    fps: int
    work: Path
    encode: list[str]

    @property
    def fit(self) -> str:
        w, h = self.width, self.height
        return f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1"

    @property
    def frame_box(self) -> tuple[int, int, int, int]:
        w, h = round(self.width * FRAME / 2) * 2, round(self.height * FRAME / 2) * 2
        return w, h, (self.width - w) // 2, (self.height - h) // 2

    @property
    def remotion_scale(self) -> float:
        """Remotion needs whole-pixel output: 1080p compositions scale by 0.5, 1, 4/3 or 2."""
        s = self.width / 1920
        return s if (1080 * s).is_integer() else 0.5


def make_canvas(ep: Episode, preview: bool) -> Canvas:
    fmt = load_format(ep)
    common = ["-pix_fmt", "yuv420p", "-r", str(fmt.fps), "-video_track_timescale", "15360"]
    if preview:
        return Canvas(640, 360, fmt.fps, ep.work / "preview",
                      ["-c:v", "libx264", "-crf", "28", "-preset", "ultrafast", *common])
    # The beat clips ARE the final encode: one high-quality lossy generation, then stream copy.
    return Canvas(fmt.width, fmt.height, fmt.fps, ep.work,
                  ["-c:v", "libx264", "-crf", "16", "-preset", "medium", *common])


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


def _face_filter(kind: str, dur: float, cv: Canvas) -> str:
    W, H = cv.width, cv.height
    if kind in ("face_zoom_in", "face_zoom_out"):
        z0, z1 = (1.0, 1.0 + ZOOM) if kind == "face_zoom_in" else (1.0 + ZOOM, 1.0)
        z = f"({z0}+({z1}-{z0})*t/{dur:.3f})"
        return (f"{cv.fit},scale=w='trunc({W}*{z}/2)*2':h=-2:eval=frame,"
                f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*{FOCUS_Y}")
    if kind == "face_framed":
        w, h, _, _ = cv.frame_box
        return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
    return cv.fit


def _face_clip(ep: Episode, beat: Beat, frames: int, teaser, out: Path, frame_bg: Path | None,
               cv: Canvas | None = None) -> None:
    ranges = source_ranges(beat.start, beat.end, teaser)
    if not ranges:
        raise MediaError(f"الـ beat ({beat.start}–{beat.end}) برا الفيديو المنظف")
    args, labels = [], ""
    for i, (s, e) in enumerate(ranges):
        args += ["-ss", f"{s:.3f}", "-t", f"{e - s + 0.1:.3f}", "-i", str(ep.clean_video)]
        labels += f"[{i}:v]"
    joined = (f"{labels}concat=n={len(ranges)}:v=1:a=0,fps={cv.fps}" if len(ranges) > 1
              else f"[0:v]fps={cv.fps}")
    graph = (f"{joined},setpts=PTS-STARTPTS,{_face_filter(beat.kind, beat.duration, cv)},"
             "tpad=stop_mode=clone:stop_duration=1")
    if beat.kind == "face_framed":
        _, _, x, y = cv.frame_box
        args += ["-loop", "1", "-i", str(frame_bg)]
        graph += (f"[face];[{len(ranges)}:v]scale={cv.width}:{cv.height},setsar=1[bg];"
                  f"[bg][face]overlay={x}:{y}")
    run_ffmpeg([*args, "-filter_complex", graph, "-frames:v", str(frames), "-an", *cv.encode, str(out)])


def _graphic_clip(ep: Episode, beat: Beat, i: int, style: Style, frames: int, out: Path, bundle: Path,
                  cv: Canvas) -> None:
    raw = render_graphic(beat, style, cv.work / f"graphic_{i}.mp4", public_dir=ep.assets, index=i,
                         bundle=bundle, scale=cv.remotion_scale)
    run_ffmpeg(["-i", str(raw), "-vf", f"{cv.fit},fps={cv.fps},tpad=stop_mode=clone:stop_duration=1",
                "-frames:v", str(frames), "-an", *cv.encode, str(out)])


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


def compose(ep: Episode, preview: bool = False) -> Path:
    plan = load_plan(ep.plan)
    style = load_style(plan.style["primary"])
    teaser = [tuple(t) for t in plan.teaser]
    cv = make_canvas(ep, preview)
    cv.work.mkdir(parents=True, exist_ok=True)
    bundle = ensure_bundle(ep.work / "bundle")
    frame_bg = None
    if any(b.kind == "face_framed" for b in plan.beats):
        frame_bg = cv.work / f"face_frame_{style.name}.png"
        if not frame_bg.exists():
            render_face_frame_bg(style, frame_bg, bundle, scale=cv.remotion_scale)

    src_stamp = str(ep.clean_video.stat().st_mtime)
    clips = []
    for i, b in enumerate(plan.beats):
        # Frame-grid boundaries: the sum of clip lengths equals the timeline exactly (no drift).
        frames = round(b.end * cv.fps) - round(b.start * cv.fps)
        out = cv.work / f"beat_{i}.mp4"
        stamp = cv.work / f"beat_{i}.hash"
        key = hashlib.sha1(json.dumps([asdict(b), style.name, teaser, src_stamp, frames, cv.encode, cv.width],
                                      ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if not (out.exists() and stamp.exists() and stamp.read_text() == key):
            if b.kind in ("image", "graphic"):
                _graphic_clip(ep, b, i, style, frames, out, bundle, cv)
            else:
                _face_clip(ep, b, frames, teaser, out, frame_bg, cv)
            stamp.write_text(key)
        clips.append(out)

    listing = cv.work / "concat.txt"
    listing.write_text("".join(f"file '{c.resolve()}'\n" for c in clips), encoding="utf-8")
    audio = cv.work / "audio.m4a"
    total_frames = round(plan.beats[-1].end * cv.fps) - round(plan.beats[0].start * cv.fps)
    _build_audio(ep, teaser, total_frames / cv.fps, audio)
    final = ep.edit / "preview.mp4" if preview else ep.final
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(audio), "-map", "0:v", "-map", "1:a",
                "-c", "copy", "-movflags", "+faststart", str(final)])
    return final
