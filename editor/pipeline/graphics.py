"""Render graphic / image beats as short clips with Remotion."""
import json
import os
import subprocess
from dataclasses import asdict
from pathlib import Path

from .media import MediaError
from .plan import Beat
from .styles import Style

REMOTION_DIR = Path(__file__).resolve().parent.parent / "remotion"
BROWSER = os.environ.get(
    "EDITOR_BROWSER", "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell")


def _style_props(style: Style) -> dict:
    return {"palette": style.palette, "fonts": style.fonts, "texture": style.texture}


def _remotion(cmd: str, comp: str, out: Path, props: dict, public_dir: Path | None, extra: list[str]) -> Path:
    out = Path(out).resolve()
    props_file = out.with_suffix(".props.json")
    props_file.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    args = ["npx", "remotion", cmd, "src/index.ts", comp, str(out), f"--props={props_file}",
            f"--browser-executable={BROWSER}", "--log=error", *extra]
    if public_dir:
        args.append(f"--public-dir={Path(public_dir).resolve()}")
    proc = subprocess.run(args, cwd=REMOTION_DIR, capture_output=True, text=True)
    if proc.returncode != 0 or not out.exists():
        raise MediaError(f"فشل رسم الگرافيك ({comp}): {(proc.stderr or proc.stdout).strip()[-800:]}")
    return out


def render_graphic(beat: Beat, style: Style, out: Path, public_dir: Path | None = None,
                   index: int | None = None) -> Path:
    """`image` beats read assets/img_<index>.* from `public_dir` (the episode's assets folder)."""
    props = {"style": _style_props(style), "durationSec": round(beat.duration, 3)}
    if beat.kind == "image":
        src = next(Path(public_dir).glob(f"img_{index}.*"), None) if public_dir else None
        if src is None:
            raise MediaError(f"صورة الـ beat {index} مو موجودة")
        comp = "image"
        props.update(src=src.name, treatment=beat.treatment or style.image_treatment)
    else:
        g = dict(beat.graphic or {})
        comp = g.pop("type")
        props.update(g)
    return _remotion("render", comp, out, props, public_dir,
                     ["--codec=h264", "--crf=18", "--concurrency=4", "--muted"])


def render_face_frame_bg(style: Style, out_png: Path) -> Path:
    props = {"style": _style_props(style), "durationSec": 1}
    return _remotion("still", "face-frame-bg", out_png, props, None, [])
