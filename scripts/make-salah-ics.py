#!/usr/bin/env python3
"""يصنع ملف تقويم (salah.ics) من جدول مسجد توركو: حدث لكل صلاة ويا تنبيه قبلها بنص ساعة.
التشغيل: python3 scripts/make-salah-ics.py   (يكتب links/salah/salah.ics من اليوم لحد آخر السنة الجاية)"""
import json, re, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent / "links" / "salah"
BEFORE_MIN = 30
NAMES = {0: "الفجر", 2: "الظهر", 3: "العصر", 4: "المغرب", 5: "العشاء"}
TZ, UTC = ZoneInfo("Europe/Helsinki"), dt.timezone.utc
CUM = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

table = json.loads(re.search(r"window\.SALAH=(\{.*?\});\n", (ROOT / "data.js").read_text(encoding="utf-8")).group(1))["t"]

def row(d):
    day = 28 if (d.month, d.day) == (2, 29) else d.day
    return table[CUM[d.month - 1] + day - 1]

start = dt.date.today().replace(day=1)
end = dt.date(dt.date.today().year + 1, 12, 31)
stamp = dt.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//aboodi23//salah-turku//AR", "CALSCALE:GREGORIAN",
       "X-WR-CALNAME:مواقيت الصلاة توركو", "X-WR-TIMEZONE:Europe/Helsinki",
       "REFRESH-INTERVAL;VALUE=DURATION:P7D", "X-PUBLISHED-TTL:P7D"]
d = start
while d <= end:
    noon = dt.datetime(d.year, d.month, d.day, 12, tzinfo=TZ)
    summer = int(noon.utcoffset().total_seconds() // 60) - 120          # 0 بالشتا، 60 بالصيف
    midnight_utc = dt.datetime(d.year, d.month, d.day, tzinfo=UTC) - dt.timedelta(minutes=120 + summer)
    for i, name in NAMES.items():
        t = midnight_utc + dt.timedelta(minutes=row(d)[i] + summer)   # الجدول بالتوقيت الشتوي
        out += ["BEGIN:VEVENT", f"UID:{d:%Y%m%d}-{i}@salah-turku", f"DTSTAMP:{stamp}",
                f"DTSTART:{t:%Y%m%dT%H%M%SZ}", f"DTEND:{t + dt.timedelta(minutes=10):%Y%m%dT%H%M%SZ}",
                f"SUMMARY:صلاة {name}", "TRANSP:TRANSPARENT",
                "BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:باقي نص ساعة على صلاة {name}",
                f"TRIGGER:-PT{BEFORE_MIN}M", "END:VALARM", "END:VEVENT"]
    d += dt.timedelta(days=1)
out.append("END:VCALENDAR")
(ROOT / "salah.ics").write_text("\r\n".join(out) + "\r\n", encoding="utf-8")
print(f"{out.count('BEGIN:VEVENT')} حدث من {start} لحد {end}")
