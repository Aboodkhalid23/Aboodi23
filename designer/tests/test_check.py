import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HAS_NP = importlib.util.find_spec("numpy") is not None
EVERGRANDE = ROOT / "episodes/2026-09-23-evergrande/design"
EVERGRANDE_THUMBS_EXIST = all((EVERGRANDE / f"thumb-{t}.jpg").exists() for t in "ABCD")
SIZE = (1280, 720)


def no_faces(*a):
    return []


def colorful():
    return Image.merge("HSV", (Image.linear_gradient("L").resize(SIZE), Image.new("L", SIZE, 255),
                               Image.new("L", SIZE, 200))).convert("RGB")


def color_warnings(r):
    return [w for w in r["warnings"] if "غامق" in w or "باهتة" in w]


@unittest.skipUnless(HAS_NP, "numpy ماكو")
class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def analyze(self, img, faces=no_faces):
        with mock.patch.object(check.face, "detect_faces", faces):
            return check.analyze(img)

    def test_black_is_dark(self):
        r = self.analyze(Image.new("RGB", SIZE))
        self.assertTrue(any("غامق" in w for w in r["warnings"]))

    def test_gray_is_dull(self):
        r = self.analyze(Image.new("RGB", SIZE, (128, 128, 128)))
        self.assertTrue(any("باهتة" in w for w in r["warnings"]))

    def test_colorful_has_no_color_warnings(self):
        self.assertEqual(color_warnings(self.analyze(colorful())), [])

    def test_small_face_warns(self):
        with mock.patch.object(check.face, "detect_faces", return_value=[(0, 0, 100, 72)]):
            r = check.analyze(Image.new("RGB", SIZE, (200, 30, 30)))
        self.assertAlmostEqual(r["face_ratio"], 0.1)
        self.assertTrue(any("الوجه صغير" in w for w in r["warnings"]))

    def test_big_face_no_face_warning(self):
        with mock.patch.object(check.face, "detect_faces", return_value=[(500, 100, 300, 360)]):
            r = check.analyze(colorful())
        self.assertAlmostEqual(r["face_ratio"], 0.5)
        self.assertFalse(any("الوجه" in w for w in r["warnings"]))

    def test_no_face_is_note(self):
        r = self.analyze(colorful())
        self.assertIsNone(r["face_ratio"])
        self.assertTrue(any("ماكو وجه" in n for n in r["notes"]))
        self.assertFalse(any("وجه" in w for w in r["warnings"]))

    def test_face_unavailable_is_note(self):
        with mock.patch.object(check.face, "detect_faces", side_effect=check.face.FaceUnavailable("بدون OpenCV")):
            r = check.analyze(colorful())
        self.assertTrue(any("فحص الوجه ما اشتغل" in n and "بدون OpenCV" in n for n in r["notes"]))

    def test_numbers_note_always_present(self):
        r = self.analyze(colorful())
        self.assertTrue(any("الإضاءة" in n and "المراجع" in n for n in r["notes"]))

    def test_calibrate_writes_stats(self):
        refs = self.dir / "refs"
        refs.mkdir()
        for i, c in enumerate([(10, 10, 10), (128, 64, 32), (250, 200, 30)]):
            Image.new("RGB", (320, 180), c).save(refs / f"{i}.jpg")
        stats_file = self.dir / "stats.json"
        with mock.patch.object(check, "STATS_FILE", stats_file):
            stats = check.calibrate(refs)
            self.assertEqual(check.load_stats(), stats)
        self.assertEqual(set(json.loads(stats_file.read_text(encoding="utf-8"))), set(check.DEFAULT_STATS))

    def test_load_stats_defaults_without_file(self):
        with mock.patch.object(check, "STATS_FILE", self.dir / "nope.json"):
            self.assertEqual(check.load_stats(), check.DEFAULT_STATS)

    def test_squint_sheet_rows(self):
        paths = []
        for i in range(2):
            p = self.dir / f"t{i}.jpg"
            colorful().save(p)
            paths.append(p)
        sheet = check.squint_sheet(paths)
        self.assertEqual(sheet.size, (3 * 320 + 4 * 20, 2 * (180 + 20) + 20))

    def test_cli_missing_file(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = check.main([str(self.dir / "nope.jpg"), "-o", str(self.dir / "check.jpg")])
        self.assertEqual(code, 1)
        self.assertIn("✗ خطأ", buf.getvalue())

    def test_cli_reports_and_saves(self):
        p = self.dir / "dark.jpg"
        Image.new("RGB", SIZE).save(p)
        out = self.dir / "check.jpg"
        buf = io.StringIO()
        with mock.patch.object(check.face, "detect_faces", no_faces), contextlib.redirect_stdout(buf):
            code = check.main([str(p), "-o", str(out)])
        self.assertEqual(code, 0)
        self.assertIn("— dark.jpg", buf.getvalue())
        self.assertIn("⚠️", buf.getvalue())
        self.assertTrue(out.exists())

    @unittest.skipUnless(EVERGRANDE_THUMBS_EXIST, "أغلفة إيفرغراند المحلية ماكو")
    def test_evergrande_thumbs_not_flagged(self):
        for t in "ABCD":
            with Image.open(EVERGRANDE / f"thumb-{t}.jpg") as im:
                self.assertEqual(color_warnings(self.analyze(im)), [], t)


if __name__ == "__main__":
    unittest.main()
