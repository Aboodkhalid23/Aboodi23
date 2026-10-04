"""Mandatory self-check before anything is sent (CRAFT.md §8): technical checks on the finished file and
contact sheets with one labelled frame from the middle of every beat, so Claude reviews every scene."""
import json
import re
import subprocess
from pathlib import Path

from .media import probe
from .paths import Episode
from .plan import load_plan

PER_SHEET = 30          # beats per contact sheet (6 × 5 tiles)
TILE = (384, 216)


def _loudness(video: Path) -> tuple[float | None, float | None]:
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vn", "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", log)
    return (float(i[-1]) if i else None, float(tp[-1]) if tp else None)


def _black(video: Path) -> list[tuple[float, float]]:
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf", "blackdetect=d=0.4:pix_th=0.08",
                          "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    return [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log)]


def _ts(t: float) -> str:
    m, s = divmod(int(t), 60)
    return f"{m}:{s:02d}"


def contact_sheets(video: Path, beats, out_dir: Path) -> list[Path]:
    sheets = []
    w, h = TILE
    for n in range(0, len(beats), PER_SHEET):
        group = beats[n:n + PER_SHEET]
        tiles = []
        for k, b in enumerate(group):
            i = n + k
            t = (b.start + b.end) / 2
            label = f"{i} {b.kind}{'/' + b.fx if b.fx else ''} {_ts(t)}".replace(":", "\\:")
            f = out_dir / f"qa_tile_{i}.jpg"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-vf",
                            f"scale={w}:{h},drawtext=text='{label}':x=6:y=6:fontsize=18:fontcolor=white:"
                            "box=1:boxcolor=black@0.6", str(f)], check=True)
            tiles.append(f)
        cols = 5
        while len(tiles) % cols:   # pad the last row with black
            pad = out_dir / f"qa_pad_{len(tiles)}.jpg"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=black:s={w}x{h}", "-frames:v", "1",
                            str(pad)], check=True)
            tiles.append(pad)
        inputs = sum((["-i", str(f)] for f in tiles), [])
        layout = "|".join(f"{(i % cols) * w}_{(i // cols) * h}" for i in range(len(tiles)))
        sheet = out_dir / f"qa_sheet_{n // PER_SHEET + 1}.jpg"
        subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex",
                        f"xstack=inputs={len(tiles)}:layout={layout}", "-frames:v", "1", str(sheet)], check=True)
        for f in tiles:
            f.unlink()
        sheets.append(sheet)
    return sheets


def qa(ep: Episode, preview: bool = False) -> dict:
    video = ep.edit / "preview.mp4" if preview else ep.final
    plan = load_plan(ep.plan)
    info = probe(video)
    expected = plan.beats[-1].end
    lufs, peak = _loudness(video) if info.has_audio else (None, None)
    issues = []
    if abs(info.duration - expected) > 0.2:
        issues.append(f"المدة {info.duration:.1f} ث والخطة {expected:.1f} ث")
    if not info.has_audio:
        issues.append("الفيديو ما بيه صوت")
    elif lufs is None or not -16 <= lufs <= -12:
        issues.append(f"مستوى الصوت {lufs} LUFS (المطلوب قريب من −14)")
    if peak is not None and peak > -0.5:
        issues.append(f"ذروة الصوت عالية ({peak} dBFS)")
    blacks = _black(video)
    if blacks:
        issues.append("فريمات سودة: " + "، ".join(f"{_ts(a)}–{_ts(b)}" for a, b in blacks[:5]))
    sheets = contact_sheets(video, plan.beats, ep.work)
    d = {"video": str(video), "duration": round(info.duration, 2), "size": f"{info.width}x{info.height}",
         "fps": info.fps, "lufs": lufs, "peak": peak, "issues": issues, "sheets": [str(s) for s in sheets]}
    (ep.work / "qa.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d
