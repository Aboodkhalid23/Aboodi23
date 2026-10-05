import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import face  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HAS_CV = importlib.util.find_spec("cv2") is not None and importlib.util.find_spec("numpy") is not None
FACE = ROOT / "designer/faces/abood-face-crop.jpg"  # محلي بس، ما ينرفع للريبو


class FaceTest(unittest.TestCase):
    def test_missing_cv2_raises_arabic(self):
        with mock.patch.dict(sys.modules, {"cv2": None}):
            with self.assertRaisesRegex(face.FaceUnavailable, "OpenCV"):
                face.detect_faces(Image.new("RGB", (64, 36)))

    def test_model_error_becomes_face_unavailable(self):
        with mock.patch.object(face.models, "ensure_model", side_effect=face.models.ModelError("ما گدرت أنزّل")):
            with self.assertRaisesRegex(face.FaceUnavailable, "ما گدرت أنزّل"):
                face.detect_faces(Image.new("RGB", (64, 36)))

    @unittest.skipUnless(HAS_CV, "OpenCV ماكو")
    def test_blank_image_has_no_faces(self):
        self.assertEqual(face.detect_faces(Image.new("RGB", (640, 360), (120, 120, 120))), [])

    @unittest.skipUnless(HAS_CV and FACE.exists(), "صورة الوجه المحلية ماكو")
    def test_owner_face_found_and_big(self):
        img = Image.open(FACE)
        boxes = face.detect_faces(img)
        self.assertGreaterEqual(len(boxes), 1)
        self.assertGreater(boxes[0][3], 0.2 * img.height)

    @unittest.skipUnless(HAS_CV and FACE.exists(), "صورة الوجه المحلية ماكو")
    def test_boxes_are_in_original_pixels_for_big_images(self):
        small = Image.open(FACE).convert("RGB")
        big = small.resize((small.width * 3, small.height * 3))
        b_small = face.detect_faces(small)[0]
        b_big = face.detect_faces(big)[0]
        self.assertAlmostEqual(b_big[3] / b_small[3], 3, delta=0.3)


if __name__ == "__main__":
    unittest.main()
