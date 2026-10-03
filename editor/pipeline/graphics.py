"""Render graphic / image beats as short clips with Remotion."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from .media import MediaError
from .plan import Beat
from .styles import Style

REMOTION_DIR = Path(__file__).resolve().parent.parent / "remotion"
BROWSER = os.environ.get(
    "EDITOR_BROWSER", "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell")


def _style_props(style: Style) -> dict:
    return {"palette": style.palette, "fonts": style.fonts, "texture": style.texture}


def _source_hash() -> str:
    h = hashlib.sha1()
    for d in ("src", "public"):
        for f in sorted((REMOTION_DIR / d).rglob("*")):
            if f.is_file():
                h.update(str(f.relative_to(REMOTION_DIR)).encode() + f.read_bytes())
    return h.hexdigest()


def ensure_bundle(out_dir: Path | None = None) -> Path:
    """Bundle the Remotion project once; later renders reuse it (rebuilt only if src/ changes)."""
    out_dir = Path(out_dir or REMOTION_DIR / "out" / "bundle").resolve()
    stamp, key = out_dir / ".source-hash", _source_hash()
    if (out_dir / "index.html").exists() and stamp.exists() and stamp.read_text() == key:
        return out_dir
    shutil.rmtree(out_dir, ignore_errors=True)
    proc = subprocess.run(["npx", "remotion", "bundle", "src/index.ts", f"--out-dir={out_dir}",
                           "--public-dir=public", "--log=error"], cwd=REMOTION_DIR, capture_output=True, text=True)
    if proc.returncode != 0:
        raise MediaError(f"فشل تجهيز الگرافيكس (remotion bundle): {(proc.stderr or proc.stdout).strip()[-800:]}")
    stamp.write_text(key)
    return out_dir


def _remotion(cmd: str, comp: str, out: Path, props: dict, bundle: Path, extra: list[str]) -> Path:
    out = Path(out).resolve()
    props_file = out.with_suffix(".props.json")
    props_file.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    args = ["npx", "remotion", cmd, str(bundle), comp, str(out), f"--props={props_file}",
            f"--browser-executable={BROWSER}", "--log=error", *extra]
    proc = subprocess.run(args, cwd=REMOTION_DIR, capture_output=True, text=True)
    if proc.returncode != 0 or not out.exists():
        raise MediaError(f"فشل رسم الگرافيك ({comp}): {(proc.stderr or proc.stdout).strip()[-800:]}")
    return out


def _publish(bundle: Path, src: Path, name: str | None = None) -> str:
    """Copy a file into the bundle's public/ folder so a composition can staticFile() it."""
    name = name or Path(src).name
    shutil.copyfile(src, bundle / "public" / name)
    return name


VIDEO_FLAGS = ["--codec=h264", "--crf=10", "--concurrency=4", "--muted"]


def render_graphic(beat: Beat, style: Style, out: Path, public_dir: Path | None = None,
                   index: int | None = None, bundle: Path | None = None, scale: float = 1.0,
                   src: Path | None = None, extra_props: dict | None = None) -> Path:
    """Render an image / ai_image / entity / graphic beat. Pictures come from `src`, or for `image`
    beats from assets/img_<index>.* in `public_dir` (the episode's assets folder)."""
    bundle = bundle or ensure_bundle()
    props = {"style": _style_props(style), "durationSec": round(beat.duration, 3), **(extra_props or {})}
    if beat.kind in ("image", "ai_image"):
        if src is None and public_dir is not None:
            src = next(Path(public_dir).glob(f"img_{index}.*"), None)
        if src is None:
            raise MediaError(f"صورة الـ beat {index} مو موجودة")
        comp = "image"
        props.update(src=_publish(bundle, src), treatment=beat.treatment or style.image_treatment)
    elif beat.kind == "entity":
        comp = "entity"
        if src is not None:
            props["src"] = _publish(bundle, src)
    else:
        g = dict(beat.graphic or {})
        comp = g.pop("type")
        props.update(g)
    return _remotion("render", comp, out, props, bundle, [*VIDEO_FLAGS, f"--scale={scale!r}"])


def render_face_fx(beat: Beat, style: Style, face: Path, out: Path, fps: int, channel: dict,
                   bundle: Path | None = None, scale: float = 1.0, avatar: Path | None = None) -> Path:
    """The presenter's own footage (`face`, already canvas-sized) wrapped in a YouTube-style scene."""
    bundle = bundle or ensure_bundle()
    ch = dict(channel)
    ch["avatar"] = _publish(bundle, avatar, "channel_avatar" + avatar.suffix) if avatar else None
    props = {"style": _style_props(style), "durationSec": round(beat.duration, 3), "fps": fps,
             "src": _publish(bundle, face), "fx": beat.fx or "none", "stickers": beat.stickers or [],
             "channel": ch}
    return _remotion("render", "face-fx", out, props, bundle, [*VIDEO_FLAGS, f"--scale={scale!r}"])


def render_face_frame_bg(style: Style, out_png: Path, bundle: Path | None = None, scale: float = 1.0) -> Path:
    props = {"style": _style_props(style), "durationSec": 1}
    return _remotion("still", "face-frame-bg", out_png, props, bundle or ensure_bundle(), [f"--scale={scale!r}"])
