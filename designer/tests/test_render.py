import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render  # noqa: E402
from render import SpecError  # noqa: E402

GRADIENT = {"gradient": ["#101018", "#303040"]}


class RenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        Image.new("RGB", (800, 800), (200, 30, 30)).save(cls.dir / "square.png")
        face = Image.new("RGBA", (300, 400))
        ImageDraw.Draw(face).ellipse((50, 20, 250, 380), fill=(220, 170, 110, 255))
        face.save(cls.dir / "face.png")
        Image.new("RGB", (300, 400), (220, 170, 110)).save(cls.dir / "face_opaque.jpg")
        Image.frombytes("RGB", (1280, 720), os.urandom(1280 * 720 * 3)).save(cls.dir / "noise.png")
        (cls.dir / "corrupt.png").write_bytes(b"<xml>error</xml>")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def render(self, spec):
        return render.render(spec, self.dir)

    def text(self, text, **kw):
        layer = {"type": "text", "text": text, "x": 0.5, "y": 0.4, "size": 0.12}
        layer.update(kw)
        return layer

    # المقاسات
    def test_youtube_size(self):
        img, _ = self.render({"size": "youtube", "background": GRADIENT})
        self.assertEqual(img.size, (1280, 720))

    def test_reels_size(self):
        img, _ = self.render({"size": "reels", "background": GRADIENT})
        self.assertEqual(img.size, (1080, 1920))

    def test_custom_size(self):
        img, _ = self.render({"size": [1080, 1350], "background": {"color": "#000000"}})
        self.assertEqual(img.size, (1080, 1350))

    def test_square_background_fills_without_stretching(self):
        img, _ = self.render({"size": "youtube", "background": {"image": "square.png"}})
        self.assertEqual(img.size, (1280, 720))
        self.assertEqual(img.getpixel((5, 5))[:3], (200, 30, 30))

    # أخطاء واضحة
    def test_unknown_size(self):
        with self.assertRaisesRegex(SpecError, "مقاس مو معروف"):
            self.render({"size": "tiktok", "background": GRADIENT})

    def test_missing_background(self):
        with self.assertRaisesRegex(SpecError, "ناقصه background"):
            self.render({"size": "youtube"})

    def test_missing_image_names_the_file(self):
        with self.assertRaisesRegex(SpecError, "ghost.png"):
            self.render({"background": GRADIENT, "layers": [{"type": "image", "src": "ghost.png"}]})

    def test_unknown_font(self):
        with self.assertRaisesRegex(SpecError, "خط مو معروف"):
            self.render({"background": GRADIENT, "layers": [self.text("هلا", font="Arial")]})

    def test_unknown_layer_type(self):
        with self.assertRaisesRegex(SpecError, "نوع مو معروف"):
            self.render({"background": GRADIENT, "layers": [{"type": "video"}]})

    def test_empty_text(self):
        with self.assertRaisesRegex(SpecError, "فارغة"):
            self.render({"background": GRADIENT, "layers": [self.text("  ")]})

    def test_bad_color(self):
        with self.assertRaisesRegex(SpecError, "لون غلط"):
            self.render({"background": {"color": "red"}})

    # التحذيرات
    def test_centered_text_no_warnings(self):
        _, warnings = self.render({"background": GRADIENT, "layers": [self.text("فلوس الناس")]})
        self.assertEqual(warnings, [])

    def test_text_over_youtube_timestamp_warns(self):
        spec = {"background": GRADIENT, "layers": [self.text("وين؟", x=0.92, y=0.92, size=0.1)]}
        _, warnings = self.render(spec)
        self.assertTrue(any("زاوية مدة الفيديو" in w for w in warnings), warnings)

    def test_reels_text_in_caption_zone_warns(self):
        spec = {"size": "reels", "background": GRADIENT, "layers": [self.text("وين؟", x=0.4, y=0.9, size=0.05)]}
        _, warnings = self.render(spec)
        self.assertTrue(any("منطقة الكابشن" in w for w in warnings), warnings)

    def test_too_many_words_warns(self):
        spec = {"background": GRADIENT, "layers": [self.text("هذا نص طويل\nهواية بالغلاف", size=0.08)]}
        _, warnings = self.render(spec)
        self.assertTrue(any("5 كلمات" in w for w in warnings), warnings)

    def test_text_overflowing_canvas_warns(self):
        spec = {"background": GRADIENT, "layers": [self.text("الإمبراطورية انهارت بالكامل", size=0.3)]}
        _, warnings = self.render(spec)
        self.assertTrue(any("برا حدود الصورة" in w for w in warnings), warnings)

    def test_opaque_face_with_outline_warns(self):
        layer = {"type": "image", "src": "face_opaque.jpg", "x": 0.7, "h": 0.8, "outline": {"color": "#FFFFFF"}}
        _, warnings = self.render({"background": GRADIENT, "layers": [layer]})
        self.assertTrue(any("ما بيها شفافية" in w for w in warnings), warnings)

    def test_transparent_face_with_outline_no_warning(self):
        layer = {"type": "image", "src": "face.png", "x": 0.7, "h": 0.8, "outline": {"color": "#FFFFFF"}}
        img, warnings = self.render({"background": GRADIENT, "layers": [layer]})
        self.assertEqual(warnings, [])
        self.assertEqual(img.getpixel((int(0.7 * 1280), 720 - 288))[:3], (220, 170, 110))  # نص الوجه

    # الكلمة المميزة
    def test_highlight_ignores_punctuation(self):
        layer = self.text("وين راحت؟", highlight={"word": "راحت", "color": "#FFD400"})
        _, _, placed = render._layout_text(layer, 1280, 720)
        fills = [p[4] for p in placed]
        self.assertEqual(sorted(fills), ["#FFD400", "#FFFFFF"])

    # ستايل أغلفة صاحب القناة: تدرج، ميلان، ورق ممزق
    def test_line_colors_white_then_gradient(self):
        layer = self.text("نهاية\nالكون!", size=0.2, line_colors=["#FFFFFF", ["#FFD000", "#FF6A00"]])
        img, warnings = self.render({"background": {"color": "#000000"}, "layers": [layer]})
        self.assertEqual(warnings, [])
        _, _, placed = render._layout_text(layer, 1280, 720)
        self.assertEqual([p[4] for p in placed], ["#FFFFFF", ["#FFD000", "#FF6A00"]])

    def test_gradient_fill_top_differs_from_bottom(self):
        fill = render._fill_image(["#FFD000", "#FF6A00"], 100, 300, (1280, 720))
        self.assertEqual(fill.getpixel((5, 50))[:3], (255, 208, 0))
        self.assertEqual(fill.getpixel((5, 400))[:3], (255, 106, 0))
        mid = fill.getpixel((5, 200))[1]
        self.assertTrue(106 < mid < 208, mid)

    def test_bad_gradient_fill(self):
        with self.assertRaisesRegex(SpecError, "لون الكتابة"):
            self.render({"background": GRADIENT, "layers": [self.text("هلا", color=["#FFFFFF"])]})

    def test_rotated_text_still_warns_in_unsafe_zone(self):
        spec = {"background": GRADIENT, "layers": [self.text("وين؟", x=0.9, y=0.9, size=0.1, rotate=6)]}
        _, warnings = self.render(spec)
        self.assertTrue(any("زاوية مدة الفيديو" in w for w in warnings), warnings)

    def test_brand_headline_template_has_no_false_warning(self):
        # قالب الكتابة الأساسي بـ studio/brand.md: الحبر بعيد عن الزاوية، فلازم ماكو تحذير
        layer = {"type": "text", "text": "نهاية\nالكون!", "font": "Baloo", "x": 0.27, "y": 0.47, "size": 0.2,
                 "line_spacing": 0.62, "line_colors": ["#FFFFFF", ["#FFC400", "#FF6A00"]],
                 "stroke": {"color": "#0B0B0F", "width": 0.1}, "shadow": True, "rotate": 5}
        _, warnings = self.render({"background": GRADIENT, "layers": [layer]})
        self.assertEqual(warnings, [])

    def test_text_bbox_is_real_ink(self):
        canvas = Image.new("RGBA", (1280, 720), (0, 0, 0, 255))
        bbox, _ = render._text_layer(canvas, self.text("وين", x=0.5, y=0.5, size=0.1))
        x0, y0, x1, y1 = bbox
        self.assertTrue(560 < x0 < 640 < x1 < 720, (x0, x1))
        self.assertTrue(290 < y0 < 360 < y1 < 430, (y0, y1))

    def test_paper_box_is_light(self):
        layer = self.text("مش لوحدنا", x=0.5, y=0.5, size=0.12, color="#111111",
                          box={"style": "paper", "pad": 0.4})
        img, _ = self.render({"background": {"color": "#000000"}, "layers": [layer]})
        bright = sum(img.convert("L").histogram()[151:])
        self.assertGreater(bright, 40000)  # الورق الفاتح واضح خلف الكتابة الداكنة

    def test_background_finish_options(self):
        spec = {"background": {"image": "square.png", "contrast": 1.2, "saturation": 1.3, "sharpen": 1}}
        img, _ = self.render(spec)
        self.assertEqual(img.size, (1280, 720))

    # الأشكال والحفظ والفحص
    def test_shapes_render(self):
        layers = [
            {"type": "shape", "shape": "arrow", "from": [0.2, 0.8], "to": [0.4, 0.5]},
            {"type": "shape", "shape": "circle", "center": [0.7, 0.5], "r": 0.2},
            {"type": "shape", "shape": "rect", "box": [0.1, 0.1, 0.3, 0.3], "fill": True, "color": "#FFD400"},
        ]
        img, _ = self.render({"background": GRADIENT, "layers": layers})
        self.assertEqual(img.getpixel((int(0.2 * 1280), int(0.2 * 720)))[:3], (255, 212, 0))

    def test_unknown_shape(self):
        with self.assertRaisesRegex(SpecError, "شكل مو معروف"):
            self.render({"background": GRADIENT, "layers": [{"type": "shape", "shape": "star"}]})

    def test_guides_paint_unsafe_zone_red(self):
        img, _ = self.render({"background": {"color": "#000000"}})
        guided = render.draw_guides(img, "youtube")
        r, g, b, _ = guided.getpixel((1270, 710))
        self.assertGreater(r, 60)
        self.assertLess(g, 20)

    def run_cli(self, spec: dict, out_name: str) -> tuple[int, str]:
        spec_path = self.dir / f"{out_name}.json"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = render.main([str(spec_path), "-o", str(self.dir / out_name)])
        return code, buf.getvalue()

    def test_cli_saves_jpg_under_2mb(self):
        code, out = self.run_cli({"background": {"image": "noise.png"}}, "ok.jpg")
        self.assertEqual(code, 0)
        self.assertIn("انحفظ", out)
        self.assertLess((self.dir / "ok.jpg").stat().st_size, render.YOUTUBE_MAX_BYTES)

    def test_cli_warns_when_png_too_big_for_youtube(self):
        code, out = self.run_cli({"background": {"image": "noise.png"}}, "big.png")
        self.assertEqual(code, 0)
        self.assertIn("أكبر من 2MB", out)

    def test_cli_bad_spec_returns_error(self):
        code, out = self.run_cli({"size": "tiktok", "background": GRADIENT}, "bad.jpg")
        self.assertEqual(code, 1)
        self.assertIn("✗ خطأ", out)

    def test_cli_broken_json(self):
        bad = self.dir / "broken.json"
        bad.write_text("{ not json", encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = render.main([str(bad), "-o", str(self.dir / "x.jpg")])
        self.assertEqual(code, 1)
        self.assertIn("غلط بالصيغة", buf.getvalue())

    # Fix round 1 tests for error handling
    def test_image_layer_without_src_raises_spec_error(self):
        with self.assertRaisesRegex(SpecError, "ناقصها src"):
            self.render({"background": GRADIENT, "layers": [{"type": "image", "x": 0.5}]})

    def test_arrow_shape_without_from_raises_spec_error(self):
        with self.assertRaisesRegex(SpecError, "ناقصها from"):
            self.render({"background": GRADIENT, "layers": [{"type": "shape", "shape": "arrow", "to": [0.5, 0.5]}]})

    def test_bad_gradient_raises_spec_error(self):
        with self.assertRaisesRegex(SpecError, "الخلفية"):
            self.render({"background": {"gradient": ["#000000"]}, "layers": []})

    def test_rotated_text_not_warning_on_empty_corner(self):
        # Finding 2 reproduction: rotated text with empty bbox corner in unsafe zone should not warn if no ink pixels there
        spec = {
            "background": GRADIENT,
            "layers": [
                {
                    "type": "text",
                    "text": "لا تقرب\nمنه!",
                    "font": "Baloo",
                    "x": 0.29,
                    "y": 0.62,
                    "size": 0.17,
                    "line_spacing": 0.62,
                    "line_colors": ["#FFFFFF", ["#FFC400", "#FF6A00"]],
                    "stroke": {"color": "#0B0B0F", "width": 0.1},
                    "shadow": True,
                    "rotate": 5
                }
            ]
        }
        _, warnings = self.render(spec)
        self.assertEqual(warnings, [])

    # Fix round 2 tests
    def test_circle_without_center_raises_spec_error(self):
        with self.assertRaisesRegex(SpecError, "ناقصها center"):
            self.render({"background": GRADIENT, "layers": [{"type": "shape", "shape": "circle", "r": 0.2}]})

    def test_rect_without_box_raises_spec_error(self):
        with self.assertRaisesRegex(SpecError, "ناقصها box"):
            self.render({"background": GRADIENT, "layers": [{"type": "shape", "shape": "rect", "fill": True}]})

    def test_empty_text_not_double_wrapped(self):
        # FINDING A: SpecError should pass through unchanged, not double-wrapped
        try:
            self.render({"background": GRADIENT, "layers": [self.text("  ")]})
            self.fail("Expected SpecError")
        except SpecError as e:
            msg = str(e)
            self.assertNotIn("قيمة غلط", msg)
            self.assertIn("الكتابة فارغة", msg)

    def test_unknown_shape_not_double_wrapped(self):
        # FINDING A: SpecError from _shape_layer should not be wrapped as "قيمة غلط"
        try:
            self.render({"background": GRADIENT, "layers": [{"type": "shape", "shape": "star"}]})
            self.fail("Expected SpecError")
        except SpecError as e:
            msg = str(e)
            self.assertTrue(msg.startswith("شكل مو معروف"))

    def test_bad_background_color_not_double_wrapped(self):
        # FINDING A: SpecError from hex_rgba should not be wrapped as "قيمة غلط"
        try:
            self.render({"background": {"color": "red"}, "layers": []})
            self.fail("Expected SpecError")
        except SpecError as e:
            msg = str(e)
            self.assertTrue(msg.startswith("لون غلط"))

    def test_text_overlapping_two_zones_warns_both(self):
        # FINDING B: Text overlapping two zones should warn for both (no break)
        spec = {
            "size": "reels",
            "background": GRADIENT,
            "layers": [self.text("وين؟", x=0.93, y=0.9, size=0.05)]
        }
        _, warnings = self.render(spec)
        self.assertTrue(any("منطقة الكابشن" in w for w in warnings), warnings)
        self.assertTrue(any("أزرار اليمين" in w for w in warnings), warnings)

    # Final-fix wave item 1: corrupt/non-image files
    def test_corrupt_background_image_gives_arabic_error(self):
        with self.assertRaisesRegex(SpecError, "مو صورة"):
            self.render({"background": {"image": "corrupt.png"}})

    def test_corrupt_image_layer_gives_arabic_error(self):
        layer = {"type": "image", "src": "corrupt.png", "x": 0.5}
        with self.assertRaisesRegex(SpecError, "مو صورة"):
            self.render({"background": GRADIENT, "layers": [layer]})

    def test_cli_corrupt_background_exits_with_error(self):
        code, out = self.run_cli({"background": {"image": "corrupt.png"}}, "corrupt-out.jpg")
        self.assertEqual(code, 1)
        self.assertIn("✗ خطأ", out)

    # Final-fix wave item 3: malformed spec shapes
    def test_top_level_array_spec_gives_arabic_error(self):
        with self.assertRaisesRegex(SpecError, "كائن JSON"):
            render.render(["not", "a", "dict"], self.dir)

    def test_layers_not_a_list_gives_arabic_error(self):
        with self.assertRaisesRegex(SpecError, "layers لازم تكون قائمة"):
            self.render({"background": GRADIENT, "layers": {"type": "text"}})

    def test_bool_stroke_gives_arabic_error(self):
        with self.assertRaisesRegex(SpecError, "قيمة غلط"):
            self.render({"background": GRADIENT, "layers": [self.text("هلا", stroke=True)]})

    def test_non_string_text_gives_arabic_error_naming_layer(self):
        with self.assertRaisesRegex(SpecError, "الطبقة 1"):
            self.render({"background": GRADIENT, "layers": [{"type": "text", "text": 2008, "x": 0.5, "y": 0.5}]})

    # Final-fix wave item 4: bad output file name
    def test_cli_bad_output_extension(self):
        code, out = self.run_cli({"background": GRADIENT}, "out")
        self.assertEqual(code, 1)
        self.assertIn("لازم ينتهي بـ .jpg أو .png", out)

    def test_cli_save_oserror_gives_arabic_error(self):
        spec_path = self.dir / "save-error.json"
        spec_path.write_text(json.dumps({"background": GRADIENT}, ensure_ascii=False), encoding="utf-8")
        buf = io.StringIO()
        with mock.patch.object(Image.Image, "save", side_effect=OSError("disk full")), \
                contextlib.redirect_stdout(buf):
            code = render.main([str(spec_path), "-o", str(self.dir / "save-error.jpg")])
        self.assertEqual(code, 1)
        self.assertIn("✗ خطأ", buf.getvalue())

    # Final-fix wave item 5: resolve() order
    def test_resolve_prefers_base_dir_over_cwd(self):
        with tempfile.TemporaryDirectory() as cwd_dir, tempfile.TemporaryDirectory() as base_dir:
            cwd, base = Path(cwd_dir), Path(base_dir)
            Image.new("RGB", (10, 10), (1, 2, 3)).save(cwd / "img.png")
            Image.new("RGB", (10, 10), (9, 9, 9)).save(base / "img.png")
            old_cwd = os.getcwd()
            os.chdir(cwd)
            try:
                found = render.resolve("img.png", base)
            finally:
                os.chdir(old_cwd)
            self.assertEqual(found, base / "img.png")


if __name__ == "__main__":
    unittest.main()
