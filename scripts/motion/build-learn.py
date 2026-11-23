#!/usr/bin/env python3
"""يضيف دروس جديدة لقسم التعليم (links/salah/learn.js)، كل نص بالحرف من مصدره:
- القرآن: api.alquran.cloud (الرسم العثماني + ترجمة صحيح إنترناشونال)، والتلاوة مشاري العفاسي (everyayah.com)
- الحديث: صحيح البخاري من مجموعة hadith-api المفتوحة (عربي + إنگليزي)
- الأذكار: حصن المسلم (hisnmuslim.com) النص والترجمة الرسمية والتسجيل البشري
الخطوة: [عربي، إنگليزي، رسمة، نطق، عنوان عربي، عنوان إنگليزي، تسجيل]
التشغيل: python3 scripts/motion/build-learn.py"""
import json, re, time, urllib.request
from pathlib import Path
F = Path(__file__).resolve().parents[2] / "links" / "salah" / "learn.js"
AR_DIG = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

def get(url):
    for i in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "awwab"}), timeout=60).read().decode("utf-8-sig")
        except Exception:
            if i == 4: raise
            time.sleep(3)

def ayah(s, a, art):
    ar = json.loads(get(f"https://api.alquran.cloud/v1/ayah/{s}:{a}/quran-uthmani"))["data"]
    en = json.loads(get(f"https://api.alquran.cloud/v1/ayah/{s}:{a}/en.sahih"))["data"]
    txt = ar["text"]
    return [txt + " ﴿" + str(a).translate(AR_DIG) + "﴾", en["text"], art, "", f"{ar['surah']['name']} · {str(a).translate(AR_DIG)}",
            f"Surah {ar['surah']['englishName']} {s}:{a}", "https://everyayah.com/data/Alafasy_128kbps/%03d%03d.mp3" % (s, a)]

def hisn(ch, art, n=5, maxc=420):
    a = json.loads(get(f"https://www.hisnmuslim.com/api/ar/{ch}.json")); e = json.loads(get(f"https://www.hisnmuslim.com/api/en/{ch}.json"))
    ta, te = list(a)[0], list(e)[0]; out = []
    for x, y in zip(a[ta], e[te]):
        if len(x["ARABIC_TEXT"]) > maxc or not y.get("TRANSLATED_TEXT"): continue
        out.append([x["ARABIC_TEXT"].strip(), y["TRANSLATED_TEXT"].strip(), art, y.get("LANGUAGE_ARABIC_TRANSLATED_TEXT", "").strip(), ta.strip(), te.strip(), x["AUDIO"].replace("http://", "https://")])
        if len(out) >= n: break
    return out

def arkan():
    h = lambda ed: json.loads(get(f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{ed}-bukhari/8.min.json"))["hadiths"][0]["text"]
    ar = h("ara").replace("‏", "").replace("‎", ""); en = h("eng")
    ar = ar[ar.index("عَنِ ابْنِ عُمَرَ"):]
    bare = lambda w: re.sub(r"[\u064B-\u0652\u0670]", "", w)
    cut = ["شهادة", "وإقام", "وإيتاء", "والحج", "وصوم"]
    ws = ar.split(" "); idx = [next(i for i, w in enumerate(ws) if bare(w).strip("،") == c) for c in cut]
    b = [0] + idx + [len(ws)]
    pa = [re.sub(r"\s+", " ", " ".join(ws[b[i]:b[i + 1]])).strip() for i in range(6)]
    pe = re.split(r"\s(?=\d\.\s)", en)
    assert len(pa) == 6 and len(pe) == 6, (pa, pe)
    arts = ["pillars", "p1", "p2", "p3", "p4", "p5"]
    return [[pa[i].replace('"', "").strip(" ،"), pe[i].strip(), arts[i], "", "", ""] for i in range(6)]

SRC_Q = ["المصدر: القرآن الكريم (الرسم العثماني) بتلاوة مشاري العفاسي، والترجمة: صحيح إنترناشونال", "Source: The Holy Quran (Uthmani script), recited by Mishary Alafasy. Translation: Saheeh International"]
SRC_H = ["المصدر: كتاب حصن المسلم (hisnmuslim.com)، النص العربي وترجمته الإنگليزية الرسمية، بالحرف", "Source: Fortress of the Muslim (hisnmuslim.com), Arabic text and its official English translation, verbatim"]
SRC_B = ["المصدر: صحيح البخاري، رقم ٨ (النص من مجموعة hadith-api المفتوحة، بالحرف)", "Source: Sahih al-Bukhari 8 (text from the open hadith-api collection, verbatim)"]

def lessons():
    S, A = {}, {}
    S["arkan"] = {"t": ["أركان الإسلام", "The pillars of Islam"], "src": SRC_B, "steps": arkan()}
    A["zakat"] = {"t": ["الزكاة", "Zakah"], "src": SRC_Q, "steps": [ayah(2, 43, "zakah"), ayah(9, 103, "zakah"), ayah(9, 60, "zakah")]}
    A["siyam"] = {"t": ["الصيام", "Fasting"], "src": SRC_Q, "steps": [ayah(2, 183, "sawm"), ayah(2, 184, "sawm"), ayah(2, 185, "sawm")]}
    A["hajj"] = {"t": ["الحج", "Hajj"], "src": [SRC_Q[0] + "، والأذكار من حصن المسلم", SRC_Q[1] + ". Supplications from Fortress of the Muslim"],
                 "steps": [ayah(3, 97, "hajj"), ayah(22, 27, "hajj"), ayah(2, 197, "hajj")] + hisn(115, "dua", 1) + hisn(117, "dua", 1) + hisn(119, "dua", 1)}
    A["slt"] = {"t": ["مكانة الصلاة", "The place of prayer"], "src": SRC_Q, "steps": [ayah(20, 14, "salahp"), ayah(29, 45, "salahp"), ayah(2, 238, "salahp"), ayah(23, 1, "salahp"), ayah(23, 2, "salahp")]}
    A["as"] = {"t": ["الأذكار بعد السلام", "After the prayer"], "src": SRC_H, "steps": hisn(25, "dua", 6)}
    A["sl"] = {"t": ["النوم والاستيقاظ", "Sleep & waking"], "src": SRC_H, "steps": hisn(28, "dua", 4) + hisn(1, "dua", 2)}
    A["cl"] = {"t": ["اللباس", "Clothing"], "src": SRC_H, "steps": hisn(2, "dua", 1) + hisn(3, "dua", 1) + hisn(5, "dua", 1)}
    A["hz"] = {"t": ["الهم والكرب", "Worry & distress"], "src": SRC_H, "steps": hisn(34, "dua", 2) + hisn(35, "dua", 3)}
    A["tb"] = {"t": ["التوبة والاستغفار", "Repentance"], "src": SRC_H, "steps": hisn(44, "dua", 1) + hisn(129, "dua", 4)}
    A["mr"] = {"t": ["المرض والمصيبة", "Illness & hardship"], "src": SRC_H, "steps": hisn(49, "dua", 2) + hisn(124, "dua", 1) + hisn(53, "dua", 2)}
    A["rn"] = {"t": ["المطر والريح", "Rain & wind"], "src": SRC_H, "steps": hisn(61, "dua", 1) + hisn(62, "dua", 1) + hisn(64, "dua", 1) + hisn(65, "dua", 1)}
    A["ak"] = {"t": ["الغضب والمجلس والعطاس", "Anger, gatherings & sneezing"], "src": SRC_H, "steps": hisn(82, "dua", 1) + hisn(85, "dua", 1) + hisn(77, "dua", 1) + hisn(87, "dua", 1)}
    A["sm"] = {"t": ["أذكار الصائم", "The fasting person"], "src": SRC_H, "steps": hisn(68, "dua", 2) + hisn(75, "dua", 1) + hisn(67, "dua", 1)}
    return S, A

def main():
    t = F.read_text(encoding="utf-8")
    head = t[:t.index("window.LEARN=")]
    L = json.loads(re.search(r"window\.LEARN=(\{.*\});?\s*$", t, re.S).group(1))
    S, A = lessons()
    L.setdefault("sunni", {}).update(S); L.setdefault("all", {}).update(A)
    F.write_text(head + "window.LEARN=" + json.dumps(L, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    for g in (S, A):
        for k, d in g.items(): print(k, d["t"][0], len(d["steps"]), "خطوات")

if __name__ == "__main__":
    main()
