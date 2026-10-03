"""Sound effects synthesised with ffmpeg (no licences, no downloads), cached in editor/sfx/."""
import re
import subprocess
from pathlib import Path

from .media import run_ffmpeg

SFX_DIR = Path(__file__).resolve().parent.parent / "sfx"

# name -> (lavfi source, extra filter chain). Rendered mono 48 kHz, then peak-normalised to PEAK_DB.
RECIPES = {
    "whoosh": ("anoisesrc=color=pink:duration=0.45:sample_rate=48000",
               "bandpass=f=1200:width_type=o:w=2,afade=t=in:d=0.25:curve=exp,afade=t=out:st=0.25:d=0.2,volume=2.5"),
    "pop": ("sine=f=880:duration=0.09:sample_rate=48000",
            "afade=t=out:st=0.01:d=0.08:curve=exp,volume=0.8"),
    "click": ("anoisesrc=color=white:duration=0.025:sample_rate=48000",
              "highpass=f=2500,afade=t=out:st=0.004:d=0.02,volume=0.9"),
    "ding": ("sine=f=1320:duration=0.9:sample_rate=48000",
             "afade=t=out:st=0.02:d=0.88:curve=exp,volume=0.5"),
    "hit": ("sine=f=55:duration=0.6:sample_rate=48000",
            "afade=t=out:st=0.02:d=0.58:curve=exp,volume=1.4"),
    "riser": ("aevalsrc='0.4*sin(2*PI*(200+900*t*t/1.2)*t)':s=48000:d=1.2",
              "afade=t=in:d=1.0,afade=t=out:st=1.1:d=0.1"),
    "paper": ("anoisesrc=color=brown:duration=0.3:sample_rate=48000",
              "highpass=f=900,lowpass=f=6000,afade=t=in:d=0.03,afade=t=out:st=0.08:d=0.22,volume=2"),
    "glitch": ("anoisesrc=color=white:duration=0.22:sample_rate=48000",
               "bandpass=f=3000:w=800,apulsator=hz=28,afade=t=out:st=0.12:d=0.1,volume=1.2"),
}

PEAK_DB = -3.0

# Sound that goes with each transition / special beat when the plan names none.
TRANSITION_SFX = {"zoom": "whoosh", "whip": "whoosh", "flash": "hit", "glitch": "glitch"}


def sfx_path(name: str) -> Path:
    if name not in RECIPES:
        raise KeyError(f"صوت '{name}' مو موجود. الموجود: {', '.join(RECIPES)}")
    out = SFX_DIR / f"{name}.wav"
    if not out.exists():
        SFX_DIR.mkdir(parents=True, exist_ok=True)
        src, chain = RECIPES[name]
        raw, tmp = out.with_suffix(".raw.wav"), out.with_suffix(".partial.wav")
        run_ffmpeg(["-f", "lavfi", "-i", src, "-af", f"{chain},aformat=sample_rates=48000:channel_layouts=mono",
                    "-c:a", "pcm_f32le", str(raw)])
        gain = PEAK_DB - _peak_db(raw)
        run_ffmpeg(["-i", str(raw), "-af", f"volume={gain:.2f}dB", "-c:a", "pcm_s16le", str(tmp)])
        raw.unlink()
        tmp.rename(out)
    return out


def _peak_db(path: Path) -> float:
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"max_volume: (-?[\d.]+) dB", log)
    return float(m.group(1)) if m else 0.0


def beat_cues(beats, fx_cues: dict[str, list[tuple[float, str]]] | None = None) -> list[tuple[float, str]]:
    """(time on final timeline, sfx name) for every beat: explicit `sfx`, else its transition's sound,
    plus fixed cues inside special beats (subscribe click + bell, entity card pop)."""
    fx_cues = fx_cues or {}
    cues = []
    for b in beats:
        name = b.sfx or TRANSITION_SFX.get(b.transition or "")
        if name:
            cues.append((b.start, name))
        key = f"fx:{b.fx}" if b.kind == "face_fx" else b.kind
        cues += [(b.start + off, n) for off, n in fx_cues.get(key, [])]
    return sorted(cues)
