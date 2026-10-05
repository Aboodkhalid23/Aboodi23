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


def halftone_cutout(cut: Path, edge_rgb: tuple[int, int, int], out: Path | None = None) -> Path:
    """The cut-out person printed in black and white with halftone dots and a paper edge of `edge_rgb`
    (done once here: the same look drawn live in the browser costs minutes per scene)."""
    import cv2
    out = Path(out or Path(cut).with_name(Path(cut).stem + "_halftone.png"))
    if out.exists() and out.stat().st_mtime >= Path(cut).stat().st_mtime:
        return out
    rgba = cv2.imread(str(cut), cv2.IMREAD_UNCHANGED)
    h, w = rgba.shape[:2]
    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    gray = np.clip((gray - 0.5) * 1.45 + 0.53, 0, 1)                          # punchy print contrast
    cell = max(4, round(w / 270))                                            # ~7 px dots at 1920
    yy, xx = np.mgrid[0:h, 0:w]
    u, v = (xx + yy) / cell, (xx - yy) / cell                                # 45° screen like newsprint
    dist = np.hypot(u - np.round(u), v - np.round(v)) / 0.7071               # 0 at a dot centre → 1 between
    ink = (dist < np.sqrt(np.clip(1 - gray, 0, 1)) * 0.9).astype(np.float32)
    ink = cv2.GaussianBlur(ink, (0, 0), 0.6)
    printed = np.clip(gray * 0.55 + (1 - ink) * 0.45, 0, 1)                  # tone + dots, still a readable face
    a = rgba[:, :, 3].astype(np.float32) / 255
    hard = (a > 0.5).astype(np.uint8)                                        # keep real people, drop specks
    n, labels, stats, _ = cv2.connectedComponentsWithStats(hard)
    keep = [k for k in range(1, n) if stats[k, cv2.CC_STAT_AREA] >= 0.02 * hard.size] or \
        ([int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1] if n > 1 else [])
    a = a * np.isin(labels, keep)
    r = max(3, round(w / 210))
    ring = cv2.dilate((a > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1,) * 2))
    ring = cv2.GaussianBlur(ring.astype(np.float32), (0, 0), 1.0)
    body = (printed * 255)[..., None].repeat(3, 2)
    edge = np.array(edge_rgb[::-1], np.float32)[None, None, :]
    color = body * a[..., None] + edge * (1 - a[..., None])
    alpha = np.maximum(a, ring)
    cv2.imwrite(str(out), np.dstack([color.clip(0, 255).astype(np.uint8), (alpha * 255).astype(np.uint8)]))
    return out


MAX_PARTS = 5
PART_AREA = 0.012            # a silhouette smaller than 1.2% of the picture is noise, not a person


def _faces(img, min_frac: float = 1 / 30):
    import cv2
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    m = max(20, round(gray.shape[1] * min_frac))
    return det.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=7, minSize=(m, m))


def person_parts(src: Path) -> list[Path]:
    """One white-silhouette PNG per person in `src`, right → left as Arabic reads, for the archive
    "who is who" reveal. People standing close merge in the mask, so the mask is split between the
    faces found on it (each pixel goes to the nearest face, mostly by column); blobs without a face
    count as one person each. Empty when nobody is found."""
    import cv2
    cut = person_cutout(src)
    if cut is None:
        return []
    rgba = cv2.imread(str(cut), cv2.IMREAD_UNCHANGED)
    alpha = rgba[:, :, 3]
    hard = (alpha > 127).astype(np.uint8)
    h, w = hard.shape
    found = sorted(_faces(rgba[:, :, :3]), key=lambda f: -f[2])
    faces = []                                             # real faces: not tiny next to the biggest, not overlapping
    for x, y, fw, fh in found:
        c = (x + fw / 2, y + fh / 2)
        if fw >= 0.35 * found[0][2] and all(abs(c[0] - o[0]) > fw * 0.8 for o in faces):
            faces.append(c)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(hard)
    owner = np.zeros((h, w), np.int32)                     # 0 = nobody, g = person g
    yy, xx = np.mgrid[0:h, 0:w]
    for k in range(1, n):
        if stats[k, cv2.CC_STAT_AREA] < PART_AREA * hard.size:
            continue
        blob = labels == k
        mine = [(fx, fy) for fx, fy in faces if labels[int(fy), int(fx)] == k]
        if len(mine) < 2:                                  # one person (or no face seen): the whole blob
            owner[blob] = owner.max() + 1
            continue
        dist = np.stack([np.hypot(xx - fx, (yy - fy) * 0.25) for fx, fy in mine])
        base = owner.max()
        owner[blob] = base + 1 + dist.argmin(0)[blob]
    groups = [g for g in range(1, owner.max() + 1) if (owner == g).sum() >= PART_AREA * hard.size]
    groups = sorted(groups, key=lambda g: -(owner == g).sum())[:MAX_PARTS]
    groups.sort(key=lambda g: -np.nonzero(owner == g)[1].mean())
    out = []
    for i, g in enumerate(groups):
        part = Path(src).with_name(f"{Path(src).stem}_sil{i}.png")
        mine = cv2.dilate((owner == g).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0   # keep the soft edge
        a = np.where(mine, alpha, 0).astype(np.uint8)
        cv2.imwrite(str(part), np.dstack([np.full((h, w, 3), 248, np.uint8), a]))
        out.append(part)
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


def clean_plate(src: Path, cut: Path, out: Path | None = None) -> Path:
    """The scene with the figure painted out (OpenCV inpainting under a slightly grown mask), so his separate
    layer can move without a second copy of him showing behind it."""
    import cv2
    out = Path(out or Path(src).with_name(Path(src).stem + "_plate.png"))
    if out.exists() and out.stat().st_mtime >= max(Path(src).stat().st_mtime, Path(cut).stat().st_mtime):
        return out
    img = cv2.imread(str(src), cv2.IMREAD_COLOR)
    a = cv2.imread(str(cut), cv2.IMREAD_UNCHANGED)
    alpha = a[:, :, 3] if a is not None and a.ndim == 3 and a.shape[2] == 4 else None
    if img is None or alpha is None:
        return Path(src)
    alpha = cv2.resize(alpha, (img.shape[1], img.shape[0]))
    grow = max(9, img.shape[1] // 90) | 1
    hole = cv2.dilate((alpha > 25).astype(np.uint8) * 255, np.ones((grow, grow), np.uint8))
    scale = 0.5                                   # inpaint at half size (fast), then put back only the hole
    small = cv2.inpaint(cv2.resize(img, None, fx=scale, fy=scale), cv2.resize(hole, None, fx=scale, fy=scale), 9,
                        cv2.INPAINT_TELEA)
    filled = cv2.resize(small, (img.shape[1], img.shape[0]))
    m = cv2.GaussianBlur(hole.astype(np.float32) / 255, (0, 0), grow / 3)[..., None]
    cv2.imwrite(str(out), (img * (1 - m) + filled * m).astype(np.uint8))
    return out
