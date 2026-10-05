"""تجهيز الكتابة العربية للرسم: كل كلمة تنرسم لحالها، والكلمات تترتب من اليمين لليسار."""
import re

from PIL import ImageFont, features

RAQM = features.check("raqm")
ARABIC = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")


def is_rtl(text: str) -> bool:
    return bool(ARABIC.search(text))


def load_font(path, px: int) -> ImageFont.FreeTypeFont:
    engine = ImageFont.Layout.RAQM if RAQM else ImageFont.Layout.BASIC
    return ImageFont.truetype(str(path), px, layout_engine=engine)


def shape_word(word: str) -> tuple[str, dict]:
    """يرجع النص الجاهز للرسم ومعاملات draw.text الإضافية."""
    if not is_rtl(word):
        return word, {}
    if RAQM:
        return word, {"direction": "rtl", "language": "ar"}
    import arabic_reshaper
    from bidi.algorithm import get_display
    return get_display(arabic_reshaper.reshape(word)), {}


def visual_words(line: str) -> list[str]:
    """ترتيب الكلمات مثل ما تنرسم من اليسار لليمين.

    بسطر فيه عربي: كل كلمة عربية تبقى بمكانها، وكل مجموعة كلمات لاتينية
    متلاصقة (مثل "Apple Watch!") تنحسب وحدة (ترتيبها الداخلي ما ينعكس)،
    وبعدين ترتيب المجموعات نفسها ينعكس.
    """
    words = line.split()
    if not is_rtl(line):
        return words
    runs: list[list[str]] = []
    latin_run: list[str] = []
    for word in words:
        if is_rtl(word):
            if latin_run:
                runs.append(latin_run)
                latin_run = []
            runs.append([word])
        else:
            latin_run.append(word)
    if latin_run:
        runs.append(latin_run)
    result: list[str] = []
    for run in reversed(runs):
        result.extend(run)
    return result
