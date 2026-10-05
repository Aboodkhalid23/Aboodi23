"""Clear pictures of the owner's FACE, the reference his drawn character is made from (avatar.py). The sharpest,
biggest-face frames of the episode are found and cropped to the head (hair and beard included).
(The thumbnail maker that lived here was dropped: the owner has his own designer.)"""
import subprocess
from pathlib import Path

import numpy as np

from .media import MediaError, probe, run_ffmpeg

SAMPLES = 48


def best_frames(video: Path, n: int = 3) -> list[float]:
    """Times of the n best frames: a big, sharp, frontal face, spread over the episode."""
    import cv2
    dur = probe(video).duration
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    scored = []
    for k in range(SAMPLES):
        t = dur * (k + 0.5) / SAMPLES
        png = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-vf",
                              "scale=640:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        img = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_GRAYSCALE) if png else None
        if img is None:
            continue
        faces = det.detectMultiScale(img, 1.1, 6, minSize=(img.shape[1] // 10,) * 2)
        if len(faces) == 0:
            continue
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        sharp = cv2.Laplacian(img[y:y + h, x:x + w], cv2.CV_64F).var()
        scored.append((w * h / img.size * np.log1p(sharp), t))
    picked = []
    for _, t in sorted(scored, reverse=True):
        if all(abs(t - p) > dur * 0.08 for p in picked):
            picked.append(t)
        if len(picked) == n:
            break
    return picked


def face_crops(video: Path, out_dir: Path, n: int = 3, size: int = 1024) -> list[Path]:
    """`n` square head crops (face_ref_1.jpg …) from the best frames: what the character designer works from."""
    import cv2
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    outs = []
    for k, t in enumerate(best_frames(video, n), 1):
        frame = out_dir / f"face_ref_{k}_frame.png"
        run_ffmpeg(["-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", str(frame)])
        img = cv2.imread(str(frame), cv2.IMREAD_COLOR)
        frame.unlink(missing_ok=True)
        faces = det.detectMultiScale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.1, 6, minSize=(img.shape[1] // 12,) * 2)
        if len(faces) == 0:
            continue
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        side = int(max(w, h) * 2.0)                       # the whole head: hair, ears, beard, a bit of neck
        cx, cy = x + w // 2, y + h // 2 - int(h * 0.12)
        x0, y0 = max(0, cx - side // 2), max(0, cy - side // 2)
        crop = img[y0:y0 + side, x0:x0 + side]
        out = out_dir / f"face_ref_{k}.jpg"
        cv2.imwrite(str(out), cv2.resize(crop, (size, size), interpolation=cv2.INTER_LANCZOS4), [cv2.IMWRITE_JPEG_QUALITY, 95])
        outs.append(out)
    if not outs:
        raise MediaError("ما لگيت فريم واضح لوجهه")
    return outs
