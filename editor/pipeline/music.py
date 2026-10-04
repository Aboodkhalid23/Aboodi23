"""Music. Free first (free_audio.music-free, owner's rule); a cue nothing free fits can be made by AI:
Claude generates it with
Artlist (Lyria 3 Pro, instrumental), `music-fetch` downloads it, compose lays the bed under the voice.

plan.music = [{"t": 0, "prompt": "slow mysterious pulse, light piano", "genre": "cinematic", "mood": "mysterious",
               "tempo": "slow_med"}, {"t": 312.0, ...}]   # t on the final timeline; each plays until the next
"""
import json
import math
import subprocess
from pathlib import Path

import requests

from .media import MediaError
from .paths import Episode
from .plan import load_plan
from .styles import load_style

MODEL_ID = 2285                    # Artlist "Lyria 3 Pro - T2M - Instrumental"
DURATIONS = (60, 90, 120, 180)     # Artlist duration options (seconds)
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg")


def audio_duration(path: Path) -> float:
    proc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                           "stream=duration:format=duration", "-of", "json", str(path)], capture_output=True, text=True)
    if proc.returncode != 0:
        raise MediaError(f"الملف {path} مو صوت")
    d = json.loads(proc.stdout)
    if not d.get("streams"):
        raise MediaError(f"الملف {path} ما بيه صوت")
    return float(d["streams"][0].get("duration") or d.get("format", {}).get("duration") or 0)


def music_asset(ep: Episode, k: int) -> Path | None:
    return next((p for p in sorted(ep.assets.glob(f"music_{k}.*")) if p.suffix.lower() in AUDIO_EXT), None)


def segments(plan, total: float) -> list[tuple[int, float, float]]:
    """(cue index, start, end) on the final timeline."""
    ts = [m["t"] for m in plan.music]
    return [(k, t, ts[k + 1] if k + 1 < len(ts) else total) for k, t in enumerate(ts)]


def music_jobs(ep: Episode, total: float) -> list[dict]:
    plan = load_plan(ep.plan)
    mood = load_style(plan.style["primary"]).music_mood
    jobs = []
    for k, start, end in segments(plan, total):
        m = plan.music[k]
        need = end - start
        have = music_asset(ep, k)
        jobs.append({
            "cue": k, "start": round(start, 2), "seconds": round(need, 1), "model_id": MODEL_ID,
            "prompt": f"{(m.get('prompt') or m.get('search', '')).rstrip('. ')}. Background score for a documentary voice-over: {mood}. "
                      "Instrumental, no vocals, steady, leaves room for speech.",
            "settings": {"song_type": "instrumental", "song_theme": "documentary",
                         "duration": str(next((d for d in DURATIONS if d >= need), DURATIONS[-1])),
                         "song_genre": m.get("genre", "cinematic"), "song_mood": m.get("mood", "auto"),
                         "song_tempo": m.get("tempo", "auto")},
            "asset": str(have or ep.assets / f"music_{k}.mp3"), "done": have is not None,
        })
    (ep.work / "music_jobs.json").write_text(json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")
    return jobs


def music_fetch(ep: Episode, cue: int, url: str, session=None) -> Path:
    session = session or requests.Session()
    try:
        resp = session.get(url, timeout=300)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise MediaError(f"ما گدرت أنزّل الموسيقى: {exc}") from exc
    ctype = resp.headers.get("Content-Type", "").split(";")[0]
    ext = {"audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/mp4": ".m4a",
           "audio/ogg": ".ogg", "audio/flac": ".flac"}.get(ctype) or Path(url.split("?")[0]).suffix.lower()
    ext = ext if ext in AUDIO_EXT else ".mp3"
    for old in ep.assets.glob(f"music_{cue}.*"):
        old.unlink()
    out = ep.assets / f"music_{cue}{ext}"
    out.write_bytes(resp.content)
    try:
        audio_duration(out)
    except MediaError:
        out.unlink()
        raise MediaError(f"الملف الي نزل مو موسيقى ({ctype or 'نوع غير معروف'})")
    return out


XFADE = 2.0   # seconds of crossfade between loops of one track and between cues


def bed_filter(inputs: list[tuple[int, Path, float, float]], first_input: int, lufs: float) -> tuple[list[str], str]:
    """ffmpeg args + filter graph producing [mus] from (cue, file, start, end) segments.
    A track shorter than its segment is repeated with crossfades (no audible loop seam)."""
    args, graph, labels = [], [], []
    n = first_input
    for cue, path, start, end in inputs:
        need = end - start + (XFADE if end > start else 0)
        dur = audio_duration(path)
        copies = 1 if dur >= need else math.ceil((need - XFADE) / max(dur - XFADE, 1.0))
        for _ in range(copies):
            args += ["-i", str(path)]
        chain = [f"[{n + c}:a]aresample=48000,aformat=channel_layouts=stereo[m{cue}_{c}]" for c in range(copies)]
        cur = f"m{cue}_0"
        for c in range(1, copies):
            chain.append(f"[{cur}][m{cue}_{c}]acrossfade=d={XFADE}[m{cue}_x{c}]")
            cur = f"m{cue}_x{c}"
        ms = round(start * 1000)
        chain.append(f"[{cur}]atrim=0:{need:.3f},loudnorm=I={lufs}:TP=-8,"
                     f"afade=t=in:d={0.8 if start else 1.5},afade=t=out:st={max(0.0, need - XFADE):.3f}:d={XFADE},"
                     f"adelay={ms}|{ms}[seg{cue}]")
        graph += chain
        labels.append(f"[seg{cue}]")
        n += copies
    if len(labels) == 1:
        graph.append(f"{labels[0]}anull[mus]")
    else:
        graph.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0[mus]")
    return args, ";".join(graph)
