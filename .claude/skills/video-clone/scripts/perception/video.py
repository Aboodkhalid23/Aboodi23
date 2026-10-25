"""Decoded frames on a fixed clock.

Every signal in a fingerprint is sampled on one clock, so the reference and our film can be compared frame for frame no
matter what frame rate either was encoded at. Frames are streamed from an ffmpeg pipe: a three-minute reference never
sits in memory as a whole.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Iterator

import numpy as np


def ensure_ffmpeg() -> None:
    """Put FFMPEG_DIR on PATH when ffmpeg is not already there (same rule as analyze.py)."""
    extra = os.environ.get("FFMPEG_DIR", "")
    if not shutil.which("ffmpeg") and extra and os.path.isdir(extra):
        os.environ["PATH"] += os.pathsep + extra


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    duration: float
    has_audio: bool


def probe(path: str) -> VideoInfo:
    ensure_ffmpeg()
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                        "-of", "json", path], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    return VideoInfo(int(v["width"]), int(v["height"]), float(j["format"]["duration"]),
                     any(s["codec_type"] == "audio" for s in j["streams"]))


def frame_size(info: VideoInfo, width: int) -> tuple[int, int]:
    """(width, height) after scaling to `width`, height rounded to an even number like ffmpeg's scale=w:-2."""
    return width, max(2, round(width * info.height / info.width / 2) * 2)


def frames(path: str, fps: float = 24.0, width: int = 320, start: float = 0.0, end: float | None = None) -> Iterator[np.ndarray]:
    """BGR frames at `fps`, scaled to `width`; frame i shows time start + i / fps."""
    ensure_ffmpeg()
    w, h = frame_size(probe(path), width)
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", path]
    if end is not None:
        cmd += ["-t", f"{max(0.0, end - start):.3f}"]
    cmd += ["-vf", f"fps={fps},scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    size = w * h * 3
    try:
        while True:
            buf = p.stdout.read(size)
            if len(buf) < size:
                break
            yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    finally:
        p.stdout.close()
        p.kill()
        p.wait()


def static_mask(path: str, size: tuple[int, int], start: float = 0.0, end: float | None = None,
                std_max: float = 3.0, sample_fps: float = 4.0) -> np.ndarray | None:
    """uint8 mask (255 = usable) at `size` that excludes pixels which never change over the whole clip: a phone UI
    over a screen recording, a watermark, a channel logo, letterbox bars. Their corners would vote for "the camera did
    not move". None when nothing (or nearly everything) is static — then there is nothing to exclude safely."""
    import cv2
    stack = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames(path, fps=sample_fps, width=96, start=start, end=end)]).astype(np.float32)
    if len(stack) < 8:
        return None
    static = (stack.std(axis=0) < std_max).astype(np.uint8)
    frac = float(static.mean())
    if frac < 0.01 or frac > 0.6:
        return None
    static = cv2.dilate(static, np.ones((3, 3), np.uint8))
    return np.where(cv2.resize(static, size, interpolation=cv2.INTER_NEAREST) > 0, 0, 255).astype(np.uint8)


def extract_audio(path: str, sr: int = 22050) -> str | None:
    """Mono wav of the video's sound in a temp file (the caller deletes it), or None when there is no audio."""
    if not probe(path).has_audio:
        return None
    fd, wav = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), wav], check=True)
    return wav
