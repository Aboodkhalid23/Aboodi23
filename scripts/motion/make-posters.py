#!/usr/bin/env python3
"""صور الغلاف (البوستر) لمقاطع أوّاب.

لكل مقطع بـ links/salah/v/index.json يطلّع صورة وحدة من الفيديو (حوالي 40٪ من طوله)
ويحفظها بـ links/salah/v/p/<id>-ar.jpg و <id>-en.jpg بحجم 360x640 وجودة متوسطة (ملفات صغيرة).

التشغيل:
  python3 scripts/motion/make-posters.py          # يسوي الناقص بس
  python3 scripts/motion/make-posters.py --force  # يعيدها كلها
  python3 scripts/motion/make-posters.py --at 0.35  # يختار لحظة ثانية من الفيديو
"""
import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "links" / "salah" / "v"


def duration(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                         capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def poster(src, dst, at):
    t = max(0.0, duration(src) * at)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1",
                    "-vf", "scale=360:640:force_original_aspect_ratio=increase,crop=360:640",
                    "-q:v", "7", str(dst)], check=True)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--at", type=float, default=0.4)
    a = ap.parse_args()
    idx = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    out = ROOT / "p"
    out.mkdir(exist_ok=True)
    jobs = []
    for it in idx["items"]:
        for lang in ("ar", "en"):
            src = ROOT / it[lang]
            dst = out / f"{it['id']}-{lang}.jpg"
            if src.exists() and (a.force or not dst.exists()):
                jobs.append((src, dst))
    with ThreadPoolExecutor(4) as ex:
        for d in ex.map(lambda j: poster(*j, a.at), jobs):
            print("ok", d.name)
    total = sum(f.stat().st_size for f in out.glob("*.jpg"))
    print(f"{len(jobs)} made, {len(list(out.glob('*.jpg')))} posters, {total // 1024} KB total")


if __name__ == "__main__":
    main()
