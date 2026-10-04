"""The presenter cut out of his room, precisely (hair included) and without flicker, then placed somewhere else.

Matting: Robust Video Matting (RVM, MobileNetV3, ONNX on the CPU, free) — a model made for people in video: it
keeps a memory of the previous frames, so the edge is steady and hair is soft, not a jagged blob. The model is
downloaded once into ~/.cache/aboodi-models (not the repo). If it can't be had, MediaPipe selfie segmentation
(the old way) takes over.

Three looks (`treatment` on a face_cutout beat):
  paper  he stands on the episode's paper world with a white paper-cut edge (the collage look), caption beside him
  scene  he is moved into a real place (the beat's picture fills the frame: a farm, a factory, a city), softly
         defocused and drifting behind him, the edge of his body lit by it — no outline, it should look shot there
  title  big words stand BEHIND him in his own room and stretch out as they appear (the text-behind-the-back look)
"""
import subprocess
from pathlib import Path

import numpy as np

from .media import MediaError

SMOOTH = 0.55      # MediaPipe fallback only: temporal smoothing of the mask
OUTLINE = 9        # px of white "paper cut" edge at 1080p
MODEL_DIR = Path.home() / ".cache" / "aboodi-models"
RVM_URL = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx"
MODES = ("paper", "scene", "title")


def rvm_model() -> Path | None:
    path = MODEL_DIR / "rvm_mobilenetv3_fp32.onnx"
    if path.exists() and path.stat().st_size > 10_000_000:
        return path
    try:
        import requests
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        r = requests.get(RVM_URL, timeout=120)
        r.raise_for_status()
        part = path.with_suffix(".part")
        part.write_bytes(r.content)
        part.rename(path)
        return path
    except Exception:   # no network / blocked: the MediaPipe fallback still works
        return None


class Matter:
    """alpha (0–1, float32, h×w) for each frame of one shot, in order."""

    def __init__(self, prefer_rvm: bool = True):
        self.kind, self.rec = "mediapipe", None
        model = rvm_model() if prefer_rvm else None
        if model is not None:
            try:
                import onnxruntime as ort
                self.sess = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
                self.rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
                self.kind = "rvm"
                import mediapipe as mp   # knows what a PERSON is: keeps chairs and lamps that touch him out of RVM's matte
                self.gate = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0)
            except Exception:
                self.kind = "mediapipe"
        if self.kind == "mediapipe":
            import mediapipe as mp
            self.seg, self.prev = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0), None

    def __call__(self, rgb: np.ndarray) -> np.ndarray:
        import cv2
        h, w = rgb.shape[:2]
        if self.kind == "rvm":
            src = (rgb.astype(np.float32) / 255).transpose(2, 0, 1)[None]
            ratio = np.array([min(1.0, 512 / max(h, w))], np.float32)
            _, pha, *self.rec = self.sess.run(None, {"src": src, "r1i": self.rec[0], "r2i": self.rec[1],
                                                     "r3i": self.rec[2], "r4i": self.rec[3], "downsample_ratio": ratio})
            alpha = pha[0, 0].astype(np.float32)
            small = cv2.resize(rgb, (256, max(64, round(256 * h / w))))
            person = cv2.resize(self.gate.process(small).segmentation_mask, (w, h)) > 0.25
            k = max(9, w // 40) | 1   # a margin around him, so hair and edges stay RVM's (fine) work
            return alpha * cv2.GaussianBlur(cv2.dilate(person.astype(np.uint8), np.ones((k, k), np.uint8)).astype(np.float32), (k, k), 0)
        small = cv2.resize(rgb, (256, max(64, round(256 * h / w))))
        m = cv2.resize(self.seg.process(small).segmentation_mask, (w, h))
        self.prev = m if self.prev is None else SMOOTH * self.prev + (1 - SMOOTH) * m
        return cv2.GaussianBlur(np.clip((self.prev - 0.35) / 0.3, 0, 1), (5, 5), 0)

    @staticmethod
    def clean(alpha: np.ndarray) -> np.ndarray:
        """Only the person: keep the biggest blob (and blobs nearly as big — two people), drop bits of the room."""
        import cv2
        h, w = alpha.shape
        small = cv2.resize(alpha, (max(1, w // 4), max(1, h // 4)))
        n, labels, stats, _ = cv2.connectedComponentsWithStats((small > 0.5).astype(np.uint8))
        if n <= 2:
            return alpha
        areas = stats[1:, cv2.CC_STAT_AREA]
        keep = [k + 1 for k, a in enumerate(areas) if a >= 0.3 * areas.max()]
        mask = np.isin(labels, keep).astype(np.uint8)
        mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))
        return alpha * cv2.resize(mask.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)

    def close(self):
        if self.kind == "mediapipe":
            self.seg.close()
        else:
            self.gate.close()


def _frames(path: Path, width: int, height: int, n: int):
    """Raw RGB frames of a video scaled to width×height (a still image repeats)."""
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", str(n), "-vf",
                             f"scale={width}:{height}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    size, last = width * height * 3, None
    try:
        for _ in range(n):
            buf = proc.stdout.read(size)
            if len(buf) < size:
                if last is None:
                    raise MediaError(f"الملف فارغ: {path}")
                yield last
                continue
            last = np.frombuffer(buf, np.uint8).reshape(height, width, 3)
            yield last
    finally:
        proc.stdout.close()
        proc.wait()


def _scene_frame(bg: np.ndarray, t: float):
    """The place behind him: drifts closer slowly (1.00 → 1.06) and is gently out of focus, like a real lens."""
    import cv2
    h, w = bg.shape[:2]
    s = 1.0 + 0.06 * t
    m = np.float32([[s, 0, (1 - s) * w / 2], [0, s, (1 - s) * h / 2]])
    return cv2.GaussianBlur(cv2.warpAffine(bg, m, (w, h), borderMode=cv2.BORDER_REFLECT), (0, 0), max(1.0, w / 640))


def cutout_clip(face: Path, background: Path, out: Path, width: int, height: int, fps: int, frames: int,
                encode: list[str], shift: float = 0.18, vf: str = "", region: tuple[int, int] | None = None,
                mode: str = "paper", text: Path | None = None, text_rgb: tuple[int, int, int] = (247, 208, 70),
                matter: Matter | None = None) -> Path:
    """`face`: canvas-sized footage (black outside the camera picture). `background`: for "paper" the scene PNG
    behind him, for "scene" the place he is moved into. `text` ("title"): a video of white words on black — the
    words are laid between his room and him. `region`: x range of the real camera picture (narrow for phone
    video) — he is found there only. "paper" moves him right by `shift` × width to free the left side."""
    import cv2
    bg = None
    if mode in ("paper", "scene"):
        img = cv2.imread(str(background), cv2.IMREAD_COLOR)
        if img is None:
            raise MediaError(f"خلفية القص مو موجودة: {background}")
        if mode == "scene":   # cover the frame, no bars
            ih, iw = img.shape[:2]
            s = max(width / iw, height / ih)
            img = cv2.resize(img, (round(iw * s), round(ih * s)))
            y0, x0 = (img.shape[0] - height) // 4, (img.shape[1] - width) // 2
            img = img[y0:y0 + height, x0:x0 + width]
        bg = cv2.resize(img, (width, height))[:, :, ::-1].astype(np.float32)
    dx = int(round(shift * width)) if mode == "paper" else 0
    edge = max(2, round(OUTLINE * height / 1080))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * edge + 1, 2 * edge + 1))
    words = _frames(text, width, height, frames) if mode == "title" and text else None
    writer = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
                               "-r", str(fps), "-i", "-", *(["-vf", vf.lstrip(",")] if vf else []), "-frames:v", str(frames),
                               "-an", *encode, str(out)], stdin=subprocess.PIPE)
    side_fade = None
    if mode == "scene":
        x0, x1 = region or (0, width)
        ramp = max(8, (x1 - x0) // 10)
        xs = np.arange(width, dtype=np.float32)
        side_fade = np.clip(np.minimum(xs - x0, x1 - 1 - xs) / ramp, 0, 1)[None, :]
    own = matter is None
    matter = matter or Matter()
    try:
        for n, img in enumerate(_frames(face, width, height, frames)):
            x0, x1 = region or (0, width)
            mask = np.zeros((height, width), np.float32)
            mask[:, x0:x1] = matter.clean(matter(np.ascontiguousarray(img[:, x0:x1])))
            if mode == "scene" and (x0 > 0 or x1 < width):
                mask *= side_fade   # the phone picture cut his shoulders: let them fade, not end on a hard line
            m3 = mask[..., None]
            person = img.astype(np.float32)
            if mode == "paper":
                hard = (mask > 0.5).astype(np.uint8)
                ring = cv2.dilate(hard, kernel).astype(np.float32)
                if dx:   # slide him to the right; nothing wraps around from the other side
                    person = np.roll(person, dx, axis=1); person[:, :dx] = 0
                    m3 = np.roll(m3, dx, axis=1); m3[:, :dx] = 0
                    ring = np.roll(ring, dx, axis=1); ring[:, :dx] = 0
                ring = cv2.GaussianBlur(ring, (3, 3), 0)[..., None]
                frame = bg * (1 - ring) + 250.0 * ring                     # white paper edge
            elif mode == "scene":
                place = _scene_frame(bg, n / max(1, frames - 1))
                # light wrap: the place's light spills a little over his edges, so he sits in it
                band = (m3[..., 0] - cv2.erode(m3[..., 0], np.ones((9, 9), np.uint8)))[..., None]
                person = person * (1 - 0.35 * band) + cv2.GaussianBlur(place, (0, 0), 12) * 0.35 * band
                frame = place
            else:   # title: his room, a little darker, the words, then him
                frame = person * 0.8
                if words is not None:
                    wf = next(words).astype(np.float32)
                    a = (wf.max(axis=2) / 255.0)[..., None]                # white words on black = their alpha
                    glow = cv2.GaussianBlur(a[..., 0], (0, 0), 14)[..., None]
                    color = np.array(text_rgb, np.float32)
                    frame = frame * (1 - 0.45 * glow) + color * 0.45 * glow
                    frame = frame * (1 - a) + color * a
            frame = frame * (1 - m3) + person * m3
            writer.stdin.write(frame.clip(0, 255).astype(np.uint8).tobytes())
    finally:
        writer.stdin.close()
        code = writer.wait()
        if own:
            matter.close()
    if code != 0 or not out.exists():
        raise MediaError("فشل تركيب القص (ffmpeg)")
    return out
