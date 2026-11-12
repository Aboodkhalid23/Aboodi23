#!/usr/bin/env python3
"""مقطع اليوم لتطبيق أوّاب: يصنع فيديو موشن گرافيك عمودي لحديث اليوم (الأربعون النووية)، بصوت عربي وصوت إنگليزي.
النص من hadith.js بالحرف (نفس حديث اليوم بالتطبيق)، والصوت من أصوات مايكروسوفت المجانية (edge-tts)، والرسم بالكود.
التشغيل: python3 scripts/daily-video.py [--n رقم_الحديث] [--date 2026-11-12]
المخرجات: links/salah/daily/<التاريخ>-ar.mp4 و -en.mp4 و daily.json (يبقى آخر 7 أيام بس)"""
import argparse, asyncio, datetime as dt, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent / "links" / "salah"
OUT = ROOT / "daily"
VOICE = {"ar": "ar-SA-HamedNeural", "en": "en-US-AndrewNeural"}
FPS, W, H = 24, 720, 1280

def hadiths():
    t = (ROOT / "hadith.js").read_text(encoding="utf-8")
    return json.loads(re.search(r"window\.HADITH=(\[.*\]);", t, re.S).group(1))

def segments(text, lang):
    """نقسم النص عند علامات الوقف بدون ما نغيّر حرف، وكل مقطع ما يزيد عن 12 كلمة"""
    parts = re.split(r"(?<=[،,:؛;.؟?!\]])\s+|\s+(?=—)|\n+", text.strip())
    out = []
    for p in parts:
        w = p.split()
        while len(w) > 12:
            # نقطع بمكان خارج الأقواس قدر الإمكان، وقريب من النص
            k = max(1, -(-len(w) // 12)); want = len(w) // k
            best, depth, cands = want, 0, []
            for i, x in enumerate(w[:-1], 1):
                depth += x.count("(") - x.count(")")
                if depth <= 0 and 5 <= i <= 12: cands.append(i)
            if cands: best = min(cands, key=lambda i: abs(i - want))
            out.append(" ".join(w[:best])); w = w[best:]
        if w: out.append(" ".join(w))
    # مقطع بدون حروف (علامة بس) أو قصير كلش يلتصق بالي قبله
    m = []
    for x in out:
        if m and (not re.search(r"[\u0621-\u064Aa-zA-Z]", x) or len(x.split()) < 2): m[-1] += " " + x
        else: m.append(x)
    out = m
    assert re.sub(r"\s+", "", "".join(out)) == re.sub(r"\s+", "", text), "التقسيم غيّر النص"
    return out

async def tts(text, voice, path):
    import edge_tts
    for i in range(5):  # خدمة الصوت أحياناً ما ترد، نعيد المحاولة
        try:
            await edge_tts.Communicate(text, voice, rate="-8%").save(str(path)); return
        except Exception:
            if i == 4: raise
            await asyncio.sleep(2 + i * 2)

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).decode())

def build(n, ar, en, lang, day, tmp):
    text = ar if lang == "ar" else en
    segs = segments(text, lang)
    # الصوت: مقطع لكل جملة، وبيناتهن سكتة قصيرة
    times, files, t = [], [], 2.6
    for i, s in enumerate(segs):
        f = tmp / f"{lang}{i}.mp3"; asyncio.run(tts(s, VOICE[lang], f)); d = dur(f)
        times.append([round(t, 2), round(t + d, 2)]); files.append((f, t)); t += d + 0.45
    total = t + 3.2
    # نجمع الصوت على خط زمني واحد
    inp, flt = [], []
    for i, (f, st) in enumerate(files):
        inp += ["-i", str(f)]; flt.append(f"[{i}]adelay={int(st*1000)}|{int(st*1000)}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(files)))
    audio = tmp / f"{lang}.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(flt) + f";{mix}amix=inputs={len(files)}:normalize=0,apad=whole_dur={total}[o]", "-map", "[o]", "-t", str(total), "-c:a", "aac", "-b:a", "96k", str(audio)], check=True)
    # الصورة: صفحة HTML ترسم كل لحظة، ونصوّرها إطار إطار
    page = (Path(__file__).parent / "daily-video.html").read_text(encoding="utf-8")
    data = {"lang": lang, "n": n, "segs": segs, "times": times, "total": total, "day": day}
    html = tmp / f"{lang}.html"; html.write_text(page.replace("/*DATA*/", "window.D=" + json.dumps(data, ensure_ascii=False) + ";"), encoding="utf-8")
    for f in ("fonts/ui-700.woff2", "fonts/amiri.woff2", "icon-192.png"):
        dst = tmp / f; dst.parent.mkdir(exist_ok=True); shutil.copy(ROOT / f, dst)
    frames = tmp / f"fr_{lang}"; frames.mkdir(exist_ok=True)
    js = tmp / "shot.js"
    js.write_text("""const {chromium}=require('playwright');(async()=>{const [h,dir,fps,tot]=process.argv.slice(2);const b=await chromium.launch();const p=await b.newPage({viewport:{width:%d,height:%d}});
await p.goto('file://'+h);await p.evaluate(()=>document.fonts.ready);const N=Math.ceil(+tot*+fps);
for(let i=0;i<N;i++){await p.evaluate(t=>window.R(t),i/fps);await p.screenshot({path:dir+'/'+String(i).padStart(5,'0')+'.jpg',type:'jpeg',quality:88})}await b.close()})()""" % (W, H))
    subprocess.run(["node", str(js), str(html), str(frames), str(FPS), str(total)], check=True, cwd=str(Path(__file__).parent))
    out = OUT / f"{day}-{lang}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(frames / "%05d.jpg"), "-i", str(audio), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "26", "-movflags", "+faststart", "-shortest", str(out)], check=True)
    return out, total

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int); ap.add_argument("--date"); a = ap.parse_args()
    day = a.date or dt.date.today().isoformat()
    H = hadiths()
    # نفس اختيار التطبيق: رقم اليوم من 1970 باقي القسمة على عدد الأحاديث
    k = (dt.date.fromisoformat(day) - dt.date(1970, 1, 1)).days % len(H)
    h = next(x for x in H if x[0] == a.n) if a.n else H[k]
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); res = {}
        for lang in ("ar", "en"):
            f, t = build(h[0], h[1], h[2], lang, day, tmp); res[lang] = f.name; print(lang, f.name, round(t, 1), "s", f.stat().st_size // 1024, "KB")
    info = {"date": day, "n": h[0], "ar": res["ar"], "en": res["en"]}
    vids = sorted(OUT.glob("*.mp4"))
    for old in vids:
        if old.name[:10] < (dt.date.fromisoformat(day) - dt.timedelta(days=6)).isoformat(): old.unlink()
    (OUT / "daily.json").write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()
