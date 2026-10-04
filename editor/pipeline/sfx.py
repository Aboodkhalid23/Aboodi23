"""Sound effects: CC0 recordings in editor/sfx/library/<name>/ (Kenney, plus Freesound CC0 fetched the first
time a plan names a sound we don't have) and sounds synthesised with ffmpeg. No copyright on either. Normalised copies are cached as wav."""
import re
import subprocess
from pathlib import Path

from .media import run_ffmpeg

SFX_DIR = Path(__file__).resolve().parent.parent / "sfx"
LIBRARY = SFX_DIR / "library"
CACHE = SFX_DIR / "cache"

# name -> (lavfi source, extra filter chain). Rendered mono 48 kHz, then peak-normalised to PEAK_DB.
RECIPES = {
    "whoosh": ("anoisesrc=color=pink:duration=0.55:sample_rate=48000",
               "highpass=f=300,lowpass=f=5000,flanger=delay=6:depth=8:speed=2.5,"
               "afade=t=in:d=0.32:curve=qsin,afade=t=out:st=0.32:d=0.23:curve=exp"),
    "swoosh": ("anoisesrc=color=white:duration=0.28:sample_rate=48000",
               "bandpass=f=2500:width_type=o:w=1.5,flanger=delay=3:depth=5:speed=6,"
               "afade=t=in:d=0.12:curve=qsin,afade=t=out:st=0.12:d=0.16:curve=exp"),
    "boom": ("aevalsrc='0.9*sin(2*PI*(70-30*t)*t)*exp(-3*t)':s=48000:d=1.4",
             "lowpass=f=180,afade=t=out:st=0.9:d=0.5"),
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
TRANSITION_SFX = {"zoom": "whoosh", "whip": "swoosh", "flash": "hit", "glitch": "glitch", "tear": "paper",
                  "burn": "whoosh", "dive": "whoosh", "pan": "swoosh"}


def variants(name: str) -> list[Path]:
    """Recorded takes of a sound (several, so repeats don't sound copy-pasted)."""
    d = LIBRARY / name
    return sorted(p for p in d.glob("*") if p.suffix.lower() in (".ogg", ".wav", ".mp3", ".flac")) if d.is_dir() else []


def names() -> list[str]:
    return sorted(set(RECIPES) | {d.name for d in LIBRARY.iterdir() if d.is_dir() and variants(d.name)})


def sfx_path(name: str, variant: int = 0) -> Path:
    """Normalised wav of `name`: recorded take number `variant` (wrapping), else the synthesised one."""
    takes = variants(name)
    if not takes and name not in RECIPES:   # a sound we don't have yet: free CC0 recordings, kept for next time
        from .free_audio import fetch_sfx
        takes = fetch_sfx(name, LIBRARY) and variants(name)
    if not takes and name not in RECIPES:
        raise KeyError(f"صوت '{name}' مو موجود. الموجود: {', '.join(names())}")
    take = takes[variant % len(takes)] if takes else None
    out = CACHE / (f"{name}_{take.stem}.wav" if take else f"{name}.wav")
    if not out.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        raw, tmp = out.with_suffix(".raw.wav"), out.with_suffix(".partial.wav")
        if take:
            src = ["-i", str(take), "-af", "aformat=sample_rates=48000:channel_layouts=mono"]
        else:
            lavfi, chain = RECIPES[name]
            src = ["-f", "lavfi", "-i", lavfi, "-af", f"{chain},aformat=sample_rates=48000:channel_layouts=mono"]
        run_ffmpeg([*src, "-c:a", "pcm_f32le", str(raw)])
        gain = PEAK_DB - _peak_db(raw)
        for _ in range(3):   # re-measure: decoders and resamplers move the peak a little
            run_ffmpeg(["-i", str(raw), "-af", f"volume={gain:.2f}dB", "-c:a", "pcm_s16le", str(tmp)])
            miss = PEAK_DB - _peak_db(tmp)
            if abs(miss) < 0.3:
                break
            gain += miss
        raw.unlink()
        tmp.rename(out)
    return out


def _peak_db(path: Path) -> float:
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af",
                          "astats=measure_overall=Peak_level:measure_perchannel=none", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"Peak level dB: (-?[\d.]+|-inf)", log)
    return float(m.group(1)) if m and m.group(1) != "-inf" else PEAK_DB


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
