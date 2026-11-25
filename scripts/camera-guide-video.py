#!/usr/bin/env python3
"""يصنع فيديو شرح إعدادات الكاميرا (Sony ZV-E10 II) خطوة بخطوة، بصوت عراقي.

كل شريحة: رقم الخطوة، شنو تسوي بالعربي، والمسار بالكاميرا بالضبط مثل ما يبين بالشاشة.
التشغيل:  python3 scripts/camera-guide-video.py   ->  studio/camera/guide-video.mp4
"""
import asyncio
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "designer" / "fonts"
OUT = ROOT / "studio" / "camera" / "guide-video.mp4"
VOICE = "ar-IQ-BasselNeural"
W, H = 1920, 1080
BG, CARD, GOLD, WHITE, GRAY = (12, 12, 16), (28, 28, 36), (255, 196, 0), (245, 245, 245), (160, 160, 170)

# (العنوان، المسار بالكاميرا (سطور)، الشرح على الشاشة، الي يحچيه الصوت)
STEPS = [
    ("إعداد الكاميرا من الصفر", [], "مرة وحدة بس. بعدها كل يوم: تشغّل، تختار MR 1، وتدوس تسجيل",
     "هلا بيك. هذا الفيديو يضبطلك الكاميرا من الصفر. تسويها مرة وحدة بس، وبعدها كل يوم تشغّل الكاميرا وتدوس تسجيل، والفيديو يطلع جاهز."),
    ("قبل كل شي: الكارت", ["MENU > Shooting > Media > Format"],
     "كارت SD سرعته V30 أو أعلى (مكتوب عليه). فرمته بالكاميرا. (انتبه: يمسح كل شي عليه)",
     "أول شي الكارت. لازم يكون مكتوب عليه في ثلاثين أو أعلى. انقل أي شي عليه للموبايل، وبعدين فرمته من داخل الكاميرا."),
    ("النظام: NTSC", ["MENU > Setup > Area/Date", "> NTSC/PAL Selector > NTSC"],
     "هذا يفتح الإعداد الي يخلي الفيديو صغير وواضح. الكاميرا تطفي وتشتغل وتطلب فرمتة: وافق",
     "هسه نغيّر نظام الكاميرا لـ إن تي إس سي. هذا الي يفتح أحسن إعداد للجودة والحجم. الكاميرا راح تطلب فرمتة، وافق."),
    ("نوع الملف", ["MENU > Shooting > Image Quality/Rec", "> File Format > XAVC HS 4K"],
     "XAVC HS = ضغط حديث: نفس الوضوح بنص الحجم",
     "نوع الملف، اختار إكس إيه في سي، إتش إس، فور كي. هذا ضغط حديث، يعطيك نفس الوضوح بنص الحجم."),
    ("الفريمات والجودة", ["Movie Settings > Rec Frame Rate > 24p", "Record Setting > 30M 4:2:0 10bit"],
     "24 فريم = شكل سينما. 30M = تقريباً 4.5 گيگا لكل 20 دقيقة. 10bit = ألوان بلا تكسّر",
     "الفريمات أربعة وعشرين، شكل السينما. والجودة ثلاثين ميگا، عشرة بت. يعني كل عشرين دقيقة تقريباً أربعة گيگا ونص، والألوان ما تتكسر."),
    ("النسخة الصغيرة: طفّيها", ["MENU > Shooting > Image Quality/Rec", "> Proxy Settings > Proxy Recording > Off"],
     "حتى ما تنتقل نسخة ضعيفة للموبايل وتبين الفيديو مكسّر",
     "طفّي النسخة الصغيرة، حتى ما تنتقل نسخة ضعيفة لموبايلك وتحس الفيديو مكسّر."),
    ("الوضع اليدوي (أهم خطوة)", ["زر الوضع (فوگ الكاميرا) > فيديو", "MENU > Shooting > Shooting Mode > Exposure Mode", "> Manual Exposure"],
     "بالوضع الأوتوماتيكي (علامة i الخضرة) الفلاتر ما تشتغل أبداً",
     "أهم خطوة. حوّل الكاميرا لوضع الفيديو، وبعدين الوضع اليدوي. بالأوتوماتيكي، العلامة الخضرة، الفلاتر ما تشتغل أبداً."),
    ("الغالق والفتحة", ["Shutter: 1/50", "F: أصغر رقم بعدستك (مثلاً F3.5 أو F1.8)"],
     "1/50 = حركة طبيعية وبلا رمشة ضوء. الفتحة المفتوحة = ضوء أكثر وخلفية ضبابية",
     "سرعة الغالق واحد على خمسين، حتى الحركة تطلع طبيعية والضوء ما يرمش. والفتحة على أصغر رقم بعدستك."),
    ("ISO ثابت", ["ISO: أقل رقم تقبله الكاميرا ويا الفلتر", "مو AUTO"],
     "كل ما يرتفع ISO، الحبوب تزيد. الصورة غامگة؟ قوّي الضوء، مو ISO",
     "الآيزو خليه ثابت على أقل رقم، مو أوتوماتيكي. إذا الصورة غامگة، قوّي الضوء على وجهك، لا ترفع الآيزو."),
    ("توازن الأبيض", ["MENU > Exposure/Color > White Balance", "> Custom 1 > SET", "وجّه الكاميرا على ورقة بيضة تحت ضوء وجهك"],
     "هيچ لون وجهك يطلع صح بكل مرة، مهما غيّرت لون الخلفية",
     "توازن الأبيض. اختار كستم، وحط ورقة بيضة تحت ضوء وجهك، والكاميرا تتعلم اللون الصح. هيچ وجهك يطلع صح كل مرة."),
    ("الفوكس على وجهك", ["MENU > Focus > AF/MF > Focus Mode > AF-C", "Subject Recognition > On > Human"],
     "الكاميرا تلحق عيونك وحدها. لا تخليه يدوي (MF)",
     "الفوكس، خليه أوتوماتيكي مستمر، وفعّل التعرف على الإنسان. الكاميرا تلحق عيونك وحدها."),
    ("حط الفلاتر بالكاميرا", ["Creators' App > Camera Settings > LUT Management", "حط 1.cube بمكان User1 ... لحد 7.cube بـ User7"],
     "أو بالكارت: PRIVATE > SONY > PRO > LUT",
     "هسه الفلاتر. من تطبيق سوني على موبايلك، ادخل على إدارة الفلاتر، وحط الملف واحد بمكان يوزر واحد، لحد الملف سبعة."),
    ("تعويض الإضاءة لكل فلتر", ["MENU > Exposure/Color > Color/Tone", "> Manage User LUTs > Import/Edit", "> AE Level Offset > +5/3EV"],
     "لكل فلتر من السبعة. هذا الي يشيل الحبوب",
     "لكل فلتر من السبعة، ادخل على تعويض الإضاءة وخليه زائد خمسة على ثلاثة. هذا الي يشيل الحبوب من الصورة."),
    ("اختار الستايل", ["MENU > Exposure/Color > Color/Tone", "> Log Shooting Setting > Off", "Picture Profile > PPLUT1 > Basic Look > User1"],
     "PPLUT1=1 وثائقي | PPLUT2=2 فيلم | PPLUT3=3 دراما | PPLUT4=4 غموض",
     "طفّي التصوير الخام. وبعدين بالبكچر بروفايل، اختار بي بي لت واحد، وحط بيه الفلتر واحد، الوثائقي. وبي بي لت اثنين الفيلم، وثلاثة الدراما، وأربعة الغموض."),
    ("شغلات صغيرة مهمة", ["SteadyShot > Off   (الكاميرا على حامل)", "Shading Comp. > Off", "Zebra > On > 70"],
     "الزيبرا: خطوط خفيفة على خدودك بس = الإضاءة مضبوطة",
     "شغلات صغيرة: طفّي المثبت لأن الكاميرا على حامل، وطفّي تعويض ظلام الزوايا، وشغّل الزيبرا على سبعين. خطوط خفيفة على خدودك يعني الإضاءة مضبوطة."),
    ("احفظ كل شي", ["MENU > Shooting > Shooting Mode", "> Camera Set. Memory > 1"],
     "من هسه: شغّل الكاميرا، اختار MR 1، دوس تسجيل",
     "آخر شي، احفظ كل الإعدادات بالذاكرة رقم واحد. من هسه، كل يوم تشغّل الكاميرا، تختار إم آر واحد، وتدوس تسجيل."),
    ("الإضاءة: سر الصورة", ["ضوء أبيض قوي على وجهك (45 درجة، قريب)", "الضوء الملوّن على الخلفية بس، وأضعف من وجهك", "ضوء الغرفة: مطفي"],
     "الفلتر يرتّب الألوان. الوضوح يجي من الضوء",
     "وتذكّر، الوضوح يجي من الضوء. ضوء أبيض قوي وقريب على وجهك، والضوء الملوّن على الخلفية بس، وضوء الغرفة مطفي."),
    ("حجم الفيديو", ["20 دقيقة = تقريباً 4.5 گيگا", "30 دقيقة = تقريباً 6.7 گيگا"],
     "تريد كل ملف أقل من 5 گيگا؟ وگّف التسجيل وابديه من جديد كل 20 دقيقة",
     "بهالإعدادات، كل عشرين دقيقة تقريباً أربعة گيگا ونص. إذا تريد كل ملف أقل من خمسة، وگّف وابدي التسجيل كل عشرين دقيقة. بالتوفيق."),
]


def font(size, name="Tajawal-Black.ttf"):
    return ImageFont.truetype(str(FONTS / name), size)


def slide(i, title, path, note):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=GOLD)
    if i:
        d.ellipse((W - 230, 70, W - 90, 210), fill=GOLD)
        d.text((W - 160, 140), str(i), fill=BG, font=font(80, "Cairo-Black.ttf"), anchor="mm")
        d.text((W - 270, 140), title, fill=WHITE, font=font(72), anchor="rm", direction="rtl")
    else:
        d.text((W // 2, 330), title, fill=WHITE, font=font(110), anchor="mm", direction="rtl")
    y = 300
    for line in path:
        d.rounded_rectangle((140, y, W - 140, y + 110), 22, fill=CARD, outline=GOLD, width=3)
        arabic = any("؀" <= c <= "ۿ" for c in line)
        d.text((W // 2, y + 55), line, fill=GOLD if not arabic else WHITE, font=font(50), anchor="mm",
               direction="rtl" if arabic else None)
        y += 135
    d.text((W // 2, H - 130 if path else 560), note, fill=GRAY if path else GOLD, font=font(40), anchor="mm",
           direction="rtl")
    d.text((W // 2, H - 40), f"{i} / {len(STEPS) - 1}" if i else "", fill=GRAY, font=font(28), anchor="mm")
    return im


async def voice(text, out):
    import edge_tts
    await edge_tts.Communicate(text, VOICE, rate="-8%").save(str(out))


def dur(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        parts = []
        for i, (title, path, note, say) in enumerate(STEPS):
            png, mp3, mp4 = tmp / f"{i}.png", tmp / f"{i}.mp3", tmp / f"{i}.mp4"
            slide(i, title, path, note).save(png)
            asyncio.run(voice(say, mp3))
            t = dur(mp3) + 1.6   # وقفة بعد الحچي حتى يلحق يقرا المسار
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-i", str(mp3),
                            "-af", "apad", "-t", f"{t:.2f}", "-c:v", "libx264", "-tune", "stillimage", "-r", "25",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", str(mp4)], check=True)
            parts.append(mp4)
            print(f"✓ {i}: {title}  ({t:.0f} ثانية)")
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", "-movflags", "+faststart", str(OUT)], check=True)
    print("✓", OUT, f"({dur(OUT) / 60:.1f} دقيقة)")


if __name__ == "__main__":
    main()
