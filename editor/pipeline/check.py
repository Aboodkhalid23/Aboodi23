"""Right after the download: show the owner what was fetched (length, quality, a few frames, the first
words) so he confirms it is the right episode before any work or money is spent on it."""
import json
import subprocess
from pathlib import Path

from .media import probe
from .paths import Episode


def _hms(t: float) -> str:
    h, rest = divmod(int(round(t)), 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def contact_sheet(video: Path, out: Path, duration: float, n: int = 6) -> Path:
    """n frames spread over the video, with their time stamps, in one picture."""
    frames = []
    for i in range(n):
        t = duration * (i + 0.5) / n
        f = out.with_name(f"{out.stem}_{i}.jpg")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-vf",
                        f"scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2,"
                        f"drawtext=text='{_hms(t)}':x=12:y=12:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.6",
                        str(f)], check=True)
        frames.append(f)
    inputs = sum((["-i", str(f)] for f in frames), [])
    cols = 3
    layout = "|".join(f"{(i % cols) * 640}_{(i // cols) * 360}" for i in range(n))
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex",
                    f"xstack=inputs={n}:layout={layout}", "-frames:v", "1", str(out)], check=True)
    for f in frames:
        f.unlink()
    return out


def first_words(ep: Episode, seconds: float = 40.0, model=None) -> str:
    """What he says at the start (Whisper on the first `seconds` only — quick)."""
    clip = ep.work / "check_start.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(ep.source), "-t", str(seconds), "-vn", "-ac", "1",
                    "-ar", "16000", str(clip)], check=True)
    if model is None:
        from faster_whisper import WhisperModel
        model = WhisperModel("large-v3", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(str(clip), language="ar", vad_filter=True)
    text = " ".join(s.text.strip() for s in segs).strip()
    clip.unlink()
    return text


def check_source(ep: Episode, words: bool = True, model=None) -> dict:
    info = probe(ep.source)
    rec = ep.work / "source.json"
    raw = json.loads(rec.read_text(encoding="utf-8")) if rec.exists() else {}
    d = {"name": raw.get("name", ""), "duration": round(info.duration, 1), "length": _hms(info.duration),
         "width": raw.get("raw_width", info.width), "height": raw.get("raw_height", info.height),
         "fps": raw.get("raw_fps", info.fps), "has_audio": info.has_audio, "size_mb": raw.get("raw_size_mb"),
         "fetched_at": raw.get("fetched_at", ""), "frames": str(ep.work / "source_check.jpg")}
    contact_sheet(ep.source, ep.work / "source_check.jpg", info.duration)
    if words and info.has_audio:
        d["first_words"] = first_words(ep, model=model)
    (ep.work / "source_check.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d
