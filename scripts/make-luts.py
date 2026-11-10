#!/usr/bin/env python3
"""يصنع فلاتر (LUT) خاصة لكاميرا سوني ZV-E10 II.

الفلتر ياخذ صورة الكاميرا الخام (S-Log3 / S-Gamut3.Cine) ويطلعها جاهزة (Rec.709)
بستايل معين. الملفات تنحط بالكاميرا وتنطبع داخل الفيديو عن طريق PPLUT1-4.

النسخة الثانية (تشرين الثاني 2026)، بعد ما اشتكى صاحب القناة إن الفلاتر ضعيفة وبيها حبوب:
- كل فلتر ينزّل الإضاءة 5/3 وقفة، فتصوّر أفتح بنفس المقدار (AE Level Offset = 5/3EV).
  ضوء أكثر على الحساس = حبوب أقل. هذا حل سوني الرسمي لتشويش S-Log3.
- ظلال أعمق وألوانها أهدأ (التشويش الملوّن يعيش بالظلال)، وألوان أغنى وتباين أقوى.
- ناتج الفلتر بمستوى الفيديو (مثل فلاتر سوني الرسمية) مو المدى الكامل.

التشغيل:
    python3 scripts/make-luts.py            # يصنع كل الفلاتر بـ studio/camera/luts
    python3 scripts/make-luts.py --preview  # وياها صورة لكل فلتر وصورة مقارنة
    python3 scripts/make-luts.py --list     # قائمة الفلاتر (JSON)
"""
import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CAM = ROOT / "studio" / "camera"
OUT = CAM / "luts"
SIZE = 33  # الكاميرا تقبل 17 أو 33 نقطة، وحجم الملف لازم أقل من 1 ميگا

EXPO = 5.0 / 3.0   # الفلتر ينزّل الإضاءة بهالمقدار (وقفات)، فالتصوير لازم يكون أفتح بيه
WHITE_IN = 3.2     # ضوء المشهد (بعد التنزيل) الي يوصل للأبيض الكامل = حد احتراگ الحساس تقريباً
OUT_GAMMA = 2.2    # شاشات الموبايل والكمبيوتر
SHADOW_SAT = 0.4   # تشبع أعمق الظلال (أقل = تشويش ملوّن أقل)
# مستوى الناتج: الكاميرا تكتب ناتج الفلتر بالملف مثل ما هو، والمشغلات تعتبر 64 أسود و940 أبيض
# (هيچ فلاتر سوني الرسمية). محد وثّق هذا لكاميرتنا بالذات، فنختار مستوى "آمن" بالنص:
# يطلع صح بالحالة الأرجح، ويبقى مقبول (أسود 3% مو رمادي) لو الكاميرا تعامله كمدى كامل.
BLACK_OUT, WHITE_OUT = 0.030, 0.940
LEGAL_LO, LEGAL_HI = 64 / 1023, 940 / 1023

# ---------- رياضيات سوني الرسمية ----------
# S-Gamut3.Cine -> XYZ -> Rec.709 (كلها D65)
SG3C_TO_XYZ = np.array([
    [0.5990839208, 0.2489255161, 0.1024464902],
    [0.2150758201, 0.8850685017, -0.1001443219],
    [-0.0320658495, -0.0276583907, 1.1487819910],
])
XYZ_TO_709 = np.array([
    [3.2404542, -1.5371385, -0.4985314],
    [-0.9692660, 1.8760108, 0.0415560],
    [0.0556434, -0.2040259, 1.0572252],
])
SG3C_TO_709 = XYZ_TO_709 @ SG3C_TO_XYZ
LUMA = np.array([0.2126, 0.7152, 0.0722])

# Oklab: فضاء لون قريب من إحساس العين. نعدّل بيه التشبع واللون حتى ما تنكسر الألوان
OK_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                  [0.2119034982, 0.6806995451, 0.1073969566],
                  [0.0883024619, 0.2817188376, 0.6299787005]])
OK_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                  [1.9779984951, -2.4285922050, 0.4505937099],
                  [0.0259040371, 0.7827717662, -0.8086757660]])
OK_M1I, OK_M2I = np.linalg.inv(OK_M1), np.linalg.inv(OK_M2)


def slog3_to_lin(x):
    x = np.asarray(x, dtype=np.float64)
    cut = 171.2102946929 / 1023.0
    hi = (10.0 ** ((x * 1023.0 - 420.0) / 261.5)) * (0.18 + 0.01) - 0.01
    lo = (x * 1023.0 - 95.0) * 0.01125 / (171.2102946929 - 95.0)
    return np.where(x >= cut, hi, lo)


def lin_to_slog3(y):
    y = np.asarray(y, dtype=np.float64)
    hi = (420.0 + np.log10((np.maximum(y, 0) + 0.01) / (0.18 + 0.01)) * 261.5) / 1023.0
    lo = (y * (171.2102946929 - 95.0) / 0.01125 + 95.0) / 1023.0
    return np.where(y >= 0.01125, hi, lo)


def to_lab(rgb):
    return np.cbrt(np.maximum(rgb, 0) @ OK_M1.T) @ OK_M2.T


def from_lab(lab):
    return ((lab @ OK_M2I.T) ** 3) @ OK_M1I.T


# ---------- أدوات الستايل ----------
def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def gamut_compress(rgb, threshold=0.8, limit=1.25):
    """ألوان أضواء RGB القوية تطلع برا Rec.709. نرجّعها بنعومة بدل ما تتكسر."""
    ach = np.max(rgb, axis=-1, keepdims=True)
    safe = np.where(ach == 0, 1, np.abs(ach))
    d = np.where(ach == 0, 0, (ach - rgb) / safe)
    scale = (limit - threshold) / np.power(np.power((1 - threshold) / (limit - threshold), -2.0) - 1.0, 0.5)
    over = (d - threshold) / scale
    dc = np.where(d < threshold, d, threshold + scale * over / np.power(1 + over * over, 0.5))
    return ach - dc * safe


def toe(x, t):
    """ظلال أعمق: الي جوه الرمادي بخمس وقفات تقريباً ينضغط للأسود (وياه تشويش الأسود)."""
    x = np.maximum(x, 0)
    return x * x / (x + t) * (0.18 + t) / 0.18


def curve_consts(c, g):
    """ثوابت المنحنى السينمائي: الرمادي 18% يطلع بسطوع g، وحد الاحتراگ يطلع أبيض كامل."""
    wc, gc = WHITE_IN ** c, 0.18 ** c
    k = wc * gc * (g - 1) / (gc - g * wc)
    return k, (wc + k) / wc


def tonemap(x, c, g, t):
    """منحنى سينمائي: ظلال عميقة وإضاءات تنطفي بهدوء (مو تحترگ)."""
    k, s = curve_consts(c, g)
    xc = np.minimum(toe(x, t), WHITE_IN) ** c
    return s * xc / (xc + k)


def tonemap_inv(y, c, g, t):
    """عكس المنحنى (للمعاينة بس: من صورة جاهزة نرجع لضوء المشهد)."""
    k, s = curve_consts(c, g)
    u = (k * y / np.maximum(s - y, 1e-6)) ** (1 / c) * 0.18 / (0.18 + t)
    return (u + np.sqrt(u * u + 4 * u * t)) / 2


def hdiff(h, center):
    """الفرق بالدرجات بين لون والمركز (-180 لـ 180)، يحسب الدوران صح."""
    return (h - center + 180) % 360 - 180


def hw(h, center, width):
    return smoothstep(width, 0, np.abs(hdiff(h, center)))


# ---------- الستايلات ----------
# contrast/gray/toe: المنحنى (التباين، سطوع الرمادي، عمق الأسود) | wb: (أحمر، أزرق) دفء أو برودة
# sat/vib: تشبع عام وحيوية | dens: كثافة فيلم (اللون القوي يغمگ بدل ما يفقع) | teal: قوة تيل-أورنج
# sh/hi: لون الظلال والإضاءات (درجة اللون، القوة) | skin: حماية البشرة | fade: رفع الأسود
# rgb_pop: إبراز أضواء RGB | green/blue: تحريك الأخضر والأزرق بالدرجات
# درجات اللون: 25 أحمر، 60 برتقالي، 85 ذهبي، 145 أخضر، 200 تيل، 255 أزرق، 300 بنفسجي
BASE = dict(contrast=1.6, gray=0.17, toe=0.004, wb=(1.0, 1.0), sat=1.0, vib=0.0, dens=0.3, teal=0.0,
            sh=(0, 0.0), hi=(0, 0.0), skin=0.6, fade=0.0, rgb_pop=0.15)
LOOKS = {}


def look(key, name, cat, use, **kw):
    LOOKS[key] = dict(BASE, **kw, name=name, cat=cat, use=use)


# الأساسية
look("ABCLEAN", "استوديو نظيف", "الأساسية", "الحچي اليومي. ابدأ بيه",
     contrast=1.5, gray=0.175, sat=1.06, dens=0.25, rgb_pop=0.2)
look("ABWARM", "سينمائي دافئ", "الأساسية", "قصص الشركات",
     contrast=1.62, gray=0.165, wb=(1.05, 0.94), sat=1.06, teal=0.3, sh=(215, 0.022), hi=(75, 0.02), dens=0.4)
look("ABTEAL", "وثائقي تيل وأورنج", "الأساسية", "الوثائقيات",
     contrast=1.68, gray=0.16, sat=1.08, teal=0.85, sh=(205, 0.04), hi=(65, 0.022), dens=0.45, skin=0.7)
look("ABNEON", "نيون RGB", "الأساسية", "أضواء RGB وراك",
     contrast=1.65, gray=0.155, sat=1.18, wb=(0.975, 1.035), vib=0.15, rgb_pop=0.6, sh=(280, 0.035),
     dens=0.35, skin=0.8)
look("ABMOODY", "غموض داكن", "الأساسية", "الأسرار والجرائم",
     contrast=1.85, gray=0.115, toe=0.007, sat=0.8, teal=0.6, sh=(210, 0.035), hi=(70, 0.012), dens=0.55)
look("ABFILM", "فيلم قديم", "الأساسية", "القصص التاريخية",
     contrast=1.5, gray=0.165, sat=0.95, wb=(1.035, 0.95), teal=0.15, sh=(150, 0.015), hi=(85, 0.03),
     fade=0.03, dens=0.5, film=True)
look("ABDAY", "خارجي طبيعي", "الأساسية", "برا بالشمس",
     contrast=1.5, gray=0.17, sat=1.08, vib=0.1)
look("ABBW", "أبيض وأسود", "الأساسية", "لقطات درامية",
     contrast=1.8, gray=0.155, mono=(0.40, 0.48, 0.12))
# استوديو وحچي للكاميرا
look("STBRIGHT", "استوديو مشرق", "استوديو", "حلقات خفيفة ومرحة",
     contrast=1.45, gray=0.195, sat=1.08, vib=0.15, wb=(1.01, 0.99), dens=0.2)
look("STSOFT", "بشرة ناعمة", "استوديو", "لقطات قريبة للوجه",
     contrast=1.35, gray=0.185, wb=(1.025, 0.975), hi=(70, 0.012), fade=0.012, skin=0.9, dens=0.2)
look("STPOP", "ألوان قوية", "استوديو", "محتوى شبابي سريع",
     contrast=1.7, gray=0.17, sat=1.15, vib=0.2, rgb_pop=0.4, skin=0.9)
look("STTECH", "تقني بارد", "استوديو", "مراجعات أجهزة وتقنية",
     contrast=1.62, gray=0.165, wb=(0.965, 1.045), sh=(235, 0.03), hi=(230, 0.012), skin=0.7, dens=0.35)
look("STGOLD", "ذهبي فخم", "استوديو", "قصص الأغنياء والماركات",
     contrast=1.68, gray=0.155, sat=1.05, wb=(1.06, 0.92), sh=(60, 0.012), hi=(82, 0.035), warm_sat=0.15,
     dens=0.5)
look("STPODCST", "بودكاست داكن", "استوديو", "جلسة حوار بإضاءة خفيفة",
     contrast=1.78, gray=0.13, toe=0.006, wb=(1.02, 0.98), teal=0.35, sh=(215, 0.022), rgb_pop=0.35, dens=0.45)
look("STLUXE", "فخامة سينمائية", "استوديو", "المقدمات المهمة",
     contrast=1.72, gray=0.15, wb=(1.025, 0.97), teal=0.5, sh=(212, 0.03), hi=(72, 0.022), dens=0.5)
look("STPURPLE", "بنفسجي RGB", "استوديو", "خلفية بنفسجية وزرگة",
     contrast=1.65, gray=0.15, sat=1.15, blue=22, rgb_pop=0.55, sh=(300, 0.05), hi=(330, 0.012), skin=0.85,
     dens=0.35)
# سينمائي
look("CNNIGHT", "ليل أزرق", "سينمائي", "مشاهد الليل والتوتر",
     contrast=1.72, gray=0.12, sat=0.92, wb=(0.93, 1.09), sh=(245, 0.045), hi=(225, 0.015), dens=0.45)
look("CNMATRIX", "أخضر الأفلام", "سينمائي", "قصص الهكر والتكنولوجيا",
     contrast=1.75, gray=0.14, sat=0.88, sh=(150, 0.04), hi=(125, 0.022), green=-10, dens=0.45)
look("CNBLEACH", "تبييض أكشن", "سينمائي", "الحروب والأكشن",
     contrast=1.7, gray=0.155, sat=0.9, bleach=0.7, sh=(215, 0.012))
look("CNFADE", "باهت ناعم", "سينمائي", "ذكريات وحنين",
     contrast=1.3, gray=0.17, sat=0.85, fade=0.06, sh=(215, 0.02), hi=(75, 0.02))
look("CNDUNE", "صحراء برتقالية", "سينمائي", "الصحراء والشرق",
     contrast=1.7, gray=0.155, sat=1.02, wb=(1.09, 0.86), sh=(45, 0.02), hi=(75, 0.04), warm_sat=0.2,
     green=-15, dens=0.5)
look("CNNOIR", "نوار أبيض وأسود", "سينمائي", "الجرائم القديمة",
     contrast=2.0, gray=0.125, toe=0.008, mono=(0.30, 0.59, 0.11))
look("CNPASTEL", "باستيل", "سينمائي", "محتوى هادئ وناعم",
     contrast=1.28, gray=0.195, sat=0.85, vib=0.15, fade=0.045, sh=(300, 0.015), hi=(60, 0.015))
look("CNSEVNTY", "سبعينات", "سينمائي", "قصص السبعينات والثمانينات",
     contrast=1.45, gray=0.165, sat=0.95, wb=(1.06, 0.9), fade=0.04, sh=(70, 0.02), hi=(88, 0.04), green=-12,
     dens=0.5, film=True)
look("CNBLKBUS", "بلوكبستر", "سينمائي", "تيل وأورنج قوي مثل أفلام هوليوود",
     contrast=1.85, gray=0.145, sat=1.1, teal=1.0, sh=(205, 0.05), hi=(62, 0.028), skin=0.75, dens=0.55)
look("CNSEPIA", "سيبيا قديم", "سينمائي", "صور وتاريخ قديم",
     contrast=1.55, gray=0.155, mono=(0.35, 0.53, 0.12), fade=0.03, sh=(65, 0.035), hi=(85, 0.045))
# فلوگات وتصوير برا
look("VLSUNSET", "غروب ذهبي", "فلوگ وبرا", "وقت الغروب",
     contrast=1.55, gray=0.17, sat=1.1, wb=(1.08, 0.9), hi=(70, 0.04), warm_sat=0.2, vib=0.15, dens=0.4)
look("VLAIRY", "مشرق هوائي", "فلوگ وبرا", "نهار مشمس وناعم",
     contrast=1.3, gray=0.2, sat=0.98, vib=0.2, fade=0.02, wb=(1.0, 1.01), dens=0.15)
look("VLSEA", "بحر تركواز", "فلوگ وبرا", "البحر والمسابح",
     contrast=1.55, gray=0.17, sat=1.1, blue=-16, blue_sat=0.2, vib=0.15, teal=0.5, dens=0.35)
look("VLCITY", "مدينة بالليل", "فلوگ وبرا", "شوارع وأضواء الليل",
     contrast=1.7, gray=0.14, sat=1.1, teal=0.8, rgb_pop=0.55, sh=(212, 0.035), hi=(65, 0.025), dens=0.45)
look("VLNATURE", "طبيعة خضرة", "فلوگ وبرا", "الحدائق والجبال",
     contrast=1.5, gray=0.17, sat=1.08, green=8, green_sat=0.15, vib=0.15, dens=0.35)
look("VLSNOW", "ثلج بارد", "فلوگ وبرا", "الثلج والشتاء",
     contrast=1.5, gray=0.185, sat=0.92, wb=(0.95, 1.07), sh=(240, 0.03), dens=0.25)
look("VLTRAVEL", "سفر سينمائي", "فلوگ وبرا", "فلوگات السفر",
     contrast=1.62, gray=0.165, sat=1.08, teal=0.6, vib=0.15, wb=(1.025, 0.975), fade=0.008, sh=(210, 0.02),
     hi=(68, 0.015), dens=0.4)
look("VLCAFE", "كوفي دافئ", "فلوگ وبرا", "المقاهي والمطاعم",
     contrast=1.5, gray=0.16, sat=0.97, wb=(1.065, 0.91), sh=(50, 0.02), hi=(78, 0.03), fade=0.02, green=-10,
     dens=0.45)
look("VLMOODY", "سفر غامق", "فلوگ وبرا", "سفر بستايل هادئ وغامق",
     contrast=1.75, gray=0.13, sat=0.8, teal=0.6, green=-18, green_sat=-0.35, fade=0.015, sh=(205, 0.025),
     dens=0.5)
look("VLHDR", "مشهد ساطع", "فلوگ وبرا", "شمس قوية وسما مشرقة",
     contrast=1.45, gray=0.18, sat=1.1, vib=0.3, dens=0.25)
# ريلز وتيك توك
look("RLVIRAL", "ريلز فاقع", "ريلز", "ريلز تلفت النظر",
     contrast=1.7, gray=0.18, sat=1.15, vib=0.22, rgb_pop=0.4, skin=0.95)
look("RLWARM", "ريلز دافي", "ريلز", "ريلز يومية",
     contrast=1.55, gray=0.18, sat=1.08, wb=(1.05, 0.94), vib=0.2, hi=(72, 0.025), dens=0.35)
look("RLCLEAN", "ريلز نظيف", "ريلز", "ريلز حچي للكاميرا",
     contrast=1.48, gray=0.185, sat=1.06, vib=0.15, skin=0.85, dens=0.25)
look("RLDRAMA", "ريلز درامي", "ريلز", "ريلز قصص وغموض",
     contrast=1.9, gray=0.13, toe=0.007, sat=0.98, teal=0.7, sh=(208, 0.04), dens=0.55)

# الـ16 الي تنحط بالكاميرا (استوديو قصص)، وأول أربعة منهم للاختيار السريع PPLUT1-4
TOP16 = ["ABCLEAN", "ABTEAL", "ABMOODY", "ABNEON", "ABWARM", "ABFILM", "STGOLD", "STLUXE", "STPODCST",
         "STPURPLE", "CNBLKBUS", "CNNIGHT", "CNNOIR", "RLVIRAL", "RLDRAMA", "VLTRAVEL"]
OUTDOOR = {"فلوگ وبرا"}  # هاي تنعرض على صورة خارجية (وياها ABDAY)


def apply_look(slog, p):
    """slog: مصفوفة (...,3) بقيم S-Log3. يرجع قيم الفلتر الجاهزة (بمستوى الناتج)."""
    lin = slog3_to_lin(slog) * 2.0 ** -EXPO                      # نرجّع الإضاءة الزايدة
    lin = gamut_compress(lin @ SG3C_TO_709.T)
    lin = lin * np.array([p["wb"][0], 1.0, p["wb"][1]])
    mono = p.get("mono")
    if mono:
        lin = np.repeat(np.maximum(lin @ np.array(mono), 0)[..., None], 3, -1)

    # الأضواء القوية كلش تروح للأبيض بنعومة (مثل العين والفيلم) بدل ما تبقى لون فاقع ومكسور
    Y = np.maximum(lin @ LUMA, 0)[..., None]
    peak = np.max(lin, -1, keepdims=True)
    w = smoothstep(WHITE_IN * 0.2, WHITE_IN * 0.95, np.maximum(Y, peak * 0.5))
    lin = np.maximum(lin * (1 - w) + np.maximum(Y, peak * 0.6) * w, 0)

    # المنحنى: نخلط بين قناة-قناة (مظهر فيلم) وحفظ اللون (ألوان RGB ما تتكسر)
    c, g, t = p["contrast"], p["gray"], p["toe"]
    per = tonemap(lin, c, g, t)
    Y = np.maximum(lin @ LUMA, 1e-9)[..., None]
    keep = np.clip(lin / Y, 0, 4) * tonemap(Y, c, g, t)
    mix = 0.55 - 0.35 * p["rgb_pop"]
    disp = per * mix + keep * (1 - mix)
    hl = smoothstep(0.6, 1.6, np.max(disp, -1, keepdims=True))   # الإضاءات القوية تبيّض مثل الفيلم
    disp = np.clip(disp * (1 - hl) + per * hl, 0, 1)

    # اللون: نشتغل بـ Oklab (سطوع L، قوة اللون C، درجة اللون h)
    lab = to_lab(disp)
    L = lab[..., 0]
    C = np.hypot(lab[..., 1], lab[..., 2])
    h = np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360
    if not mono:
        skin = hw(h, 55, 30) * smoothstep(0.015, 0.045, C) * smoothstep(0.21, 0.13, C)
        sel = smoothstep(0.012, 0.05, C)   # تعديلات اللون المحدد ما تلمس الرمادي (حتى الأبيض يبقى أبيض)
        warm, cool = hw(h, 60, 60) * sel, hw(h, 225, 80) * sel
        green, mag, blue = hw(h, 140, 42) * sel * (1 - cool), hw(h, 335, 40) * sel, hw(h, 262, 50) * sel
        tl = p["teal"]
        # تيل وأورنج: الدافي يتجمع عند البرتقالي، والبارد عند التيل، والأخضر يميل للزيتي
        h = h - tl * (0.45 * warm * hdiff(h, 58) + 0.55 * cool * hdiff(h, 212) + 14 * green)
        h = h + p.get("green", 0) * green + p.get("blue", 0) * blue
        h = h - 0.3 * p["skin"] * skin * hdiff(h, 55)              # البشرة ما تروح للأحمر ولا للأصفر
        gain = p["sat"] * (1 + 0.20 * tl * warm) * (1 + 0.15 * tl * cool) * (1 - 0.30 * tl * green)
        gain = gain * (1 - 0.25 * tl * mag) * (1 + p.get("green_sat", 0) * green)
        gain = gain * (1 + p.get("warm_sat", 0) * warm) * (1 + p.get("blue_sat", 0) * blue)
        # حيوية: تقوي الألوان الضعيفة أكثر من القوية | أضواء RGB: تقوي الألوان القوية بس
        gain = gain * (1 + p["vib"] * smoothstep(0.01, 0.05, C) * smoothstep(0.2, 0.08, C))
        gain = gain * (1 + 0.35 * p["rgb_pop"] * smoothstep(0.09, 0.2, C) * (1 - skin))
        gain = 1 + (gain - 1) * (1 - np.where(gain > 1, 0.65, 0.35) * p["skin"] * skin)
        gain = gain * (SHADOW_SAT + (1 - SHADOW_SAT) * smoothstep(0.07, 0.24, L))  # ظلال بلا تشويش ملوّن
        C = C * gain
        if p.get("bleach"):
            C = C * (1 - 0.55 * p["bleach"])
        # كثافة الفيلم: اللون القوي يغمگ ويصير غني، بدل ما يصير فاقع مثل الموبايل
        L = L * (1 - 0.16 * p["dens"] * smoothstep(0.04, 0.24, C) * (1 - 0.7 * skin))
    if p.get("bleach"):
        L = L + 0.07 * p["bleach"] * np.sin(2 * np.pi * (L - 0.5))  # تباين زايد (ظلال أغمگ، إضاءات أفتح)

    # تلوين الظلال والإضاءات (الأسود الصافي يبقى نظيف)
    ws = smoothstep(0.02, 0.2, L) * smoothstep(0.62, 0.22, L)
    wh = smoothstep(0.5, 0.88, L)
    (sh_h, sh_a), (hi_h, hi_a) = p["sh"], p["hi"]
    hr = np.radians(h)
    a = C * np.cos(hr) + sh_a * np.cos(np.radians(sh_h)) * ws + hi_a * np.cos(np.radians(hi_h)) * wh
    b = C * np.sin(hr) + sh_a * np.sin(np.radians(sh_h)) * ws + hi_a * np.sin(np.radians(hi_h)) * wh
    L = np.clip(L, 0, 1)

    # حد الشاشة: نلگي أقصى تشبع تتحمله الشاشة لهذا اللون، ونقرّب اللون منه بنعومة
    # (بدل ما ينقص فجأة: القص يسوي حواف خشنة بأضواء النيون ويكبّر التشويش)
    def rgb_at(s):
        return from_lab(np.stack([L, a * s, b * s], -1))

    lo, hi_s = np.zeros_like(L), np.full_like(L, 4.0)
    for _ in range(14):
        mid = (lo + hi_s) / 2
        rgb = rgb_at(mid)
        ok = (rgb.min(-1) >= 0) & (rgb.max(-1) <= 1)
        lo, hi_s = np.where(ok, mid, lo), np.where(ok, hi_s, mid)
    x = 1 / np.maximum(lo, 1e-3)                  # تشبع اللون نسبة لحد الشاشة (1 = على الحد)
    knee = 0.6
    soft = knee + (1 - knee) * np.tanh((x - knee) / (1 - knee))
    v = np.clip(rgb_at(np.where(x > knee, soft / x, 1.0)), 0, 1) ** (1 / OUT_GAMMA)

    if p.get("film"):
        v = v - 0.05 * smoothstep(0.7, 1.0, v)   # قص الإضاءات العالية شوية مثل طباعة الفيلم
    v = p["fade"] + v * (1 - p["fade"])           # رفع الأسود (مظهر سينمائي ناعم)
    return BLACK_OUT + (WHITE_OUT - BLACK_OUT) * np.clip(v, 0, 1)


def smooth_jumps(lut, limit=0.15, passes=3):
    """ينعّم بس الأماكن الي بيها قفزة لون كبيرة (أضواء نيون قوية كلش)، والباقي يبقى مثل ما هو."""
    g = np.linspace(0, 1, SIZE)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")
    grid = np.stack([r, gg, b], -1)
    # الألوان الرمادية والبيضة ما ننعمها حتى يبقى الأبيض أبيض
    chroma = smoothstep(0.06, 0.16, grid.max(-1) - grid.min(-1))[..., None]
    for _ in range(passes):
        pad = np.pad(lut, ((1, 1), (1, 1), (1, 1), (0, 0)), mode="edge")
        blur = sum(pad[i:i + SIZE, j:j + SIZE, k:k + SIZE]
                   for i in range(3) for j in range(3) for k in range(3)) / 27.0
        jump = np.zeros(lut.shape[:3])
        for ax in range(3):
            d = np.abs(np.diff(lut, axis=ax)).max(-1)
            sl = [slice(None)] * 3
            sl[ax] = slice(0, -1)
            jump[tuple(sl)] = np.maximum(jump[tuple(sl)], d)
            sl[ax] = slice(1, None)
            jump[tuple(sl)] = np.maximum(jump[tuple(sl)], d)
        w = smoothstep(limit * 0.6, limit * 1.5, jump)[..., None] * chroma
        lut = lut * (1 - w) + blur * w
    return np.clip(lut, 0, 1)


def write_cube(path, title, p):
    g = np.linspace(0, 1, SIZE)
    # ترتيب cube: الأحمر يتغير أسرع
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")
    inp = np.stack([r, gg, b], -1).reshape(-1, 3)
    out = smooth_jumps(apply_look(inp, p).reshape(SIZE, SIZE, SIZE, 3)).reshape(-1, 3)
    # بدون أسطر تعليق: بعض الكاميرات ترفض الملف إذا بيه "#"
    gray = out.reshape(SIZE, SIZE, SIZE, 3)[np.arange(SIZE), np.arange(SIZE), np.arange(SIZE)] @ LUMA
    assert np.all(np.diff(gray) > -1e-4), f"{title}: التدرج من الأسود للأبيض مو متصاعد"
    assert gray[3] < BLACK_OUT + 0.08 and gray[-1] > WHITE_OUT - 0.05, f"{title}: الأسود أو الأبيض بمكان غلط"
    lines = [f'TITLE "{title}"', f"LUT_3D_SIZE {SIZE}", "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0"]
    lines += [f"{a:.5f} {c:.5f} {d:.5f}" for a, c, d in out]
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return out


# ---------- صور المعاينة ----------
def photo_to_slog3(path):
    """يحوّل صورة عادية إلى شكلها لو صوّرتها الكاميرا خام (S-Log3) وبإضاءة أفتح بمقدار EXPO.

    الصورة الجاهزة مطبّق عليها منحنى، فنعكس منحنى الفلتر النظيف حتى نرجع لضوء المشهد.
    """
    from PIL import Image
    v = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64) / 255.0
    disp = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    p = LOOKS["ABCLEAN"]
    Y = np.maximum(disp @ LUMA, 1e-6)[..., None]
    Ys = tonemap_inv(np.minimum(Y, 0.999), p["contrast"], p["gray"], p["toe"])
    scene = Ys + (disp / Y * Ys - Ys) / 1.12    # المنحنى يزيد التشبع، فننقصه هنا حتى يتعادلون
    scene = np.maximum(scene, 0) * 2.0 ** EXPO
    return lin_to_slog3(np.clip(scene @ np.linalg.inv(SG3C_TO_709).T, -0.01, None))


def apply_cube(img, table):
    """تطبيق ملف cube فعلي (تقريب ثلاثي خطي) حتى نفحص الملف نفسه مو الدالة."""
    n = SIZE
    lut = table.reshape(n, n, n, 3)  # [b][g][r]
    x = np.clip(img, 0, 1) * (n - 1)
    i0 = np.floor(x).astype(int).clip(0, n - 2)
    f = x - i0
    out = 0
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                wgt = ((f[..., 0] if dr else 1 - f[..., 0]) * (f[..., 1] if dg else 1 - f[..., 1]) *
                       (f[..., 2] if db else 1 - f[..., 2]))[..., None]
                out = out + wgt * lut[i0[..., 2] + db, i0[..., 1] + dg, i0[..., 0] + dr]
    return out


def on_screen(v):
    """شلون المشغّل يعرض قيم الملف: 64 أسود و940 أبيض."""
    return np.clip((v - LEGAL_LO) / (LEGAL_HI - LEGAL_LO), 0, 1)


def preview(tables):
    """صورة لكل فلتر (previews/الاسم.jpg: مشهدين فوگ بعض) وصورة مقارنة وحدة (preview.jpg)."""
    from PIL import Image, ImageDraw, ImageFont
    fonts = ROOT / "designer" / "fonts"

    def font(size, name="Tajawal-Black.ttf"):
        return ImageFont.truetype(str(fonts / name), size)

    def shot(scene, table, size):
        im = Image.fromarray((on_screen(apply_cube(scene, table)) * 255 + 0.5).astype(np.uint8))
        return im.resize(size, Image.LANCZOS)

    scenes = {k: photo_to_slog3(CAM / "scenes" / f"{k}.jpg") for k in ("studio", "studio2", "outdoor")}
    out = CAM / "previews"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.jpg"):
        old.unlink()
    tw, th, bar, cols = 384, 216, 34, 5
    sheet = Image.new("RGB", (cols * tw, -(-len(tables) // cols) * (th + bar)), (14, 14, 16))
    ds = ImageDraw.Draw(sheet)
    W, H, B = 960, 540, 104
    for i, (key, table) in enumerate(tables.items()):
        p = LOOKS[key]
        first = "outdoor" if p["cat"] in OUTDOOR or key == "ABDAY" else "studio"
        x, y = (i % cols) * tw, (i // cols) * (th + bar)
        sheet.paste(shot(scenes["studio2" if first == "studio" else "outdoor"], table, (tw, th)), (x, y + bar))
        ds.text((x + tw - 8, y + 5), f"{p['name']}  {key}", fill=(235, 235, 235), font=font(17), anchor="ra",
                direction="rtl")
        card = Image.new("RGB", (W, 2 * H + B), (11, 11, 15))
        card.paste(shot(scenes[first], table, (W, H)), (0, 0))
        card.paste(shot(scenes["studio2"], table, (W, H)), (0, H))
        d = ImageDraw.Draw(card)
        d.text((W - 24, 2 * H + 10), p["name"], fill=(255, 255, 255), font=font(40), anchor="ra", direction="rtl")
        d.text((W - 24, 2 * H + 62), p["use"], fill=(255, 196, 0), font=font(25), anchor="ra", direction="rtl")
        d.text((24, 2 * H + 26), key, fill=(255, 255, 255), font=font(40, "Cairo-Black.ttf"))
        card.save(out / f"{key}.jpg", quality=85)
    sheet.save(CAM / "preview.jpg", quality=90)


def main():
    ap = argparse.ArgumentParser(description="يصنع فلاتر ZV-E10 II")
    ap.add_argument("--preview", action="store_true", help="يطلع صورة لكل فلتر وصورة مقارنة")
    ap.add_argument("--list", action="store_true", help="يطبع قائمة الفلاتر JSON وما يصنع شي")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    if a.list:
        print(json.dumps([dict(key=k, name=p["name"], cat=p["cat"], use=p["use"], top=k in TOP16)
                          for k, p in LOOKS.items()], ensure_ascii=False, indent=1))
        return
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tables = {}
    for key, p in LOOKS.items():
        assert len(key) <= 8, f"{key}: الكارت يعرض 8 حروف بس"
        tables[key] = write_cube(out / f"{key}.cube", f"{key} - Aboodi Studio", p)
        size = (out / f"{key}.cube").stat().st_size
        assert size < 1_000_000, f"{key} أكبر من 1 ميگا"
        print(f"✓ {key}.cube  ({p['name']})  {size // 1024} KB")
    if a.preview:
        preview(tables)
        print("✓ صور المعاينة:", CAM / "previews", "و", CAM / "preview.jpg")


if __name__ == "__main__":
    main()
