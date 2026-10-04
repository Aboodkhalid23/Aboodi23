"""Where the presenter's face is (OpenCV face detector on a dozen frames). Used to light the face
correctly (grade.py) and to keep it centred when the camera zooms (compose.py)."""
import json
import statistics
import subprocess
from pathlib import Path

from .paths import Episode

SAMPLES = 12


def _frame(video: Path, t: float):
    import cv2
    import numpy as np
    png = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                          "-vf", "scale=640:-2", "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True).stdout
    return cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR) if png else None


def locate_face(video: Path, duration: float) -> dict | None:
    """Median face box over the video as fractions of the frame: cx, cy (centre), h (height), and the
    face's average brightness `luma` (0–1). None if no face is found (e.g. a screen recording)."""
    import cv2
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    boxes, lumas = [], []
    for i in range(SAMPLES):
        img = _frame(video, duration * (i + 0.5) / SAMPLES)
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        H, W = gray.shape
        faces = det.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(W // 12, W // 12))
        if len(faces) == 0:
            continue
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        boxes.append(((x + w / 2) / W, (y + h / 2) / H, h / H))
        inner = gray[y + h // 5: y + h * 4 // 5, x + w // 5: x + w * 4 // 5]   # skin, not hair/background
        lumas.append(float(inner.mean()) / 255)
    if len(boxes) < max(3, SAMPLES // 4):
        return None
    cx, cy, h = (statistics.median(b[k] for b in boxes) for k in range(3))
    return {"cx": round(cx, 3), "cy": round(cy, 3), "h": round(h, 3), "luma": round(statistics.median(lumas), 3)}


def face_info(ep: Episode) -> dict | None:
    f = ep.work / "face.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8")) or None
    from .media import probe
    d = locate_face(ep.clean_video, probe(ep.clean_video).duration)
    f.write_text(json.dumps(d or {}), encoding="utf-8")
    return d
