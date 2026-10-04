"""Wipe transitions that need the clip before them (from the owner's references, update 1): the new
shot tears in through a ragged white paper edge (`tear`), or the old shot burns away from a glowing,
charred edge (`burn`). The edge runs right → left, the way Arabic reads. Done after all clips exist,
re-encoding only the clip that enters."""
import hashlib
from pathlib import Path

from .media import run_ffmpeg

WIPES = ("tear", "burn")
DUR = 0.5          # seconds the edge takes to cross the frame


def _dist(kind: str) -> str:
    """Signed distance (px) of pixel X from the edge on row Y at time T: > 0 = the new shot. The edge
    starts past the right side and leaves past the left. (No st()/ld(): blend runs on several threads
    that would share those variables.)"""
    if kind == "tear":   # ragged, fine-toothed paper
        jag = "W*(0.012*sin(Y/53)+0.008*sin(Y/19+1)+0.004*sin(Y/6.1+2)+0.0025*sin(Y/2.3))"
    else:                # wavy, flickering fire line
        jag = "W*0.03*(sin(Y/41+T*9)+0.5*sin(Y/13+2)+0.3*sin(Y/5+T*25))"
    return f"(X-W*(1.12-1.24*min(T/{DUR},1))-{jag})"


def wipe_filter(kind: str) -> str:
    """blend options on gbrp planes (c0 = G, c1 = B, c2 = R); top = incoming clip, bottom = old frame."""
    d = _dist(kind)
    if kind == "tear":
        edge = "W*0.012"        # white paper margin of the torn sheet
        shade = "W*0.03"        # soft shadow the sheet casts on the new shot
        expr = f"if(gt({d},0),A*(0.72+0.28*min({d}/({shade}),1)),if(gt({d},-{edge}),246,B))"
        return f"all_expr='{expr}'"
    g = f"(1+{d}/(W*0.05))"     # 1 at the flame front → 0 inside the old frame
    hot = {"c2": "255", "c0": f"110+230*({g}-0.6)", "c1": "25"}    # R, G, B of the flame
    char = {"c2": "38", "c0": "18", "c1": "10"}                      # charred paper
    return ":".join(f"{c}_expr='if(gt({d},0),A,if(gt({g},0.6),{hot[c]},if(gt({g},0.2),{char[c]},B)))'"
                    for c in ("c0", "c1", "c2"))


def apply_wipe(kind: str, prev: Path, clip: Path, out: Path, width: int, height: int, fps: int,
               encode: list[str]) -> Path:
    """`clip` with its first DUR seconds wiping in over the last frame of `prev`."""
    key = hashlib.sha1(f"{kind}|{prev.stat().st_mtime}|{prev.stat().st_size}|{clip.stat().st_mtime}|"
                       f"{clip.stat().st_size}|{wipe_filter(kind)}".encode()).hexdigest()
    stamp = out.with_suffix(".hash")
    if out.exists() and stamp.exists() and stamp.read_text() == key:
        return out
    last = out.with_name(out.stem + "_last.png")
    run_ffmpeg(["-sseof", "-0.3", "-i", str(prev), "-update", "1", "-frames:v", "8", str(last)])
    run_ffmpeg(["-i", str(clip), "-loop", "1", "-framerate", str(fps), "-i", str(last), "-filter_complex",
                f"[0:v]format=gbrp,setsar=1[a];[1:v]scale={width}:{height},format=gbrp,setsar=1[b];"
                f"[a][b]blend={wipe_filter(kind)}:shortest=1,format=yuv420p",
                "-an", *encode, str(out)])
    stamp.write_text(key)
    return out
