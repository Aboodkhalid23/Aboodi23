"""`doctor`: checks everything the editor needs and repairs what it can by itself (owner's rule: problems are
found and fixed without him asking). Runs at the start of every session (quick mode, prints only problems);
`--full` also compiles the scenes and runs the fast tests.

Repairs it makes: missing Python packages (pip), Remotion packages (npm ci), the person-matting model."""
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = {"faster_whisper": "faster-whisper", "cv2": "opencv-python-headless", "mediapipe": "mediapipe",
            "onnxruntime": "onnxruntime", "numpy": "numpy", "requests": "requests", "yaml": "PyYAML", "gdown": "gdown"}
SOURCES = {"Openverse (صور وموسيقى وأصوات)": "https://api.openverse.org/v1/images/?q=test&page_size=1",
           "أرشيف الإنترنت (أفلام)": "https://archive.org/advancedsearch.php?q=prelinger&rows=1&output=json",
           "مكتبة الكونگرس": "https://www.loc.gov/photos/?q=test&fo=json&c=1",
           "ناسا": "https://images-api.nasa.gov/search?q=moon&media_type=image",
           "ويكيميديا": "https://commons.wikimedia.org/w/api.php?action=query&format=json"}


def _line(ok: bool | None, text: str) -> tuple[bool | None, str]:
    return ok, ("✅ " if ok else "⚠️ " if ok is None else "❌ ") + text


def check(full: bool = False, fix: bool = True) -> list[tuple[bool | None, str]]:
    out = []
    for tool in ("ffmpeg", "ffprobe", "node", "npx"):
        out.append(_line(shutil.which(tool) is not None, f"أداة {tool}"))
    missing = []
    for mod, pkg in PACKAGES.items():
        try:
            importlib.import_module(mod)
        except Exception:
            missing.append(pkg)
    if missing and fix:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(ROOT / "editor/requirements.txt")],
                       capture_output=True)
        missing = [p for m, p in PACKAGES.items() if importlib.util.find_spec(m) is None]
    out.append(_line(not missing, "مكتبات بايثون" + (f" (ناقص: {', '.join(missing)})" if missing else "")))
    remotion = ROOT / "editor/remotion"
    if not (remotion / "node_modules").is_dir() and fix:
        subprocess.run(["npm", "ci", "--prefix", str(remotion), "--silent"], capture_output=True)
    out.append(_line((remotion / "node_modules").is_dir(), "مكتبات المشاهد (Remotion)"))
    from .graphics import BROWSER
    out.append(_line(Path(BROWSER).exists(), "المتصفح الي يرسم المشاهد"))
    from .cutout import rvm_model
    out.append(_line(rvm_model() is not None, "موديل قص الشخص الدقيق"))
    free = shutil.disk_usage(ROOT).free / 1e9
    out.append(_line(free > 15 if free > 5 else False, f"المساحة الفاضية {free:.0f} گيگا"))
    for name, url in SOURCES.items():
        try:
            ok = requests.get(url, timeout=8, headers={"User-Agent": "Aboodi23-editor/0.1"}).status_code < 500
        except requests.RequestException:
            ok = False
        out.append(_line(ok if ok else None, f"مصدر: {name}"))
    keys = [k for k in ("PEXELS_API_KEY", "PIXABAY_API_KEY") if os.environ.get(k)]
    out.append(_line(True if keys else None, "مفاتيح الصور الحديثة: " + ("موجودة" if keys else "مو موجودة (اختيارية)")))
    if full:
        tsc = subprocess.run(["npx", "tsc", "--noEmit", "-p", "."], cwd=remotion, capture_output=True, text=True)
        out.append(_line(tsc.returncode == 0, "كود المشاهد يتجمع بلا أخطاء" + ("" if tsc.returncode == 0 else f": {tsc.stdout[-300:]}")))
        tests = subprocess.run([sys.executable, "-m", "pytest", "-q", "-m", "not slow", "editor/tests"], cwd=ROOT,
                               capture_output=True, text=True)
        out.append(_line(tests.returncode == 0, "الاختبارات: " + (tests.stdout.strip().splitlines() or ["?"])[-1]))
    return out


def report(full: bool = False, quiet: bool = False) -> int:
    lines = check(full)
    bad = [t for ok, t in lines if ok is False]
    if quiet:
        if bad:
            print("🩺 فحص المونتير: اكو مشاكل لازم تنصلح قبل الشغل:\n" + "\n".join(bad))
        return 1 if bad else 0
    print("\n".join(t for _, t in lines))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(report(full="--full" in sys.argv, quiet="--quiet" in sys.argv))
