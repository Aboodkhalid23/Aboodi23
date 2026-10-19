#!/usr/bin/env python3
"""يسحب نص فيديو يوتيوب (الترجمة التلقائية) وتعليقاته، أو يدوّر على فيديوهات منافسين.

الاستخدام:
    python3 scripts/yt-transcript.py <رابط أو id>              # النص بالعربي (أو الإنگليزي إذا ماكو)
    python3 scripts/yt-transcript.py <رابط> --comments         # + أول 30 تعليق
    python3 scripts/yt-transcript.py --search "قصة شركة نوكيا" # أقوى 10 نتائج: القناة، المشاهدات، الرابط

يعتمد على yt-dlp (مثبت). youtube-transcript-api محجوب أغلب الوقت من السيرفرات.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def run(args):
    return subprocess.run(["yt-dlp", "--no-warnings", *args], capture_output=True, text=True, timeout=180)


def search(q, n=10):
    r = run(["--flat-playlist", "-j", f"ytsearch{n}:{q}"])
    for line in r.stdout.splitlines():
        v = json.loads(line)
        views = v.get("view_count") or 0
        print(f"{views:>12,} | {v.get('channel') or v.get('uploader')} | {v.get('title')} | https://youtu.be/{v.get('id')}")


def vtt_to_text(raw):
    out, last = [], ""
    for ln in raw.splitlines():
        if "-->" in ln or not ln.strip() or ln.startswith(("WEBVTT", "Kind:", "Language:")) or ln.strip().isdigit():
            continue
        ln = re.sub(r"<[^>]+>", "", ln).strip()
        if ln and ln != last:
            out.append(ln)
            last = ln
    return "\n".join(out)


def transcript(url, comments=False):
    with tempfile.TemporaryDirectory() as d:
        args = ["--skip-download", "--write-auto-subs", "--write-subs", "--sub-langs", "ar,ar-orig,en,en-orig",
                "--sub-format", "vtt", "-o", f"{d}/v.%(ext)s"]
        if comments:
            args += ["--write-comments", "--extractor-args", "youtube:max_comments=30,all,0,0", "--write-info-json"]
        r = run(args + [url])
        if not list(Path(d).glob("*.vtt")):  # يوتيوب يطلب تسجيل دخول أحياناً، نجرب واجهة الأندرويد
            r = run(args + ["--extractor-args", "youtube:player_client=android", url])
        subs = sorted(Path(d).glob("*.vtt"), key=lambda p: (not ".ar" in p.name, p.name))
        if not subs:
            print("ما لگيت ترجمة لهالفيديو.\n" + r.stderr[-500:])
        else:
            print(f"# النص ({subs[0].name})\n")
            print(vtt_to_text(subs[0].read_text(encoding="utf-8", errors="ignore")))
        if comments:
            info = next(Path(d).glob("*.info.json"), None)
            if info:
                data = json.loads(info.read_text(encoding="utf-8"))
                print("\n# التعليقات\n")
                for c in (data.get("comments") or [])[:30]:
                    print(f"- ({c.get('like_count', 0)}) {c.get('text', '').strip()[:300]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "--search":
        search(" ".join(sys.argv[2:]))
    else:
        transcript(sys.argv[1], "--comments" in sys.argv)
