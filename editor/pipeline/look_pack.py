"""The big colour library (owner, 2026-10-25: "LUT جديد حوالي 100+ … الوان وموثرات قوية").

Every look here is written by us from a few numbers (contrast, lifted blacks, rolled highlights, a colour push in
the shadows / mids / highlights, saturation, hue, black-and-white with a tint, grain), turned into ffmpeg colour
filters. Colour-only filters bake into the same 3D cube the render already uses, so each look also works with his
strength slider and with Sony log footage. No look is copied from another app: they are ours, free to use.
"""

CATS = {"cinema": "سينما", "film": "فلم قديم", "warm": "دافي", "cool": "بارد", "bold": "ألوان قوية",
        "soft": "ناعم وباستيل", "mono": "أبيض وأسود", "night": "ليل ونيون", "nature": "طبيعة وسفر",
        "doc": "وثائقي وأخبار", "skin": "وجوه وبشرة", "mood": "مزاج ودراما"}


def _look(c=0.0, lift=0.0, roll=0.0, sh=(0, 0, 0), mid=(0, 0, 0), hi=(0, 0, 0), sat=1.0, vib=0.0, hue=0,
          mono=False, grain=0, gamma=1.0):
    """A few numbers → an ffmpeg chain. c: S-curve strength (0–0.12); lift/roll: faded blacks / soft whites;
    sh/mid/hi: colour push (r, g, b) in shadows / mids / highlights (−0.15…0.15)."""
    parts = []
    if mono:
        parts.append("hue=s=0")
    if c or lift or roll or gamma != 1.0:
        q, h = 0.25 - c, 0.75 + c
        m = 0.5 ** gamma if gamma != 1.0 else 0.5
        parts.append(f"curves=master='0/{lift:.3f} 0.25/{q:.3f} 0.5/{m:.3f} 0.75/{h:.3f} 1/{1 - roll:.3f}'")
    if mono:   # a grey picture needs a stronger push to read as a tint
        sh, mid, hi = ([v * 1.8 for v in t] for t in (sh, mid, hi))
    vals = {"rs": sh[0], "gs": sh[1], "bs": sh[2], "rm": mid[0], "gm": mid[1], "bm": mid[2],
            "rh": hi[0], "gh": hi[1], "bh": hi[2]}
    if any(vals.values()):
        parts.append("colorbalance=" + ":".join(f"{k}={v:.3f}" for k, v in vals.items() if v))
    if hue:
        parts.append(f"hue=h={hue}")
    if sat != 1.0 and not mono:
        parts.append(f"eq=saturation={sat:.2f}")
    if vib:
        parts.append(f"vibrance=intensity={vib:.2f}")
    if grain:
        parts.append(f"noise=alls={grain}:allf=t")
    return ",".join(parts)


W, C = (0.06, 0.02, -0.06), (-0.05, 0.0, 0.07)     # warm and cool pushes
_T = [
    # cinema
    ("cine-blockbuster", "بلوك بستر", "cinema", dict(c=0.06, sh=(-0.1, 0, 0.1), hi=(0.09, 0.02, -0.08), sat=1.1)),
    ("cine-netflix", "دراما منصّات", "cinema", dict(c=0.04, lift=0.025, roll=0.02, sh=(-0.03, 0, 0.04), hi=(0.03, 0.01, -0.03), sat=1.04)),
    ("cine-thriller", "إثارة", "cinema", dict(c=0.07, lift=0.01, sh=(-0.04, 0.03, 0.05), mid=(-0.02, 0.02, 0), sat=0.85)),
    ("cine-matrix", "شاشة خضرة", "cinema", dict(c=0.06, sh=(-0.05, 0.06, -0.02), mid=(-0.03, 0.05, -0.03), hi=(0, 0.03, 0), sat=0.85)),
    ("cine-dune", "صحراء ملحمية", "cinema", dict(c=0.05, lift=0.02, mid=(0.06, 0.02, -0.07), hi=(0.08, 0.03, -0.08), sat=0.95)),
    ("cine-noir-color", "نوار ملوّن", "cinema", dict(c=0.09, sh=(0, 0, 0.06), hi=(0.03, 0, -0.02), sat=0.6)),
    ("cine-epic", "ملحمي", "cinema", dict(c=0.08, roll=0.02, sh=(-0.06, -0.01, 0.07), hi=(0.07, 0.03, -0.05), sat=1.12, vib=0.15)),
    ("cine-indie", "سينما مستقلة", "cinema", dict(c=0.03, lift=0.05, roll=0.04, mid=(0.02, 0.02, -0.02), sat=0.9)),
    ("cine-heist", "سرقة كبرى", "cinema", dict(c=0.07, sh=(-0.02, 0.02, 0.06), hi=(0.06, 0.04, -0.04), sat=1.0)),
    ("cine-spy", "جاسوسية", "cinema", dict(c=0.06, sh=(-0.03, 0, 0.05), mid=(-0.02, 0, 0.02), sat=0.8)),
    ("cine-war", "حرب", "cinema", dict(c=0.08, lift=0.02, mid=(0.02, 0.02, -0.03), sat=0.55, grain=4)),
    ("cine-scifi", "خيال علمي", "cinema", dict(c=0.05, sh=(-0.06, 0.02, 0.09), hi=(-0.02, 0.02, 0.05), sat=1.05)),
    ("cine-anamorphic", "عدسة سينمائية", "cinema", dict(c=0.05, lift=0.02, sh=(-0.04, 0, 0.08), hi=(0.05, 0.02, -0.03), sat=1.05)),
    ("cine-trailer", "تريلر", "cinema", dict(c=0.1, sh=(-0.08, 0, 0.1), hi=(0.1, 0.03, -0.08), sat=1.18, vib=0.1)),
    ("cine-gold-hour", "ساعة ذهبية", "cinema", dict(c=0.05, mid=(0.05, 0.02, -0.05), hi=(0.08, 0.04, -0.06), sat=1.08)),
    # old film
    ("film-kodak", "شريط كوداك", "film", dict(c=0.05, lift=0.03, roll=0.03, mid=(0.04, 0.01, -0.04), hi=(0.04, 0.02, -0.05), sat=1.05, grain=3)),
    ("film-fuji", "شريط فوجي", "film", dict(c=0.04, lift=0.03, sh=(-0.02, 0.03, 0.03), hi=(0.01, 0.02, -0.02), sat=1.0, grain=3)),
    ("film-70s", "سبعينات", "film", dict(c=0.03, lift=0.06, roll=0.05, mid=(0.06, 0.03, -0.07), sat=0.85, grain=5)),
    ("film-80s", "ثمانينات", "film", dict(c=0.05, lift=0.04, sh=(0.03, -0.02, 0.06), hi=(0.06, 0, 0.02), sat=1.15, grain=4)),
    ("film-90s", "تسعينات", "film", dict(c=0.03, lift=0.04, roll=0.03, sh=(0, 0.03, 0.01), mid=(0.02, 0.02, -0.02), sat=0.92, grain=4)),
    ("film-polaroid", "بولارويد", "film", dict(c=0.02, lift=0.08, roll=0.06, sh=(0, 0.03, 0.05), hi=(0.05, 0.03, -0.04), sat=0.85)),
    ("film-faded", "صورة باهتة", "film", dict(lift=0.1, roll=0.06, mid=(0.02, 0.01, -0.01), sat=0.75)),
    ("film-sepia", "بني قديم", "film", dict(c=0.03, lift=0.04, mono=True, mid=(0.08, 0.03, -0.08), hi=(0.06, 0.03, -0.06), grain=5)),
    ("film-archive", "أرشيف", "film", dict(c=0.06, lift=0.05, roll=0.05, sat=0.5, mid=(0.04, 0.02, -0.04), grain=7)),
    ("film-super8", "سوبر ٨", "film", dict(c=0.04, lift=0.06, mid=(0.07, 0.03, -0.06), sat=1.1, grain=8)),
    ("film-crossprocess", "تحميض معكوس", "film", dict(c=0.07, sh=(-0.02, 0.04, 0.08), hi=(0.08, 0.06, -0.08), sat=1.2)),
    ("film-technicolor", "تكنيكولر", "film", dict(c=0.05, sh=(0.02, -0.02, 0.03), sat=1.35, vib=0.1)),
    ("film-bleach", "بلا تبييض", "film", dict(c=0.1, sat=0.55, mid=(0.01, 0.01, 0))),
    ("film-vhs", "شريط فيديو", "film", dict(c=0.02, lift=0.06, roll=0.06, sh=(0, 0, 0.05), mid=(0.03, -0.01, 0.02), sat=1.15, grain=9)),
    ("film-daguerre", "صورة جدّو", "film", dict(c=0.06, lift=0.06, roll=0.08, mono=True, mid=(0.05, 0.03, -0.03), grain=8)),
    # warm
    ("warm-sunset", "غروب", "warm", dict(c=0.04, mid=(0.08, 0.02, -0.08), hi=(0.09, 0.03, -0.06), sat=1.1)),
    ("warm-honey", "عسلي", "warm", dict(c=0.03, lift=0.02, mid=(0.06, 0.03, -0.07), sat=1.04)),
    ("warm-desert", "رملي", "warm", dict(c=0.04, mid=(0.07, 0.04, -0.06), hi=(0.05, 0.03, -0.05), sat=0.9)),
    ("warm-candle", "ضوء شمعة", "warm", dict(c=0.06, lift=0.01, mid=(0.09, 0.03, -0.1), sat=1.05)),
    ("warm-autumn", "خريف", "warm", dict(c=0.05, mid=(0.07, 0.01, -0.06), hue=-6, sat=1.15)),
    ("warm-cafe", "مقهى", "warm", dict(c=0.04, lift=0.03, roll=0.02, mid=(0.05, 0.02, -0.05), sat=0.9)),
    ("warm-summer", "صيفي", "warm", dict(c=0.03, hi=(0.06, 0.04, -0.04), sat=1.15, vib=0.15)),
    ("warm-copper", "نحاسي", "warm", dict(c=0.06, sh=(0.02, -0.01, -0.03), mid=(0.08, 0.02, -0.06), sat=0.95)),
    ("warm-peach", "خوخي", "warm", dict(c=0.02, lift=0.03, mid=(0.05, 0.02, -0.02), hi=(0.05, 0.03, 0), sat=1.0)),
    ("warm-amber", "كهرماني", "warm", dict(c=0.05, mid=(0.08, 0.05, -0.08), sat=1.08)),
    # cool
    ("cool-winter", "شتوي", "cool", dict(c=0.04, mid=C, hi=(-0.02, 0.01, 0.05), sat=0.9)),
    ("cool-ice", "ثلجي", "cool", dict(c=0.03, lift=0.03, mid=(-0.06, 0, 0.08), hi=(-0.03, 0.01, 0.06), sat=0.8)),
    ("cool-ocean", "بحري", "cool", dict(c=0.04, sh=(-0.05, 0.02, 0.07), mid=(-0.04, 0.02, 0.05), sat=1.08)),
    ("cool-steel", "فولاذي", "cool", dict(c=0.07, mid=(-0.04, 0, 0.04), sat=0.6)),
    ("cool-moon", "ضوء القمر", "cool", dict(c=0.05, gamma=1.15, mid=(-0.06, 0, 0.09), sat=0.75)),
    ("cool-tech", "تكنولوجيا", "cool", dict(c=0.05, sh=(-0.06, 0.02, 0.09), hi=(-0.01, 0.02, 0.04), sat=1.0)),
    ("cool-rain", "مطر", "cool", dict(c=0.03, lift=0.03, mid=(-0.04, 0.01, 0.04), sat=0.7)),
    ("cool-mint", "نعناعي", "cool", dict(c=0.03, sh=(-0.03, 0.04, 0.03), mid=(-0.02, 0.03, 0.01), sat=0.95)),
    ("cool-arctic", "قطبي", "cool", dict(c=0.06, lift=0.02, mid=(-0.07, -0.01, 0.1), sat=0.7)),
    ("cool-hospital", "عيادة", "cool", dict(c=0.04, mid=(-0.03, 0.03, 0.03), sat=0.7)),
    # bold
    ("bold-pop", "بوب", "bold", dict(c=0.06, sat=1.5, vib=0.2)),
    ("bold-punch", "ضربة", "bold", dict(c=0.1, sat=1.3, vib=0.15)),
    ("bold-hdr", "إتش دي آر", "bold", dict(c=0.03, lift=-0.0, gamma=0.92, sat=1.25, vib=0.3)),
    ("bold-comic", "كوميكس", "bold", dict(c=0.12, sat=1.6)),
    ("bold-fire", "نار", "bold", dict(c=0.08, mid=(0.1, 0.02, -0.1), hi=(0.08, 0.03, -0.08), sat=1.3)),
    ("bold-electric", "كهرباء", "bold", dict(c=0.08, sh=(-0.06, 0, 0.12), hi=(0.02, 0.04, 0.06), sat=1.3)),
    ("bold-tropic", "استوائي", "bold", dict(c=0.05, sh=(-0.03, 0.04, 0.03), hi=(0.06, 0.04, -0.04), sat=1.4, vib=0.2)),
    ("bold-candy", "حلاوة", "bold", dict(c=0.04, mid=(0.04, -0.02, 0.04), sat=1.45, vib=0.2)),
    ("bold-sport", "رياضة", "bold", dict(c=0.09, sh=(-0.04, 0, 0.06), hi=(0.04, 0.02, -0.03), sat=1.25, vib=0.15)),
    ("bold-gamer", "گيمر", "bold", dict(c=0.08, sh=(0.04, -0.04, 0.1), hi=(-0.02, 0.06, 0.04), sat=1.35)),
    ("bold-velvia", "مشبّع", "bold", dict(c=0.07, sat=1.55, hue=-4)),
    ("bold-red", "أحمر قوي", "bold", dict(c=0.08, mid=(0.08, -0.03, -0.03), sat=1.2)),
    # soft & pastel
    ("soft-dream", "حلم", "soft", dict(lift=0.06, roll=0.04, mid=(0.02, 0, 0.03), sat=0.85)),
    ("soft-pastel", "باستيل", "soft", dict(lift=0.08, roll=0.03, sat=0.7, hi=(0.03, 0.02, 0.03))),
    ("soft-cotton", "قطني", "soft", dict(lift=0.07, roll=0.05, mid=(0.03, 0.01, 0), sat=0.8)),
    ("soft-blush", "وردي ناعم", "soft", dict(lift=0.05, mid=(0.05, -0.01, 0.02), sat=0.9)),
    ("soft-lavender", "خزامى", "soft", dict(lift=0.05, mid=(0.02, -0.02, 0.06), sat=0.85)),
    ("soft-milk", "حليبي", "soft", dict(lift=0.1, roll=0.04, sat=0.75)),
    ("soft-airy", "فاتح ومنعش", "soft", dict(lift=0.04, gamma=0.9, hi=(-0.01, 0.01, 0.02), sat=0.95)),
    ("soft-spring", "ربيعي", "soft", dict(lift=0.04, sh=(0, 0.03, 0), hi=(0.03, 0.03, -0.01), sat=1.05)),
    ("soft-cream", "كريمي", "soft", dict(lift=0.06, mid=(0.04, 0.03, -0.03), sat=0.85)),
    ("soft-haze", "ضباب", "soft", dict(lift=0.12, roll=0.08, sat=0.8)),
    # black & white
    ("mono-classic", "أبيض وأسود كلاسيك", "mono", dict(c=0.05, mono=True)),
    ("mono-contrast", "أبيض وأسود قوي", "mono", dict(c=0.12, mono=True)),
    ("mono-soft", "أبيض وأسود ناعم", "mono", dict(lift=0.06, roll=0.04, mono=True)),
    ("mono-noir", "نوار", "mono", dict(c=0.12, gamma=1.2, mono=True, grain=4)),
    ("mono-silver", "فضّي", "mono", dict(c=0.06, mono=True, hi=(-0.01, 0, 0.02))),
    ("mono-blue", "أزرق أحادي", "mono", dict(c=0.05, mono=True, mid=(-0.06, 0, 0.08))),
    ("mono-green", "أخضر أحادي", "mono", dict(c=0.05, mono=True, mid=(-0.05, 0.06, -0.03))),
    ("mono-red", "أحمر أحادي", "mono", dict(c=0.07, mono=True, mid=(0.1, -0.03, -0.04))),
    ("mono-gold", "ذهبي أحادي", "mono", dict(c=0.05, mono=True, mid=(0.08, 0.04, -0.08))),
    ("mono-cyan", "سماوي أحادي", "mono", dict(c=0.05, mono=True, mid=(-0.08, 0.03, 0.06))),
    # night & neon
    ("night-neon", "نيون", "night", dict(c=0.08, sh=(0.04, -0.04, 0.12), hi=(0.08, -0.02, 0.06), sat=1.35)),
    ("night-cyber", "سايبر", "night", dict(c=0.08, sh=(-0.04, 0.04, 0.12), hi=(0.1, -0.02, 0.08), sat=1.3)),
    ("night-city", "مدينة بالليل", "night", dict(c=0.07, sh=(-0.04, 0.01, 0.07), hi=(0.07, 0.03, -0.04), sat=1.1)),
    ("night-purple", "بنفسجي", "night", dict(c=0.06, sh=(0.04, -0.04, 0.1), mid=(0.03, -0.03, 0.06), sat=1.15)),
    ("night-miami", "ميامي", "night", dict(c=0.05, sh=(0.06, -0.03, 0.08), hi=(0.02, 0.06, 0.06), sat=1.25)),
    ("night-club", "سهرة", "night", dict(c=0.09, mid=(0.06, -0.05, 0.08), sat=1.3)),
    ("night-vision", "رؤية ليلية", "night", dict(c=0.08, mono=True, mid=(-0.1, 0.12, -0.1), grain=6)),
    ("night-streetlamp", "عمود ضوء", "night", dict(c=0.07, sh=(-0.04, 0, 0.06), mid=(0.08, 0.04, -0.08), sat=1.0)),
    ("night-blade", "مستقبل مظلم", "night", dict(c=0.08, sh=(-0.03, 0.03, 0.07), mid=(0.07, 0.03, -0.06), sat=0.95)),
    ("night-blue-hour", "ساعة زرقة", "night", dict(c=0.04, mid=(-0.04, 0, 0.08), hi=(0.03, 0, 0.02), sat=1.1)),
    # nature & travel
    ("nature-forest", "غابة", "nature", dict(c=0.05, sh=(-0.02, 0.04, 0), mid=(-0.01, 0.04, -0.02), sat=1.15)),
    ("nature-green", "أخضر طبيعي", "nature", dict(c=0.04, mid=(-0.02, 0.03, -0.01), sat=1.2, vib=0.15)),
    ("nature-sky", "سماء صافية", "nature", dict(c=0.04, hi=(-0.03, 0.01, 0.06), sat=1.15, vib=0.2)),
    ("nature-beach", "شاطئ", "nature", dict(c=0.03, lift=0.02, sh=(-0.03, 0.03, 0.04), hi=(0.05, 0.04, -0.02), sat=1.2)),
    ("nature-mountain", "جبال", "nature", dict(c=0.06, mid=(-0.02, 0.01, 0.03), sat=1.05, vib=0.15)),
    ("nature-safari", "سفاري", "nature", dict(c=0.05, mid=(0.06, 0.04, -0.06), sat=1.05)),
    ("nature-travel", "سفر", "nature", dict(c=0.05, sh=(-0.03, 0.01, 0.04), hi=(0.05, 0.03, -0.03), sat=1.2, vib=0.2)),
    ("nature-drone", "تصوير جوي", "nature", dict(c=0.06, gamma=0.95, sat=1.2, vib=0.25)),
    ("nature-moody-green", "أخضر غامق", "nature", dict(c=0.07, lift=0.02, mid=(-0.03, 0.03, 0), sat=0.85)),
    ("nature-sahara", "صحراء", "nature", dict(c=0.05, mid=(0.08, 0.04, -0.07), hi=(0.06, 0.04, -0.06), sat=1.05)),
    # documentary & news
    ("doc-clean", "نظيف", "doc", dict(c=0.03, sat=1.05, vib=0.1)),
    ("doc-investigate", "تحقيق", "doc", dict(c=0.07, lift=0.02, sh=(-0.02, 0.02, 0.04), sat=0.8)),
    ("doc-news", "نشرة أخبار", "doc", dict(c=0.04, hi=(-0.01, 0, 0.02), sat=1.08)),
    ("doc-history", "تاريخي", "doc", dict(c=0.05, lift=0.03, mid=(0.04, 0.02, -0.04), sat=0.75, grain=3)),
    ("doc-crime", "جريمة", "doc", dict(c=0.08, sh=(-0.02, 0.03, 0.05), mid=(-0.01, 0.02, 0.01), sat=0.7)),
    ("doc-business", "شركات", "doc", dict(c=0.05, sh=(-0.03, 0, 0.05), hi=(0.03, 0.02, -0.02), sat=1.02)),
    ("doc-interview", "مقابلة", "doc", dict(c=0.04, lift=0.02, mid=(0.02, 0.01, -0.02), sat=1.0)),
    ("doc-street", "شارع", "doc", dict(c=0.06, lift=0.02, sat=0.9, grain=2)),
    # skin & faces
    ("skin-natural", "بشرة طبيعية", "skin", dict(c=0.03, mid=(0.02, 0.01, -0.02), sat=1.02)),
    ("skin-glow", "بشرة مضيئة", "skin", dict(c=0.02, gamma=0.92, mid=(0.03, 0.01, -0.01), sat=1.0)),
    ("skin-tan", "سمرة", "skin", dict(c=0.04, mid=(0.05, 0.02, -0.04), sat=1.05)),
    ("skin-portrait", "پورتريه", "skin", dict(c=0.04, lift=0.02, sh=(-0.02, 0, 0.03), mid=(0.03, 0.01, -0.02), sat=0.95)),
    ("skin-beauty", "تجميل", "skin", dict(lift=0.03, gamma=0.94, mid=(0.03, 0, 0.01), sat=0.95)),
    ("skin-studio", "استوديو", "skin", dict(c=0.05, mid=(0.02, 0.01, -0.01), sat=1.0, vib=0.08)),
    ("skin-matte", "مطفي", "skin", dict(c=0.03, lift=0.05, roll=0.03, mid=(0.02, 0.01, -0.01), sat=0.9)),
    ("skin-podcast", "بودكاست", "skin", dict(c=0.05, sh=(-0.02, 0, 0.03), mid=(0.04, 0.02, -0.03), sat=1.0)),
    # mood & drama
    ("mood-dark", "غامق ودرامي", "mood", dict(c=0.08, gamma=1.15, sh=(-0.02, 0, 0.04), sat=0.8)),
    ("mood-sad", "حزين", "mood", dict(c=0.03, lift=0.04, mid=(-0.03, 0, 0.04), sat=0.6)),
    ("mood-horror", "رعب", "mood", dict(c=0.1, gamma=1.2, sh=(-0.03, 0.04, 0.02), sat=0.5, grain=5)),
    ("mood-mystery", "غموض", "mood", dict(c=0.07, gamma=1.1, sh=(-0.03, 0.02, 0.06), mid=(-0.02, 0.01, 0.03), sat=0.75)),
    ("mood-hope", "أمل", "mood", dict(c=0.03, gamma=0.92, hi=(0.05, 0.03, -0.02), sat=1.08)),
    ("mood-tension", "توتر", "mood", dict(c=0.09, mid=(0.03, 0.03, -0.04), sat=0.85)),
    ("mood-blood", "دم", "mood", dict(c=0.1, gamma=1.1, mid=(0.08, -0.04, -0.04), sat=0.9)),
    ("mood-memory", "ذكرى", "mood", dict(lift=0.08, roll=0.06, mid=(0.04, 0.02, -0.03), sat=0.7, grain=3)),
    ("mood-toxic", "سام", "mood", dict(c=0.08, mid=(-0.02, 0.07, -0.05), sat=1.1)),
    ("mood-royal", "ملكي", "mood", dict(c=0.06, sh=(0.02, -0.03, 0.07), hi=(0.07, 0.05, -0.05), sat=1.1)),
]

PACK_LOOKS = {k: _look(**p) for k, _, _, p in _T}
PACK_NAMES = {k: n for k, n, _, _ in _T}
PACK_CATS = {k: c for k, _, c, _ in _T}
