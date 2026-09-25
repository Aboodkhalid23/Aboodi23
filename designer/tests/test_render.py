import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

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
        x0, y0, x1, y1 = render._text_layer(canvas, self.text("وين", x=0.5, y=0.5, size=0.1))
        self.assertTrue(560 < x0 < 640 < x1 < 720, (x0, x1))
        self.assertTrue(290 < y0 < 360 < y1 < 430, (y0, y1))

    def test_paper_box_is_light(self):
        layer = self.text("مش لوحدنا", x=0.5, y=0.5, size=0.12, color="#111111",
                          box={"style": "paper", "pad": 0.4})
        img, _ = self.render({"background": {"color": "#000000"}, "layers": [layer]})
        bright = sum(1 for v in img.convert("L").getdata() if v > 150)
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


if __name__ == "__main__":
    unittest.main()
