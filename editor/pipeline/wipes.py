"""Wipe transitions that need the clip before them (from the owner's references, update 1): the new
shot tears in through a ragged white paper edge (`tear`), or the old shot burns away from a glowing,
charred edge (`burn`). The edge runs right → left, the way Arabic reads. Done after all clips exist,
re-encoding only the clip that enters.

Camera moves (from the research update, 2026-10-04-research.md), drawn frame by frame in numpy:
  `dive`  zoom-through: the camera flies into the old shot until it fills past the frame, the new shot
          arrives still magnified and settles. One log-zoom curve across both, so the speed never drops at
          the cut; zoom blur from sub-frame supersampling (the faster, the more samples).
  `pan`   whip-pan: both shots on one strip, the camera whips to the next (new shot enters from the left,
          the way the eye moves reading Arabic), blur only along the travel, strongest at the fastest frame."""
import hashlib
from pathlib import Path

import numpy as np

from .media import run_ffmpeg

WIPES = ("tear", "burn", "dive", "pan")
MOVES = ("dive", "pan")
MOVE_DUR = 0.6     # seconds of a camera move
DIVE_ZOOM = (2.4, 1.9)   # old shot leaves at 2.4x, new shot arrives at 1.9x
DUR = 0.5          # seconds the edge takes to cross the frame


def _dist(kind: str) -> str:
    """Signed distance (px) of pixel X from the edge on row Y at time T: > 0 = the new shot. The edge
    starts past the right side and leaves past the left. (No st()/ld(): blend runs on several threads
    that would share those variables.)"""
    if kind == "tear":   # ragged, fine-toothed paper
        jag = "W*(0.012*sin(Y/53)+0.008*sin(Y/19+1)+0.004*sin(Y/6.1+2)+0.0025*sin(Y/2.3))"
    else:                # wavy, flickering fire line
        jag = "W*0.03*(sin(Y/41+T*9)+0.5*sin(Y/13+2)+0.3*sin(Y/5+T*25))"
    return f"(X-W*(1.12-1.24*min(T/{DUR},1))-{jag})"


def wipe_filter(kind: str) -> str:
    """blend options on gbrp planes (c0 = G, c1 = B, c2 = R); top = incoming clip, bottom = old frame."""
    if kind in MOVES:
        return f"move:{kind}:{MOVE_DUR}:{DIVE_ZOOM}"
    d = _dist(kind)
    if kind == "tear":
        edge = "W*0.012"        # white paper margin of the torn sheet
        shade = "W*0.03"        # soft shadow the sheet casts on the new shot
        expr = f"if(gt({d},0),A*(0.72+0.28*min({d}/({shade}),1)),if(gt({d},-{edge}),246,B))"
        return f"all_expr='{expr}'"
    g = f"(1+{d}/(W*0.05))"     # 1 at the flame front → 0 inside the old frame
    hot = {"c2": "255", "c0": f"110+230*({g}-0.6)", "c1": "25"}    # R, G, B of the flame
    char = {"c2": "38", "c0": "18", "c1": "10"}                      # charred paper
    return ":".join(f"{c}_expr='if(gt({d},0),A,if(gt({g},0.6),{hot[c]},if(gt({g},0.2),{char[c]},B)))'"
                    for c in ("c0", "c1", "c2"))


def apply_wipe(kind: str, prev: Path, clip: Path, out: Path, width: int, height: int, fps: int,
               encode: list[str]) -> Path:
    """`clip` with its first DUR seconds wiping in over the last frame of `prev`."""
    key = hashlib.sha1(f"{kind}|{prev.stat().st_mtime}|{prev.stat().st_size}|{clip.stat().st_mtime}|"
                       f"{clip.stat().st_size}|{wipe_filter(kind)}".encode()).hexdigest()
    stamp = out.with_suffix(".hash")
    if out.exists() and stamp.exists() and stamp.read_text() == key:
        return out
    last = out.with_name(out.stem + "_last.png")
    run_ffmpeg(["-sseof", "-0.3", "-i", str(prev), "-update", "1", "-frames:v", "8", str(last)])
    if kind in MOVES:
        _camera_move(kind, last, clip, out, width, height, fps, encode)
        stamp.write_text(key)
        return out
    run_ffmpeg(["-i", str(clip), "-loop", "1", "-framerate", str(fps), "-i", str(last), "-filter_complex",
                f"[0:v]format=gbrp,setsar=1[a];[1:v]scale={width}:{height},format=gbrp,setsar=1[b];"
                f"[a][b]blend={wipe_filter(kind)}:shortest=1,format=yuv420p",
                "-an", *encode, str(out)])
    stamp.write_text(key)
    return out


def _whip(p: float) -> float:
    """ease.whip (0.77, 0, 0.175, 1): very slow ends, violent middle."""
    from .graphics_curves import bezier
    return bezier(0.77, 0.0, 0.175, 1.0, p)


def _scaled(img, s: float):
    import cv2
    h, w = img.shape[:2]
    m = np.float32([[s, 0, (1 - s) * w / 2], [0, s, (1 - s) * h / 2]])
    return cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def _zoomed(img, l0: float, l1: float):
    """`img` magnified from exp(l0) to exp(l1) during one frame's shutter: averaged sub-frames = zoom blur."""
    n = int(min(9, 1 + abs(l1 - l0) * 40))
    acc = np.zeros(img.shape, np.float32)
    for k in range(n):
        acc += _scaled(img, float(np.exp(l0 + (l1 - l0) * k / max(1, n - 1))))
    return acc / n


def move_frame(kind: str, old, new, p: float, step: float):
    """One frame of a camera move at progress p (0–1); `step` = progress per frame (for the blur)."""
    import cv2
    if kind == "dive":
        a, b = np.log(DIVE_ZOOM[0]), np.log(DIVE_ZOOM[1])
        total = a + b
        cut = _cut_point(a / total)
        l0, l1 = total * _whip(max(0.0, p - step * 0.5)), total * _whip(p)
        if p < cut:
            return _zoomed(old.astype(np.float32), l0, l1)
        return _zoomed(new.astype(np.float32), total - l0, total - l1)   # arrives at 1.9x, settles to 1x
    h, w = old.shape[:2]
    x0, x1 = w * _whip(max(0.0, p - step * 0.5)), w * _whip(p)
    x = int(round(x1))
    strip = np.zeros_like(old, dtype=np.float32)
    strip[:, x:] = old[:, : w - x] if x < w else 0          # old shot slides right…
    strip[:, :x] = new[:, w - x:] if x > 0 else 0           # …new shot follows from the left
    k = int(abs(x1 - x0) * 0.8)
    return cv2.blur(strip, (k, 1)) if k > 2 else strip


def _cut_point(share: float) -> float:
    """Progress at which the whip curve has covered `share` of the zoom (where the shots swap)."""
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _whip(mid) < share else (lo, mid)
    return (lo + hi) / 2


def _camera_move(kind: str, last: Path, clip: Path, out: Path, width: int, height: int, fps: int, encode: list[str]):
    import subprocess
    import cv2
    old = cv2.resize(cv2.imread(str(last), cv2.IMREAD_COLOR)[:, :, ::-1], (width, height))
    n_move = max(2, round(MOVE_DUR * fps))
    size = width * height * 3
    reader = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(clip), "-vf", f"scale={width}:{height}",
                               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    writer = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                               f"{width}x{height}", "-r", str(fps), "-i", "-", "-an", *encode, str(out)],
                              stdin=subprocess.PIPE)
    try:
        i = 0
        while True:
            buf = reader.stdout.read(size)
            if len(buf) < size:
                break
            frame = np.frombuffer(buf, np.uint8).reshape(height, width, 3)
            if i < n_move:
                p = (i + 1) / n_move
                frame = move_frame(kind, old, frame, p, 1 / n_move).clip(0, 255).astype(np.uint8)
            writer.stdin.write(frame.tobytes())
            i += 1
    finally:
        reader.stdout.close()
        reader.wait()
        writer.stdin.close()
        code = writer.wait()
    if code != 0:
        from .media import MediaError
        raise MediaError("فشل انتقال الكاميرا (ffmpeg)")
