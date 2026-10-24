"""Colour correction only: levels, exposure and white balance measured from the footage, then a light
polish. Colours stay natural (owner's decision); skin never breaks (CRAFT.md §6)."""
import json
import re
import subprocess
from pathlib import Path

from .paths import Episode

# The owner's rule (2026-10-04): natural colours — correct the footage. Updated 2026-10-22: a light cinematic
# touch is wanted by default ("cinema"); still no heavy filters or old-film colours.
# "natural" = measured correction + a light polish (a touch of clarity and of colour in dull areas).
# "none"    = the footage untouched.
# "cinema"  = (owner, 2026-10-22: "لمسة خفيفة من الأفلام، كأنك داخل فيلم نتفليكس") the correction, then a gentle
#             film look: soft S-curve with lifted blacks and rolled-off highlights, shadows a touch cooler and
#             highlights a touch warmer (skin in the mids stays itself), a whisper of saturation, light
#             denoise instead of sharpening (smooth, not plastic), fine moving grain and a faint vignette.
LOOKS = {"natural": "", "none": "",
         "cinema": ("curves=master='0/0.025 0.25/0.215 0.5/0.5 0.75/0.785 1/0.975',"
                    "colorbalance=rs=-0.025:bs=0.035:rh=0.035:gh=0.008:bh=-0.03,"
                    "eq=saturation=1.05,hqdn3d=1.2:1.2:2.5:2.5,noise=alls=3:allf=t,vignette=angle=0.42")}
# Looks the owner picks in the Mac app before preparing a clip (owner, 2026-10-24: "نفس الاستوديو"). All made of
# ffmpeg filters (ours, free). "log" and "log-vivid" turn flat/log footage (DJI D-Log, phone "Log") into normal
# contrast and colour; the film looks are gentle and keep skin believable.
LOOKS.update({
    "log": "curves=master='0/0 0.18/0.12 0.5/0.52 0.82/0.9 1/1',eq=saturation=1.35:contrast=1.06",
    "log-vivid": "curves=master='0/0 0.2/0.1 0.5/0.53 0.8/0.93 1/1',eq=saturation=1.6:contrast=1.08,vibrance=intensity=0.15",
    "warm-film": ("curves=r='0/0.02 0.5/0.53 1/0.98':g='0/0.01 0.5/0.5 1/0.96':b='0/0.06 0.5/0.46 1/0.9',"
                  "eq=saturation=0.95,noise=alls=4:allf=t"),
    "soft-film": "curves=master='0/0.04 0.5/0.5 1/0.95',colorbalance=gs=0.03:bs=0.02:rh=0.02,eq=saturation=0.88",
    "teal-orange": "colorbalance=rs=-0.08:bs=0.08:rh=0.08:bh=-0.06,eq=saturation=1.1:contrast=1.05",
    "mono": "hue=s=0,curves=master='0/0.03 0.5/0.5 1/0.97'",
})
LOOK_NAMES = {"none": "بدون تحويل", "natural": "طبيعي", "cinema": "سينما", "log": "لوگ ← عادي",
              "log-vivid": "لوگ ← حيوي", "warm-film": "فلم دافي", "soft-film": "فلم ناعم",
              "teal-orange": "سينما أكشن", "mono": "أبيض وأسود"}
CINEMA_POLISH = "vibrance=intensity=0.08,unsharp=5:5:0.15:5:5:0"   # softer than POLISH: the film look is smooth
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


def adjust_filter(temp: float = 0, tint: float = 0, exposure: float = 0) -> str:
    """The app's balance sliders: temperature and tint (−100…100) and exposure (stops, −2…2)."""
    parts = []
    if temp or tint:
        rm, bm, gm = temp * 0.0015, -temp * 0.0015, -tint * 0.0015
        parts.append(f"colorbalance=rm={rm:.4f}:gm={gm:.4f}:bm={bm:.4f}")
    if exposure:
        parts.append(f"exposure=exposure={exposure:.3f}")
    return ",".join(parts)


def look_settings(ep: Episode) -> dict:
    """What the owner chose in the app (edit/look.json): {"look", "lut", "temp", "tint", "exposure"}; {} if none."""
    f = ep.edit / "look.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def grade_filter(correct: str, look: str | None, extra: str = "", lut: str | None = None) -> str:
    """',<filters>' to append to a chain (empty when there is nothing to do). `extra`: the app's balance sliders;
    `lut`: a .cube file the owner added (replaces the look)."""
    look = look or "natural"
    if look not in LOOKS:
        raise KeyError(f"'{look}' مو موجود. الموجود: {', '.join(LOOKS)}")
    if lut:
        parts = [p for p in (correct, "lut3d=file='" + str(lut).replace("'", "") + "'") if p]
    elif look == "none":
        parts = []
    elif look == "cinema":
        parts = [p for p in (correct, CINEMA_POLISH, LOOKS["cinema"]) if p]
    else:
        parts = [p for p in (correct, POLISH, LOOKS[look]) if p]
    parts += [extra] if extra else []
    return "," + ",".join(parts) if parts else ""
