"""Measure a reference video the way an editor would study it (owner, 2026-10-29: "تحلل الفيديو نقطة نقطة… تفهم الموشن
شلون يتحرك، الفديوات شلون تمشي"), with numbers instead of guesses, so a style can be rebuilt from them:

  shots     every cut (scene change), shot lengths, the rhythm over time
  motion    per shot, from optical flow: push-in / pull-out speed, pan, parallax (layers moving differently), still
  look      per shot: black and white or colour, brightness, contrast
  sound     loudness, the transients (hits, whooshes, clicks) and how many cuts land on one, quiet gaps
  sheet     a contact strip of every shot (first, middle, last frame) to look at the layouts quickly

  python3 scripts/analyze_reference.py VIDEO [OUT_DIR]   → OUT_DIR/<name>.json, <name>_shots.jpg
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

FPS = 12          # analysis frame rate: enough for cuts of 2 frames at 24 fps, cheap
SW, SH = 192, 108


def frames(video: Path, w: int, h: int, fps: int = FPS, gray: bool = False) -> np.ndarray:
    pix = "gray" if gray else "rgb24"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                          f"fps={fps},scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
                          "-f", "rawvideo", "-pix_fmt", pix, "-"], capture_output=True).stdout
    c = 1 if gray else 3
    n = len(raw) // (w * h * c)
    a = np.frombuffer(raw[: n * w * h * c], np.uint8)
    return a.reshape(n, h, w) if gray else a.reshape(n, h, w, 3)


def probe(video: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height,r_frame_rate:format=duration",
                          "-of", "json", str(video)], capture_output=True, text=True).stdout
    d = json.loads(out)
    v = next(s for s in d["streams"] if "width" in s)
    return {"w": v["width"], "h": v["height"], "fps": v["r_frame_rate"], "duration": float(d["format"]["duration"])}


# ---------- cuts ----------

def cuts(rgb: np.ndarray) -> list[int]:
    """Frame indices where a new shot starts: colour histogram jump well above the local level."""
    hists = []
    for f in rgb:
        hsv = np.stack([np.histogram(f[..., k], bins=16, range=(0, 256))[0] for k in range(3)]).astype(np.float32)
        hists.append(hsv / max(1, hsv.sum()))
    hists = np.array(hists)
    d = np.abs(np.diff(hists, axis=0)).sum(axis=(1, 2))           # 0..2
    px = np.abs(np.diff(rgb.astype(np.int16), axis=0)).mean(axis=(1, 2, 3)) / 255
    score = d + px * 2
    out = [0]
    for i, s in enumerate(score):
        lo, hi = max(0, i - 6), min(len(score), i + 7)
        local = np.median(score[lo:hi])
        if s > max(0.35, local * 3.0) and i + 1 - out[-1] >= 2:
            out.append(i + 1)
    return out


# ---------- motion ----------

def motion(gray: np.ndarray) -> dict:
    """Mean optical flow over a shot: zoom (%/s, + = push in), pan (frame widths/s), parallax, shake."""
    import cv2
    if len(gray) < 3:
        return {"zoom": 0.0, "pan_x": 0.0, "pan_y": 0.0, "parallax": 0.0, "shake": 0.0, "kind": "still"}
    h, w = gray.shape[1:]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rx, ry = xx - w / 2, yy - h / 2
    rn = np.sqrt(rx ** 2 + ry ** 2) + 1e-3
    zs, px, py, par, mags = [], [], [], [], []
    for a, b in zip(gray[:-1], gray[1:]):
        f = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        fx, fy = f[..., 0], f[..., 1]
        radial = (fx * rx + fy * ry) / rn                   # outward flow = the picture grows = push in
        zs.append(float(np.median(radial / rn)))            # per frame scale change
        px.append(float(np.median(fx)) / w)
        py.append(float(np.median(fy)) / h)
        mag = np.sqrt((fx - np.median(fx)) ** 2 + (fy - np.median(fy)) ** 2)
        mags.append(float(mag.mean()))
        # parallax: the middle of the frame moves differently from the edges (a cut-out over a background)
        cm = np.sqrt(fx[h // 4: 3 * h // 4, w // 4: 3 * w // 4].mean() ** 2 + fy[h // 4: 3 * h // 4, w // 4: 3 * w // 4].mean() ** 2)
        em = np.sqrt(np.concatenate([fx[:, : w // 6].ravel(), fx[:, -w // 6:].ravel()]).mean() ** 2)
        par.append(float(abs(cm - em)))
    zoom = float(np.mean(zs)) * FPS * 100
    pan_x, pan_y = float(np.mean(px)) * FPS, float(np.mean(py)) * FPS
    shake = float(np.std(px) * FPS + np.std(py) * FPS)
    kind = "still"
    if abs(zoom) > 1.2:
        kind = "push-in" if zoom > 0 else "pull-out"
    if abs(pan_x) > 0.03 and abs(pan_x) * 100 > abs(zoom):
        kind = "pan-left" if pan_x < 0 else "pan-right"
    if abs(pan_y) > 0.03 and abs(pan_y) > abs(pan_x) and abs(pan_y) * 100 > abs(zoom):
        kind = "tilt-up" if pan_y < 0 else "tilt-down"
    if np.mean(mags) > 1.2 and kind == "still":
        kind = "inner-motion"          # things move inside a still frame (footage, animation)
    return {"zoom": round(zoom, 2), "pan_x": round(pan_x, 3), "pan_y": round(pan_y, 3),
            "parallax": round(float(np.mean(par)), 3), "shake": round(shake, 3), "activity": round(float(np.mean(mags)), 2),
            "kind": kind}


# ---------- look ----------

def look(rgb: np.ndarray) -> dict:
    f = rgb.astype(np.float32) / 255
    mx, mn = f.max(axis=-1), f.min(axis=-1)
    sat = float(np.mean((mx - mn) / (mx + 1e-4)))
    lum = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
    warm = float(np.mean(f[..., 0] - f[..., 2]))
    return {"saturation": round(sat, 3), "bw": sat < 0.08, "brightness": round(float(lum.mean()), 3),
            "contrast": round(float(lum.std()), 3), "warmth": round(warm, 3)}


# ---------- sound ----------

def sound(video: Path, cut_times: list[float]) -> dict:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    if len(x) < 16000:
        return {}
    hop = 160                                                            # 10 ms
    n = len(x) // hop
    fr = x[: n * hop].reshape(n, hop)
    rms = np.sqrt((fr ** 2).mean(axis=1)) + 1e-6
    db = 20 * np.log10(rms)
    # high band energy (whooshes, clicks, paper, hits live above the voice)
    hp = np.abs(np.diff(x[: n * hop]))
    hf = np.sqrt((np.concatenate([hp, [0]]).reshape(n, hop) ** 2).mean(axis=1)) + 1e-6
    onset = np.maximum(0, np.diff(20 * np.log10(hf), prepend=-120))
    thr = np.median(onset) + 3.5 * onset.std()
    peaks = [i for i in range(1, n - 1) if onset[i] > thr and onset[i] >= onset[i - 1] and onset[i] >= onset[i + 1]]
    hits = []
    for p in peaks:
        if not hits or p - hits[-1] > 15:
            hits.append(p)
    hit_t = np.array(hits) * 0.01
    on_cut = sum(1 for c in cut_times[1:] if len(hit_t) and np.min(np.abs(hit_t - c)) < 0.08)
    quiet = (db < np.percentile(db, 95) - 35).mean()
    lufs = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "ebur128", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    il = [ln for ln in lufs.splitlines() if ln.strip().startswith("I:")]
    lra = [ln for ln in lufs.splitlines() if ln.strip().startswith("LRA:")]
    return {"lufs": il[-1].split()[1] if il else None, "lra": lra[-1].split()[1] if lra else None,
            "transients": len(hits), "transients_per_min": round(len(hits) / (n / 6000), 1),
            "cuts_on_a_transient": f"{on_cut}/{max(0, len(cut_times) - 1)}", "quiet_share": round(float(quiet), 3),
            "hit_times": [round(float(t), 2) for t in hit_t[:200]]}


# ---------- all ----------

def analyse(video: Path, out_dir: Path) -> dict:
    from PIL import Image
    info = probe(video)
    vw, vh = (SW, SH) if info["w"] >= info["h"] else (SH, SW)
    rgb = frames(video, vw, vh)
    gray = frames(video, vw, vh, gray=True)
    starts = cuts(rgb)
    ends = starts[1:] + [len(rgb)]
    shots = []
    for s, e in zip(starts, ends):
        m = motion(gray[s:e])
        lk = look(rgb[s:e])
        shots.append({"start": round(s / FPS, 2), "length": round((e - s) / FPS, 2), **m, **lk})
    lens = np.array([x["length"] for x in shots])
    kinds = {}
    for x in shots:
        kinds[x["kind"]] = kinds.get(x["kind"], 0) + 1
    snd = sound(video, [x["start"] for x in shots])
    summary = {
        "video": video.name, **info, "shots": len(shots),
        "shot_length": {"mean": round(float(lens.mean()), 2), "median": round(float(np.median(lens)), 2),
                        "min": round(float(lens.min()), 2), "max": round(float(lens.max()), 2)},
        "cuts_per_10s_over_time": [int(((np.array([x['start'] for x in shots]) >= t) & (np.array([x['start'] for x in shots]) < t + 10)).sum())
                                   for t in range(0, int(info["duration"]) + 1, 10)],
        "motion_kinds": kinds,
        "mean_zoom_when_moving": round(float(np.mean([abs(x["zoom"]) for x in shots if x["kind"] in ("push-in", "pull-out")] or [0])), 2),
        "bw_share": round(float(np.mean([x["bw"] for x in shots])), 2),
        "sound": {k: v for k, v in snd.items() if k != "hit_times"},
    }
    # contact strip: first / middle / last frame of every shot
    big = frames(video, vw * 2, vh * 2, fps=FPS)
    tiles = []
    for s, e in zip(starts, ends):
        for i in (s, (s + e - 1) // 2, e - 1):
            tiles.append(Image.fromarray(big[min(i, len(big) - 1)]))
    cols = 9
    tw, th = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 4), rows * (th + 4)), (255, 255, 255))
    for k, t in enumerate(tiles):
        sheet.paste(t, ((k % cols) * (tw + 4), (k // cols) * (th + 4)))
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = video.stem[:12]
    sheet.save(out_dir / f"{stem}_shots.jpg", quality=80)
    (out_dir / f"{stem}.json").write_text(json.dumps({"summary": summary, "shots": shots, "hits": snd.get("hit_times", [])},
                                                     ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


if __name__ == "__main__":
    video = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("reference_scan")
    print(json.dumps(analyse(video, out), ensure_ascii=False, indent=1))
