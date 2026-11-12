#!/usr/bin/env python3
"""مكتبة مقاطع أوّاب: يصنع فيديو موشن گرافيك عمودي لكل حديث (عربي + إنگليزي)، كله بالكود.
- النص: من hadith.js بالحرف (الأربعون النووية). ما نغيّر حرف.
- المشاهد: scenes.json (لكل حديث لقطات تبدي عند كلمة معيّنة بالنص).
- الرسم: engine.js على canvas، ونصوّر كل إطار بمتصفح Playwright.
- الصوت: أصوات مايكروسوفت المجانية (edge-tts)، الجملة بنَفَس واحد، ومعالجة وتسوية بـ audio.py.
التشغيل: python3 scripts/motion/make-videos.py [أرقام الأحاديث...] [--lang ar|en] [--preview] [--audio-only DIR] [--no-amb]
المخرجات: links/salah/v/h<رقم>-<لغة>.mp4 و links/salah/v/index.json"""
import argparse, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audio as AU  # الصوت: الراوي ومعالجته، والجو، والتسوية النهائية (audio.py)
ROOT = HERE.parent.parent / "links" / "salah"
OUT = ROOT / "v"
VOICE = {"ar": "ar-SA-HamedNeural", "en": "en-US-AndrewNeural"}
FPS = 24
INTRO, OUTRO = 2.6, 3.2
# صوت الراوي المعتمد (اختاره صاحب القناة 12 تشرين الثاني 2026): حامد السعودي، أبطأ وأعمق
PROSODY = {"ar": (-14, -4), "en": (-10, -2)}   # (السرعة %، طبقة الصوت Hz)
# الراوي يقرا الجملة كاملة بنَفَس واحد، والسكتة بعدها حسب علامة الوقف
GAP = {"end": 0.6, "colon": 0.34, "comma": 0.24, "quran": 0.45}
AMBIENCE = True   # جو طبيعي خفيف (هوا، ماي، غرفة) بلا موسيقى، وبس بمقاطع الأحاديث

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

def say_units(segs, lang, hl):
    """نجمع مقاطع العرض بجمل: كل جملة تنقرا بنفس واحد (الصوت طبيعي وما ينقطع بنص العبارة)"""
    out, cur = [], []
    for sg in segs:
        cur.append(sg); t = strip(sg).strip(); w = sum(len(x.split()) for x in cur)
        kind = ("end" if re.search(r"[.؟?!][\"”’'\]\)\s]*$", t) else "colon" if re.search(r"[:：]\W*$", t)
                else "comma" if (w >= 22 and re.search(r"[،,;؛]\W*$", t)) or w >= 40 else None)
        if kind: out.append([cur, kind]); cur = []
    if cur: out.append([cur, "end"])
    body = [i for i, (c, _) in enumerate(out) if not re.match(r"\s*(رواه|تابعه|\[)", norm(" ".join(c)).strip() + " ")]
    units = []
    for i, (c, kind) in enumerate(out):
        txt = " ".join(c); r, p = PROSODY[lang]
        nw = len(txt.split())
        if i not in body: r += 5                          # المصدر (رواه...): أسرع شوية
        elif nw <= 4: r -= 6; p -= 1                     # عبارة قصيرة مهمة: أبطأ وأعمق
        else:
            if any(norm(h).strip() in norm(txt) for h in hl): r -= 3   # بيها الكلمة المفتاح
            if i == body[-1]: r -= 3                      # آخر جملة: نختم بهدوء
        units.append({"segs": c, "say": [speakable(x, lang) for x in c], "gap": GAP[kind], "rate": r, "pitch": p})
    return units

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

def build(I, lang, tmp, preview=False, audio_dir=None):
    key, sc = I["key"], I["sc"]
    hl = sc.get("hl", {}).get(lang, [])
    # الوحدات: كل وحدة مقطع صوت واحد (جملة كاملة أو آية)، وبيها مقطع عرض أو أكثر
    units = []
    if I["kind"] == "q":
        C = I["c"]; s_ = C["surah"]
        bas = "In the name of Allah, the Entirely Merciful, the Especially Merciful."
        if C["basmala"]: units.append({"segs": [C["basmala"]], "q": (1, 1), "gap": GAP["quran"]} if lang == "ar" else
                                      {"segs": [bas], "say": [bas], "gap": GAP["end"], "rate": PROSODY[lang][0] - 3, "pitch": PROSODY[lang][1]})
        for a in C["ayat"]:
            if lang == "ar":
                cs = chunks(a["ar"]); cs[-1] += " ﴿" + str(a["k"]).translate(AR_DIG) + "﴾"
                units.append({"segs": cs, "q": (s_, a["k"]), "gap": GAP["quran"]})
            else:
                us = say_units(segments(a["en"]), "en", hl)
                for u in us[:-1]: units.append(u)
                us[-1]["gap"] = GAP["end"] + 0.15; units.append(us[-1])   # سكتة أطول بين الآيات
    else:
        units = say_units(segments(I["ar"] if lang == "ar" else I["en"]), lang, hl)
    segs, times, clips, t = [], [], [], INTRO
    for i, u in enumerate(units):
        if preview:
            d = 0.42 * sum(len(x.split()) for x in u["segs"]) + .3; rel = None
        elif "q" in u:
            f = tmp / f"{lang}{key}_{i}.mp3"
            fetch("https://everyayah.com/data/Alafasy_128kbps/%03d%03d.mp3" % u["q"], f)
            x = AU.decode(f); d = len(x) / AU.SR; rel = None; clips.append((x, t))
        elif not re.search(r"[\u0621-\u064Aa-zA-Z]", " ".join(u["say"])):
            d = 0.3; rel = None   # ما بيها كلام (علامة بس): سكتة قصيرة
        else:
            v, f_ = VOICE[lang], lambda n: f"{n:+d}"
            x, rel = AU.speak(u["say"], v, f_(u["rate"]) + "%", f_(u["pitch"]) + "Hz")
            d = len(x) / AU.SR; clips.append((x, t))
        if rel is None:
            rel = AU._even(u["segs"], 0.0, d)
        for sg, (a_, b_) in zip(u["segs"], rel):
            segs.append(sg); times.append([round(t + a_, 2), round(t + b_, 2)])
        t += d + u["gap"]
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
    voice = AU.np.zeros(int(total * AU.SR) + 1, AU.np.float32)
    for x, st in clips:
        a_ = int(st * AU.SR); voice[a_:a_ + len(x)] += x[:len(voice) - a_]
    recite = I["kind"] == "q" and lang == "ar"
    m = AU.master(voice, audio, beats, total, amb=AMBIENCE and I["kind"] != "q", seed=sum(map(ord, key + lang)), quran=recite)
    print(f"  🔊 {key}-{lang}: {m['I']:.1f} LUFS · ذروة {m['TP']:.1f} dBTP · مدى {m['LRA']:.1f} LU", flush=True)
    if audio_dir:
        Path(audio_dir).mkdir(parents=True, exist_ok=True); shutil.copy(audio, Path(audio_dir) / f"{key}-{lang}.m4a")
        return Path(audio_dir) / f"{key}-{lang}.m4a", total
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
    ap.add_argument("--audio-only", metavar="DIR", help="يصنع الصوت بس (m4a) بهذا المجلد، بلا فيديو")
    ap.add_argument("--no-amb", action="store_true", help="بلا جو طبيعي")
    a = ap.parse_args()
    global AMBIENCE
    if a.no_amb: AMBIENCE = False
    if a.index: print("index", index()); return
    OUT.mkdir(parents=True, exist_ok=True)
    keys = a.n or ([x["id"] for x in CAT["items"]] if a.new else [str(k) for k in sorted(hadiths())])
    for k in keys:
        I = item(k)
        with tempfile.TemporaryDirectory() as td:
            for lang in ([a.lang] if a.lang else ["ar", "en"]):
                f, t = build(I, lang, Path(td), a.preview, a.audio_only)
                print(k, lang, f.name, round(t, 1), "s", (f.stat().st_size // 1024), "KB", flush=True)
    if not a.preview and not a.n and not a.audio_only: print("index", index())

if __name__ == "__main__":
    main()
