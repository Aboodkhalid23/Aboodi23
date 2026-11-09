#!/usr/bin/env python3
"""يصنع فلاتر (LUT) خاصة لكاميرا سوني ZV-E10 II.

الفلتر ياخذ صورة الكاميرا الخام (S-Log3 / S-Gamut3.Cine) ويطلعها جاهزة (Rec.709)
بستايل معين. الملفات تنحط بالكارت وتنطبع داخل الفيديو عن طريق PPLUT1-4.

التشغيل:
    python3 scripts/make-luts.py            # يصنع كل الفلاتر بـ studio/camera/luts
    python3 scripts/make-luts.py --preview  # وياها صورة مقارنة
"""
import argparse
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "studio" / "camera" / "luts"
SIZE = 33  # الكاميرا تقبل 17 أو 33 نقطة، وحجم الملف لازم أقل من 1 ميگا

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


def tonemap(x, contrast, gray_out, white_in=14.0):
    """منحنى سينمائي: ظلال ناعمة وإضاءات تنطفي بهدوء (مو تحترگ)."""
    x = np.maximum(x, 0)
    c = contrast
    # نختار k حتى الرمادي 18% يطلع بالسطوع المطلوب
    wc = white_in ** c
    gc = 0.18 ** c
    # s*gc/(gc+k)=gray_out , s=(wc+k)/wc
    # => (wc+k)*gc = gray_out*wc*(gc+k)  => k(gc - gray_out*wc) = gray_out*wc*gc - wc*gc
    k = (gray_out * wc * gc - wc * gc) / (gc - gray_out * wc)
    s = (wc + k) / wc
    xc = x ** c
    return s * xc / (xc + k)


def rgb_to_hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.max(rgb, -1)
    mn = np.min(rgb, -1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-9
    rc = np.where(m, (mx - r) / np.where(m, d, 1), 0)
    gc = np.where(m, (mx - g) / np.where(m, d, 1), 0)
    bc = np.where(m, (mx - b) / np.where(m, d, 1), 0)
    h = np.where(r == mx, bc - gc, np.where(g == mx, 2.0 + rc - bc, 4.0 + gc - rc))
    h = np.where(m, (h / 6.0) % 1.0, 0)
    s = np.where(mx > 1e-9, d / np.where(mx > 1e-9, mx, 1), 0)
    return h, s, mx


def hsv_to_rgb(h, s, v):
    i = np.floor(h * 6.0)
    f = h * 6.0 - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    i = i.astype(int) % 6
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], -1)


def hue_diff(h, center_deg):
    """الفرق بالدرجات بين لون والمركز (-180 لـ 180)، يحسب الدوران صح."""
    return ((h * 360 - center_deg) + 180) % 360 - 180


def hue_weight(h, center_deg, width_deg):
    d = np.abs(hue_diff(h, center_deg))
    return smoothstep(width_deg, 0, d) if width_deg > 0 else 0 * h


# ---------- الستايلات ----------
# exposure: تعويض إضاءة بالـ stops | wb: (أحمر، أزرق) دفء أو برودة
# contrast/gray: المنحنى | sat: تشبع عام | shadows/highlights: لون الظلال والإضاءات
# teal: قوة تيل-أورنج | skin: حماية لون البشرة | fade: رفع الأسود | rgb_pop: إبراز أضواء RGB
LOOKS = {
    "ABCLEAN": dict(name="استوديو نظيف", contrast=1.25, gray=0.155, sat=1.05, wb=(1.0, 1.0),
                    shadows=(0, 0, 0), highlights=(0, 0, 0), split=0.0, teal=0.0, skin=0.35,
                    fade=0.0, rgb_pop=0.15),
    "ABWARM": dict(name="سينمائي دافئ", contrast=1.38, gray=0.145, sat=1.08, wb=(1.035, 0.965),
                   shadows=(-0.010, 0.004, 0.012), highlights=(0.018, 0.006, -0.016), split=1.0,
                   teal=0.25, skin=0.5, fade=0.012, rgb_pop=0.15),
    "ABTEAL": dict(name="وثائقي تيل وأورنج", contrast=1.45, gray=0.140, sat=1.10, wb=(1.01, 0.995),
                   shadows=(-0.020, 0.010, 0.022), highlights=(0.016, 0.004, -0.012), split=1.0,
                   teal=0.85, skin=0.6, fade=0.010, rgb_pop=0.2),
    "ABNEON": dict(name="نيون RGB", contrast=1.42, gray=0.135, sat=1.22, wb=(0.99, 1.01),
                   shadows=(-0.006, -0.010, 0.020), highlights=(0, 0, 0), split=1.0,
                   teal=0.2, skin=0.75, fade=0.0, rgb_pop=0.55),
    "ABMOODY": dict(name="غموض داكن", contrast=1.6, gray=0.10, sat=0.74, wb=(0.99, 1.02),
                    shadows=(-0.012, 0.008, 0.018), highlights=(0.010, 0.006, -0.004), split=1.0,
                    teal=0.7, skin=0.55, fade=0.025, rgb_pop=0.0),
    "ABFILM": dict(name="فيلم قديم", contrast=1.30, gray=0.150, sat=0.92, wb=(1.03, 0.96),
                   shadows=(0.004, 0.010, 0.006), highlights=(0.020, 0.012, -0.020), split=1.0,
                   teal=0.15, skin=0.4, fade=0.035, rgb_pop=0.0, film=True),
    "ABDAY": dict(name="خارجي طبيعي", contrast=1.30, gray=0.150, sat=1.06, wb=(1.0, 1.0),
                  shadows=(0, 0, 0.004), highlights=(0.004, 0.002, -0.004), split=1.0,
                  teal=0.1, skin=0.35, fade=0.0, rgb_pop=0.05, white_in=20.0),
    "ABBW": dict(name="أبيض وأسود", contrast=1.55, gray=0.140, sat=0.0, wb=(1.0, 1.0),
                 shadows=(0, 0, 0), highlights=(0, 0, 0), split=0.0, teal=0.0, skin=0.0,
                 fade=0.008, rgb_pop=0.0, mono=(0.40, 0.48, 0.12)),
}


# ---------- 32 ستايل إضافي بأشهر أنماط صناع المحتوى ----------
BASE = dict(contrast=1.32, gray=0.15, sat=1.0, wb=(1.0, 1.0), shadows=(0, 0, 0), highlights=(0, 0, 0),
            split=1.0, teal=0.0, skin=0.5, fade=0.0, rgb_pop=0.1)


def look(name, cat, **kw):
    d = dict(BASE)
    d.update(kw, name=name, cat=cat)
    return d


for _k in LOOKS:
    LOOKS[_k]["cat"] = "الأساسية"

LOOKS.update({
    # استوديو وحچي للكاميرا
    "STBRIGHT": look("استوديو مشرق", "استوديو", contrast=1.2, gray=0.17, sat=1.04, vib=0.15, wb=(1.01, 0.99)),
    "STSOFT": look("بشرة ناعمة", "استوديو", contrast=1.12, gray=0.16, sat=0.98, wb=(1.02, 0.98), fade=0.015,
                   highlights=(0.006, 0.003, -0.004), skin=0.8),
    "STPOP": look("ألوان قوية", "استوديو", contrast=1.4, gray=0.15, sat=1.12, vib=0.3, rgb_pop=0.4, skin=0.8),
    "STTECH": look("تقني بارد", "استوديو", contrast=1.38, gray=0.145, sat=0.98, wb=(0.975, 1.03),
                   shadows=(-0.006, 0.0, 0.012), highlights=(-0.004, 0.002, 0.008), skin=0.6),
    "STGOLD": look("ذهبي فخم", "استوديو", contrast=1.42, gray=0.14, sat=1.02, wb=(1.04, 0.95),
                   shadows=(0.004, 0.0, -0.006), highlights=(0.016, 0.010, -0.014), warm_sat=0.12, fade=0.01),
    "STPODCST": look("بودكاست داكن", "استوديو", contrast=1.55, gray=0.12, sat=0.95, wb=(1.015, 0.985),
                     shadows=(-0.006, 0.002, 0.010), teal=0.35, fade=0.012, rgb_pop=0.3),
    "STLUXE": look("فخامة سينمائية", "استوديو", contrast=1.48, gray=0.135, sat=0.96, wb=(1.02, 0.98),
                   shadows=(-0.012, 0.004, 0.014), highlights=(0.012, 0.006, -0.008), teal=0.5, fade=0.018),
    "STPURPLE": look("بنفسجي RGB", "استوديو", contrast=1.42, gray=0.135, sat=1.1, blue=18, rgb_pop=0.5,
                     shadows=(0.004, -0.008, 0.016), skin=0.8),
    # سينمائي
    "CNNIGHT": look("ليل أزرق", "سينمائي", contrast=1.5, gray=0.11, sat=0.9, wb=(0.95, 1.07),
                    shadows=(-0.012, 0.0, 0.022), highlights=(-0.004, 0.004, 0.010), fade=0.01),
    "CNMATRIX": look("أخضر الأفلام", "سينمائي", contrast=1.5, gray=0.13, sat=0.85,
                     shadows=(-0.006, 0.014, 0.002), highlights=(0.0, 0.010, -0.006), green=-10, fade=0.012),
    "CNBLEACH": look("تبييض أكشن", "سينمائي", contrast=1.45, gray=0.14, sat=0.9, bleach=0.6,
                     shadows=(-0.004, 0.002, 0.006)),
    "CNFADE": look("باهت ناعم", "سينمائي", contrast=1.15, gray=0.15, sat=0.86, fade=0.06,
                   shadows=(0.0, 0.006, 0.010), highlights=(0.010, 0.006, 0.0)),
    "CNDUNE": look("صحراء برتقالية", "سينمائي", contrast=1.45, gray=0.14, sat=1.0, wb=(1.07, 0.9),
                   shadows=(0.006, 0.0, -0.006), highlights=(0.020, 0.010, -0.020), warm_sat=0.15, green=-15,
                   fade=0.012),
    "CNNOIR": look("نوار أبيض وأسود", "سينمائي", contrast=1.7, gray=0.12, mono=(0.30, 0.59, 0.11), fade=0.0,
                   split=0.0, skin=0.0, rgb_pop=0.0),
    "CNPASTEL": look("باستيل", "سينمائي", contrast=1.1, gray=0.17, sat=0.82, fade=0.045, vib=0.1,
                     shadows=(0.006, 0.0, 0.010), highlights=(0.010, 0.004, 0.004)),
    "CNSEVNTY": look("سبعينات", "سينمائي", contrast=1.25, gray=0.15, sat=0.9, wb=(1.05, 0.92), fade=0.04,
                     shadows=(0.010, 0.006, -0.004), highlights=(0.018, 0.012, -0.022), green=-12, film=True),
    "CNBLKBUS": look("بلوكبستر", "سينمائي", contrast=1.6, gray=0.13, sat=1.05, teal=1.0,
                     shadows=(-0.024, 0.010, 0.026), highlights=(0.018, 0.006, -0.014), skin=0.7),
    "CNSEPIA": look("سيبيا قديم", "سينمائي", contrast=1.35, gray=0.14, mono=(0.35, 0.53, 0.12), fade=0.03,
                    shadows=(0.010, 0.004, -0.006), highlights=(0.016, 0.008, -0.014), skin=0.0, rgb_pop=0.0),
    # فلوگات وتصوير برا
    "VLSUNSET": look("غروب ذهبي", "فلوگ وبرا", contrast=1.35, gray=0.15, sat=1.08, wb=(1.06, 0.92),
                     highlights=(0.022, 0.010, -0.018), warm_sat=0.2, vib=0.15, white_in=20.0),
    "VLAIRY": look("مشرق هوائي", "فلوگ وبرا", contrast=1.12, gray=0.18, sat=0.95, vib=0.2, fade=0.02,
                   wb=(1.0, 1.01), white_in=24.0),
    "VLSEA": look("بحر تركواز", "فلوگ وبرا", contrast=1.35, gray=0.15, sat=1.08, blue=-14, vib=0.25,
                  teal=0.5, white_in=20.0),
    "VLCITY": look("مدينة بالليل", "فلوگ وبرا", contrast=1.45, gray=0.125, sat=1.08, teal=0.8, rgb_pop=0.5,
                   shadows=(-0.010, 0.006, 0.018), highlights=(0.016, 0.006, -0.010)),
    "VLNATURE": look("طبيعة خضرة", "فلوگ وبرا", contrast=1.3, gray=0.15, sat=1.05, green=8, green_sat=0.15,
                     vib=0.2, white_in=20.0),
    "VLSNOW": look("ثلج بارد", "فلوگ وبرا", contrast=1.3, gray=0.16, sat=0.92, wb=(0.96, 1.05),
                   shadows=(-0.006, 0.0, 0.012), white_in=24.0),
    "VLTRAVEL": look("سفر سينمائي", "فلوگ وبرا", contrast=1.4, gray=0.145, sat=1.05, teal=0.6, vib=0.15,
                     wb=(1.02, 0.98), fade=0.01, white_in=20.0),
    "VLCAFE": look("كوفي دافئ", "فلوگ وبرا", contrast=1.3, gray=0.145, sat=0.95, wb=(1.05, 0.93),
                   shadows=(0.008, 0.002, -0.008), highlights=(0.014, 0.008, -0.010), fade=0.025, green=-10),
    "VLMOODY": look("سفر غامق", "فلوگ وبرا", contrast=1.5, gray=0.12, sat=0.8, teal=0.6, green=-18,
                    green_sat=-0.3, fade=0.02, white_in=20.0),
    "VLHDR": look("مشهد ساطع", "فلوگ وبرا", contrast=1.25, gray=0.16, sat=1.05, vib=0.3, white_in=32.0),
    # ريلز وتيك توك
    "RLVIRAL": look("ريلز فاقع", "ريلز", contrast=1.4, gray=0.16, sat=1.15, vib=0.35, rgb_pop=0.4, skin=0.9),
    "RLWARM": look("ريلز دافي", "ريلز", contrast=1.3, gray=0.165, sat=1.06, wb=(1.04, 0.95), vib=0.2,
                   highlights=(0.012, 0.006, -0.010)),
    "RLCLEAN": look("ريلز نظيف", "ريلز", contrast=1.22, gray=0.17, sat=1.04, vib=0.15, skin=0.8),
    "RLDRAMA": look("ريلز درامي", "ريلز", contrast=1.65, gray=0.12, sat=0.95, teal=0.7, fade=0.0,
                    shadows=(-0.014, 0.006, 0.016)),
})


def apply_look(slog, p):
    """slog: مصفوفة (...,3) بقيم S-Log3. يرجع Rec.709 جاهز للعرض (0-1)."""
    lin = slog3_to_lin(slog) @ SG3C_TO_709.T
    lin = gamut_compress(lin)
    lin = lin * np.array([p["wb"][0], 1.0, p["wb"][1]])

    # تشبع بالخطي (حول السطوع) ويا حماية البشرة
    Y = np.maximum(lin @ LUMA, 0)[..., None]
    lin = Y + (lin - Y) * p["sat"] if p.get("mono") is None else lin
    lin = gamut_compress(lin, threshold=0.7, limit=1.15)  # بعد التشبع: لا قيم سالبة تكسر الألوان

    if p.get("mono") is not None:
        Yb = np.maximum(lin @ np.array(p["mono"]), 0)[..., None]
        lin = np.repeat(Yb, 3, -1)

    # الأضواء القوية كلش تروح للأبيض بنعومة (مثل العين والفيلم) بدل ما تبقى لون فاقع ومكسور
    wi0 = p.get("white_in", 14.0)
    Yh = np.maximum(lin @ LUMA, 0)[..., None]
    peak = np.max(lin, -1, keepdims=True)
    w = smoothstep(wi0 * 0.15, wi0 * 0.9, np.maximum(Yh, peak * 0.5))
    lin = lin * (1 - w) + np.maximum(Yh, peak * 0.6) * w
    lin = np.maximum(lin, 0)

    # المنحنى: نخلط بين قناة-قناة (مظهر فيلم) وحفظ اللون (ألوان RGB ما تتكسر)
    wi = p.get("white_in", 14.0)
    per = tonemap(lin, p["contrast"], p["gray"], wi)
    Y = np.maximum(lin @ LUMA, 1e-9)[..., None]
    Yt = tonemap(Y, p["contrast"], p["gray"], wi)
    keep = np.clip(lin / Y, 0, 4) * Yt
    mix = 0.55 - 0.35 * p["rgb_pop"]
    disp = per * mix + keep * (1 - mix)
    # الإضاءات القوية تبيّض بنعومة مثل الفيلم
    hl = smoothstep(0.5, 2.2, np.max(disp, -1, keepdims=True))
    disp = disp * (1 - hl) + np.minimum(per, 1.0) * hl
    disp = np.clip(disp, 0, None)

    # من خطي للعرض (gamma 2.4 مثل الشاشات)
    v = np.clip(disp, 0, 1) ** (1 / 2.4)

    if p.get("mono") is None:
        # تيل وأورنج ويا حماية البشرة
        h, s, val = rgb_to_hsv(v)
        skin = hue_weight(h, 25, 22) * smoothstep(0.08, 0.25, s) * smoothstep(0.65, 0.2, s)
        orange = hue_weight(h, 32, 45)
        cyan = hue_weight(h, 195, 60)
        green = hue_weight(h, 110, 45)
        t = p["teal"]
        h = h - hue_diff(h, 30) / 360 * orange * 0.35 * t          # البرتقالي يتجمع
        h = h - hue_diff(h, 195) / 360 * cyan * 0.45 * t           # الأزرق يروح للتيل
        h = h + (-0.04) * green * 0.5 * t                             # الأخضر يميل للزيتي
        h = h + p.get("green", 0) / 360 * green                       # تحريك الأخضر (موجب = نحو التركواز)
        h = h + p.get("blue", 0) / 360 * hue_weight(h, 220, 50)       # تحريك الأزرق
        s = s * (1 + 0.12 * t * orange) * (1 - 0.15 * t * green)
        s = s * (1 + p.get("green_sat", 0) * green) * (1 + p.get("warm_sat", 0) * orange)
        # حيوية: تقوي الألوان الضعيفة أكثر من القوية
        s = s + p.get("vib", 0) * s * (1 - s)
        # البشرة: لا تشبع زايد ولا تروح للأحمر
        s = s * (1 - skin * p["skin"] * 0.18 * max(0, p["sat"] - 0.9))
        # أضواء RGB: تشبع أكثر للألوان القوية بس
        pop = p["rgb_pop"] * smoothstep(0.45, 0.85, s) * (1 - hue_weight(h, 25, 30))
        s = np.clip(s * (1 + 0.25 * pop), 0, 1)
        v = hsv_to_rgb(h % 1.0, s, val)

    if p.get("bleach"):
        # تبييض: تباين قوي وألوان مطفية (مظهر أفلام الحرب والأكشن)
        L = (v @ LUMA)[..., None]
        Lc = smoothstep(0.0, 1.0, L)
        b = p["bleach"]
        v = v * (1 - b) + (L + (v - L) * 0.35 + (Lc - L)) * b

    # تلوين الظلال والإضاءات
    luma = v @ LUMA
    sh = smoothstep(0.55, 0.0, luma)[..., None]
    hi = smoothstep(0.45, 1.0, luma)[..., None]
    v = v + p["split"] * (sh * np.array(p["shadows"]) * 1.6 + hi * np.array(p["highlights"]) * 1.6)
    v = v + np.array(p.get("tint", (0, 0, 0)))

    if p.get("film"):
        # قص الإضاءات العالية شوية مثل طباعة الفيلم
        v = v - 0.04 * smoothstep(0.7, 1.0, v)

    # رفع الأسود (مظهر سينمائي ناعم)
    v = p["fade"] + v * (1 - p["fade"])
    return np.clip(v, 0, 1)


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
    lines = [f'TITLE "{title}"', f"LUT_3D_SIZE {SIZE}", "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0"]
    lines += [f"{a:.5f} {c:.5f} {d:.5f}" for a, c, d in out]
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return out


# ---------- صورة المقارنة ----------
def test_scene(w=640, h=360):
    """مشهد استوديو صناعي: خلفية RGB، بشرة، لوحة ألوان، وتدرج رمادي (كلها بإضاءة حقيقية خطية)."""
    yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    # خلفية: توهج أزرق-بنفسجي يسار وأحمر-وردي يمين (أضواء RGB)
    bg = 0.015 + 0 * xx[..., None]
    glow1 = np.exp(-(((xx - 0.12) / 0.22) ** 2 + ((yy - 0.35) / 0.45) ** 2))[..., None]
    glow2 = np.exp(-(((xx - 0.92) / 0.18) ** 2 + ((yy - 0.30) / 0.40) ** 2))[..., None]
    img = bg + glow1 * np.array([0.05, 0.10, 1.4]) * 1.2 + glow2 * np.array([1.6, 0.05, 0.55])
    # وجه (بيضوي) بإضاءة سوفت بوكس من اليسار
    fx, fy = (xx - 0.50) / 0.13, (yy - 0.45) / 0.30
    face = (fx ** 2 + fy ** 2) < 1
    # سوفت بوكس من اليسار: الجهة اليسرى منورة والضوء ينزل بنعومة لليمين
    shade = np.clip(0.6 + 0.55 * (-(xx - 0.5) / 0.13), 0.18, 1.2) * np.clip(1.05 - 0.35 * (fx ** 2 + fy ** 2), 0.5, 1)
    skin = np.array([0.42, 0.24, 0.16]) * 0.95
    img = np.where(face[..., None], skin * shade[..., None] * 1.1 + glow2 * 0.15 * np.array([1, 0.1, 0.4]), img)
    # كتف (تيشيرت رمادي غامق)
    body = ((xx - 0.5) / 0.30) ** 2 + ((yy - 1.05) / 0.32) ** 2 < 1
    img = np.where(body[..., None], np.array([0.05, 0.05, 0.055]) * shade[..., None] * 1.3, img)
    # لوحة ألوان صغيرة تحت يمين
    patches = [(0.40, 0.24, 0.16), (0.65, 0.48, 0.38), (0.18, 0.25, 0.40), (0.10, 0.17, 0.07),
               (0.45, 0.07, 0.06), (0.06, 0.32, 0.12), (0.05, 0.08, 0.40), (0.70, 0.55, 0.05),
               (0.03, 0.03, 0.03), (0.09, 0.09, 0.09), (0.18, 0.18, 0.18), (0.90, 0.90, 0.88)]
    pw, ph = int(w * 0.045), int(h * 0.07)
    for i, c in enumerate(patches):
        x0 = int(w * 0.70) + (i % 6) * (pw + 2)
        y0 = int(h * 0.78) + (i // 6) * (ph + 2)
        img[y0:y0 + ph, x0:x0 + pw] = c
    # تدرج من الأسود للأبيض المحترگ (16 stops تقريباً)
    ramp_y = slice(int(h * 0.94), h)
    img[ramp_y, :] = (0.18 * 2.0 ** np.linspace(-8, 6.5, w))[None, :, None]
    # من Rec.709 خطي إلى S-Gamut3.Cine ثم S-Log3 (مثل ما تسجل الكاميرا)
    to_sg = np.linalg.inv(SG3C_TO_709)
    return lin_to_slog3(np.clip(img @ to_sg.T, -0.01, None))


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


def preview(tables, path):
    from PIL import Image, ImageDraw, ImageFont
    scene = test_scene(384, 216)
    tiles = [("الخام من الكاميرا (S-Log3)", scene)]
    tiles += [(LOOKS[k]["name"] + "  " + k, apply_cube(scene, t)) for k, t in tables.items()]
    tw, th = scene.shape[1], scene.shape[0]
    cols = 5
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 34)), (14, 14, 16))
    font = None
    for fp in [str(ROOT / "designer/fonts/Tajawal-Black.ttf"),
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if Path(fp).exists():
            font = ImageFont.truetype(fp, 17)
            break
    from PIL import features
    if features.check("raqm"):  # المكتبة ترتب العربي بنفسها
        fix = lambda s: s
    else:
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            fix = lambda s: get_display(arabic_reshaper.reshape(s))
        except ImportError:
            fix = lambda s: s
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(tiles):
        x, y = (i % cols) * tw, (i // cols) * (th + 34)
        sheet.paste(Image.fromarray((np.clip(im, 0, 1) * 255).astype(np.uint8)), (x, y + 34))
        d.text((x + tw - 10, y + 6), fix(label), fill=(235, 235, 235), font=font, anchor="ra")
    sheet.save(path, quality=92)


def main():
    ap = argparse.ArgumentParser(description="يصنع فلاتر ZV-E10 II")
    ap.add_argument("--preview", action="store_true", help="يطلع صورة مقارنة")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tables = {}
    for key, p in LOOKS.items():
        tables[key] = write_cube(out / f"{key}.cube", f"{key} - Aboodi Studio", p)
        size = (out / f"{key}.cube").stat().st_size
        assert size < 1_000_000, f"{key} أكبر من 1 ميگا"
        print(f"✓ {key}.cube  ({p['name']})  {size // 1024} KB")
    if a.preview:
        preview(tables, out.parent / "preview.jpg")
        print("✓ صورة المقارنة:", out.parent / "preview.jpg")


if __name__ == "__main__":
    main()
