"""His episode in other languages, in his own voice (owner, 2026-10-25: "الصوت مالي يكون دوبلاج إنگليزي، صيني…").

ElevenLabs Dubbing does it: it hears the Arabic, translates, and speaks it with a clone of his voice, keeping the music
and sound effects. It needs his ElevenLabs key (kept in $MONTIER_HOME/elevenlabs.json, mode 600, never in the repo)
and spends his ElevenLabs credit per minute and language, so the app shows the cost and asks first.
Out: edit/dubs/<lang>.mp3 (an extra audio track for YouTube: Studio → Languages → Add audio) and
edit/dubs/<episode>-<lang>.mp4 (the video with that voice, for other platforms)."""
import json
import os
import subprocess
import time
from pathlib import Path

import requests

API = "https://api.elevenlabs.io/v1"
LANGS = {"en": "الإنگليزية", "es": "الإسبانية", "fr": "الفرنسية", "de": "الألمانية", "pt": "البرتغالية", "ru": "الروسية",
         "zh": "الصينية", "ja": "اليابانية", "ko": "الكورية", "hi": "الهندية", "tr": "التركية", "id": "الإندونيسية",
         "th": "التايلندية", "it": "الإيطالية"}


def _file(home: Path) -> Path:
    return home / "elevenlabs.json"


def status(home: Path) -> dict:
    try:
        return {"linked": bool(json.loads(_file(home).read_text(encoding="utf-8")).get("key"))}
    except (OSError, ValueError):
        return {"linked": False}


def set_key(home: Path, key: str) -> dict:
    key = key.strip()
    if len(key) < 20:
        raise ValueError("المفتاح مو صحيح. انسخه مثل ما هو من موقع إلفن لابس")
    f = _file(home)
    f.write_text(json.dumps({"key": key}), encoding="utf-8")
    os.chmod(f, 0o600)
    return status(home)


def unlink(home: Path) -> dict:
    _file(home).unlink(missing_ok=True)
    return status(home)


def _key(home: Path) -> str:
    try:
        return json.loads(_file(home).read_text(encoding="utf-8"))["key"]
    except (OSError, ValueError, KeyError):
        raise ValueError("اربط حساب إلفن لابس من الإعدادات أول")


def dub(home: Path, video: Path, lang: str, out_dir: Path, say=print, session=None, poll: float = 15.0,
        timeout: float = 3 * 3600) -> Path:
    """One language. Returns the dubbed video."""
    if lang not in LANGS:
        raise ValueError("لغة مو معروفة")
    s = session or requests.Session()
    head = {"xi-api-key": _key(home)}
    out_dir.mkdir(parents=True, exist_ok=True)
    audio = out_dir / "source-audio.m4a"
    if not audio.exists():   # the sound only: a much smaller upload than the 4K video
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-c:a", "aac", "-b:a", "192k", str(audio)], check=True)
    with open(audio, "rb") as f:
        r = s.post(f"{API}/dubbing", headers=head, timeout=600,
                   files={"file": (audio.name, f, "audio/mp4")},
                   data={"target_lang": lang, "source_lang": "ar", "num_speakers": "1", "name": f"{video.stem}-{lang}"})
    if r.status_code != 200:
        raise ValueError("إلفن لابس رفض: " + r.text[:300])
    job = r.json()["dubbing_id"]
    t0 = time.time()
    while True:
        st = s.get(f"{API}/dubbing/{job}", headers=head, timeout=60).json()
        if st.get("status") == "dubbed":
            break
        if st.get("status") in ("failed", "error"):
            raise ValueError("الدبلجة فشلت: " + str(st.get("error") or "")[:200])
        if time.time() - t0 > timeout:
            raise ValueError("الدبلجة طولت كلش، جرّب بعدين")
        say(f"   {LANGS[lang]}: دا تتدبلج…")
        time.sleep(poll)
    r = s.get(f"{API}/dubbing/{job}/audio/{lang}", headers=head, timeout=600)
    if r.status_code != 200:
        raise ValueError("ما گدرت أنزّل الصوت المدبلج")
    track = out_dir / f"{lang}.mp3"
    track.write_bytes(r.content)
    out = out_dir / f"{video.stem}-{lang}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(track), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    return out


def _voice_id(home: Path, sample_from: Path, s) -> str:
    """His voice on ElevenLabs (instant voice clone from a minute of his own speech), made once and remembered."""
    f = _file(home)
    d = json.loads(f.read_text(encoding="utf-8"))
    if d.get("voice_id"):
        return d["voice_id"]
    sample = f.parent / "voice_sample.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "20", "-t", "90", "-i", str(sample_from), "-vn", "-ac", "1",
                    "-b:a", "128k", str(sample)], check=True)
    with open(sample, "rb") as fh:
        r = s.post(f"{API}/voices/add", headers={"xi-api-key": d["key"]}, timeout=300,
                   data={"name": "URU — صوتي", "remove_background_noise": "true"},
                   files={"files": ("voice.mp3", fh, "audio/mpeg")})
    sample.unlink(missing_ok=True)
    if r.status_code != 200:
        raise ValueError("إلفن لابس ما سوى نسخة من صوتك (يحتاج اشتراك يسمح بنسخ الصوت): " + r.text[:200])
    d["voice_id"] = r.json()["voice_id"]
    f.write_text(json.dumps(d), encoding="utf-8")
    os.chmod(f, 0o600)
    return d["voice_id"]


def fix_word(home: Path, ep_root: Path, start: float, end: float, text: str, session=None) -> dict:
    """A word or sentence he said wrong: the right words in his voice, saved as a patch the next build lays in
    (editor/pipeline/voicepatch.py). Spends a little ElevenLabs credit (characters)."""
    text = str(text).strip()
    if not text or len(text) > 300:
        raise ValueError("اكتب الكلمة أو الجملة الصحيحة (أقل من ٣٠٠ حرف)")
    if not 0 <= start < end or end - start > 15:
        raise ValueError("حدد مكان الكلمة (أقل من ١٥ ثانية)")
    s = session or requests.Session()
    key = _key(home)
    clean = ep_root / "edit" / "work" / "clean.mp4"
    vid = _voice_id(home, clean, s)
    r = s.post(f"{API}/text-to-speech/{vid}", params={"output_format": "mp3_44100_128"}, timeout=120,
               headers={"xi-api-key": key, "Content-Type": "application/json"},
               json={"text": text, "model_id": "eleven_multilingual_v2",
                     "voice_settings": {"stability": 0.6, "similarity_boost": 0.9, "style": 0.2}})
    if r.status_code != 200:
        raise ValueError("إلفن لابس ما طلّع الصوت: " + r.text[:200])
    out_dir = ep_root / "edit" / "voice"
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"fix_{int(start * 1000)}.mp3"
    (out_dir / name).write_bytes(r.content)
    lst = ep_root / "edit" / "voice_patches.json"
    items = json.loads(lst.read_text(encoding="utf-8")) if lst.exists() else []
    items = [p for p in items if p["end"] <= start or p["start"] >= end]   # a new fix replaces an overlapping one
    items.append({"start": round(start, 3), "end": round(end, 3), "file": name, "text": text})
    lst.write_text(json.dumps(sorted(items, key=lambda p: p["start"]), ensure_ascii=False, indent=1), encoding="utf-8")
    return {"patches": items}
