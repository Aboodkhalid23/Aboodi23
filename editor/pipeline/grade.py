"""Colour: correct the footage first (levels, exposure, white balance), then a film look, then finish
(vignette + fine grain). CRAFT.md §6: correction before style, skin never breaks."""
import json
import re
import subprocess
from pathlib import Path

from .paths import Episode

# Looks applied after correction. All keep skin warm (no hue shifts in the midtones' red channel).
LOOKS = {
    "clean": "",
    # teal shadows, warm highlights, gentle S-curve: the "YouTube documentary" look
    "cinematic": ("colorbalance=rs=-0.05:gs=-0.01:bs=0.06:rh=0.05:gh=0.015:bh=-0.05,"
                  "curves=master='0/0.02 0.25/0.22 0.5/0.5 0.75/0.78 1/0.98',eq=saturation=1.04"),
    # warm, soft, slightly faded blacks: stories, nostalgia
    "warm": ("colorbalance=rs=0.03:bs=-0.03:rm=0.03:bm=-0.03:rh=0.02:bh=-0.03,"
             "curves=master='0/0.04 0.5/0.52 1/0.97',eq=saturation=1.02"),
    # film stock: lifted blacks, rolled highlights, muted colour, visible grain
    "film": ("curves=master='0/0.06 0.3/0.29 0.7/0.73 1/0.93',"
             "colorbalance=rs=0.02:bs=-0.02:rh=0.03:bh=-0.04,eq=saturation=0.86"),
    # cold and tense: investigations, crime
    "cold": ("colorbalance=rs=-0.04:bs=0.05:rm=-0.02:bm=0.03,"
             "curves=master='0/0 0.25/0.2 0.75/0.8 1/1',eq=saturation=0.9"),
    # black and white, punchy: flashbacks, archive moments
    "noir": "hue=s=0,curves=master='0/0 0.3/0.22 0.7/0.8 1/1'",
}
GRAIN = {"film": 9, "noir": 10}   # other looks get a fine 4
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


def correction(stats: dict) -> str:
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
    # white balance: undo half of any colour cast in the averages (U = blue-yellow, V = red-cyan)
    du, dv = stats["UAVG"] - 128, stats["VAVG"] - 128
    if abs(du) > 2 or abs(dv) > 2:
        rm = max(min(-dv * 0.006, 0.06), -0.06)
        bm = max(min(-du * 0.006, 0.06), -0.06)
        parts.append(f"colorbalance=rm={rm:.3f}:bm={bm:.3f}")
    if stats.get("SATAVG", 20) < 10:   # washed out: lift the dull colours, leave saturated ones (skin) alone
        parts.append("vibrance=intensity=0.18")
    return ",".join(parts)


def analyse(ep: Episode) -> dict:
    """Measure the cleaned video once; cached in work/grade.json."""
    f = ep.work / "grade.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    stats = _stats(ep.clean_video)
    d = {"stats": stats, "correction": correction(stats)}
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


def grade_filter(correct: str, look: str | None) -> str:
    """',<filters>' to append to a chain (empty when there is nothing to do)."""
    look = look or "clean"
    if look not in LOOKS:
        raise KeyError(f"لون '{look}' مو موجود. الموجود: {', '.join(LOOKS)}")
    parts = [p for p in (correct, LOOKS[look]) if p]
    if look != "clean":
        parts.append("vignette=angle=PI/5:mode=forward")
        parts.append(f"noise=alls={GRAIN.get(look, 4)}:allf=t")
    return "," + ",".join(parts) if parts else ""
