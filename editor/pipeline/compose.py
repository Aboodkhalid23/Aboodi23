"""Stage 6: build final.mp4 (or preview.mp4) — per-beat video clips + one continuous audio track."""
import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .channel import channel_avatar, load_channel
from .entities import entity_image, load_entities
from .fmt import load_format
from .grade import analyse, app_chain, grade_filter, look_settings
from .graphics import (_source_hash, ensure_bundle, face_fx_job, face_paper_job, graphic_job, render_batch,
                       render_face_frame_bg)
from .media import MediaError, run_ffmpeg
from .music import AUDIO_EXT, bed_filter, music_asset, segments
from .paths import Episode
from .plan import Beat, load_plan
from .sfx import beat_cues, sfx_path
from .styles import Style, load_style
from .wipes import WIPES, apply_wipe

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
           "fx:search": [(0.0, "whoosh"), (0.65, "click"), (0.95, "click"), (1.25, "click"), (1.65, "pop"),
                         (3.0, "click"), (3.15, "ding")],
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
    # The beat clips ARE the final encode: one lossy generation, then stream copy. Owner's rule: the highest
    # quality, file size no object (CRF 12 ≈ visually lossless; aq-mode 3 keeps dark gradients free of banding).
    return Canvas(fmt.width, fmt.height, fmt.fps, ep.work,
                  ["-c:v", "libx264", "-crf", "12", "-preset", "medium", "-profile:v", "high",
                   "-x264-params", "aq-mode=3", *common])


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
    if not name or name in WIPES:   # wipes need the clip before: done after all clips exist (wipes.py)
        return ""
    on = f"enable='lt(t,{TRANS})'"
    punch = lambda amount: _zoom_crop(f"(1+{amount}*pow(1-min(t/{TRANS},1),3))", cv, 0.5)
    return {
        "flash": f",fade=t=in:st=0:d={TRANS}:color=white",
        "zoom": f",{punch(0.25)}",
        "whip": f",{punch(0.08)},gblur=sigma=45:sigmaV=0.5:{on}",
        "glitch": f",rgbashift=rh=-18:bh=18:gv=6:{on},noise=alls=40:allf=t:{on}",
    }[name]


def effect_filter(name: str | None, cv: "Canvas") -> str:
    """',<filters>' for a video effect from the app's library, on his footage (after the colours)."""
    w, h = cv.width, cv.height
    shake = (f"crop=iw*0.94:ih*0.94:iw*0.03+iw*0.022*sin(t*31):ih*0.03+ih*0.022*cos(t*23),"
             f"scale={w}:{h}:flags=bicubic,setsar=1")
    vhs = "noise=alls=14:allf=t,chromashift=cbh=4:crh=-4,curves=preset=vintage,eq=saturation=0.85"
    chains = {"shake": shake, "vhs": vhs, "retro_shake": f"{shake},{vhs}", "bw": "hue=s=0,eq=contrast=1.12",
              "night": "curves=preset=darker,colorbalance=bs=0.15:bm=0.1,eq=saturation=0.6",
              "dream": "gblur=sigma=1.6,eq=brightness=0.03:saturation=1.12", "rgb_split": "chromashift=cbh=9:crh=-9:cbv=3:crv=-3",
              "flash_in": "fade=t=in:st=0:d=0.3:color=white", "sharpen": "unsharp=7:7:1.1:7:7:0",
              "film": "noise=alls=8:allf=t,vignette=angle=0.5,curves=preset=increase_contrast",
              # his reference (2026-10-25): the negative "X-ray" look; and a soft bloom
              "xray": "negate,hue=s=0,curves=master='0/0 0.45/0.55 1/1',eq=contrast=1.35:brightness=0.04",
              "glow": "split[g0][g1];[g1]gblur=sigma=18,eq=brightness=0.06[gb];[g0][gb]blend=all_mode=screen:all_opacity=0.45",
              # 2026-10-25 (owner: "المؤثرات كلش قليلة")
              "slow_push": f"scale=w='trunc({w}*(1+0.08*min(t,5)/5)/2)*2':h=-2:eval=frame,crop={w}:{h},setsar=1",
              "letterbox": f"drawbox=x=0:y=0:w=iw:h=ih*0.11:color=black:t=fill,drawbox=x=0:y=ih*0.89:w=iw:h=ih*0.11:color=black:t=fill",
              "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,eq=contrast=1.05",
              "warm": "colorbalance=rs=0.08:gs=0.02:bs=-0.08:rm=0.06:bm=-0.05,eq=saturation=1.08",
              "cold": "colorbalance=rs=-0.08:bs=0.1:rm=-0.04:bm=0.08,eq=saturation=0.92",
              "spotlight": "vignette=angle=0.9:mode=forward,eq=brightness=0.02:contrast=1.08",
              "pixel_in": "pixelize=w=28:h=28:enable='lt(t,0.2)',pixelize=w=10:h=10:enable='between(t,0.2,0.4)'",
              "blur_in": "boxblur=20:2:enable='lt(t,0.25)',boxblur=8:1:enable='between(t,0.25,0.45)'",
              "punchy": "eq=contrast=1.18:saturation=1.25,unsharp=5:5:0.6:5:5:0",
              "dreamy_glow": "split[d0][d1];[d1]gblur=sigma=28,eq=brightness=0.08:saturation=1.2[db];[d0][db]blend=all_mode=screen:all_opacity=0.55"}
    return "," + chains[name] if name in chains else ""


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


STORM_FIRST = 0.15   # headline storm timing, same numbers as Update2.tsx (stormGap)


def storm_gap(n: int, dur: float) -> float:
    return min(0.6, max(0.25, dur * 0.55 / max(1, n)))


def paper_images(ep: Episode, i: int, b: Beat) -> dict:
    """Pictures downloaded for the papers of beat i (assets/paper_<i>_<k>.*)."""
    if b.kind != "face_paper":
        return {}
    return {k: a for k in range(len(b.papers or [])) if (a := _asset(ep.assets, f"paper_{i}_{k}", IMAGE_EXT))}


def paper_cues(b: Beat) -> list[tuple[float, str]]:
    """A paper slap as each paper lands beside him (same timing as FacePaper.tsx)."""
    if b.kind != "face_paper":
        return []
    n = len(b.papers or [])
    return [(b.start + float(p.get("at", 0.25 + k * max(1.6, (b.duration - 1) / max(1, n)))), "paper")
            for k, p in enumerate(b.papers or [])]


def graphic_cues(b: Beat) -> list[tuple[float, str]]:
    """Sounds inside the research-update scenes: a paper slap on every landing headline, a pop as the
    people light up."""
    g = b.graphic or {}
    if b.kind != "graphic":
        return []
    if g.get("type") == "headlines":
        n = len(g.get("items") or [])
        return [(b.start + STORM_FIRST + k * storm_gap(n, b.duration), "paper") for k in range(n)]
    if g.get("type") == "units":
        return [(b.start + 1.0, "pop")]
    return []


def kinetic_times(ep: Episode, plan, b: Beat) -> list[float | None]:
    """When each word of a kinetic sentence is said (seconds from the beat's start), from the cleaned transcript;
    a word not found gets None (the scene spaces it evenly)."""
    from .clean import normalize_ar, same
    from .transcribe import load_words
    words = (b.graphic or {}).get("text", "").split()
    if not ep.clean_words.exists() or b.start < plan.teaser_total:
        return [None] * len(words)
    cs = b.start - plan.teaser_total
    heard = [w for w in load_words(ep.clean_words) if cs - 0.3 <= w.start < cs + b.duration]
    out, j = [], 0
    for w in words:
        k = next((k for k in range(j, min(len(heard), j + 4)) if same(normalize_ar(w), normalize_ar(heard[k].text))), None)
        out.append(round(max(0.0, heard[k].start - cs), 3) if k is not None else None)
        j = k + 1 if k is not None else j
    return out


def chapter_cues(plan) -> list[tuple[float, str]]:
    """Long documentaries mark each new chapter with sound: a short riser into a heavy hit on its first frame."""
    out = []
    for t in plan.chapter_times()[1:]:
        out += [(max(0.0, t - 1.2), "riser"), (t, "hit")]
    return out


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
CLEAN_NR = {0: 0, 1: 8, 2: 14, 3: 22}   # the app's "صوت نظيف" levels → afftdn noise reduction (dB)


def sound_settings(ep: Episode) -> dict:
    """The Mac app's sound step (edit/sound.json): {"clean": 0–3, "music": "auto"|mood|"off", "level": LUFS,
    "sfx": bool}; defaults when absent."""
    try:
        d = json.loads((ep.edit / "sound.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    return {"clean": int(d.get("clean", 1)), "music": d.get("music", "auto"), "level": float(d.get("level", MUSIC_LUFS)),
            "sfx": bool(d.get("sfx", True))}


# "طبيعي" (owner, 2026-10-25: "يتوضح بس مو كأنه متوضح بالذكاء الاصطناعي"): light denoise that leaves the room's air,
# a soft de-esser, gentle compression and a touch of chest warmth — clear, but still his real voice
NATURAL_VOICE = ("highpass=f=70,afftdn=nr=5:nf=-55:tn=1,deesser=i=0.25,"
                 "acompressor=threshold=-22dB:ratio=1.8:attack=15:release=220:makeup=1,"
                 "equalizer=f=180:t=q:w=1:g=1.2,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000")


def voice_chain(clean: int = 1) -> str:
    if clean == 4:
        return NATURAL_VOICE
    nr = CLEAN_NR.get(clean, 8)
    chain = VOICE_CHAIN.replace("afftdn=nr=8:nf=-50,", f"afftdn=nr={nr}:nf=-50," if nr else "")
    return chain.replace("highpass=f=80,", "highpass=f=80,equalizer=f=3000:t=q:w=1.2:g=2," if clean >= 2 else "highpass=f=80,")


def _build_audio(ep: Episode, teaser, duration: float, out: Path,
                 cues: list[tuple[float, str]] = (), music: list[tuple[int, Path, float, float]] = ()) -> None:
    """Voice (cleaned, -14 LUFS) + effects at their cue times + music segments ducked under the voice.
    `music`: (cue, file, start, end) on the final timeline."""
    snd = sound_settings(ep)
    if snd["music"] == "off":
        music = ()
    if not snd["sfx"]:
        cues = ()
    args, labels = [], ""
    from .voicepatch import voice_source
    voice = voice_source(ep)   # the cut video's sound, with any word he re-said in his own voice laid in
    for i, (s, e) in enumerate(teaser):
        args += ["-ss", f"{s:.3f}", "-t", f"{e - s:.3f}", "-i", str(voice)]
        labels += f"[{i}:a]"
    args += ["-i", str(voice)]
    labels += f"[{len(teaser)}:a]"
    n = len(teaser) + 1
    graph = (f"{labels}concat=n={n}:v=0:a=1,{voice_chain(snd['clean'])},aformat=channel_layouts=stereo,"
             f"apad,atrim=0:{duration:.4f}")
    mix = []
    if music:
        margs, mgraph = bed_filter(list(music), n, snd["level"])
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
    run_ffmpeg([*args, "-filter_complex", graph, "-vn", "-c:a", "aac", "-b:a", "320k", str(out)])


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


def ep_index(out: Path) -> int:
    return int(re.search(r"beat_(\d+)", out.name).group(1))


def _fetch_one(ep: Episode, query: str, stem: str) -> Path | None:
    """One free picture for `query` saved as assets/<stem>.<ext>; None when nothing comes (offline too)."""
    import requests
    from .sources import download, find
    try:
        s = requests.Session()
        for c in find(query, "image", None, s, set(), [])[:3]:
            try:
                data = download(c, s)
            except requests.RequestException:
                continue
            ext = Path(c.url.split("?")[0]).suffix.lower()
            ep.assets.mkdir(parents=True, exist_ok=True)
            dest = ep.assets / f"{stem}{ext if ext in ('.jpg', '.jpeg', '.png', '.webp') else '.jpg'}"
            dest.write_bytes(data)
            return dest
    except Exception:   # never lose the build over one picture
        return None
    return None


def _split(ep: Episode, b: Beat, frames: int, teaser, style: Style, cv: Canvas, grade: str,
           pic: Path | None, out: Path) -> None:
    """Split screen: the picture on one half, him on the other (wide: picture left, him right, as Arabic reads;
    tall: picture on top, him below), a thin accent line between. No picture found: just him."""
    if pic is None and b.query:   # set from the app after the pictures were fetched: get this one now
        pic = _fetch_one(ep, b.query, f"img_{ep_index(out)}")
    if pic is None:
        _face_clip(ep, replace(b, kind="face"), frames, teaser, out, None, cv, grade=grade)
        return
    face = out.with_name(out.stem + "_face.mp4")
    _face_clip(ep, replace(b, kind="face", transition=None), frames, teaser, face, None, cv,
               encode=[*INTERMEDIATE, "-r", str(cv.fps)], grade=grade)
    W, H, dur = cv.width, cv.height, max(b.duration, 0.1)
    fx, fy = cv.face or (0.5, 0.42)
    accent = style.palette.get("accent", "#FFFFFF").lstrip("#")
    if W >= H:
        hw = W // 2 // 2 * 2
        cut = f"crop={hw}:{H}:x='max(0,min(iw-{hw},{fx:.3f}*iw-{hw}/2))':y=0"
        pic_size, stack, line = (hw, H), "hstack=inputs=2", f"drawbox=x={hw}-3:y=0:w=6:h=ih:color=0x{accent}:t=fill"
    else:
        hh = H // 2 // 2 * 2
        cut = f"crop={W}:{hh}:x=0:y='max(0,min(ih-{hh},{fy:.3f}*ih-{hh}/2))'"
        pic_size, stack, line = (W, hh), "vstack=inputs=2", f"drawbox=x=0:y={hh}-3:w=iw:h=6:color=0x{accent}:t=fill"
    pw, ph = pic_size
    zw, zh = round(pw * 1.12 / 2) * 2, round(ph * 1.12 / 2) * 2   # a slow drift across the picture (alive, not a still)
    graph = (f"[1:v]scale={zw}:{zh}:force_original_aspect_ratio=increase,crop={zw}:{zh},"
             f"crop={pw}:{ph}:x='(iw-ow)*t/{dur:.3f}':y='(ih-oh)/2',fps={cv.fps},setsar=1[p];"
             f"[0:v]{cut},setsar=1[f];[p][f]{stack},{line}{_transition_filter(b.transition, cv)},"
             "tpad=stop_mode=clone:stop_duration=1")
    run_ffmpeg(["-i", str(face), "-loop", "1", "-i", str(pic), "-filter_complex", graph,
                "-frames:v", str(frames), "-an", *cv.encode, str(out)])


def _cutout(ep: Episode, b: Beat, i: int, frames: int, teaser, style: Style, bundle: Path, cv: Canvas,
            grade: str, out: Path) -> None:
    """He is cut out of his room (precise video matting) and: stands on the episode's paper world ("paper"),
    or has big stretching words behind his back ("title")."""
    from .cutout import cutout_clip
    from .graphics import RenderJob, _publish, _style_props
    face = cv.work / f"face_{i}.mp4"
    _face_clip(ep, replace(b, kind="face", transition=None), frames, teaser, face, None, cv,
               encode=[*INTERMEDIATE, "-r", str(cv.fps)], grade=grade, plain=True)
    fw = min(cv.width, round(cv.height * (cv.src_aspect or cv.width / cv.height)))
    region = ((cv.width - fw) // 2, (cv.width - fw) // 2 + fw)
    pic = _asset(ep.assets, f"img_{i}", IMAGE_EXT)
    mode = b.treatment or "paper"
    vf = _transition_filter(b.transition, cv)
    if mode == "title":
        words = RenderJob("cutout-title", {"style": _style_props(style), "durationSec": round(frames / cv.fps, 3),
                                           "text": b.title or b.caption or ""}, cv.work / f"cutout_title_{i}.mp4",
                          cv.remotion_scale)
        render_batch([words], bundle)
        accent = style.palette.get("accent", "#F7D046").lstrip("#")
        cutout_clip(face, None, out, cv.width, cv.height, cv.fps, frames, cv.encode, vf=vf, region=region, mode="title",
                    text=words.out, text_rgb=tuple(int(accent[k:k + 2], 16) for k in (0, 2, 4)))
        return
    shift = round(0.66 - cv.face[0], 3) if cv.face else 0.18
    props = {"style": _style_props(style), "durationSec": 1, "caption": b.caption or "", "personX": 0.66,
             **({"src": _publish(bundle, pic)} if pic else {})}
    bg = RenderJob("cutout-bg", props, cv.work / f"cutout_bg_{i}.png", cv.remotion_scale, still=True)
    render_batch([bg], bundle)
    cutout_clip(face, bg.out, out, cv.width, cv.height, cv.fps, frames, cv.encode, shift, vf=vf, region=region)


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
    # chosen in the Mac app (camera, look, strength, LUT, balance sliders): one chain for the whole episode
    app_grade = app_chain(ep, correct) if look_settings(ep) else None
    design = _source_hash()   # a changed graphic design re-renders the clips that use it
    clips, missing, pending = [], [], []   # pending: Remotion renders, done together with one browser
    for i, b in enumerate(plan.beats):
        # Frame-grid boundaries: the sum of clip lengths equals the timeline exactly (no drift).
        frames = round(b.end * cv.fps) - round(b.start * cv.fps)
        look = b.grade or plan.grade or style.grade
        # his camera: measured correction + light polish, or the look he chose in the app
        footage_grade = app_grade if app_grade is not None and not b.grade else grade_filter(correct, look)
        footage_grade += effect_filter(b.effect, cv)    # an effect he put on this scene in the app
        ai_grade = ""                                  # generated clips are left as they came
        asset = None
        if b.kind == "ai_image":
            asset = _asset(ep.assets, f"ai_{i}", IMAGE_EXT)
        elif b.kind in ("ai_video", "avatar"):   # avatar: the moving drawing if made, else the still drawing
            asset = _asset(ep.assets, f"ai_{i}", VIDEO_EXT) or _asset(ep.assets, f"ai_{i}", IMAGE_EXT)
        elif b.kind == "entity":
            asset = entity_image(ep, b.entity)
        elif b.kind == "footage":
            asset = ep.assets / f"footage_{i}.mp4"
            if not asset.exists():
                raise MediaError(f"beat {i}: مقطع الأرشيف ناقص، شغّل مرحلة images أول")
        elif b.kind == "face_split":
            asset = _asset(ep.assets, f"img_{i}", IMAGE_EXT)
        elif b.kind == "graphic" and (b.graphic or {}).get("type") == "article":
            asset = ep.assets / f"article_{i}.png"
            if not asset.exists():
                raise MediaError(f"beat {i}: لقطة المقالة ناقصة، شغّل مرحلة images أول")
        if b.kind in ("ai_image", "ai_video", "avatar") and asset is None:
            missing.append(i)
        out = cv.work / f"beat_{i}.mp4"
        stamp = cv.work / f"beat_{i}.hash"
        key = hashlib.sha1(json.dumps([asdict(b), style.name, teaser, src_stamp, frames, cv.encode, cv.width, cv.face,
                                       _stamp(asset), _stamp(_asset(ep.assets, f"ai_{i}_fg", IMAGE_EXT)),
                                       entities.get(b.entity or ""), channel,
                                       "" if b.kind.startswith("face") and b.kind not in ("face_fx", "face_paper") else design,
                                       [_stamp(x) for x in paper_images(ep, i, b).values()],
                                       footage_grade],
                                      ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if not (out.exists() and stamp.exists() and stamp.read_text() == key):
            job = None
            if b.kind in ("ai_image", "ai_video", "avatar") and asset is None:
                job = _graphic_job(ep, _fallback_text(b), i, style, bundle, cv)
            elif b.kind == "avatar" and asset.suffix.lower() in VIDEO_EXT:
                _finish(asset, frames, out, cv, b.transition, cover=True, loop=True)
            elif b.kind == "avatar":   # the drawing, alive in layers (Update3.tsx)
                job = _graphic_job(ep, replace(b, kind="ai_image", treatment="avatar"), i, style, bundle, cv, src=asset)
            elif b.kind == "footage" and b.treatment == "full":
                _finish(asset, frames, out, cv, b.transition, cover=True, loop=True)
            elif b.kind == "footage":
                job = _graphic_job(ep, b, i, style, bundle, cv, src=asset)
            elif b.kind == "ai_video" and asset.suffix.lower() in VIDEO_EXT:
                _finish(asset, frames, out, cv, b.transition, cover=True, loop=True, grade=ai_grade)
            elif b.kind == "ai_video":  # only a still came back: animate it like an AI image
                job = _graphic_job(ep, replace(b, kind="ai_image"), i, style, bundle, cv, src=asset)
            elif b.kind == "graphic" and (b.graphic or {}).get("type") == "kinetic":
                job = _graphic_job(ep, b, i, style, bundle, cv, extra_props={"times": kinetic_times(ep, plan, b)})
            elif b.kind in ("image", "ai_image", "graphic"):
                job = _graphic_job(ep, b, i, style, bundle, cv, src=asset)
            elif b.kind == "entity":
                e = entities.get(b.entity) or {"name": b.entity, "kind": "person"}
                job = _graphic_job(ep, b, i, style, bundle, cv, src=asset,
                                   extra_props={"name": e["name"], "role": e.get("role", ""),
                                                "entityKind": e.get("kind", "person")})
            elif b.kind == "face_split":
                _split(ep, b, frames, teaser, style, cv, footage_grade, asset, out)
            elif b.kind == "face_cutout":
                _cutout(ep, b, i, frames, teaser, style, bundle, cv, footage_grade, out)
            elif b.kind == "face_paper":
                face = cv.work / f"face_{i}.mp4"
                _face_clip(ep, replace(b, kind="face", transition=None), frames, teaser, face, None, cv,
                           encode=[*INTERMEDIATE, "-r", str(cv.fps)], grade=footage_grade, plain=True)
                pic_w = min(1.0, cv.height * (cv.src_aspect or cv.width / cv.height) / cv.width)
                behind = b.treatment == "behind" and pic_w > 0.9   # phone footage has no room to slip behind
                job = face_paper_job(replace(b, treatment="overlay") if behind else
                                     (replace(b, treatment=None) if b.treatment == "behind" else b),
                                     style, face, cv.work / f"paper_{i}.{'mov' if behind else 'mp4'}", cv.fps, bundle,
                                     scale=cv.remotion_scale, images=paper_images(ep, i, b), pic_w=pic_w,
                                     face_x=cv.face[0] if cv.face else None, layer_only=behind)
                if behind:   # the papers come out from behind his shoulder: room → papers → him (precise matting)
                    from .cutout import cutout_clip
                    render_batch([job], bundle)
                    cutout_clip(face, None, out, cv.width, cv.height, cv.fps, frames, cv.encode,
                                vf=_transition_filter(b.transition, cv), mode="layer", text=job.out)
                    job = None
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
    for i, b in enumerate(plan.beats):
        if b.transition in WIPES and i > 0:
            clips[i] = apply_wipe(b.transition, clips[i - 1], clips[i], cv.work / f"beat_{i}_{b.transition}.mp4",
                                  cv.width, cv.height, cv.fps, cv.encode)
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
        cues += graphic_cues(b) + paper_cues(b)
    cues += chapter_cues(plan)
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
    own = str(sound_settings(ep)["music"])
    if own.startswith("own:") and (ep.edit / "media" / own[4:]).is_file():   # music he bought or made: the whole episode
        music = [(0, ep.edit / "media" / own[4:], 0.0, duration)]
    _build_audio(ep, teaser, duration, audio, sorted(cues), music)
    final = ep.edit / "preview.mp4" if preview else ep.final
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(audio), "-map", "0:v", "-map", "1:a",
                "-c", "copy", "-movflags", "+faststart", str(final)])
    from .options import post_process
    return post_process(ep, final, plan.teaser_total)   # captions on the video / the opening, if he turned them on
