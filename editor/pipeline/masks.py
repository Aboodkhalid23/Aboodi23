"""Cut the person out of a still picture (MediaPipe, free, local) so scenes can put text behind them
or move them apart from the background (2.5D parallax)."""
from pathlib import Path

import numpy as np

MIN_AREA = 0.03     # under 3% of the picture: no usable person


def person_cutout(src: Path, out: Path | None = None) -> Path | None:
    """PNG of `src` with everything but the person transparent; None when there is no clear person."""
    import cv2
    import mediapipe as mp
    out = Path(out or Path(src).with_name(Path(src).stem + "_person.png"))
    if out.exists() and out.stat().st_mtime >= Path(src).stat().st_mtime:
        return out
    img = cv2.imread(str(src), cv2.IMREAD_COLOR)
    if img is None:
        return None
    h, w = img.shape[:2]
    with mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0) as seg:
        m = seg.process(cv2.cvtColor(cv2.resize(img, (512, max(64, round(512 * h / w)))), cv2.COLOR_BGR2RGB)).segmentation_mask
    m = cv2.resize(m, (w, h))
    m = cv2.GaussianBlur(np.clip((m - 0.4) / 0.25, 0, 1), (0, 0), max(1.0, w / 900))
    if float((m > 0.5).mean()) < MIN_AREA:
        return None
    rgba = np.dstack([img, (m * 255).astype(np.uint8)])
    cv2.imwrite(str(out), rgba)
    return out


FRAME = (1920, 1080)
FOCUS = (0.5, 0.22)          # objectPosition of the full-bleed picture treatments (ImageCard.tsx FOCUS)
FULL_BLEED = ("cinematic_title", "parallax", "ken_burns", "film_grain")
TITLE_BAND = 0.26            # height of the giant in-scene word, fraction of the frame


def _cover(w: int, h: int, frame=FRAME, focus=FOCUS):
    """(scale, x offset, y offset) of a picture laid with objectFit: cover on the frame."""
    W, H = frame
    s = max(W / w, H / h)
    return s, (W - w * s) * focus[0], (H - h * s) * focus[1]


def image_layout(src: Path, cut: Path | None = None, frame=FRAME) -> dict:
    """Where things are once the picture fills the frame: `face` [cx, cy, w, h] (fractions) or None,
    and where the giant title fits — `titleY` (centre) and `titleFront` (True when the person covers
    every band, so the word goes in front instead of hiding behind him)."""
    import cv2
    img = cv2.imread(str(src), cv2.IMREAD_COLOR)
    if img is None:
        return {"face": None, "titleY": 0.5, "titleFront": False}
    h, w = img.shape[:2]
    W, H = frame
    s, ox, oy = _cover(w, h, frame)
    out: dict = {"face": None}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = det.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(max(24, w // 20),) * 2)
    if len(faces):
        x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
        out["face"] = [round(float(v), 3) for v in ((ox + (x + fw / 2) * s) / W, (oy + (y + fh / 2) * s) / H,
                                                    fw * s / W, fh * s / H)]
    # the person's coverage of the frame, row by row, across the middle where the word sits
    alpha = None
    if cut is not None and Path(cut).exists():
        rgba = cv2.imread(str(cut), cv2.IMREAD_UNCHANGED)
        if rgba is not None and rgba.ndim == 3 and rgba.shape[2] == 4:
            alpha = rgba[:, :, 3].astype(np.float32) / 255
    if alpha is None:
        out.update(titleY=0.5, titleFront=False)
        return out
    small = 4                                            # work at 1/4 size
    M = np.float32([[s / small, 0, ox / small], [0, s / small, oy / small]])
    m = cv2.warpAffine(alpha, M, (W // small, H // small))
    rows = m[:, int(m.shape[1] * 0.25): int(m.shape[1] * 0.75)].mean(axis=1)   # where the word sits
    n = len(rows)
    band = max(1, int(TITLE_BAND * n))
    face = out["face"]
    f0, f1 = (face[1] - face[3] / 2, face[1] + face[3] / 2) if face else (0.0, 0.0)

    def on_face(y: float) -> float:                      # share of the band that crosses the face
        a, z = max(y - TITLE_BAND / 2, f0), min(y + TITLE_BAND / 2, f1)
        return max(0.0, z - a) / TITLE_BAND

    tops = range(int(0.06 * n), int(0.94 * n) - band + 1)
    best = None                                          # (score, y)
    for top in tops:
        hidden = float(rows[top: top + band].mean())
        y = (top + band / 2) / n
        if hidden > 0.25 or on_face(y) > 0.3:          # the person would hide the word, or the word the face
            continue
        # a little overlap gives depth (word behind him); off the face, readable, upper half preferred
        score = min(hidden, 0.12) - max(0.0, hidden - 0.12) * 2 - on_face(y) * 0.6 - abs(y - 0.42) * 0.15
        if best is None or score > best[0]:
            best = (score, y)
    if best is not None:
        out.update(titleY=round(best[1], 3), titleFront=False)
    else:                                                # a close-up fills the frame: word in front, under the face
        y = min(max(f1 + TITLE_BAND / 2, 0.5), 0.8) if face else \
            (min(tops, key=lambda t: rows[t: t + band].mean()) + band / 2) / n
        out.update(titleY=round(float(y), 3), titleFront=True)
    return out


def place_on_face(stickers: list[dict], face: list[float] | None) -> list[dict]:
    """Stickers that follow the face when their spot is not given: `censor` across the eyes,
    `name_tag` under the chin, `scribble_circle` around the head."""
    if not face:
        return stickers
    cx, cy, fw, fh = face
    out = []
    for st in stickers:
        st = dict(st)
        if st.get("x") is None and st.get("y") is None:
            t = st.get("type")
            if t == "censor":
                st.update(x=cx, y=round(cy - fh * 0.1, 3))
                st.setdefault("w", round(min(0.6, fw * 1.35), 3))
                st.setdefault("h", round(max(0.05, fh * 0.22), 3))
            elif t == "name_tag":
                st.update(x=cx, y=round(min(0.9, cy + fh * 0.85), 3))
            elif t == "scribble_circle":
                st.update(x=cx, y=cy)
                st.setdefault("w", round(min(0.7, fw * 1.45), 3))
                st.setdefault("h", round(min(0.9, fh * 1.3), 3))
        out.append(st)
    return out
