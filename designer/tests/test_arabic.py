import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import arabic  # noqa: E402

FONT = Path(__file__).resolve().parents[1] / "fonts" / "Lalezar-Regular.ttf"


class ArabicTest(unittest.TestCase):
    def test_is_rtl(self):
        self.assertTrue(arabic.is_rtl("فلوس"))
        self.assertFalse(arabic.is_rtl("iPhone 17"))

    def test_arabic_line_words_reversed_for_drawing(self):
        self.assertEqual(arabic.visual_words("فلوس الناس وين"), ["وين", "الناس", "فلوس"])

    def test_english_line_keeps_order(self):
        self.assertEqual(arabic.visual_words("iPhone 17 Pro"), ["iPhone", "17", "Pro"])

    def test_mixed_numbers_and_arabic(self):
        self.assertEqual(arabic.visual_words("300 مليار $"), ["$", "مليار", "300"])

    def test_mixed_arabic_and_multiword_latin_keeps_run_order(self):
        self.assertEqual(arabic.visual_words("خسرت Apple Watch!"), ["Apple", "Watch!", "خسرت"])

    def test_raqm_available_in_pillow(self):
        self.assertTrue(arabic.RAQM, "Pillow بدون raqm: الحروف العربية راح تطلع مقطعة")

    def test_shape_word_arabic_uses_rtl_with_raqm(self):
        with mock.patch.object(arabic, "RAQM", True):
            self.assertEqual(arabic.shape_word("فلوس"), ("فلوس", {"direction": "rtl", "language": "ar"}))

    def test_shape_word_latin_untouched(self):
        self.assertEqual(arabic.shape_word("300"), ("300", {}))

    def test_fallback_without_raqm_connects_letters(self):
        with mock.patch.object(arabic, "RAQM", False):
            text, kw = arabic.shape_word("فلوس")
        self.assertEqual(kw, {})
        self.assertNotEqual(text, "فلوس")  # صارت أشكال حروف متصلة ومعكوسة للرسم

    def test_load_font(self):
        font = arabic.load_font(FONT, 40)
        self.assertGreater(font.getlength("فلوس", direction="rtl"), 0)


if __name__ == "__main__":
    unittest.main()
