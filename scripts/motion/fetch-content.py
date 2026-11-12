#!/usr/bin/env python3
"""يجمع نصوص المقاطع من مصادرها بالحرف ويحفظها بـ content.json (حتى الصنع يرجع نفسه كل مرة):
- القرآن: api.alquran.cloud (الرسم العثماني + ترجمة Saheeh International)، والتلاوة من everyayah.com (مشاري العفاسي) وقت الصنع.
- البخاري: hadith-api (fawazahmed0) بالعربي والإنگليزي. العربي يبدي من الصحابي (نشيل سلسلة الرواة الطويلة بس، بدون تغيير كلمة).
التشغيل: python3 scripts/motion/fetch-content.py"""
import json, re, urllib.request
from pathlib import Path
HERE = Path(__file__).resolve().parent
BASMALA = "\u0628\u0650\u0633\u0652\u0645\u0650 \u0671\u0644\u0644\u0651\u064e\u0647\u0650 \u0671\u0644\u0631\u0651\u064e\u062d\u0652\u0645\u064e\u0670\u0646\u0650 \u0671\u0644\u0631\u0651\u064e\u062d\u0650\u064a\u0645\u0650"

def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "awwab"}), timeout=60))

def norm(s):
    s = re.sub(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]", "", s)
    return re.sub(r"[أإآٱ]", "ا", s)

def main():
    cat = json.loads((HERE / "catalog.json").read_text(encoding="utf-8"))
    out = {}
    for it in cat["items"]:
        if "q" in it:
            s, a, b = it["q"]
            d = get(f"https://api.alquran.cloud/v1/surah/{s}/editions/quran-uthmani,en.sahih")["data"]
            ar, en = d[0]["ayahs"], d[1]["ayahs"]
            ay = []
            for k in range(a, b + 1):
                t = ar[k - 1]["text"]
                if k == 1 and s not in (1, 9):
                    # الـAPI يلصق البسملة بأول آية؛ نشيلها ونخليها مقطع لحالها بتلاوتها
                    assert t.startswith(BASMALA), (s, t[:40])
                    t = t[len(BASMALA):].strip()
                ay.append({"k": k, "ar": t, "en": en[k - 1]["text"]})
            out[it["id"]] = {"surah": s, "name": d[0]["name"], "ename": d[0]["englishName"], "ayat": ay, "basmala": BASMALA if a == 1 and s not in (1, 9) else ""}
        else:
            n = it["b"]
            ar = get(f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-bukhari/{n}.min.json")["hadiths"][0]["text"].strip()
            en = get(f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-bukhari/{n}.min.json")["hadiths"][0]["text"].strip()
            # نبدي من الصحابي: نلگى أول مكان تبدي بيه العبارة (بدون تشكيل)
            plain = norm(ar); key = norm(it["from"])
            pos = plain.find(key); assert pos >= 0, (n, it["from"])
            # نرجّع الموقع للنص الأصلي (المشكّل)
            j = c = 0
            while c < pos:
                if norm(ar[j]) : c += 1
                j += 1
            ar = ar[j:].strip()
            en = re.sub(r"^Narrated ([^:]+):\s*", r"Narrated \1: ", en)
            out[it["id"]] = {"b": n, "ar": ar, "en": en}
        print(it["id"], "ok")
    (HERE / "content.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main()
