import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import make  # noqa: E402
import render  # noqa: E402
import upscale  # noqa: E402


def picked_card(label, text=None, zone=None, font=None, font_latin=None):
    card = {"id": f"W{label}", "label": label, "text": text, "score": 80.0,
            "layout": {"face": "right", "hero": "foreground", "text_zone": zone}}
    if font:
        card["font"] = font
    if font_latin:
        card["font_latin"] = font_latin
    return card


def fast_upscale(img, *a, **k):
    return img.convert("RGB").resize(upscale.TARGET), "classic"


class AutoSpecTest(unittest.TestCase):
    def test_no_text_spec(self):
        spec = make.auto_spec(picked_card("A"))
        self.assertEqual(spec["size"], "youtube4k")
        self.assertEqual(spec["background"]["image"], "scene-A-4k.png")
        self.assertEqual(spec["background"]["sharpen"], 0.5)
        self.assertEqual(spec["layers"], [])

    def test_text_spec_uses_card_font_and_zone(self):
        spec = make.auto_spec(picked_card("B", "السلاح\nالجديد!", "top_right", "Kufam"))
        layer = spec["layers"][0]
        self.assertEqual(layer["text"], "السلاح\nالجديد!")
        self.assertEqual(layer["font"], "Kufam")
        self.assertEqual(layer["line_spacing"], 0.62)
        self.assertNotIn("font_latin", layer)

    def test_latin_line_gets_wider_spacing(self):
        layer = make.auto_spec(picked_card("C", "خسارة\n300 BILLION", "top_left", "Tajawal", "Bebas"))["layers"][0]
        self.assertEqual(layer["font_latin"], "Bebas")
        self.assertEqual(layer["line_spacing"], 0.85)

    def test_auto_text_fits_its_zone_without_warnings(self):
        texts = [("نهاية العالم؟", "Baloo"), ("السلاح\nالجديد!", "Kufam"), ("خسارة\n300 BILLION", "Tajawal")]
        for zone, (x0, y0, x1, y1) in make.ZONE_BOX.items():
            for text, font in texts:
                with self.subTest(zone=zone, text=text):
                    layer = make.auto_spec(picked_card("A", text, zone, font, "Bebas"))["layers"][0]
                    from PIL import Image as _I
                    bbox, _ = render._text_layer(_I.new("RGBA", (1280, 720)), layer)
                    self.assertGreaterEqual(bbox[0] / 1280, x0 - 0.01)
                    self.assertLessEqual(bbox[2] / 1280, x1 + 0.01)
                    self.assertGreaterEqual(bbox[1] / 720, y0 - 0.01)
                    self.assertLessEqual(bbox[3] / 720, y1 + 0.01)
                    _, warnings = render.render({"size": "youtube", "background": {"color": "#202020"},
                                                 "layers": [layer]}, ".")
                    self.assertEqual(warnings, [])


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        cards = [picked_card("A"), picked_card("B", "السلاح\nالجديد!", "top_left", "Kufam"), picked_card("C")]
        (self.dir / "picked.json").write_text(json.dumps({"notes": [], "picked": cards}, ensure_ascii=False),
                                              encoding="utf-8")

    def scenes(self, labels="ABC"):
        for i, label in enumerate(labels):
            Image.new("RGB", (1376, 768), (40 + 60 * i, 30, 90)).save(self.dir / f"scene-{label}.png")

    def run_make(self, *extra):
        buf = io.StringIO()
        with mock.patch.object(upscale, "upscale", side_effect=fast_upscale), contextlib.redirect_stdout(buf):
            code = make.main([str(self.dir), "--no-check", *extra])
        return code, buf.getvalue()

    def test_builds_thumbs_mobile_and_compare(self):
        self.scenes()
        code, out = self.run_make()
        self.assertEqual(code, 0, out)
        for label in "ABC":
            with Image.open(self.dir / f"thumb-{label}.jpg") as im:
                self.assertEqual(im.size, (3840, 2160))
            with Image.open(self.dir / f"thumb-{label}-mobile.jpg") as im:
                self.assertEqual(im.size, (1280, 720))
            self.assertTrue((self.dir / f"spec-{label}.json").exists())
        self.assertTrue((self.dir / "compare.jpg").exists())
        self.assertLessEqual(len(out.strip().splitlines()), 6)

    def test_existing_spec_is_kept(self):
        self.scenes()
        custom = {"size": "youtube4k", "background": {"image": "scene-A-4k.png"}, "layers": [], "mine": True}
        (self.dir / "spec-A.json").write_text(json.dumps(custom), encoding="utf-8")
        code, out = self.run_make()
        self.assertEqual(code, 0, out)
        self.assertTrue(json.loads((self.dir / "spec-A.json").read_text(encoding="utf-8"))["mine"])

    def test_missing_scene_reported_others_built(self):
        self.scenes("AC")
        code, out = self.run_make()
        self.assertEqual(code, 0, out)
        self.assertIn("⚠️", out)
        self.assertIn("B", out)
        self.assertTrue((self.dir / "thumb-A.jpg").exists())
        self.assertFalse((self.dir / "thumb-B.jpg").exists())

    def test_spec_from_another_card_is_replaced(self):
        self.scenes()
        old = make.auto_spec(picked_card("A", "السلاح\nالجديد!", "top_left", "Kufam"))
        old["source"] = "W9"
        (self.dir / "spec-A.json").write_text(json.dumps(old, ensure_ascii=False), encoding="utf-8")
        code, out = self.run_make()
        self.assertEqual(code, 0, out)
        spec = json.loads((self.dir / "spec-A.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["source"], "WA")
        self.assertEqual(spec["layers"], [])
        self.assertIn("⚠️", out)

    def test_scene_named_by_card_id_preferred(self):
        Image.new("RGB", (1376, 768), (200, 0, 0)).save(self.dir / "scene-WB.png")
        code, out = self.run_make()
        self.assertEqual(code, 0, out)
        self.assertTrue((self.dir / "thumb-B.jpg").exists())
        spec = json.loads((self.dir / "spec-B.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["background"]["image"], "scene-WB-4k.png")

    def test_broken_4k_is_redone(self):
        self.scenes("A")
        (self.dir / "scene-A-4k.png").write_bytes(b"half")
        code, out = self.run_make()
        self.assertEqual(code, 0, out)
        with Image.open(self.dir / "scene-A-4k.png") as im:
            self.assertEqual(im.size, (3840, 2160))

    def test_fallback_upscale_is_reported(self):
        self.scenes("A")
        buf = io.StringIO()
        with mock.patch.object(upscale, "upscale", side_effect=lambda img, *a, **k: (fast_upscale(img)[0], "fallback")), \
                contextlib.redirect_stdout(buf):
            code = make.main([str(self.dir), "--no-check"])
        self.assertEqual(code, 0)
        self.assertIn("التكبير الذكي", buf.getvalue())

    def test_check_without_numpy_does_not_crash(self):
        self.scenes()
        buf = io.StringIO()
        with mock.patch.dict(sys.modules, {"numpy": None}), \
                mock.patch.object(upscale, "upscale", side_effect=fast_upscale), contextlib.redirect_stdout(buf):
            code = make.main([str(self.dir)])
        self.assertEqual(code, 0, buf.getvalue())
        self.assertTrue((self.dir / "compare.jpg").exists())

    def test_bad_labels_in_picked(self):
        for labels in (["../x"], list("ABCDE")):
            with self.subTest(labels=labels):
                cards = [picked_card(l) for l in labels]
                (self.dir / "picked.json").write_text(json.dumps({"picked": cards}), encoding="utf-8")
                self.scenes("ABCDE")
                code, out = self.run_make()
                self.assertEqual(code, 1)
                self.assertIn("✗ خطأ", out)

    def test_no_scenes_is_error(self):
        code, out = self.run_make()
        self.assertEqual(code, 1)
        self.assertIn("✗ خطأ", out)

    def test_missing_picked_json(self):
        (self.dir / "picked.json").unlink()
        code, out = self.run_make()
        self.assertEqual(code, 1)
        self.assertIn("✗ خطأ", out)
        self.assertNotIn("Traceback", out)


if __name__ == "__main__":
    unittest.main()
