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
INTRO, GAP, OUTRO = 2.6, 0.7, 3.2
# صوت الراوي المعتمد (اختاره صاحب القناة 12 تشرين الثاني 2026): حامد السعودي، أبطأ وأعمق، ويا تدفئة وصدى خفيف
PROSODY = {"ar": ("-14%", "-4Hz"), "en": ("-10%", "-2Hz")}
VOICE_FX = "equalizer=f=140:t=q:w=1:g=3,equalizer=f=6500:t=q:w=1.5:g=-3,acompressor=threshold=-18dB:ratio=3,aecho=0.8:0.6:45|90:0.12|0.07,loudnorm=I=-16:TP=-1.5"
QURAN_FX = "loudnorm=I=-16:TP=-1.5"

def strip(s):
    return re.sub(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640\u200e\u200f]", "", s)

def norm(s):
    s = strip(s).lower()
    s = re.sub(r"[أإآٱ]", "ا", s).replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"\s+", " ", re.sub(r"[^ء-يa-z0-9 ]", " ", s))

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
    assert re.sub(r"\s+", "", "".join(m)) == re.sub(r"\s+", "", text), "التقسيم غيّر النص"
    return m

def speakable(s, lang):
    # القراءة بس (النص المعروض ما يتغير): الرموز الي الصوت يتعثر بيها
    s = s.replace("ﷺ", "peace be upon him" if lang == "en" else "صلى الله عليه وسلم")
    s = re.sub(r"\[(رقم|راجع رقم)[^\]]*\]", "", s)
    s = re.sub(r"[\[\]\"“”«»\u200e\u200f]", "", s)
    return re.sub(r"(^|\s)[-—–]+(\s|$)", " ", s).strip()

async def tts(text, voice, path, lang="ar"):
    import edge_tts
    rate, pitch = PROSODY[lang]
    if not re.search(r"[\u0621-\u064Aa-zA-Z]", text):
        # ما بيها كلام (علامة بس): سكتة قصيرة بدل الصوت
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.3", str(path)], check=True); return
    for i in range(10):  # خدمة الصوت أحياناً ترفض من كثر الطلبات، نعيد بصبر
        try:
            await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(path)); return
        except Exception:
            if i == 9: raise
            await asyncio.sleep(3 + i * 4)

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).decode())

def beat_times(beats, segs, times, lang):
    """كل لقطة تبدي ويا المقطع الي بيه كلمتها. إذا ما لگيناها، تتوزع بالنسبة"""
    full, starts = "", []
    for s in segs:
        starts.append(len(full)); full += norm(s).strip() + " "
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
CAT = json.loads((HERE / "catalog.json").read_text(encoding="utf-8"))
AR_DIG = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

def chunks(text, n=13):
    """نقسم الآية الطويلة عند علامات الوقف، وإذا بعدها طويلة بالتساوي"""
    w = text.split(" "); out, cur = [], []
    for x in w:
        cur.append(x)
        if len(cur) >= 6 and re.search(r"[ۖ-ۛ]", x) or len(cur) >= n: out.append(" ".join(cur)); cur = []
    if cur:
        if out and len(cur) < 3: out[-1] += " " + " ".join(cur)
        else: out.append(" ".join(cur))
    return out

def fetch(url, path):
    import urllib.request
    for i in range(5):
        try:
            path.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "awwab"}), timeout=60).read()); return
        except Exception:
            if i == 4: raise
            __import__("time").sleep(3)

def item(key):
    """يرجع كل شي عن المقطع: النص، المصدر، الصوت"""
    SC = json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))
    if key.isdigit():
        n = int(key); h = hadiths()[n]; ser = CAT["series"]["nawawi"]
        return {"key": f"h{n}", "kind": "h", "n": n, "ar": h[1], "en": h[2], "sc": SC[key], "ser": ser,
                "ta": f"الحديث {n}", "te": f"Hadith {n}",
                "src_ar": "المصدر: الأربعون النووية · النص بالحرف", "src_en": "Source: An-Nawawi's Forty Hadith · verbatim"}
    it = next(x for x in CAT["items"] if x["id"] == key); C = json.loads((HERE / "content.json").read_text(encoding="utf-8"))[key]
    d = {"key": key, "kind": "q" if "q" in it else "b", "sc": SC[key], "ser": CAT["series"][it["s"]], "ta": it["ta"], "te": it["te"], "s": it["s"]}
    if "q" in it:
        s_, a_, b_ = it["q"]
        d.update(c=C, src_ar=f"{C['name']} · الآيات {a_}–{b_}".translate(AR_DIG) + " · تلاوة مشاري العفاسي", src_en=f"Surah {C['ename']} {s_}:{a_}–{b_} · Saheeh International")
    else:
        d.update(ar=C["ar"], en=C["en"], src_ar=f"صحيح البخاري · رقم {C['b']}".translate(AR_DIG), src_en=f"Sahih al-Bukhari {C['b']}")
    return d

def build(I, lang, tmp, preview=False):
    key, sc = I["key"], I["sc"]
    # الوحدات: كل وحدة ملف صوت واحد، وبيها مقطع نص أو أكثر
    units = []
    if I["kind"] == "q":
        C = I["c"]; s_ = C["surah"]
        if C["basmala"]: units.append({"segs": [C["basmala"]] if lang == "ar" else ["In the name of Allah, the Entirely Merciful, the Especially Merciful."], "q": (1, 1), "say": "In the name of Allah, the Entirely Merciful, the Especially Merciful."})
        for a in C["ayat"]:
            if lang == "ar":
                cs = chunks(a["ar"]); cs[-1] += " ﴿" + str(a["k"]).translate(AR_DIG) + "﴾"
                units.append({"segs": cs, "q": (s_, a["k"])})
            else:
                for sg in segments(a["en"]): units.append({"segs": [sg], "say": speakable(sg, "en")})
    else:
        for sg in segments(I["ar"] if lang == "ar" else I["en"]): units.append({"segs": [sg], "say": speakable(sg, lang)})
    segs, times, files, t = [], [], [], INTRO
    for i, u in enumerate(units):
        f = tmp / f"{lang}{key}_{i}.mp3"
        if preview: d = 0.45 * sum(len(x.split()) for x in u["segs"]) + .4
        else:
            if lang == "ar" and "q" in u: fetch("https://everyayah.com/data/Alafasy_128kbps/%03d%03d.mp3" % u["q"], f)
            else: asyncio.run(tts(u["say"], VOICE[lang], f, lang))
            d = dur(f)
        files.append((f, t)); wc = [max(1, len(x.split())) for x in u["segs"]]; st = t
        for sg, w in zip(u["segs"], wc):
            dd = d * w / sum(wc); segs.append(sg); times.append([round(st, 2), round(st + dd, 2)]); st += dd
        t += d + (0.45 if "q" in u else GAP)
    total = t + OUTRO
    pre = [] if I["kind"] == "q" else [ISNAD]
    post = [] if I["kind"] != "h" or sc.get("noend") else [END]
    beats, miss = beat_times(pre + sc["b"] + post, segs, times, lang)
    if miss: print(f"  ⚠️ {key}-{lang} كلمات ما انلگت:", miss, file=sys.stderr)
    data = {"lang": lang, "n": I.get("n", 0), "segs": segs, "times": times, "total": total, "beats": beats, "quran": I["kind"] == "q",
            "icon": "data:image/png;base64," + __import__("base64").b64encode((ROOT / "icon-192.png").read_bytes()).decode(),
            "hl": sc.get("hl", {}).get(lang, []),
            "title": I["ta"] if lang == "ar" else I["te"], "label": I["ser"][lang],
            "src": I["src_ar"] if lang == "ar" else I["src_en"]}
    html = tmp / f"{lang}{key}.html"
    html.write_text((HERE / "page.html").read_text(encoding="utf-8").replace("/*DATA*/", "window.D=" + json.dumps(data, ensure_ascii=False) + ";"), encoding="utf-8")
    for f in ("fonts/ui-700.woff2", "fonts/ui-500.woff2", "fonts/amiri.woff2", "icon-192.png"):
        dst = tmp / f; dst.parent.mkdir(exist_ok=True)
        if not dst.exists(): shutil.copy(ROOT / f, dst)
    shutil.copy(HERE / "engine.js", tmp / "engine.js")
    if preview:
        outp = Path(__import__("os").environ.get("PREVIEW_DIR", tempfile.gettempdir())); outp.mkdir(exist_ok=True)
        subprocess.run(["node", str(HERE / "shot.js"), str(html), "preview", str(outp / f"{key}-{lang}.png"), json.dumps([b["t"] + 1.6 for b in beats][:9])], check=True)
        return outp / f"{key}-{lang}.png", total
    audio = tmp / f"{lang}{key}.m4a"
    inp, flt = [], []
    for i, (f, st) in enumerate(files):
        inp += ["-i", str(f)]; flt.append(f"[{i}]aresample=44100,adelay={int(st*1000)}|{int(st*1000)}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(files)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(flt) + f";{mix}amix=inputs={len(files)}:normalize=0,{QURAN_FX if (I["kind"] == "q" and lang == "ar") else VOICE_FX},apad=whole_dur={total}[o]", "-map", "[o]", "-t", str(total), "-ac", "1", "-c:a", "aac", "-b:a", "80k", str(audio)], check=True)
    out = OUT / f"{key}-{lang}.mp4"
    subprocess.run(["node", str(HERE / "shot.js"), str(html), "video", str(out), str(FPS), str(total), str(audio)], check=True)
    return out, total

def index():
    items = []
    H, SC = hadiths(), json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))
    def title(text, key):
        # عنوان مقطع الحديث: الجملة الي بيها أول كلمة من المشاهد، بالحرف من النص
        for sg in segments(text):
            if norm(key.split("|")[0]).strip() in norm(sg): return sg.replace(" ", " ").strip(' "“”«»')
        return segments(text)[0].replace(" ", " ")
    for it in CAT["items"]:
        a, e = OUT / f"{it['id']}-ar.mp4", OUT / f"{it['id']}-en.mp4"
        if a.exists() and e.exists():
            items.append({"id": it["id"], "s": it["s"], "ar": a.name, "en": e.name, "da": round(dur(a)), "de": round(dur(e)), "ta": it["ta"], "te": it["te"]})
    for n in sorted(H):
        a, e = OUT / f"h{n}-ar.mp4", OUT / f"h{n}-en.mp4"
        if a.exists() and e.exists():
            b0 = SC[str(n)]["b"][0]
            items.append({"id": f"h{n}", "s": "nawawi", "n": n, "ar": a.name, "en": e.name, "da": round(dur(a)), "de": round(dur(e)), "ta": title(H[n][1], b0[0]), "te": title(H[n][2], b0[1])})
    ser = [{"k": k, "ar": v["ar"], "en": v["en"]} for k, v in CAT["series"].items()]
    (OUT / "index.json").write_text(json.dumps({"series": ser, "items": items}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(items)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("n", nargs="*"); ap.add_argument("--lang"); ap.add_argument("--preview", action="store_true"); ap.add_argument("--index", action="store_true"); ap.add_argument("--new", action="store_true")
    a = ap.parse_args()
    if a.index: print("index", index()); return
    OUT.mkdir(parents=True, exist_ok=True)
    keys = a.n or ([x["id"] for x in CAT["items"]] if a.new else [str(k) for k in sorted(hadiths())])
    for k in keys:
        I = item(k)
        with tempfile.TemporaryDirectory() as td:
            for lang in ([a.lang] if a.lang else ["ar", "en"]):
                f, t = build(I, lang, Path(td), a.preview)
                print(k, lang, f.name, round(t, 1), "s", (f.stat().st_size // 1024), "KB", flush=True)
    if not a.preview and not a.n: print("index", index())

if __name__ == "__main__":
    main()
