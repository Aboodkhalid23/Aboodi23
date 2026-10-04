"""Stage 6: build final.mp4 (or preview.mp4) — per-beat video clips + one continuous audio track."""
import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .channel import channel_avatar, load_channel
from .entities import entity_image, load_entities
from .fmt import load_format
from .grade import analyse, grade_filter
from .graphics import _source_hash, ensure_bundle, face_fx_job, graphic_job, render_batch, render_face_frame_bg
from .media import MediaError, run_ffmpeg
from .music import AUDIO_EXT, bed_filter, music_asset, segments
from .paths import Episode
from .plan import Beat, load_plan
from .sfx import beat_cues, sfx_path
from .styles import Style, load_style

ZOOM = 0.15          # face zoom: 1.0 <-> 1.15
FOCUS_Y = 0.4        # keep the face (upper part of frame) in view while zooming
FRAME = 0.6          # face_framed: face box is 60% of the canvas, centred (matches FaceFrame.tsx)
PUNCH = 1.2          # face_punch: the YouTuber "cut-in" zoom, held still
MOVE = 0.8           # zooms move for this long (ease-out), then hold — never a linear crawl
TRANS = 0.25         # entry transitions last this long
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")
VIDEO_EXT = (".mp4", ".mov", ".webm")

# Sounds inside special beats (seconds from the beat start); must match FaceFx.tsx / EntityCard.tsx.
FX_CUES = {"fx:subscribe": [(0.0, "whoosh"), (1.6, "click"), (1.75, "ding")],
           "fx:tv": [(0.0, "whoosh"), (0.5, "switch")],
           "entity": [(0.0, "paper"), (0.45, "pop")]}
SFX_GAIN = 0.4       # effects sit ~8 dB under the voice
MUSIC_LUFS = -24     # music bed between sentences; the voice ducks it further


@dataclass
class Canvas:
    width: int
    height: int
    fps: int
    work: Path
    encode: list[str]
    face: tuple[float, float] | None = None   # face centre on the canvas (fractions), for the zooms
    src_aspect: float | None = None           # footage width/height; None = unknown (use the safe path)

    @property
    def fit(self) -> str:
        w, h = self.width, self.height
        return f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1"

    @property
    def face_fit(self) -> str:
        """Fit the face video; if it is narrower than the canvas (vertical phone video), fill the
        sides with a blurred, zoomed copy of the same frame instead of black bars."""
        w, h = self.width, self.height
        if self.src_aspect and abs(self.src_aspect - w / h) < 0.01:   # footage fills the canvas: no blur work
            return f"scale={w}:{h},setsar=1"
        # blur a quarter-size copy and scale it back up: same look, ~16x less work than blurring at full size
        bw, bh = w // 4 // 2 * 2, h // 4 // 2 * 2
        return (f"split=2[fg][bg];[bg]scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},"
                f"boxblur=luma_radius=10:luma_power=2,eq=brightness=-0.08,scale={w}:{h}[bgb];"
                f"[fg]scale={w}:{h}:force_original_aspect_ratio=decrease[fgs];"
                f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1")

    @property
    def frame_box(self) -> tuple[int, int, int, int]:
        w, h = round(self.width * FRAME / 2) * 2, round(self.height * FRAME / 2) * 2
        return w, h, (self.width - w) // 2, (self.height - h) // 2

    @property
    def remotion_scale(self) -> float:
        """Remotion needs whole-pixel output: 1080p compositions scale by 0.5, 1, 4/3 or 2."""
        s = self.width / 1920
        return s if (1080 * s).is_integer() else 0.5


INTERMEDIATE = ["-c:v", "libx264", "-crf", "12", "-preset", "veryfast", "-pix_fmt", "yuv420p"]


def make_canvas(ep: Episode, preview: bool) -> Canvas:
    fmt = load_format(ep)
    common = ["-pix_fmt", "yuv420p", "-r", str(fmt.fps), "-video_track_timescale", "15360"]
    if preview:
        # 720p: sharp enough for the owner to judge on a phone, ~2x faster than the final
        return Canvas(1280, 720, fmt.fps, ep.work / "preview",
                      ["-c:v", "libx264", "-crf", "23", "-preset", "veryfast", *common])
    # The beat clips ARE the final encode: one high-quality lossy generation, then stream copy.
    return Canvas(fmt.width, fmt.height, fmt.fps, ep.work,
                  ["-c:v", "libx264", "-crf", "16", "-preset", "fast", *common])


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


def _ease_out(t0: str = "t") -> str:
    """0→1 over MOVE seconds, cubic ease-out, then 1 forever (ffmpeg expression)."""
    return f"(1-pow(1-min({t0}/{MOVE},1),3))"


def _zoom_crop(z: str, cv: Canvas, focus_y: float = FOCUS_Y) -> str:
    """Zoom by `z` and crop back to the canvas. With a known face (cv.face) the crop follows the face:
    centred across, and placed a little above the middle (headroom), never past the frame edge."""
    W, H = cv.width, cv.height
    if cv.face and focus_y == FOCUS_Y:
        fx, fy = cv.face
        x, y = f"min(max(iw*{fx}-{W}/2\\,0)\\,iw-{W})", f"min(max(ih*{fy}-{H}*0.42\\,0)\\,ih-{H})"
    else:
        x, y = f"(iw-{W})/2", f"(ih-{H})*{focus_y}"
    return f"scale=w='trunc({W}*{z}/2)*2':h=-2:eval=frame,crop={W}:{H}:{x}:{y}"


def _face_filter(kind: str, dur: float, cv: Canvas) -> str:
    if kind in ("face_zoom_in", "face_zoom_out"):
        z0, z1 = (1.0, 1.0 + ZOOM) if kind == "face_zoom_in" else (1.0 + ZOOM, 1.0)
        return f"{cv.face_fit},{_zoom_crop(f'({z0}+({z1}-{z0})*{_ease_out()})', cv)}"
    if kind == "face_punch":
        return f"{cv.face_fit},{_zoom_crop(str(PUNCH), cv)}"
    if kind == "face_framed":
        w, h, _, _ = cv.frame_box
        return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
    return cv.face_fit


def _transition_filter(name: str | None, cv: Canvas) -> str:
    """Entry effect on the first TRANS seconds of a clip (it only needs the incoming clip, so clips
    stay independent and the final concat stays a stream copy)."""
    if not name:
        return ""
    on = f"enable='lt(t,{TRANS})'"
    punch = lambda amount: _zoom_crop(f"(1+{amount}*pow(1-min(t/{TRANS},1),3))", cv, 0.5)
    return {
        "flash": f",fade=t=in:st=0:d={TRANS}:color=white",
        "zoom": f",{punch(0.25)}",
        "whip": f",{punch(0.08)},gblur=sigma=45:sigmaV=0.5:{on}",
        "glitch": f",rgbashift=rh=-18:bh=18:gv=6:{on},noise=alls=40:allf=t:{on}",
    }[name]


def _face_clip(ep: Episode, beat: Beat, frames: int, teaser, out: Path, frame_bg: Path | None,
               cv: Canvas | None = None, encode: list[str] | None = None, grade: str = "", plain: bool = False) -> None:
    """`plain`: fit with black bars instead of the blurred fill (for the cut-out, which must see only him)."""
    ranges = source_ranges(beat.start, beat.end, teaser)
    if not ranges:
        raise MediaError(f"الـ beat ({beat.start}–{beat.end}) برا الفيديو المنظف")
    args, labels = [], ""
    for i, (s, e) in enumerate(ranges):
        args += ["-ss", f"{s:.3f}", "-t", f"{e - s + 0.1:.3f}", "-i", str(ep.clean_video)]
        labels += f"[{i}:v]"
    joined = (f"{labels}concat=n={len(ranges)}:v=1:a=0,fps={cv.fps}" if len(ranges) > 1
              else f"[0:v]fps={cv.fps}")
    fit = cv.fit if plain else _face_filter(beat.kind, beat.duration, cv)
    graph = f"{joined},setpts=PTS-STARTPTS,{fit}{grade}"
    if beat.kind == "face_framed":
        _, _, x, y = cv.frame_box
        args += ["-loop", "1", "-i", str(frame_bg)]
        graph += (f",tpad=stop_mode=clone:stop_duration=1[face];[{len(ranges)}:v]scale={cv.width}:{cv.height},"
                  f"setsar=1[bg];[bg][face]overlay={x}:{y}:shortest=1")
    graph += f"{_transition_filter(beat.transition, cv)},tpad=stop_mode=clone:stop_duration=1"
    run_ffmpeg([*args, "-filter_complex", graph, "-frames:v", str(frames), "-an", *(encode or cv.encode), str(out)])


def _finish(raw: Path, frames: int, out: Path, cv: Canvas, transition: str | None, cover: bool = False,
            loop: bool = False, grade: str = "") -> None:
    """Bring a rendered/generated clip to the canvas: size, fps, exact frame count, entry effect."""
    w, h = cv.width, cv.height
    fit = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1" if cover else cv.fit)
    run_ffmpeg([*(["-stream_loop", "-1"] if loop else []), "-i", str(raw), "-vf",
                f"{fit},fps={cv.fps},setpts=PTS-STARTPTS{grade}{_transition_filter(transition, cv)},"
                "tpad=stop_mode=clone:stop_duration=1",
                "-frames:v", str(frames), "-an", *cv.encode, str(out)])


def _asset(folder: Path, stem: str, exts: tuple[str, ...]) -> Path | None:
    return next((p for p in sorted(folder.glob(f"{stem}.*")) if p.suffix.lower() in exts), None)


def _graphic_job(ep: Episode, beat: Beat, i: int, style: Style, bundle: Path, cv: Canvas,
                 src: Path | None = None, extra_props: dict | None = None):
    return graphic_job(beat, style, cv.work / f"graphic_{i}.mp4", public_dir=ep.assets, index=i,
                       bundle=bundle, scale=cv.remotion_scale, src=src, extra_props=extra_props)


def _fallback_text(beat: Beat) -> Beat:
    return replace(beat, kind="graphic", graphic={"type": "text", "text": beat.caption or beat.prompt or ""})


VOICE_CHAIN = ("highpass=f=80,afftdn=nr=8:nf=-50,"
               "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=1.5,"
               "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000")


def _build_audio(ep: Episode, teaser, duration: float, out: Path,
                 cues: list[tuple[float, str]] = (), music: list[tuple[int, Path, float, float]] = ()) -> None:
    """Voice (cleaned, -14 LUFS) + effects at their cue times + music segments ducked under the voice.
    `music`: (cue, file, start, end) on the final timeline."""
    args, labels = [], ""
    for i, (s, e) in enumerate(teaser):
        args += ["-ss", f"{s:.3f}", "-t", f"{e - s:.3f}", "-i", str(ep.clean_video)]
        labels += f"[{i}:a]"
    args += ["-i", str(ep.clean_video)]
    labels += f"[{len(teaser)}:a]"
    n = len(teaser) + 1
    graph = (f"{labels}concat=n={n}:v=0:a=1,{VOICE_CHAIN},aformat=channel_layouts=stereo,"
             f"apad,atrim=0:{duration:.4f}")
    mix = []
    if music:
        margs, mgraph = bed_filter(list(music), n, MUSIC_LUFS)
        args += margs
        n += len(margs) // 2
        graph += (f",asplit=2[voice][key];{mgraph};[mus]apad,atrim=0:{duration:.4f}[mus2];"
                  "[mus2][key]sidechaincompress=threshold=0.02:ratio=6:attack=30:release=500[bed]")
        mix.append("[bed]")
    else:
        graph += "[voice]"
    used: dict[str, int] = {}
    for k, (t, name) in enumerate(c for c in cues if 0 <= c[0] < duration):
        args += ["-i", str(sfx_path(name, used.get(name, 0)))]   # rotate takes: no copy-paste repeats
        used[name] = used.get(name, 0) + 1
        ms = round(t * 1000)
        graph += (f";[{n}:a]aformat=channel_layouts=stereo,adelay={ms}|{ms},volume={SFX_GAIN}[s{k}]")
        mix.append(f"[s{k}]")
        n += 1
    if mix:
        graph += (f";[voice]{''.join(mix)}amix=inputs={len(mix) + 1}:duration=first:normalize=0,"
                  "alimiter=limit=0.89:level=false")
    else:
        graph = graph.removesuffix("[voice]")
    graph += f",atrim=0:{duration:.4f}"
    run_ffmpeg([*args, "-filter_complex", graph, "-vn", "-c:a", "aac", "-b:a", "192k", str(out)])


def _face_on_canvas(ep: Episode, cv: Canvas) -> tuple[float, float] | None:
    """The detected face centre, mapped through face_fit (narrow footage sits centred on the canvas)."""
    from .face import face_info
    from .media import probe
    f = face_info(ep)
    if not f:
        return None
    info = probe(ep.clean_video)
    scale = min(cv.width / info.width, cv.height / info.height)
    w, h = info.width * scale / cv.width, info.height * scale / cv.height
    return round((1 - w) / 2 + f["cx"] * w, 3), round((1 - h) / 2 + f["cy"] * h, 3)


def _cutout(ep: Episode, b: Beat, i: int, frames: int, teaser, style: Style, bundle: Path, cv: Canvas,
            grade: str, out: Path) -> None:
    """He is cut out of the room and stands on the episode's world; caption (or the beat's picture) on the left."""
    from .cutout import cutout_clip
    from .graphics import RenderJob, _publish, _style_props
    face = cv.work / f"face_{i}.mp4"
    _face_clip(ep, replace(b, kind="face", transition=None), frames, teaser, face, None, cv,
               encode=[*INTERMEDIATE, "-r", str(cv.fps)], grade=grade, plain=True)
    shift = round(0.66 - cv.face[0], 3) if cv.face else 0.18
    fw = min(cv.width, round(cv.height * (cv.src_aspect or cv.width / cv.height)))
    region = ((cv.width - fw) // 2, (cv.width - fw) // 2 + fw)
    pic = _asset(ep.assets, f"img_{i}", IMAGE_EXT)
    props = {"style": _style_props(style), "durationSec": 1, "caption": b.caption or "", "personX": 0.66,
             **({"src": _publish(bundle, pic)} if pic else {})}
    bg = RenderJob("cutout-bg", props, cv.work / f"cutout_bg_{i}.png", cv.remotion_scale, still=True)
    render_batch([bg], bundle)
    cutout_clip(face, bg.out, out, cv.width, cv.height, cv.fps, frames, cv.encode, shift,
                vf=_transition_filter(b.transition, cv), region=region)


def _end_screen(plan, style: Style, cv: Canvas, bundle: Path, channel: dict, avatar: Path | None) -> Path:
    """The last seconds: room for YouTube's end-screen elements (next video + subscribe)."""
    from .graphics import RenderJob, _publish, _style_props
    out = cv.work / "end_screen.mp4"
    stamp = out.with_suffix(".hash")
    key = hashlib.sha1(json.dumps([plan.end_screen, style.name, channel, cv.encode, cv.width, _stamp(avatar),
                                   _source_hash()]).encode()).hexdigest()
    if not (out.exists() and stamp.exists() and stamp.read_text() == key):
        ch = dict(channel, avatar=_publish(bundle, avatar, "channel_avatar" + avatar.suffix) if avatar else None)
        job = RenderJob("end-screen", {"style": _style_props(style), "durationSec": plan.end_screen, "channel": ch},
                        cv.work / "end_screen_raw.mp4", cv.remotion_scale)
        render_batch([job], bundle)
        _finish(job.out, round(plan.end_screen * cv.fps), out, cv, None)
        stamp.write_text(key)
    return out


def _stamp(path: Path | None) -> str:
    return f"{path.name}:{path.stat().st_mtime_ns}" if path else ""


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
    cv.face = _face_on_canvas(ep, cv)
    from .media import probe
    _info = probe(ep.clean_video)
    cv.src_aspect = _info.width / _info.height
    entities = load_entities(ep)
    channel = load_channel()
    avatar = channel_avatar(ep.work) if any(b.kind == "face_fx" for b in plan.beats) else None

    src_stamp = str(ep.clean_video.stat().st_mtime)
    correct = analyse(ep)["correction"]
    design = _source_hash()   # a changed graphic design re-renders the clips that use it
    clips, missing, pending = [], [], []   # pending: Remotion renders, done together with one browser
    for i, b in enumerate(plan.beats):
        # Frame-grid boundaries: the sum of clip lengths equals the timeline exactly (no drift).
        frames = round(b.end * cv.fps) - round(b.start * cv.fps)
        look = b.grade or plan.grade or style.grade
        footage_grade = grade_filter(correct, look)   # his camera: measured correction + light polish
        ai_grade = ""                                  # generated clips are left as they came
        asset = None
        if b.kind == "ai_image":
            asset = _asset(ep.assets, f"ai_{i}", IMAGE_EXT)
        elif b.kind == "ai_video":
            asset = _asset(ep.assets, f"ai_{i}", VIDEO_EXT) or _asset(ep.assets, f"ai_{i}", IMAGE_EXT)
        elif b.kind == "entity":
            asset = entity_image(ep, b.entity)
        elif b.kind == "footage":
            asset = ep.assets / f"footage_{i}.mp4"
            if not asset.exists():
                raise MediaError(f"beat {i}: مقطع الأرشيف ناقص، شغّل مرحلة images أول")
        elif b.kind == "graphic" and (b.graphic or {}).get("type") == "article":
            asset = ep.assets / f"article_{i}.png"
            if not asset.exists():
                raise MediaError(f"beat {i}: لقطة المقالة ناقصة، شغّل مرحلة images أول")
        if b.kind in ("ai_image", "ai_video") and asset is None:
            missing.append(i)
        out = cv.work / f"beat_{i}.mp4"
        stamp = cv.work / f"beat_{i}.hash"
        key = hashlib.sha1(json.dumps([asdict(b), style.name, teaser, src_stamp, frames, cv.encode, cv.width, cv.face,
                                       _stamp(asset), entities.get(b.entity or ""), channel,
                                       "" if b.kind.startswith("face") and b.kind != "face_fx" else design,
                                       footage_grade],
                                      ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if not (out.exists() and stamp.exists() and stamp.read_text() == key):
            job = None
            if b.kind in ("ai_image", "ai_video") and asset is None:
                job = _graphic_job(ep, _fallback_text(b), i, style, bundle, cv)
            elif b.kind == "footage" and b.treatment == "full":
                _finish(asset, frames, out, cv, b.transition, cover=True, loop=True)
            elif b.kind == "footage":
                job = _graphic_job(ep, b, i, style, bundle, cv, src=asset)
            elif b.kind == "ai_video" and asset.suffix.lower() in VIDEO_EXT:
                _finish(asset, frames, out, cv, b.transition, cover=True, loop=True, grade=ai_grade)
            elif b.kind == "ai_video":  # only a still came back: animate it like an AI image
                job = _graphic_job(ep, replace(b, kind="ai_image"), i, style, bundle, cv, src=asset)
            elif b.kind in ("image", "ai_image", "graphic"):
                job = _graphic_job(ep, b, i, style, bundle, cv, src=asset)
            elif b.kind == "entity":
                e = entities.get(b.entity) or {"name": b.entity, "kind": "person"}
                job = _graphic_job(ep, b, i, style, bundle, cv, src=asset,
                                   extra_props={"name": e["name"], "role": e.get("role", ""),
                                                "entityKind": e.get("kind", "person")})
            elif b.kind == "face_cutout":
                _cutout(ep, b, i, frames, teaser, style, bundle, cv, footage_grade, out)
            elif b.kind == "face_fx":
                face = cv.work / f"face_{i}.mp4"
                _face_clip(ep, replace(b, kind="face", transition=None), frames, teaser, face, None, cv,
                           encode=[*INTERMEDIATE, "-r", str(cv.fps)], grade=footage_grade)
                job = face_fx_job(b, style, face, cv.work / f"fx_{i}.mp4", cv.fps, channel, bundle,
                                  scale=cv.remotion_scale, avatar=avatar)
            else:
                _face_clip(ep, b, frames, teaser, out, frame_bg, cv, grade=footage_grade)
            if job is None:
                stamp.write_text(key)
            else:
                pending.append((job, frames, out, b.transition, stamp, key))
        clips.append(out)
    if pending:
        print(f"   🎨 أرسم {len(pending)} گرافيك سوه…", flush=True)
        render_batch([p[0] for p in pending], bundle)
        for job, frames, out, transition, stamp, key in pending:
            _finish(job.out, frames, out, cv, transition)
            stamp.write_text(key)
    if missing:
        print(f"⚠️  مشاهد ذكاء اصطناعي ناقصة (انكتب الـ caption بدالها): beats {missing}")

    if plan.end_screen:
        clips.append(_end_screen(plan, style, cv, bundle, channel, avatar or channel_avatar(ep.work)))

    listing = cv.work / "concat.txt"
    listing.write_text("".join(f"file '{c.resolve()}'\n" for c in clips), encoding="utf-8")
    audio = cv.work / "audio.m4a"
    total_frames = (round(plan.beats[-1].end * cv.fps) - round(plan.beats[0].start * cv.fps)
                    + round(plan.end_screen * cv.fps))
    cues = beat_cues(plan.beats, FX_CUES)
    for b in plan.beats:
        cues += [(b.start + float(st.get("at", 0.3)), "pop") for st in (b.stickers or [])]
    duration = total_frames / cv.fps
    music = []
    if plan.music:
        for k, start, end in segments(plan, duration):
            path = music_asset(ep, k)
            if path:
                music.append((k, path, start, end))
            else:
                print(f"⚠️  موسيقى المقطع {k} ناقصة (ينسمع بدون موسيقى من {start:.0f} ث)")
    else:
        single = _asset(ep.assets, "music", AUDIO_EXT)
        music = [(0, single, 0.0, duration)] if single else []
    _build_audio(ep, teaser, duration, audio, sorted(cues), music)
    final = ep.edit / "preview.mp4" if preview else ep.final
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(audio), "-map", "0:v", "-map", "1:a",
                "-c", "copy", "-movflags", "+faststart", str(final)])
    return final
