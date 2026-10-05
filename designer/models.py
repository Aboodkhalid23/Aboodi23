"""الموديلات المجانية الي يحتاجها المصمم: تنزل مرة وحدة لـ designer/models/ (يتجاهله git)،
والكود يتأكد من بصمتها (sha256) قبل ما يستعملها."""
import hashlib
import http.client
import urllib.request
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent / "models"
MODELS = {
    "upscaler": {
        "file": "realesr-general-x4v3.onnx",
        "url": "https://huggingface.co/CoderViking/realesr-general-x4v3-onnx/resolve/main/realesr-general-x4v3.onnx",
        "sha256": "1940a93ee08283a0a7286183186357b1688fe9fa8ede74604b424586aaddf112",
    },
    "face": {
        "file": "face_detection_yunet_2023mar.onnx",
        "url": "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx",
        "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
    },
}


class ModelError(Exception):
    """خطأ بتنزيل موديل، رسالته بالعربي."""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_model(name: str) -> Path:
    """يرجع مسار الموديل، وينزّله إذا ماكو أو إذا بصمته ما تطابق."""
    if name not in MODELS:
        raise ModelError(f"الموديل {name} مو معروف.")
    info = MODELS[name]
    path = MODELS_DIR / info["file"]
    if path.exists() and _sha256(path) == info["sha256"]:
        return path
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    try:
        with urllib.request.urlopen(info["url"], timeout=120) as r:
            part.write_bytes(r.read())
    except (OSError, http.client.HTTPException) as e:  # HTTPException: تنزيل انقطع بالنص (IncompleteRead)
        part.unlink(missing_ok=True)
        raise ModelError(f"ما گدرت أنزّل الموديل {name} ({e}).")
    if _sha256(part) != info["sha256"]:
        part.unlink(missing_ok=True)
        path.unlink(missing_ok=True)
        raise ModelError(f"الموديل {name} نزل خربان (البصمة ما تطابق). جرّب مرة ثانية.")
    part.replace(path)
    return path
