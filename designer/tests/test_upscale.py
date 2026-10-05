import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageEnhance, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import upscale  # noqa: E402

HAS_NP = importlib.util.find_spec("numpy") is not None
HAS_ORT = HAS_NP and importlib.util.find_spec("onnxruntime") is not None
if HAS_NP:
    import numpy as np


def nearest4(t):
    return t.repeat(4, 0).repeat(4, 1)


def no_model(*a, **k):
    raise upscale.models.ModelError("ما گدرت أنزّل الموديل")


class UpscaleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    @unittest.skipUnless(HAS_NP, "numpy ماكو")
    def test_tile_apply_has_no_seams(self):
        arr = np.random.default_rng(1).random((300, 500, 3), dtype=np.float32)
        np.testing.assert_allclose(upscale.tile_apply(arr, nearest4, 4), nearest4(arr), atol=1e-6)

    @unittest.skipUnless(HAS_NP, "numpy ماكو")
    def test_tile_apply_hides_bad_tile_edges(self):
        # الموديل الحقيقي يغلط بحواف كل قطعة؛ الدمج لازم يعطي حواف القطع وزن صغير حتى ما تبين خطوط
        def bad_edges(t):
            r = nearest4(t)
            r[:8], r[-8:], r[:, :8], r[:, -8:] = 0, 0, 0, 0
            return r
        arr = np.full((300, 500, 3), 0.5, np.float32)
        out = upscale.tile_apply(arr, bad_edges, 4)
        inner = out[64:-64, 64:-64]  # حواف الصورة نفسها ماكو قطعة ثانية تغطيها
        self.assertLess(float(np.abs(inner - 0.5).max()), 0.05)

    @unittest.skipUnless(HAS_NP, "numpy ماكو")
    def test_tile_apply_small_image(self):
        arr = np.zeros((60, 100, 3), np.float32)
        self.assertEqual(upscale.tile_apply(arr, nearest4, 4).shape, (240, 400, 3))

    def test_fit_16x9_crops_center_without_resizing(self):
        self.assertEqual(upscale.fit_16x9(Image.new("RGB", (1000, 1000))).size, (1000, 562))
        self.assertEqual(upscale.fit_16x9(Image.new("RGB", (2752, 1536))).size, (2730, 1536))

    def test_large_image_uses_classic(self):
        img, method = upscale.upscale(Image.new("RGB", (2752, 1536), (90, 60, 40)))
        self.assertEqual((img.size, method), ((3840, 2160), "classic"))

    def test_small_image_without_model_falls_back(self):
        with mock.patch.object(upscale.models, "ensure_model", side_effect=no_model):
            img, method = upscale.upscale(Image.new("RGB", (1680, 944)))
        self.assertEqual((img.size, method), ((3840, 2160), "fallback"))

    def test_model_runtime_error_of_any_type_falls_back(self):
        Fail = type("Fail", (Exception,), {})  # onnxruntime errors don't inherit RuntimeError

        def broken(tile):
            raise Fail("[ONNXRuntimeError] FAIL")
        with mock.patch.object(upscale, "_onnx_model_fn", return_value=broken):
            img, method = upscale.upscale(Image.new("RGB", (640, 360)))
        self.assertEqual((img.size, method), ((3840, 2160), "fallback"))

    def test_face_mask_survives_detector_crash(self):
        with mock.patch.object(upscale.face, "detect_faces", side_effect=ValueError("cv2.error")):
            self.assertIsNone(upscale.face_mask(Image.new("RGB", (64, 36))))

    @unittest.skipUnless(HAS_NP, "numpy ماكو")
    def test_detail_transfer_keeps_colors(self):
        base = Image.new("RGB", (400, 225), (120, 80, 60))
        up = ImageEnhance.Brightness(Image.effect_noise((400, 225), 40).convert("RGB")).enhance(1.4)
        out = upscale.detail_transfer(base, up, 0.6)

        def low(im):
            return np.asarray(im.filter(ImageFilter.GaussianBlur(8)), float).mean(axis=(0, 1))
        np.testing.assert_allclose(low(out), low(base), atol=1.5)

    @unittest.skipUnless(HAS_NP, "numpy ماكو")
    def test_face_mask_halves_detail(self):
        base = Image.new("RGB", (400, 225), (120, 80, 60))
        up = Image.effect_noise((400, 225), 40).convert("RGB")
        full = Image.new("L", (400, 225), 255)

        def detail(im):
            return (np.asarray(im, float) - np.asarray(base, float)).std()
        ratio = detail(upscale.detail_transfer(base, up, 0.6, full)) / detail(upscale.detail_transfer(base, up, 0.6))
        self.assertAlmostEqual(ratio, 0.5, delta=0.05)

    def test_rgba_and_square_inputs(self):
        img, _ = upscale.upscale(Image.new("RGBA", (3000, 3000), (10, 20, 30, 128)))
        self.assertEqual((img.size, img.mode), ((3840, 2160), "RGB"))

    def test_cli_fallback_prints_warning(self):
        src, out = self.dir / "small.png", self.dir / "big.png"
        Image.new("RGB", (400, 225), (200, 100, 50)).save(src)
        buf = io.StringIO()
        with mock.patch.object(upscale.models, "ensure_model", side_effect=no_model), \
                contextlib.redirect_stdout(buf):
            code = upscale.main([str(src), "-o", str(out)])
        self.assertEqual(code, 0)
        self.assertIn("⚠️", buf.getvalue())
        self.assertIn("بديلة", buf.getvalue())
        with Image.open(out) as im:
            self.assertEqual(im.size, (3840, 2160))

    def test_cli_corrupt_input(self):
        bad = self.dir / "bad.png"
        bad.write_bytes(b"<xml>error</xml>")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = upscale.main([str(bad), "-o", str(self.dir / "out.png")])
        self.assertEqual(code, 1)
        self.assertIn("✗ خطأ", buf.getvalue())

    def test_cli_bad_output_name(self):
        src = self.dir / "a.png"
        Image.new("RGB", (64, 36)).save(src)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = upscale.main([str(src), "-o", str(self.dir / "out")])
        self.assertEqual(code, 1)
        self.assertIn(".jpg أو .png", buf.getvalue())

    @unittest.skipUnless(HAS_ORT, "onnxruntime ماكو")
    def test_real_model_smoke(self):
        try:
            upscale.models.ensure_model("upscaler")
        except upscale.models.ModelError:
            self.skipTest("الموديل ما نزل")
        out = upscale.ai_upscale(Image.new("RGB", (320, 180), (200, 100, 50)))
        self.assertEqual(out.size, (3840, 2160))


if __name__ == "__main__":
    unittest.main()
