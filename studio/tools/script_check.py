"""Script checker: the studio's quick, free quality gate (studio skill steps 5 and 7).

    python3 studio/tools/script_check.py episodes/<ep>/04-script.md [--record]

Scores a script out of 100 against studio/script-rules.md: length, Iraqi dialect (heavy Classical Arabic words),
AI clichés, Iraq mentions (the channel's topics are global), a hook that hits in the first ~70 words, open loops
often enough, talking to the viewer, numbers, sentence rhythm, no headings. Prints what to fix first (Arabic).
--record adds the numbers to studio/growth/scripts.jsonl, so the team can see whether scripts get better."""
import json
import re
import sys
from datetime import date
from pathlib import Path

HISTORY = Path(__file__).resolve().parents[1] / "growth" / "scripts.jsonl"
MIN_WORDS = 2800

FUSHA = ["الذي", "التي", "الذين", "اللذين", "سوف", "لقد", "إنّ", "ماذا", "لماذا", "كيف", "يتوجب", "ينبغي", "آنذاك",
         "جراء", "وفقاً", "وفقا", "حيال", "يُذكر", "يذكر أن", "حيث", "ذلك", "هؤلاء", "أولئك", "ليس", "لسنا", "إذ",
         "الآن", "كثيراً", "لكنّ", "لكن", "أيضاً", "هكذا", "عندئذ", "بينما"]
CLICHES = ["في عالم مليء", "دعونا نغوص", "رحلة مثيرة", "لا يخفى على أحد", "في الختام", "وهنا تكمن", "يطرح تساؤلات",
           "خلونا نغوص", "رحلة شيقة", "على مر العصور", "منذ فجر التاريخ", "بكل ما تحمله الكلمة", "غني عن التعريف"]
IRAQ = ["العراق", "عراقي", "عراقية", "بغداد", "البصرة", "الموصل", "أربيل"]
LOOPS = ["بعدين", "راح أگولك", "راح اگولك", "الأغرب", "الاغرب", "بس هذا مو", "انتظر", "السؤال", "تعرف شنو", "خلي أگولك",
         "خلي اگولك", "الي محد", "اللي محد", "بس القصة ما خلصت", "والمفاجأة", "والمفاجئة", "الصدمة", "السر"]
ADDRESS = ["تخيل", "تخيّل", "انت ", "إنت", "انتو", "إنتو", "شوف", "تصدق", "تعرف"]


def _count(text: str, words: list[str]) -> int:
    return sum(len(re.findall(r"(?<![\w])" + re.escape(w.strip()) + r"(?![\w])", text)) for w in words)


def check(path: Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    words = text.split()
    n = len(words)
    k = max(1, n / 1000)
    issues: list[tuple[int, str]] = []

    if n < MIN_WORDS:
        issues.append((20, f"قصير: {n} كلمة (أقل شي {MIN_WORDS})، وسّع بقصص حقيقية من البحث مو حشو"))
    heads = [ln for ln in text.splitlines() if ln.strip().startswith(("#", "**المشهد", "[", "("))]
    if heads:
        issues.append((8, f"بيه عناوين أو ملاحظات إنتاج ({len(heads)}): السكربت نص واحد متواصل"))
    fusha = _count(text, FUSHA)
    if fusha / k > 6:
        issues.append((min(15, int(fusha / k)), f"فصحى: {fusha} كلمة ثقيلة (~{fusha / k:.0f} بكل ألف): مثل "
                       + "، ".join(w for w in FUSHA if _count(text, [w]))[:80]))
    cl = [c for c in CLICHES if c in text]
    if cl:
        issues.append((4 * len(cl), "كليشيهات ذكاء اصطناعي: " + "، ".join(cl)))
    iraq = _count(text, IRAQ)
    if iraq:
        issues.append((10, f"ذكر العراق {iraq} مرة: مواضيع القناة عالمية، والربط بحياة المشاهد عموماً"))
    hook = " ".join(words[:70])
    if not (re.search(r"[0-9٠-٩]", hook) or "?" in hook or "؟" in hook or _count(hook, ADDRESS)):
        issues.append((10, "الهوك (أول 70 كلمة) ما بيه رقم ولا سؤال ولا مخاطبة: ما يوقف السكرول"))
    loops = _count(text, LOOPS)
    if loops < n / 300:
        issues.append((8, f"حلقات مفتوحة قليلة: {loops} (الأحسن وحدة كل 150–200 كلمة، يعني ~{n // 180})"))
    addr = _count(text, ADDRESS)
    if addr < n / 400:
        issues.append((4, f"قليل يخاطب المشاهد: {addr} مرة (تخيّل، انت، شوف)"))
    nums = len(re.findall(r"[0-9٠-٩]+", text))
    if nums < n / 250:
        issues.append((4, f"أرقام قليلة: {nums} (الأرقام تخلي المعلومة ملموسة وتنفع المونتاج)"))
    sents = [s.split() for s in re.split(r"[.!؟?\n]+", text) if s.strip()]
    long = [s for s in sents if len(s) > 32]
    if long:
        issues.append((min(8, len(long)), f"{len(long)} جملة طويلة هواية (أكثر من 32 كلمة): قسّمها، المقدّم لازم يتنفس"))
    lens = [len(s) for s in sents]
    flat, run = 0, 1
    for a, b in zip(lens, lens[1:]):
        run = run + 1 if abs(a - b) <= 2 else 1
        flat = max(flat, run)
    if flat >= 6:
        issues.append((4, f"إيقاع مسطح: {flat} جمل ورا بعض بنفس الطول (نوّع: قصيرة للصدمة، متوسطة للسرد)"))
    latin = re.findall(r"[A-Za-z]{3,}", text)
    if len(latin) > n / 150:
        issues.append((3, f"{len(latin)} كلمة بحروف إنگليزية: اكتب الأسماء بحروف عربية حتى المقدّم يقراها بسهولة"))

    score = max(0, 100 - sum(w for w, _ in issues))
    issues.sort(key=lambda x: -x[0])
    return {"file": str(path), "score": score, "words": n, "minutes": round(n / 140, 1), "fusha_per_1000": round(fusha / k, 1),
            "loops": loops, "address": addr, "numbers": nums, "issues": [t for _, t in issues]}


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("الاستخدام: python3 studio/tools/script_check.py <ملف السكربت> [--record]")
        return 2
    r = check(Path(argv[0]))
    print(f"درجة السكربت: {r['score']}/100 | {r['words']} كلمة (~{r['minutes']} دقيقة) | فصحى {r['fusha_per_1000']} بكل ألف"
          f" | حلقات مفتوحة {r['loops']} | مخاطبة {r['address']} | أرقام {r['numbers']}")
    for i in r["issues"]:
        print("-", i)
    if not r["issues"]:
        print("✅ ما لگيت شي يحتاج تصليح")
    if "--record" in argv:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        row = {"date": date.today().isoformat(), **{k: v for k, v in r.items() if k != "issues"}}
        with HISTORY.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
