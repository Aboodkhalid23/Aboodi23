"""The presenter cut out of his room (MediaPipe selfie segmentation, free, on this machine) and placed on
the episode's world, with a white paper-cut outline — the collage look of the reference channel."""
import subprocess
from pathlib import Path

import numpy as np

from .media import MediaError

SMOOTH = 0.55      # temporal smoothing of the mask (no flicker at the hair / shoulders)
OUTLINE = 9        # px of white "paper cut" edge at 1080p


def _segmenter():
    import mediapipe as mp
    return mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0)   # general model, any shape


def cutout_clip(face: Path, background: Path, out: Path, width: int, height: int, fps: int, frames: int,
                encode: list[str], shift: float = 0.18, vf: str = "", region: tuple[int, int] | None = None) -> Path:
    """`face`: canvas-sized footage (black outside the camera picture). `background`: PNG of the scene behind
    him. `region`: x range of the real camera picture (narrow for phone video) — the person is found
    there only, at full detail. He moves right by `shift` × width to free the left side."""
    import cv2
    bg = cv2.imread(str(background), cv2.IMREAD_COLOR)
    if bg is None:
        raise MediaError(f"خلفية القص مو موجودة: {background}")
    bg = cv2.resize(bg, (width, height))[:, :, ::-1].astype(np.float32)
    dx = int(round(shift * width))
    edge = max(2, round(OUTLINE * height / 1080))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * edge + 1, 2 * edge + 1))
    reader = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(face), "-frames:v", str(frames), "-f", "rawvideo",
                               "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    writer = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
                               "-r", str(fps), "-i", "-", *(["-vf", vf.lstrip(",")] if vf else []), "-frames:v", str(frames),
                               "-an", *encode, str(out)], stdin=subprocess.PIPE)
    seg, prev, last = _segmenter(), None, None
    size = width * height * 3
    try:
        for _ in range(frames):
            buf = reader.stdout.read(size)
            if len(buf) < size:          # footage ran short: hold the last frame
                if last is None:
                    raise MediaError("فيديو القص فارغ")
                writer.stdin.write(last)
                continue
            img = np.frombuffer(buf, np.uint8).reshape(height, width, 3)
            x0, x1 = region or (0, width)
            crop = img[:, x0:x1]
            small = cv2.resize(crop, (256, max(64, round(256 * height / max(1, x1 - x0)))))
            m = np.zeros((height, width), np.float32)
            m[:, x0:x1] = cv2.resize(seg.process(small).segmentation_mask, (x1 - x0, height))
            prev = m if prev is None else SMOOTH * prev + (1 - SMOOTH) * m
            mask = cv2.GaussianBlur(np.clip((prev - 0.35) / 0.3, 0, 1), (5, 5), 0)
            hard = (mask > 0.5).astype(np.uint8)
            ring = cv2.dilate(hard, kernel).astype(np.float32)
            if dx:   # slide him to the right; nothing wraps around from the other side
                img = np.roll(img, dx, axis=1); img[:, :dx] = 0
                mask = np.roll(mask, dx, axis=1); mask[:, :dx] = 0
                ring = np.roll(ring, dx, axis=1); ring[:, :dx] = 0
            ring = cv2.GaussianBlur(ring, (3, 3), 0)[..., None]
            m3 = mask[..., None]
            frame = bg * (1 - ring) + 250.0 * ring                    # white paper edge
            frame = frame * (1 - m3) + img.astype(np.float32) * m3    # the presenter
            last = frame.clip(0, 255).astype(np.uint8).tobytes()
            writer.stdin.write(last)
    finally:
        reader.stdout.close()
        reader.wait()
        writer.stdin.close()
        code = writer.wait()
        seg.close()
    if code != 0 or not out.exists():
        raise MediaError("فشل تركيب القص (ffmpeg)")
    return out
