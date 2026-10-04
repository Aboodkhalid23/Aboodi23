"""YouTube thumbnails (the feature we forgot): the sharpest, biggest-face frames of the owner are found, he is cut
out precisely (the same matting as face_cutout), and three layouts are rendered with plan.thumbnail's words:
edit/thumbnail_1.jpg … _3.jpg (1280×720, under YouTube's 2 MB)."""
import subprocess
from pathlib import Path

import numpy as np

from .media import MediaError, probe, run_ffmpeg
from .paths import Episode
from .plan import load_plan

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


def person_png(video: Path, t: float, out: Path) -> Path:
    import cv2
    from .cutout import Matter
    frame = out.with_name(out.stem + "_frame.png")
    run_ffmpeg(["-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", str(frame)])
    img = cv2.imread(str(frame), cv2.IMREAD_COLOR)
    rgb = np.ascontiguousarray(img[:, :, ::-1])
    m = Matter()
    try:
        for _ in range(4):          # a still: let the video matting settle on it
            a = m(rgb)
        a = m.clean(a)
    finally:
        m.close()
    ys, xs = np.nonzero(a > 0.3)
    if len(xs) == 0:
        raise MediaError("ما لگيت الشخص بالفريم")
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([img, (a * 255).astype(np.uint8)])[y0:y1, x0:x1]
    cv2.imwrite(str(out), rgba)
    return out


def make_thumbnails(ep: Episode) -> list[Path]:
    from .graphics import RenderJob, _publish, _style_props, ensure_bundle, render_batch
    from .styles import load_style
    plan = load_plan(ep.plan)
    th = plan.thumbnail
    if not th.get("text"):
        raise MediaError("حط \"thumbnail\": {\"text\": \"...\"} بالخطة أول")
    times = best_frames(ep.clean_video)
    if not times:
        raise MediaError("ما لگيت فريم واضح للوجه")
    bundle = ensure_bundle(ep.work / "bundle")
    style = load_style(plan.style["primary"])
    pic = next(iter(sorted(ep.assets.glob("thumb_pic.*"))), None)
    jobs = []
    for k in range(3):
        person = person_png(ep.clean_video, times[k % len(times)], ep.work / f"thumb_person_{k}.png")
        props = {"style": _style_props(style), "durationSec": 1, "person": _publish(bundle, person), "text": th["text"],
                 "highlight": th.get("highlight", ""), "variant": k, **({"src": _publish(bundle, pic)} if pic else {})}
        jobs.append(RenderJob("thumbnail", props, ep.work / f"thumbnail_{k + 1}.png", 2 / 3, still=True))
    render_batch(jobs, bundle)
    outs = []
    for k, j in enumerate(jobs, 1):
        out = ep.edit / f"thumbnail_{k}.jpg"
        run_ffmpeg(["-i", str(j.out), "-q:v", "2", str(out)])
        outs.append(out)
    return outs
