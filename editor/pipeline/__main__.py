"""CLI: python -m editor.pipeline <stage> <episode_dir> [--source URL_OR_PATH]"""
import argparse
import json
import os
import shutil
import sys

from .brief import write_brief
from .clean import clean
from .compose import compose
from .deliver import prepare_delivery
from .fetch import fetch
from .media import MediaError
from .paths import Episode
from .plan import load_plan, validate_plan
from .styles import styles_summary
from .transcribe import transcribe
from .wikimedia import collect_images


def _clean_duration(ep: Episode) -> float:
    return round(sum(e - s for s, e in json.loads(ep.cuts.read_text(encoding="utf-8"))), 3)


def st_fetch(ep, a):
    if not a.source:
        raise MediaError("لازم تنطي --source (رابط درايف أو مسار الفيديو)")
    print("⬇️  أسحب الفيديو وأوحّده…", flush=True)
    fetch(a.source, ep)


def st_transcribe(ep, a):
    print("📝 أحوّل الكلام لنص (ياخذ وقت ويه الحلقات الطويلة)…", flush=True)
    fake = os.environ.get("EDITOR_FAKE_TRANSCRIPT")
    if fake:
        shutil.copyfile(fake, ep.transcript)
    else:
        transcribe(ep)


def st_clean(ep, a):
    print("✂️  أشيل السكتات والإعادات…", flush=True)
    print(f"   الفيديو صار {clean(ep):.1f} ثانية")


def st_brief(ep, a):
    print(f"🗒️  ملف التخطيط جاهز: {write_brief(ep, styles_summary())}")


def st_validate(ep, a):
    errs = validate_plan(load_plan(ep.plan), _clean_duration(ep))
    for e in errs:
        print("❌", e)
    if errs:
        sys.exit(2)
    print("✅ الخطة سليمة")


def st_images(ep, a):
    print("🖼️  أجيب صور مجانية من ويكيميديا…", flush=True)
    collect_images(load_plan(ep.plan), ep)
    fb = json.loads(ep.fallbacks.read_text(encoding="utf-8"))
    if fb:
        print(f"   {len(fb)} صورة ما انلگت، بدلتها بكتابة")


def st_compose(ep, a):
    print("🎬 أركّب الفيديو النهائي…", flush=True)
    compose(ep)


def st_deliver(ep, a):
    print(f"📦 جاهز: {prepare_delivery(ep)}")


STAGES = {"fetch": [st_fetch], "transcribe": [st_transcribe], "clean": [st_clean], "brief": [st_brief],
          "validate": [st_validate], "images": [st_images], "compose": [st_compose], "deliver": [st_deliver]}
STAGES["prep"] = STAGES["fetch"] + STAGES["transcribe"] + STAGES["clean"] + STAGES["brief"]
STAGES["render"] = STAGES["validate"] + STAGES["images"] + STAGES["compose"] + STAGES["deliver"]


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m editor.pipeline")
    p.add_argument("stage", choices=STAGES)
    p.add_argument("episode")
    p.add_argument("--source")
    a = p.parse_args(argv)
    ep = Episode(a.episode).ensure()
    try:
        for fn in STAGES[a.stage]:
            fn(ep, a)
    except MediaError as exc:
        print("❌", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
