#!/usr/bin/env python3
"""مكتبة مقاطع أوّاب: يصنع فيديو موشن گرافيك عمودي لكل حديث (عربي + إنگليزي)، كله بالكود.
- النص: من hadith.js بالحرف (الأربعون النووية). ما نغيّر حرف.
- المشاهد: scenes.json (لكل حديث لقطات تبدي عند كلمة معيّنة بالنص).
- الرسم: engine.js على canvas، ونصوّر كل إطار بمتصفح Playwright.
- الصوت: أصوات مايكروسوفت المجانية (edge-tts).
التشغيل: python3 scripts/motion/make-videos.py [أرقام الأحاديث...] [--lang ar|en] [--preview]
المخرجات: links/salah/v/h<رقم>-<لغة>.mp4 و links/salah/v/index.json"""
import argparse, asyncio, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent / "links" / "salah"
OUT = ROOT / "v"
VOICE = {"ar": "ar-SA-HamedNeural", "en": "en-US-AndrewNeural"}
FPS = 24
INTRO, GAP, OUTRO = 2.6, 0.4, 3.2

def strip(s):
    return re.sub(r"[ً-ٰٟـ]", "", s)

def norm(s):
    s = strip(s).lower()
    s = re.sub(r"[أإآٱ]", "ا", s).replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"[^ء-يa-z0-9 ]", " ", s)

def hadiths():
    t = (ROOT / "hadith.js").read_text(encoding="utf-8")
    return {h[0]: h for h in json.loads(re.search(r"window\.HADITH=(\[.*\]);", t, re.S).group(1))}

def segments(text):
    """نقسم عند علامات الوقف بدون ما نغيّر حرف، وكل مقطع ما يزيد عن 12 كلمة"""
    # الصلاة على النبي والترضي ما ينقطعن بالنص
    fx = lambda w: "".join(c + "[\u064B-\u0652\u0670]*" for c in w)
    keep = fx("صلى") + r"\s+\S+\s+" + fx("عليه") + r"\s+" + fx("و") + r"\s*" + fx("سلم") + "|" + fx("رضي") + r"\s+\S+\s+" + fx("عن") + r"\S*"
    text = re.sub(keep, lambda m: re.sub(r"\s+", "\u00a0", m.group(0)), text.strip())
    parts = re.split(r"(?<=[،,:؛;.؟?!\]])[ \t]+|[ \t]+(?=—)|\n+", text)
    out = []
    for p in parts:
        w = p.split(" ")
        while len(w) > 12:
            k = max(1, -(-len(w) // 12)); want = len(w) // k
            best, depth, cands = want, 0, []
            for i, x in enumerate(w[:-1], 1):
                depth += x.count("(") - x.count(")")
                if depth <= 0 and 5 <= i <= 12: cands.append(i)
            if cands: best = min(cands, key=lambda i: abs(i - want))
            out.append(" ".join(w[:best])); w = w[best:]
        if w: out.append(" ".join(w))
    m = []
    for x in out:
        if m and (not re.search(r"[ء-يa-zA-Z]", x) or len(x.split()) < 2): m[-1] += " " + x
        else: m.append(x)
    m = [x.replace("\u00a0", " ") for x in m]
    assert re.sub(r"\s+", "", "".join(m)) == re.sub(r"\s+", "", text), "التقسيم غيّر النص"
    return m

def speakable(s, lang):
    # القراءة بس (النص المعروض ما يتغير): الرموز الي الصوت يتعثر بيها
    s = s.replace("ﷺ", "peace be upon him" if lang == "en" else "صلى الله عليه وسلم")
    s = re.sub(r"\[(رقم|راجع رقم)[^\]]*\]", "", s)
    return re.sub(r"[\[\]\"“”«»]", "", s)

async def tts(text, voice, path):
    import edge_tts
    for i in range(6):
        try:
            await edge_tts.Communicate(text, voice, rate="-6%").save(str(path)); return
        except Exception:
            if i == 5: raise
            await asyncio.sleep(2 + i * 3)

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).decode())

def beat_times(beats, segs, times, lang):
    """كل لقطة تبدي ويا المقطع الي بيه كلمتها. إذا ما لگيناها، تتوزع بالنسبة"""
    full, starts = "", []
    for s in segs:
        starts.append(len(full)); full += norm(s) + " "
    out, pos, miss = [], 0, []
    body0 = times[0][0]
    for j, b in enumerate(beats):
        key = b[0] if lang == "ar" else b[1]
        t = None
        if j == 0 and not key: t = 0.0
        elif key:
            ks = [full.find(norm(o).strip(), pos) for o in key.split("|")]
            ks = [v for v in ks if v >= 0]
            k = min(ks) if ks else -1
            if k >= 0:
                pos = k + 1
                si = max(i for i, st in enumerate(starts) if st <= k)
                L = max(1, len(norm(segs[si])))
                t = max(0.0, times[si][0] + (times[si][1] - times[si][0]) * (k - starts[si]) / L - 0.15)
            else: miss.append(key)
        if t is None and b is beats[-1] and b[2] == "scroll":
            t = max(0.0, times[-1][0] - 0.15); miss = miss[:-1] if miss and miss[-1] == key else miss
        if t is None:
            t = body0 + (times[-1][1] - body0) * j / max(1, len(beats))
        if out and t < out[-1]["t"] + 0.6: t = out[-1]["t"] + 0.6
        out.append({"t": round(t, 2), "bg": b[2], "a": b[3], "p": b[4], "f": b[5] if len(b) > 5 else []})
    return out, miss

END = ["رواه|حديث حسن|رويناه", "related|bukhari|tirmidhi|ibn majah|hasan hadeeth|reported|daraqutnee|bayhaqi|nawawi says", "scroll", [], ["stand@360,1060*1.3", "lantern@170,700", "lantern@550,700"], ["sparkle@360,880"]]
ISNAD = ["", "", "scroll", [], ["stand@360,1060*1.3", "lantern@170,700", "lantern@550,700"], ["sparkle@360,880"]]

def build(n, h, sc, lang, tmp, preview=False):
    text = h[1] if lang == "ar" else h[2]
    segs = segments(text)
    times, files, t = [], [], INTRO
    for i, s in enumerate(segs):
        f = tmp / f"{lang}{n}_{i}.mp3"
        if not preview: asyncio.run(tts(speakable(s, lang), VOICE[lang], f)); d = dur(f)
        else: d = 0.42 * len(s.split()) + .4
        times.append([round(t, 2), round(t + d, 2)]); files.append((f, t)); t += d + GAP
    total = t + OUTRO
    beats, miss = beat_times([ISNAD] + sc["b"] + ([] if sc.get("noend") else [END]), segs, times, lang)
    if miss: print(f"  ⚠️ {n}-{lang} كلمات ما انلگت:", miss, file=sys.stderr)
    data = {"lang": lang, "n": n, "segs": segs, "times": times, "total": total, "beats": beats,
            "icon": "data:image/png;base64," + __import__("base64").b64encode((ROOT / "icon-192.png").read_bytes()).decode(),
            "hl": sc.get("hl", {}).get(lang, []),
            "title": (f"الحديث {n}" if lang == "ar" else f"Hadith {n}"),
            "label": ("من الأربعين النووية" if lang == "ar" else "An-Nawawi's Forty Hadith"),
            "src": ("المصدر: الأربعون النووية · النص بالحرف" if lang == "ar" else "Source: An-Nawawi's Forty Hadith · verbatim")}
    html = tmp / f"{lang}{n}.html"
    html.write_text((HERE / "page.html").read_text(encoding="utf-8").replace("/*DATA*/", "window.D=" + json.dumps(data, ensure_ascii=False) + ";"), encoding="utf-8")
    for f in ("fonts/ui-700.woff2", "fonts/ui-500.woff2", "fonts/amiri.woff2", "icon-192.png"):
        dst = tmp / f; dst.parent.mkdir(exist_ok=True)
        if not dst.exists(): shutil.copy(ROOT / f, dst)
    shutil.copy(HERE / "engine.js", tmp / "engine.js")
    if preview:
        outp = Path(__import__("os").environ.get("PREVIEW_DIR", tempfile.gettempdir())); outp.mkdir(exist_ok=True)
        subprocess.run(["node", str(HERE / "shot.js"), str(html), "preview", str(outp / f"h{n}-{lang}.png"), json.dumps([b["t"] + 1.6 for b in beats][:8])], check=True)
        return outp / f"h{n}-{lang}.png", total
    audio = tmp / f"{lang}{n}.m4a"
    inp, flt = [], []
    for i, (f, st) in enumerate(files):
        inp += ["-i", str(f)]; flt.append(f"[{i}]adelay={int(st*1000)}|{int(st*1000)}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(files)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(flt) + f";{mix}amix=inputs={len(files)}:normalize=0,apad=whole_dur={total}[o]", "-map", "[o]", "-t", str(total), "-c:a", "aac", "-b:a", "80k", str(audio)], check=True)
    out = OUT / f"h{n}-{lang}.mp4"
    subprocess.run(["node", str(HERE / "shot.js"), str(html), "video", str(out), str(FPS), str(total), str(audio)], check=True)
    return out, total

def index():
    items = []
    H, SC = hadiths(), json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))
    def title(text, key):
        # عنوان المقطع: الجملة الي بيها أول كلمة من المشاهد، بالحرف من النص
        for sg in segments(text):
            if norm(key.split("|")[0]).strip() in norm(sg): return sg.strip(' "“”«»')
        return segments(text)[0]
    for n in sorted(H):
        a, e = OUT / f"h{n}-ar.mp4", OUT / f"h{n}-en.mp4"
        if a.exists() and e.exists():
            b0 = SC[str(n)]["b"][0]
            items.append({"id": f"h{n}", "n": n, "ar": a.name, "en": e.name, "da": round(dur(a)), "de": round(dur(e)), "ta": title(H[n][1], b0[0]), "te": title(H[n][2], b0[1])})
    (OUT / "index.json").write_text(json.dumps({"series": "nawawi", "items": items}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(items)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("n", nargs="*", type=int); ap.add_argument("--lang"); ap.add_argument("--preview", action="store_true"); ap.add_argument("--index", action="store_true")
    a = ap.parse_args()
    if a.index: print("index", index()); return
    H, SC = hadiths(), json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for n in a.n or sorted(int(k) for k in SC):
        with tempfile.TemporaryDirectory() as td:
            for lang in ([a.lang] if a.lang else ["ar", "en"]):
                f, t = build(n, H[n], SC[str(n)], lang, Path(td), a.preview)
                print(n, lang, f.name, round(t, 1), "s", (f.stat().st_size // 1024), "KB", flush=True)
    if not a.preview: print("index", index())

if __name__ == "__main__":
    main()
