#!/usr/bin/env python3
"""Decode a video and create checkpoint frames plus a contact sheet."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    video = args.video.resolve()
    output = args.output_dir.resolve()
    if not video.is_file():
        parser.error(f"video not found: {video}")
    output.mkdir(parents=True, exist_ok=True)

    probe = run([
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate",
        "-of",
        "json",
        str(video),
    ])
    metadata = json.loads(probe.stdout)
    duration = float(metadata.get("format", {}).get("duration", 0))
    if not math.isfinite(duration) or duration <= 0:
        raise SystemExit("video has no positive duration")

    run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"])

    checkpoints = {
        "entry": min(0.12, duration * 0.04),
        "build": duration * 0.34,
        "settled": duration * 0.72,
        "exit": max(0.0, duration - 0.12),
    }
    frame_paths: dict[str, str] = {}
    for name, second in checkpoints.items():
        frame_path = output / f"{name}.png"
        run([
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-ss",
            f"{second:.4f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            str(frame_path),
        ])
        frame_paths[name] = str(frame_path)

    contact_sheet = output / "contact-sheet.jpg"
    sample_rate = 8.0 / duration
    run([
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        str(video),
        "-vf",
        f"fps={sample_rate:.8f},scale=480:-1,tile=4x2:padding=8:margin=8",
        "-frames:v",
        "1",
        str(contact_sheet),
    ])

    evidence = {
        "video": str(video),
        "duration": duration,
        "metadata": metadata,
        "checkpoints": checkpoints,
        "frames": frame_paths,
        "contact_sheet": str(contact_sheet),
        "decode": "pass",
    }
    evidence_path = output / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Visual evidence: {evidence_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
