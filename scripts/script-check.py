#!/usr/bin/env python3
"""فاحص السكربت: يكشف مخالفات شروط القناة تلقائياً.

الاستخدام:
    python3 scripts/script-check.py episodes/<الحلقة>/02-draft.md
    python3 scripts/script-check.py <الملف> --strict   # يرجع رمز خطأ إذا اكو مشاكل حمراء

يفحص (المنهج الثالث، studio/style/method.md): العنوان بأول الملف، الطول (15-32 دقيقة)،
طول الجمل، صيغة التواريخ وعددها، السنين الي ترجع لورا، الحروف الأجنبية (الأسماء لازم بالعربي)،
الفصحى، الكليشيهات، "بس" مقابل "وبعدين"، تكرار وعود "بآخر الحلقة"، والمناطق الميتة.
"""
import re
import sys

MIN_WORDS = 2100   # 15 دقيقة
MAX_WORDS = 4500   # تقريباً 32 دقيقة
MAX_LINE_WORDS = 20   # السطر = جملة كاملة تنقال بنفَس واحد
WARN_LINE_WORDS = 16
WORDS_PER_MIN = 140
DEAD_ZONE = 350
MAX_DATES = 3        # تواريخ كاملة: بس للأحداث الكبيرة
MAX_TIME_REFS = 8    # كل ذكر لسنة
MAX_TEASERS = 2      # وعود "بآخر الحلقة / راح تعرف"
TEASERS = ["بآخر الحلقة", "بنهاية الحلقة", "راح تعرف", "راح نعرف", "راح تكتشف", "راح أگولك", "بعدين راح", "خلّيها لبعدين", "بعد شوية راح"]
REWIND = ["خلي أرجعك شوية لورا", "نرجع للمطار", "نرجع لأول القصة", "خلي نرجع للبداية", "نرجع للمشهد"]

AR = r"؀-ۿ"

# الأسماء تنكتب بالحروف العربية (صاحب القناة يقرا من الآيباد وما يقرا إنگليزي)
LATIN = re.compile(r"[A-Za-z]{2,}")

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
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    strict = "--strict" in sys.argv
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    words = text.split()
    red, yellow = [], []

    # 0. العنوان أول سطر
    first = next((ln.strip() for ln in lines if ln.strip()), "")
    if not first.startswith("العنوان"):
        red.append("أول سطر لازم يكون \"العنوان: ...\" وبعده الهوك وبعده السكربت.")

    # 1. الطول
    n = len(words)
    if n < MIN_WORDS:
        red.append(f"الطول {n} كلمة (~{round(n / WORDS_PER_MIN)} دقيقة)، الحد الأدنى {MIN_WORDS} (15 دقيقة).")
    elif n > MAX_WORDS:
        yellow.append(f"الطول {n} كلمة (~{round(n / WORDS_PER_MIN)} دقيقة)، فوق 30 دقيقة: تأكد إن كل فصل يستاهل.")

    # 2. طول الجمل
    for i, ln in enumerate(lines, 1):
        c = len(ln.split())
        if c > MAX_LINE_WORDS:
            red.append(f"سطر {i}: {c} كلمة (الحد {MAX_LINE_WORDS}): {ln.strip()[:60]}")
        elif c > WARN_LINE_WORDS:
            yellow.append(f"سطر {i}: {c} كلمة، حاول تقصّه: {ln.strip()[:60]}")

    # 2b. التقطيع الزايد (جمل كلمة أو كلمتين ورا بعض تشتت المقدّم والمشاهد)
    body = [ln for ln in lines if ln.strip() and not ln.strip().startswith(("العنوان", "الهوك", "السكربت"))]
    frag = [ln for ln in body if len(ln.split()) <= 2]
    if body and len(frag) / len(body) > 0.15:
        red.append(f"تقطيع زايد: {len(frag)} سطر من {len(body)} بيه كلمة أو كلمتين ({round(100*len(frag)/len(body))}%). اكتب جمل كاملة متصلة (الحد 15%).")
    avg = sum(len(ln.split()) for ln in body) / max(1, len(body))
    if avg < 6:
        yellow.append(f"معدل طول السطر {avg:.1f} كلمة: قصير هواي، السرد يصير مقطّع. الأحسن 7-12.")

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

    # 3b2. سنين ترجع لورا (97 ثم 96 ثم 99 يلخبط المشاهد)
    years = [int(y) for y in re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", text)]
    back = [(a, b) for a, b in zip(years, years[1:]) if b < a]
    if back:
        yellow.append("سنين ترجع لورا: " + "، ".join(f"{a}←{b}" for a, b in back[:6]) + ". خلي الزمن يمشي لگدام، واستخدم \"قبلها بسنة\" بدل رقم.")

    # 3d. وعود "بآخر الحلقة" المكررة (تملّ المشاهد)
    t = sum(len(word_re(x).findall(text)) for x in TEASERS)
    if t > MAX_TEASERS:
        yellow.append(f"وعود \"راح تعرف/بآخر الحلقة\" {t} مرة (الحد {MAX_TEASERS}). بدالها انطي طُعم: جزء من الجواب.")

    # 3c. الرجوع لمشهد البداية بالنص (ممنوع)
    for i, ln in enumerate(lines, 1):
        if any(r in ln for r in REWIND):
            red.append(f"سطر {i}: رجوع لورا بنص الحلقة (ممنوع، التسلسل لگدام بس): {ln.strip()[:60]}")

    # 4. الحروف الأجنبية (ممنوعة)
    for i, ln in enumerate(lines, 1):
        m = LATIN.findall(ln)
        if m:
            red.append(f"سطر {i}: حروف إنگليزية ({', '.join(m[:3])})، اكتبها بالعربي بلفظ سهل")

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
    need = max(6, n // 450)
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
