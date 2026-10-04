"""Colour correction only: levels, exposure and white balance measured from the footage, then a light
polish. Colours stay natural (owner's decision); skin never breaks (CRAFT.md §6)."""
import json
import re
import subprocess
from pathlib import Path

from .paths import Episode

# The owner's rule (2026-10-04): natural colours only — correct the footage, never restyle it.
# No film looks, no colour casts, no vignette, no grain.
# "natural" = measured correction + a light polish (a touch of clarity and of colour in dull areas).
# "none"    = the footage untouched.
LOOKS = {"natural": "", "none": ""}
POLISH = "vibrance=intensity=0.12,unsharp=5:5:0.35:5:5:0"   # vibrance lifts dull colours, leaves skin
SAMPLES = 12


def _stats(video: Path) -> dict:
    """Average YAVG / YLOW / YHIGH / UAVG / VAVG / SATAVG over ~SAMPLES frames spread over the video."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(video)], capture_output=True, text=True).stdout.strip() or 0)
    every = max(dur / SAMPLES, 0.5)
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                          f"fps=1/{every:.3f},scale=480:-2,signalstats,metadata=print:file=-", "-f", "null", "-"],
                         capture_output=True, text=True).stdout
    sums: dict[str, list[float]] = {}
    for key, val in re.findall(r"lavfi\.signalstats\.(YAVG|YLOW|YHIGH|UAVG|VAVG|SATAVG)=([\d.]+)", out):
        sums.setdefault(key, []).append(float(val))
    return {k: round(sum(v) / len(v), 2) for k, v in sums.items()}


def correction(stats: dict, face_luma: float | None = None) -> str:
    """Gentle automatic correction, bounded so a bad measurement can never wreck the picture."""
    if not stats:
        return ""
    lo, hi = (stats["YLOW"] - 16) / 219, (stats["YHIGH"] - 16) / 219
    # stretch 60% of the way to full range (keeps a little air at both ends)
    imin = min(max(lo * 0.6, 0.0), 0.12)
    imax = max(min(1 - (1 - hi) * 0.6, 1.0), 0.85)
    parts = [f"colorlevels=rimin={imin:.3f}:gimin={imin:.3f}:bimin={imin:.3f}:"
             f"rimax={imax:.3f}:gimax={imax:.3f}:bimax={imax:.3f}"]
    # exposure: bring the average towards ~0.45 with a gamma move of at most ±15%
    mean = (stats["YAVG"] - 16) / 219
    stretched = min(max((mean - imin) / max(imax - imin, 0.1), 0.05), 0.95)
    gamma = min(max(stretched / 0.45, 0.87), 1.15) ** 0.5
    if abs(gamma - 1) > 0.02:
        parts.append(f"eq=gamma={gamma:.3f}")
    # backlit face (bright window behind, dark face): lift the midtones where the face sits,
    # keep black black and white white, so the background never burns
    if face_luma is not None:
        face = min(max((face_luma - imin) / max(imax - imin, 0.1), 0.02), 0.98)
        if face < 0.42:
            target = min(face + 0.12, face * 1.35, 0.5)
            parts.append(f"curves=master='0/0 {face:.3f}/{target:.3f} 1/1'")
    # white balance: undo half of any colour cast in the averages (U = blue-yellow, V = red-cyan)
    du, dv = stats["UAVG"] - 128, stats["VAVG"] - 128
    if abs(du) > 2 or abs(dv) > 2:
        rm = max(min(-dv * 0.006, 0.06), -0.06)
        bm = max(min(-du * 0.006, 0.06), -0.06)
        parts.append(f"colorbalance=rm={rm:.3f}:bm={bm:.3f}")
    return ",".join(parts)


def analyse(ep: Episode) -> dict:
    """Measure the cleaned video once; cached in work/grade.json."""
    f = ep.work / "grade.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    from .face import face_info
    stats, face = _stats(ep.clean_video), face_info(ep)
    d = {"stats": stats, "face": face, "correction": correction(stats, face["luma"] if face else None)}
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


def grade_filter(correct: str, look: str | None) -> str:
    """',<filters>' to append to a chain (empty when there is nothing to do)."""
    look = look or "natural"
    if look not in LOOKS:
        raise KeyError(f"'{look}' مو موجود. الموجود: {', '.join(LOOKS)}")
    if look == "none":
        return ""
    parts = [p for p in (correct, POLISH) if p]
    return "," + ",".join(parts)
