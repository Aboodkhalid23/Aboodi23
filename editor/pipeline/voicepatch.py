"""A word he said wrong, said again in his own voice (owner, 2026-10-25: "صوتك يصلّح كلمة غلط").

The app makes each patch (ElevenLabs, his cloned voice: editor/app/dubbing.py fix_word) and lists it in
edit/voice_patches.json: [{"start", "end", "file"}] on the cleaned timeline. Here the patches go into one voice file:
the original is silenced over [start, end] and the new words, stretched to fit that window, are laid in.
compose uses that file instead of the cut video's sound. No key needed here."""
import json
import subprocess
from pathlib import Path

from .paths import Episode


def patches(ep: Episode) -> list[dict]:
    f = ep.edit / "voice_patches.json"
    try:
        return [p for p in json.loads(f.read_text(encoding="utf-8")) if (ep.edit / "voice" / p["file"]).is_file()]
    except (OSError, ValueError, KeyError):
        return []


def _dur(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def voice_source(ep: Episode) -> Path:
    """The cut video itself, or (when he fixed words) a voice file with the fixes laid in. Rebuilt only on change."""
    ps = patches(ep)
    if not ps:
        return ep.clean_video
    out = ep.work / "voice_patched.wav"
    key = json.dumps(ps, sort_keys=True) + str(ep.clean_video.stat().st_mtime)
    stamp = ep.work / "voice_patched.key"
    if out.exists() and stamp.exists() and stamp.read_text(encoding="utf-8") == key:
        return out
    args = ["ffmpeg", "-v", "error", "-y", "-i", str(ep.clean_video)]
    mute = "+".join(f"between(t,{p['start']:.3f},{p['end']:.3f})" for p in ps)
    graph = f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume='if({mute},0,1)':eval=frame[base]"
    mix = "[base]"
    for k, p in enumerate(ps, 1):
        src = ep.edit / "voice" / p["file"]
        want = max(0.2, p["end"] - p["start"])
        speed = min(2.0, max(0.5, _dur(src) / want)) if _dur(src) else 1.0
        ms = round(p["start"] * 1000)
        args += ["-i", str(src)]
        graph += (f";[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,atempo={speed:.3f},"
                  f"atrim=0:{want:.3f},afade=t=in:d=0.02,afade=t=out:st={max(0, want - 0.04):.3f}:d=0.04,adelay={ms}|{ms}[p{k}]")
        mix += f"[p{k}]"
    graph += f";{mix}amix=inputs={len(ps) + 1}:duration=first:normalize=0[out]"
    subprocess.run(args + ["-filter_complex", graph, "-map", "[out]", str(out)], check=True)
    stamp.write_text(key, encoding="utf-8")
    return out
