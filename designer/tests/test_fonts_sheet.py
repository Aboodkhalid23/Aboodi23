import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fonts_sheet  # noqa: E402
import render  # noqa: E402


class FontsSheetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sheet = fonts_sheet.make_sheet()

    def test_one_row_per_font(self):
        self.assertEqual(self.sheet.size,
                         (fonts_sheet.SHEET_W, fonts_sheet.HEADER + fonts_sheet.ROW_H * len(render.FONTS)))

    def test_rows_have_ink(self):
        gray = self.sheet.convert("L")
        for i, name in enumerate(render.FONTS):
            with self.subTest(font=name):
                y = fonts_sheet.HEADER + i * fonts_sheet.ROW_H
                hist = gray.crop((fonts_sheet.SAMPLE_X, y, fonts_sheet.SHEET_W, y + fonts_sheet.ROW_H)).histogram()
                self.assertGreater(sum(hist[241:]), 500)   # أبيض
                self.assertGreater(sum(hist[:12]), 500)    # الحد الأسود

    def test_samples_fit_inside(self):
        margin = self.sheet.convert("L").crop((fonts_sheet.SHEET_W - 24, fonts_sheet.HEADER,
                                               fonts_sheet.SHEET_W, self.sheet.height))
        self.assertEqual(sum(margin.histogram()[200:]), 0)

    def test_cli_writes_jpg(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "s.jpg"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(fonts_sheet.main(["-o", str(out)]), 0)
            with Image.open(out) as im:
                self.assertEqual(im.size, self.sheet.size)


if __name__ == "__main__":
    unittest.main()
