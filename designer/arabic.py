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
    """ترتيب الكلمات مثل ما تنرسم من اليسار لليمين."""
    words = line.split()
    return list(reversed(words)) if is_rtl(line) else words
