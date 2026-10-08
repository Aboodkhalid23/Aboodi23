#!/usr/bin/env python3
"""فاحص السكربت: يكشف مخالفات شروط القناة تلقائياً.

الاستخدام:
    python3 scripts/script-check.py episodes/<الحلقة>/02-draft.md
    python3 scripts/script-check.py <الملف> --strict   # يرجع رمز خطأ إذا اكو مشاكل حمراء

يفحص: عدد الكلمات، طول الجمل، صيغة التواريخ، الأسماء المعرّبة (لازم إنگليزي)،
الفصحى، كليشيهات الذكاء الاصطناعي، "بس" مقابل "وبعدين"، الأسئلة بكل دقيقة،
والمقاطع الميتة (كتلة 200 كلمة بدون سؤال).
"""
import re
import sys

MIN_WORDS = 4000
MAX_LINE_WORDS = 12
WARN_LINE_WORDS = 10
WORDS_PER_MIN = 140
DEAD_ZONE = 200
MAX_DATES = 5
MAX_TIME_REFS = 10
REWIND = ["خلي أرجعك شوية لورا", "نرجع للمطار", "نرجع لأول القصة", "خلي نرجع للبداية", "نرجع للمشهد"]

AR = r"؀-ۿ"

# أسماء معرّبة لازم تنكتب بالإنگليزي
ARABIZED = {
    "أوبن إيه آي": "OpenAI", "اوبن اي اي": "OpenAI", "تشات جي بي تي": "ChatGPT",
    "أنثروبيك": "Anthropic", "انثروبيك": "Anthropic", "كلود": "Claude",
    "غوغل": "Google", "غوگل": "Google", "جوجل": "Google", "ميتا": "Meta",
    "مايكروسوفت": "Microsoft", "أمازون": "Amazon", "أبل": "Apple", "آبل": "Apple",
    "إنفيديا": "Nvidia", "انفيديا": "Nvidia", "تسلا": "Tesla", "سبيس إكس": "SpaceX",
    "فيسبوك": "Facebook", "يوتيوب": "YouTube", "تيك توك": "TikTok", "إنستغرام": "Instagram",
    "رويترز": "Reuters", "بلومبرغ": "Bloomberg", "فوربس": "Forbes", "فيفا": "FIFA",
    "إيلون ماسك": "Elon Musk", "ماسك": "Musk", "سام ألتمان": "Sam Altman", "ألتمان": "Altman",
    "ميسي": "Messi", "رونالدو": "Ronaldo", "ترامب": "Trump", "هگنگ فيس": "Hugging Face",
    "هَگنگ فيس": "Hugging Face", "نتفليكس": "Netflix", "سامسونج": "Samsung", "سامسونگ": "Samsung",
}

FUSHA = ["يتوجب", "ينبغي", "آنذاك", "جراء", "وفقاً", "حيال", "غالباً ما", "المفارقة",
         "يخيّم", "يُذكر أن", "لكن ", "الآن", "كثيراً", "ماذا", "لماذا", "كيف ", "حيث ",
         "قام بـ", "تم ", "من خلال", "سوف", "هذه ", "الذي", "التي", "ليس ", "أيضاً"]

CLICHES = ["في عالم مليء", "دعونا نغوص", "رحلة مثيرة", "لا يخفى على أحد", "في الختام",
           "وهنا تكمن المشكلة", "يطرح تساؤلات", "بالختام"]

# تواريخ مكتوبة بالحروف (ممنوع): "20 آب" / "بأيلول 2021"
MONTHS = "كانون الثاني|شباط|آذار|نيسان|أيار|حزيران|تموز|آب|أيلول|تشرين الأول|تشرين الثاني|كانون الأول|يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر"
WORD_DATE = re.compile(rf"\d{{1,2}}\s+(?:{MONTHS})|(?:{MONTHS})\s+\d{{4}}")
BAD_NUM_DATE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b")  # يوم/شهر/سنة بدل سنة/شهر/يوم


def word_re(w):
    return re.compile(rf"(?<![{AR}]){re.escape(w)}(?![{AR}])")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    strict = "--strict" in sys.argv
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    words = text.split()
    red, yellow = [], []

    # 1. الطول
    n = len(words)
    if n < MIN_WORDS:
        red.append(f"الطول {n} كلمة، والحد الأدنى {MIN_WORDS} (ناقص {MIN_WORDS - n}).")

    # 2. طول الجمل
    for i, ln in enumerate(lines, 1):
        c = len(ln.split())
        if c > MAX_LINE_WORDS:
            red.append(f"سطر {i}: {c} كلمة (الحد {MAX_LINE_WORDS}): {ln.strip()[:60]}")
        elif c > WARN_LINE_WORDS:
            yellow.append(f"سطر {i}: {c} كلمة، حاول تقصّه: {ln.strip()[:60]}")

    # 3. التواريخ
    for i, ln in enumerate(lines, 1):
        if WORD_DATE.search(ln):
            red.append(f"سطر {i}: تاريخ بالحروف، لازم بالأرقام (2026/6/18): {ln.strip()[:60]}")
        if BAD_NUM_DATE.search(ln):
            red.append(f"سطر {i}: تاريخ بصيغة يوم/شهر/سنة، لازم سنة/شهر/يوم: {ln.strip()[:60]}")

    # 3b. عدد التواريخ الكاملة (حد أقصى 5 مختلفة)
    full_dates = re.findall(r"(?<!\d)\d{4}/\d{1,2}(?:/\d{1,2})?(?!\d)", text)
    uniq = sorted(set(full_dates))
    if len(uniq) > MAX_DATES:
        red.append(f"تواريخ كاملة هواي: {len(uniq)} تاريخ مختلف (الحد {MAX_DATES}). حوّل الباقي لزمن نسبي (بعدها بـ10 أيام): {', '.join(uniq)}")

    all_time = re.findall(r"(?<!\d)(?:19|20)\d{2}(?:/\d{1,2}){0,2}(?!\d)", text)
    if len(all_time) > MAX_TIME_REFS:
        yellow.append(f"ذكر سنوات وتواريخ {len(all_time)} مرة (الأفضل {MAX_TIME_REFS} أو أقل). المشاهد يضيع: استبدل قسم منها بـ\"بعدها بـ...\".")

    # 3c. الرجوع لمشهد البداية بالنص (ممنوع)
    for i, ln in enumerate(lines, 1):
        if any(r in ln for r in REWIND):
            red.append(f"سطر {i}: رجوع لورا بنص الحلقة (ممنوع، التسلسل لگدام بس): {ln.strip()[:60]}")

    # 4. الأسماء المعرّبة
    for ar, en in ARABIZED.items():
        for i, ln in enumerate(lines, 1):
            if word_re(ar).search(ln):
                red.append(f"سطر {i}: \"{ar}\" لازم تنكتب {en}")

    # 5. الفصحى والكليشيهات
    for w in FUSHA:
        hits = [i for i, ln in enumerate(lines, 1) if word_re(w.strip()).search(ln)]
        if hits:
            yellow.append(f"فصحى \"{w.strip()}\" بالأسطر: {hits[:8]}")
    for w in CLICHES:
        if w in text:
            red.append(f"كليشيه ممنوع: \"{w}\"")

    # 6. بس / وبعدين
    bas = len(word_re("بس").findall(text))
    then = len(word_re("وبعدين").findall(text)) + len(word_re("وبعدها").findall(text))
    need = max(15, n // 270)
    if bas < need:
        yellow.append(f"\"بس\" {bas} مرة، المطلوب {need} أو أكثر (تقلب القصة).")
    if then > bas / 3:
        yellow.append(f"\"وبعدين/وبعدها\" {then} مرة: هواي، استبدلها بـ\"بس\" أو \"فلهذا\".")

    # 7. الأسئلة والمناطق الميتة
    count, since_q, block_start, dead = 0, 0, 1, []
    for i, ln in enumerate(lines, 1):
        w = len(ln.split())
        count += w
        since_q += w
        if "؟" in ln or "?" in ln:
            since_q = 0
            block_start = i + 1
        elif since_q > DEAD_ZONE:
            dead.append(f"من سطر {block_start} لسطر {i}")
            since_q = 0
            block_start = i + 1
    if dead:
        yellow.append(f"مناطق ميتة (أكثر من {DEAD_ZONE} كلمة بدون سؤال): {len(dead)}: " + "، ".join(dead[:6]))

    # التقرير
    qs = text.count("؟") + text.count("?")
    print(f"📄 {path}")
    print(f"الكلمات: {n} | المدة: ~{round(n / WORDS_PER_MIN)} دقيقة | الأسئلة: {qs} | بس: {bas} | وبعدين: {then}")
    print(f"\n🔴 مشاكل لازم تنصلح: {len(red)}")
    for r in red[:60]:
        print("  - " + r)
    print(f"\n🟡 تحذيرات: {len(yellow)}")
    for y in yellow[:60]:
        print("  - " + y)
    print("\n✅ جاهز" if not red else "\n❌ مو جاهز")
    if strict and red:
        sys.exit(2)


if __name__ == "__main__":
    main()
