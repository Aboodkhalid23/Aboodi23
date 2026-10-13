"""كاشف الوجوه: موديل YuNet من OpenCV (مجاني، Apache-2.0)، يلگى الوجوه بالصورة."""
from PIL import Image

import models

MAX_DETECT_WIDTH = 1280


class FaceUnavailable(Exception):
    """فحص الوجه ما يگدر يشتغل (مكتبة ناقصة أو الموديل ما نزل). الرسالة بالعربي."""


def detect_faces(img: Image.Image) -> list[tuple[int, int, int, int]]:
    """يرجع صناديق الوجوه (x, y, w, h) بالبكسل على الصورة الأصلية، من الأطول للأقصر."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        raise FaceUnavailable("فحص الوجه يحتاج OpenCV: pip install -r designer/requirements-quality.txt")
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)  # يسكّت تحذيرات OpenCV الداخلية
    try:
        path = models.ensure_model("face")
    except models.ModelError as e:
        raise FaceUnavailable(str(e))
    rgb = img.convert("RGB")
    scale = min(1.0, MAX_DETECT_WIDTH / rgb.width)
    if scale < 1.0:
        rgb = rgb.resize((round(rgb.width * scale), round(rgb.height * scale)), Image.LANCZOS)
    w, h = rgb.size
    detector = cv2.FaceDetectorYN.create(str(path), "", (w, h), 0.7, 0.3, 5000)
    _, faces = detector.detect(np.ascontiguousarray(np.asarray(rgb)[:, :, ::-1]))
    if faces is None:
        return []
    boxes = [tuple(round(float(v) / scale) for v in f[:4]) for f in faces]
    return sorted(boxes, key=lambda b: b[3], reverse=True)
