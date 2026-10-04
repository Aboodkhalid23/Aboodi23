"""CLI: python -m editor.pipeline <stage> <episode_dir> [--source URL_OR_PATH]"""
import argparse
import json
import os
import shutil
import sys

from .ai import ai_fetch, ai_jobs, log_spend, spent
from .align import find_script
from .check import check_source
from .brief import write_brief
from .chapters import write_chapters
from .clean import clean
from .compose import compose
from .deliver import prepare_delivery
from .entities import entities_file, fetch_entities, load_entities
from .fetch import fetch
from .media import MediaError
from .music import music_fetch, music_jobs
from .paths import Episode
from .plan import load_plan, validate_plan
from .qa import qa
from .styles import styles_summary
from .subtitles import write_srt
from .transcribe import transcribe
from .wikimedia import collect_images


def _clean_duration(ep: Episode) -> float:
    return round(sum(e - s for s, e in json.loads(ep.cuts.read_text(encoding="utf-8"))), 3)


def st_fetch(ep, a):
    if not a.source:
        raise MediaError("لازم تنطي --source (رابط درايف أو مسار الفيديو)")
    print("⬇️  أسحب الفيديو وأوحّده…", flush=True)
    fetch(a.source, ep, max_height=a.max_height)


def st_check(ep, a):
    print("🔎 أتأكد من الفيديو الي انسحب…", flush=True)
    d = check_source(ep, words=not a.no_words)
    print(f"   الملف: {d['name'] or '—'}")
    print(f"   الطول: {d['length']}  |  الدقة: {d['width']}×{d['height']}  |  {d['fps']:g} فريم  |  "
          f"{d['size_mb'] or '?'} ميگا  |  صوت: {'اي' if d['has_audio'] else 'لا ❗'}")
    if d.get("first_words"):
        print(f"   أول كلام: {d['first_words'][:200]}")
    print(f"   لقطات: {d['frames']}")


def _final_duration(ep) -> float:
    plan = load_plan(ep.plan)
    return plan.teaser_total + _clean_duration(ep)


def st_music_jobs(ep, a):
    jobs = music_jobs(ep, _final_duration(ep))
    todo = [j for j in jobs if not j["done"]]
    print(f"🎵 مقاطع الموسيقى: {len(jobs)}، الناقص {len(todo)}. التفاصيل: {ep.work / 'music_jobs.json'}")


def st_thumbnail(ep, a):
    from .thumbnail import make_thumbnails
    print("🖼️  الصور المصغرة: " + "، ".join(str(p) for p in make_thumbnails(ep)))


def st_music_free(ep, a):
    from .free_audio import free_music
    missing = free_music(ep, _final_duration(ep))
    print("🎵 موسيقى مجانية: " + ("كلها تمام" if not missing else f"ما لگيت لـ {', '.join(missing)} (تبقى بدون أو بآرتلست بموافقته)"))


def st_music_fetch(ep, a):
    if a.cue is None or not a.url:
        raise MediaError("لازم --cue و --url")
    print(f"⬇️  نزلت: {music_fetch(ep, a.cue, a.url)}")


def st_entities(ep, a):
    if not entities_file(ep).exists():
        print("   ما اكو entities.json (أسماء أشخاص وشركات)، أكمل بدونها")
        return
    print("👤 أجيب صور حقيقية للأشخاص والشركات…", flush=True)
    found, missing = fetch_entities(ep)
    print(f"   لگيت {len(found)} صورة")
    for m in missing:
        print("⚠️ ", m)


def st_ai_jobs(ep, a):
    jobs = ai_jobs(ep)
    todo = [j for j in jobs if not j.done]
    print(f"🤖 مشاهد الذكاء الاصطناعي: {len(jobs)}، الناقص {len(todo)}. الصرف {spent(ep):g} من "
          f"{load_plan(ep.plan).ai_budget:g} رصيد. التفاصيل: {ep.work / 'ai_jobs.json'}")


def st_ai_fetch(ep, a):
    if a.beat is None or not a.url:
        raise MediaError("لازم --beat و --url")
    print(f"⬇️  نزل: {ai_fetch(ep, a.beat, a.url)}")


def st_ai_log(ep, a):
    if a.beat is None or a.credits is None or not a.model:
        raise MediaError("لازم --beat و --model و --credits")
    total = log_spend(ep, a.beat, a.model, a.credits, a.job or "")
    print(f"🧾 انسجل. المجموع {total:g} من {load_plan(ep.plan).ai_budget:g} رصيد")


def st_transcribe(ep, a):
    print("📝 أحوّل الكلام لنص (ياخذ وقت ويه الحلقات الطويلة)…", flush=True)
    fake = os.environ.get("EDITOR_FAKE_TRANSCRIPT")
    if fake:
        shutil.copyfile(fake, ep.transcript)
    else:
        transcribe(ep)


def st_clean(ep, a):
    print("✂️  أشيل السكتات والإعادات…", flush=True)
    script = a.script or find_script(ep)
    print(f"🗣️  أصحح اللهجة من السكربت: {script}" if script else "   ما لگيت سكربت، التفريغ يبقى بدون تصحيح")
    print(f"   الفيديو صار {clean(ep, script=script):.1f} ثانية")


def st_brief(ep, a):
    print(f"🗒️  ملف التخطيط جاهز: {write_brief(ep, styles_summary())}")


def st_validate(ep, a):
    ents = set(load_entities(ep)) if entities_file(ep).exists() else None
    errs = validate_plan(load_plan(ep.plan), _clean_duration(ep), entities=ents, ai_spent=spent(ep))
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
    if a.preview:
        print("👀 أركّب نسخة معاينة سريعة (جودة واطية)…", flush=True)
        print(f"📦 المعاينة جاهزة: {compose(ep, preview=True)}")
        return
    print("🎬 أركّب الفيديو النهائي بالجودة الكاملة…", flush=True)
    compose(ep)


def st_qa(ep, a):
    print("🔍 أفحص الفيديو قبل التسليم…", flush=True)
    d = qa(ep, preview=a.preview)
    print(f"   {d['size']} | {d['fps']:g} فريم | {d['duration']} ث | صوت {d['lufs']} LUFS، ذروة {d['peak']}")
    for issue in d["issues"]:
        print("⚠️ ", issue)
    if not d["issues"]:
        print("   ✅ الفحص التقني سليم")
    print("   راجع لوحات المشاهد بعينك قبل الإرسال: " + "، ".join(d["sheets"]))


def st_scene_check(ep, a):
    """Render one custom scene (props from the first beat that uses it, or --props) and show 4 frames."""
    import subprocess
    from .graphics import ensure_bundle, render_graphic
    from .plan import Beat
    from .styles import load_style
    if not a.scene:
        raise MediaError("لازم --scene <Name>")
    plan = load_plan(ep.plan) if ep.plan.exists() else None
    beat = next((b for b in (plan.beats if plan else []) if b.kind == "graphic"
                 and (b.graphic or {}).get("scene") == a.scene), None)
    if beat is None:
        beat = Beat(0, 5, "body", "graphic", graphic={"type": "custom", "scene": a.scene, **json.loads(a.props or "{}")})
    style = load_style(plan.style["primary"] if plan else "retro-collage")
    out = render_graphic(beat, style, ep.work / f"scene_{a.scene}.mp4", bundle=ensure_bundle(ep.work / "bundle"), scale=0.5)
    sheet = ep.work / f"scene_{a.scene}.jpg"
    d = beat.duration
    picks = "+".join(f"eq(n\\,{int(d * 30 * q) - 1})" for q in (0.25, 0.5, 0.75, 1.0))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out), "-vf", f"select='{picks}',scale=640:-2,tile=2x2",
                    "-frames:v", "1", str(sheet)], check=True)
    print(f"🖼️  لقطات المشهد (ربع، نص، ثلاث أرباع، آخر): {sheet}")


def st_shorts(ep, a):
    from .shorts import make_shorts
    plan = load_plan(ep.plan)
    if not plan.shorts:
        print("   ما اكو shorts بالخطة")
        return
    print(f"📱 أسوي {len(plan.shorts)} شورت عمودي…", flush=True)
    for out in make_shorts(ep):
        print(f"   ✅ {out}")


def st_deliver(ep, a):
    if a.preview:
        return
    plan = load_plan(ep.plan)
    if plan.chapters:
        print(f"📑 فصول يوتيوب (انسخها للوصف): {write_chapters(plan, ep.edit / 'chapters.txt')}")
    print(f"💬 ملف الترجمة ليوتيوب (يترفع لحاله، ما يطلع على الفيديو): {write_srt(ep)}")
    out = prepare_delivery(ep, a.max_mb)
    print(f"📦 جاهز: {out} ({out.stat().st_size / 1e6:.0f} ميگا)")


STAGES = {"fetch": [st_fetch], "entities": [st_entities], "transcribe": [st_transcribe], "clean": [st_clean],
          "brief": [st_brief], "validate": [st_validate], "ai-jobs": [st_ai_jobs], "ai-fetch": [st_ai_fetch],
          "ai-log": [st_ai_log], "check": [st_check], "music-free": [st_music_free], "thumbnail": [st_thumbnail], "music-jobs": [st_music_jobs], "music-fetch": [st_music_fetch], "qa": [st_qa], "scene-check": [st_scene_check], "shorts": [st_shorts], "images": [st_images], "compose": [st_compose], "deliver": [st_deliver]}
STAGES["get"] = STAGES["fetch"] + STAGES["check"]   # download, then show the owner what came
STAGES["prep"] = STAGES["fetch"] + STAGES["entities"] + STAGES["transcribe"] + STAGES["clean"] + STAGES["brief"]
# Real pictures and free music first; what is still missing after that becomes an AI job (owner's rule).
STAGES["render"] = (STAGES["validate"] + STAGES["music-free"] + STAGES["images"] + STAGES["ai-jobs"] + STAGES["music-jobs"]
                    + STAGES["compose"] + STAGES["qa"] + STAGES["deliver"])


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m editor.pipeline")
    p.add_argument("stage", choices=STAGES)
    p.add_argument("episode")
    p.add_argument("--source")
    p.add_argument("--script", help="سكربت الحلقة لتصحيح التفريغ")
    p.add_argument("--max-height", type=int, choices=[1080, 1440, 2160], help="أعلى دقة (أصغر = أسرع)")
    p.add_argument("--preview", action="store_true", help="نسخة معاينة 1280×720 (أسرع من النهائية)")
    p.add_argument("--max-mb", type=float, help="اضغط الفيديو بس إذا عبر هذا الحجم")
    p.add_argument("--beat", type=int, help="رقم المشهد (ai-fetch / ai-log)")
    p.add_argument("--url", help="رابط الناتج من Higgsfield (ai-fetch)")
    p.add_argument("--model", help="الموديل الي ولّد (ai-log)")
    p.add_argument("--credits", type=float, help="الرصيد الي انصرف (ai-log)")
    p.add_argument("--job", help="رقم المهمة بـ Higgsfield (ai-log)")
    p.add_argument("--cue", type=int, help="رقم مقطع الموسيقى (music-fetch)")
    p.add_argument("--no-words", action="store_true", help="check بدون تفريغ أول الكلام")
    p.add_argument("--scene", help="اسم المشهد المخصص (scene-check)")
    p.add_argument("--props", help="props المشهد بصيغة JSON (scene-check)")
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
