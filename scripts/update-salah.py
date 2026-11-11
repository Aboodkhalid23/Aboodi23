#!/usr/bin/env python3
"""يسحب جدول الصلاة الرسمي من موقع مسجد توركو (tisy.fi) ويحدّث links/salah/data.js وملف التقويم.
إذا الموقع ما فتح أو الجدول طلع غريب، ما يغيّر شي ويبقى الجدول القديم.
التشغيل: python3 scripts/update-salah.py   (يشتغل تلقائياً كل يوم ويا نشر الصفحة)"""
import datetime as dt, html, json, re, subprocess, sys, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

URL = "https://tisy.fi/timetable/"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "links" / "salah" / "data.js"
TZ = ZoneInfo("Europe/Helsinki")
HIJRI = ["muharram", "safar", "rabialawwal", "rabialakhar", "jumadaalawwal", "jumadaalakhirah",
         "rajab", "shaban", "ramadan", "shawwal", "dhulqadah", "dhulhijjah"]

def fail(msg):
    print("ما تحدّث الجدول:", msg); sys.exit(0)

def minutes(s):
    h, m = s.split(":"); return int(h) * 60 + int(m)

def parse(page):
    m = re.search(r"January\s+(20\d\d)\s+([A-Za-z\- ]+?)\s+(14\d\d)", html.unescape(re.sub(r"<[^>]+>", " ", page)))
    if not m: fail("ما لگيت السنة بالصفحة")
    year = int(m.group(1))
    key = re.sub(r"[^a-z]", "", m.group(2).lower()).replace("awal", "awwal")
    hm = HIJRI.index(key) if key in HIJRI else None
    cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r'wplhc__timetable--body--item[^"]*">(.*?)</div>', page, re.S)]
    rows, i = [], 0
    while i + 8 < len(cells):                       # اليوم، اسمه، الهجري، وبعدها ست أوقات
        if ":" not in cells[i] and all(re.fullmatch(r"\d{1,2}:\d\d", c) for c in cells[i + 3:i + 9]):
            rows.append(cells[i:i + 9]); i += 9
        else: i += 1
    return year, hm, int(m.group(3)), rows

def clean(year, rows):
    days = 366 if (year % 4 == 0 and (year % 100 or year % 400 == 0)) else 365
    if len(rows) != days: fail(f"عدد الأيام {len(rows)} مو {days}")
    t, h, d = [], [], dt.date(year, 1, 1)
    for r in rows:
        if int(r[0]) != d.day: fail(f"تسلسل الأيام غلط عند {d}")
        summer = dt.datetime(d.year, d.month, d.day, 12, tzinfo=TZ).utcoffset() != dt.timedelta(hours=2)
        v = [minutes(x) - (60 if summer else 0) for x in r[3:]]     # نخزن بالتوقيت الشتوي
        if v[5] < v[4]: v[5] += 1440                                  # عشاء الصيف بعد نص الليل
        t.append(v); h.append(int(r[2])); d += dt.timedelta(days=1)
    fixed = []
    for c in range(6):                                # غلطة ساعة كاملة بيوم واحد (مطبعية أو نسيان تغيير الساعة)
        for k in range(1, len(t) - 1):
            off = t[k][c] - (t[k - 1][c] + t[k + 1][c]) / 2
            if abs(abs(off) - 60) <= 6:
                t[k][c] -= 60 if off > 0 else -60; fixed.append((k, c))
    for k in range(len(t) - 1):
        if any(abs(t[k + 1][c] - t[k][c]) > 8 for c in range(6)): fail(f"قفزة غريبة باليوم رقم {k + 2}")
        if any(t[k][c] >= t[k][c + 1] for c in range(5)): fail(f"ترتيب الأوقات غلط باليوم رقم {k + 1}")
    if days == 366: t.pop(59); h.pop(59)              # الصفحة تحسب 365 يوم؛ 29 شباط ياخذ أوقات 28
    return t, h, fixed

HEL_URL = "https://rukousajat.fi/"

def helsinki():
    """جدول مساجد هلسنكي وإسبو وفانتا: مخزون داخل ملف موقع rukousajat.fi بمفاتيح يوم+شهر. يرجع None إذا ما انسحب."""
    try:
        get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (prayer-times-updater)"}), timeout=60).read().decode("utf-8", "ignore")
        js = re.search(r'src="(/static/js/main\.[0-9a-f]+\.js)"', get(HEL_URL))
        rows = re.findall(r'date:"(\d{4})",fajr:"([\d:]+)",sunrise:"([\d:]+)",zuhur:"([\d:]+)",asr:"([\d:]+)",maghrib:"([\d:]+)",isha:"([\d:]+)"', get(HEL_URL.rstrip("/") + js.group(1)))
        by = {r[0]: [minutes(x) for x in r[1:]] for r in rows}
        t, d = [], dt.date(2026, 1, 1)                      # سنة عادية (365 يوم) بس حتى نمشي على الأيام بالترتيب
        while d.year == 2026:
            v = list(by[f"{d.day:02d}{d.month:02d}"])
            if v[5] < v[4]: v[5] += 1440
            t.append(v); d += dt.timedelta(days=1)
        # الجدول مكتوب بساعة الحايط: نلگى يوم تقديم الساعة ويوم تأخيرها من قفزة الظهر، ونرجّع الصيف للتوقيت الشتوي
        jump = [k for k in range(1, 365) if abs(abs(t[k][2] - t[k - 1][2]) - 60) <= 3]
        if len(jump) != 2: return None
        for k in range(jump[0], jump[1]): t[k] = [x - 60 for x in t[k]]
        for k in range(364):
            # الفجر والعشاء بيهم قفزات حقيقية (لحد ساعتين) يوم يتبدل حساب الصيف، والباقي لازم يمشي ناعم
            if any(abs(t[k + 1][c] - t[k][c]) > (130 if c in (0, 5) else 8) for c in range(6)) or any(t[k][c] >= t[k][c + 1] for c in range(5)): return None
        return t
    except Exception as e:
        print("جدول هلسنكي ما انسحب:", e); return None

def main():
    old = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    hel_line = next((l for l in old.splitlines() if l.startswith("window.HEL=")), "")
    ht = helsinki()
    if ht:
        hel_line = "window.HEL=" + json.dumps({"t": ht}, separators=(",", ":")) + ";"
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (prayer-times-updater)"})
        page = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore")
    except Exception as e:
        fail(f"الموقع ما فتح ({e})")
    year, hm, hy, rows = parse(page)
    t, h, fixed = clean(year, rows)
    data = {"y": year, "hm": hm, "hy": hy, "t": t, "h": h}
    new = ("// جدول مسجد توركو (tisy.fi) لسنة %d، وجدول مساجد هلسنكي (rukousajat.fi). بالدقايق من نص الليل بالتوقيت الشتوي\nwindow.SALAH=%s;\n%s\n"
           % (year, json.dumps(data, separators=(",", ":")), hel_line))
    changed = not OUT.exists() or OUT.read_text(encoding="utf-8") != new
    OUT.write_text(new, encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make-salah-ics.py")], check=True)
    print(f"جدول {year}: {'تحدّث' if changed else 'نفسه بدون تغيير'}، وتصلّحت {len(fixed)} خانة بيها غلطة ساعة. هلسنكي: {'انسحب' if ht else 'بقى القديم'}")

main()
