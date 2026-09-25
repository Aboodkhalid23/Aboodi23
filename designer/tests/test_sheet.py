import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sheet  # noqa: E402


class SheetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.paths = []
        for name, color in zip("ABCDE", [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 0, 0)]):
            p = cls.dir / f"{name}.png"
            Image.new("RGB", (1280, 720), color).save(p)
            cls.paths.append(p)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_four_images_sheet_size(self):
        img = sheet.make_sheet(self.paths[:4])
        self.assertEqual(img.size, sheet.SHEET_SIZE)

    def test_tile_b_is_top_right(self):
        img = sheet.make_sheet(self.paths[:4])
        x = sheet.GAP * 2 + sheet.TILE[0] + sheet.TILE[0] // 2
        self.assertEqual(img.getpixel((x, sheet.GAP + 200)), (0, 255, 0))

    def test_mini_previews_on_light_and_dark_rows(self):
        img = sheet.make_sheet(self.paths[:1])
        cx = sheet.GAP + sheet.MINI[0] // 2
        self.assertEqual(img.getpixel((cx, sheet.LIGHT_ROW_Y + 40))[0], 255)
        self.assertEqual(img.getpixel((cx, sheet.DARK_ROW_Y + 40))[0], 255)
        self.assertEqual(img.getpixel((sheet.SHEET_W - 5, sheet.LIGHT_ROW_Y + 40)), (255, 255, 255))
        self.assertEqual(img.getpixel((sheet.SHEET_W - 5, sheet.DARK_ROW_Y + 40)), (15, 15, 15))

    def test_one_image_ok(self):
        self.assertEqual(sheet.make_sheet(self.paths[:1]).size, sheet.SHEET_SIZE)

    def test_five_images_rejected(self):
        with self.assertRaisesRegex(ValueError, "من 1 لـ 4"):
            sheet.make_sheet(self.paths)

    def test_cli_writes_file(self):
        out = self.dir / "grid.jpg"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sheet.main([str(p) for p in self.paths[:4]] + ["-o", str(out)])
        self.assertEqual(code, 0)
        self.assertTrue(out.is_file())

    def test_cli_missing_file(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sheet.main([str(self.dir / "nope.jpg"), "-o", str(self.dir / "x.jpg")])
        self.assertEqual(code, 1)
        self.assertIn("✗ خطأ", buf.getvalue())

    def test_cli_corrupt_file_gives_error(self):
        corrupt = self.dir / "corrupt.png"
        corrupt.write_bytes(b"<xml>error</xml>")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sheet.main([str(corrupt), "-o", str(self.dir / "x.jpg")])
        self.assertEqual(code, 1)
        self.assertIn("✗ خطأ", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
