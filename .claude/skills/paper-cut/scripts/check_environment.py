#!/usr/bin/env python3
"""Read-only environment check for Paper Cut."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def version(executable: str | None, args: list[str]) -> dict[str, object]:
    path = executable or shutil.which(args[0])
    if not path:
        return {"available": False, "path": None, "version": None}
    try:
        result = subprocess.run([path, *args[1:]], capture_output=True, text=True, timeout=10, check=False)
        output = (result.stdout or result.stderr).strip().splitlines()
        return {"available": result.returncode == 0, "path": path, "version": output[0] if output else None}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": False, "path": path, "version": str(exc)}


def find_local(root: Path, name: str) -> str | None:
    candidates = [
        root / ".tools" / "ffmpeg-binaries" / "ffmpeg_binaries" / "binaries" / "bin" / f"{name}.exe",
        root / ".tools" / "ffmpeg-binaries" / "bin" / f"{name}.exe",
        root / "hyperframes" / ".tools" / "ffmpeg-binaries" / "ffmpeg_binaries" / "binaries" / "bin" / f"{name}.exe",
        root / "hyperframes" / ".tools" / "ffmpeg-binaries" / "bin" / f"{name}.exe",
    ]
    node_candidates = {
        "ffmpeg": [
            root / "node_modules" / "ffmpeg-static" / "ffmpeg.exe",
            root / "hyperframes" / "node_modules" / "ffmpeg-static" / "ffmpeg.exe",
        ],
        "ffprobe": [
            root / "node_modules" / "ffprobe-static" / "bin" / "win32" / "x64" / "ffprobe.exe",
            root / "hyperframes" / "node_modules" / "ffprobe-static" / "bin" / "win32" / "x64" / "ffprobe.exe",
        ],
    }
    candidates.extend(node_candidates[name])
    env_name = "HYPERFRAMES_FFMPEG_PATH" if name == "ffmpeg" else "HYPERFRAMES_FFPROBE_PATH"
    if os.environ.get(env_name):
        candidates.insert(0, Path(os.environ[env_name]))
    for path in candidates:
        try:
            if path.is_file():
                return str(path)
        except OSError:
            continue
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.project_dir.resolve()
    report = {
        "python": version(sys.executable, ["python", "--version"]),
        "node": version(None, ["node", "--version"]),
        "npm": version(None, ["npm", "--version"]),
        "npx": version(None, ["npx", "--version"]),
        "ffmpeg": version(find_local(root, "ffmpeg"), ["ffmpeg", "-version"]),
        "ffprobe": version(find_local(root, "ffprobe"), ["ffprobe", "-version"]),
    }
    node_version = str(report["node"].get("version") or "")
    try:
        node_major = int(node_version.lstrip("v").split(".", 1)[0])
    except ValueError:
        node_major = 0
    report["paperCutReady"] = all(report[key]["available"] for key in report) and node_major >= 22
    report["notes"] = []
    if report["node"]["available"] and node_major < 22:
        report["notes"].append("HyperFrames requires Node.js 22 or newer.")
    if not report["paperCutReady"]:
        report["notes"].append("This script is read-only and does not install missing software.")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["paperCutReady"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
