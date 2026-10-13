import importlib.util
import sys
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import arabic  # noqa: E402
import render  # noqa: E402

HAS_FONTTOOLS = importlib.util.find_spec("fontTools") is not None
ARABIC_LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي؟"
LATIN_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!"


def ink(font, text: str) -> int:
    """عدد بكسلات الحبر لما الكلمة تنرسم بهذا الخط."""
    img = Image.new("L", (900, 300))
    text, kw = arabic.shape_word(text)
    ImageDraw.Draw(img).text((20, 20), text, font=font, fill=255, **kw)
    return sum(img.histogram()[129:])


def cmap(name: str) -> set:
    from fontTools.ttLib import TTFont
    return set(TTFont(render.FONTS_DIR / render.FONTS[name]).getBestCmap())


def license_name(file_name: str) -> str:
    """اسم ملف الرخصة: OFL-<أول جزء من اسم الخط>.txt (BalooBhaijaan2-ExtraBold ← BalooBhaijaan2)."""
    return f"OFL-{file_name.split('-')[0]}.txt"


class FontsTest(unittest.TestCase):
    def test_registry_has_22_fonts(self):
        self.assertEqual(len(render.FONTS), 22)
        self.assertEqual(render.LATIN_FONTS,
                         frozenset({"Anton", "Bebas", "Bangers", "ArchivoBlack", "Montserrat", "Oswald"}))
        self.assertTrue(render.LATIN_FONTS <= set(render.FONTS))

    def test_every_registered_font_opens(self):
        for name, file_name in render.FONTS.items():
            with self.subTest(font=name):
                path = render.FONTS_DIR / file_name
                self.assertTrue(path.exists(), path)
                arabic.load_font(path, 40)

    def test_every_font_has_its_license(self):
        licenses = {p.name for p in render.FONTS_DIR.glob("OFL-*.txt")}
        for name, file_name in render.FONTS.items():
            with self.subTest(font=name):
                self.assertTrue(f"OFL-{name}.txt" in licenses or license_name(file_name) in licenses)

    @unittest.skipUnless(HAS_FONTTOOLS, "fontTools مو منصب")
    def test_arabic_fonts_cover_arabic_letters(self):
        for name in set(render.FONTS) - render.LATIN_FONTS:
            with self.subTest(font=name):
                missing = [c for c in ARABIC_LETTERS if ord(c) not in cmap(name)]
                self.assertEqual(missing, [])

    @unittest.skipUnless(HAS_FONTTOOLS, "fontTools مو منصب")
    def test_latin_fonts_cover_letters_and_digits(self):
        for name in render.LATIN_FONTS:
            with self.subTest(font=name):
                missing = [c for c in LATIN_CHARS if ord(c) not in cmap(name)]
                self.assertEqual(missing, [])

    def test_variable_font_loads_at_max_weight(self):
        path = render.FONTS_DIR / render.FONTS["Changa"]
        default = ImageFont.truetype(str(path), 120, layout_engine=ImageFont.Layout.RAQM)
        self.assertGreater(ink(arabic.load_font(path, 120), "نهاية"), ink(default, "نهاية") * 1.1)

    def test_static_font_unchanged(self):
        path = render.FONTS_DIR / render.FONTS["Cairo"]
        plain = ImageFont.truetype(str(path), 120, layout_engine=ImageFont.Layout.RAQM)
        self.assertEqual(ink(arabic.load_font(path, 120), "نهاية"), ink(plain, "نهاية"))


if __name__ == "__main__":
    unittest.main()
