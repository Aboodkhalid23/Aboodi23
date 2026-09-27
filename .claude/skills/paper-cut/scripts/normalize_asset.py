#!/usr/bin/env python3
"""Crop transparent margins and place a standalone cutout on a normalized RGBA canvas."""

from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--canvas", type=int, default=1024)
    parser.add_argument("--occupancy", type=float, default=0.78)
    parser.add_argument("--anchor", choices=("center", "bottom"), default="center")
    parser.add_argument("--padding", type=int, default=24)
    args = parser.parse_args()
    if args.canvas < 64 or not 0.1 <= args.occupancy <= 0.95:
        raise SystemExit("invalid canvas or occupancy")
    image = Image.open(args.input).convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise SystemExit("input has no visible pixels")
    cropped = image.crop(bbox)
    usable = max(1, int(args.canvas * args.occupancy) - 2 * args.padding)
    scale = min(usable / cropped.width, usable / cropped.height)
    resized = cropped.resize((max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale))), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (args.canvas, args.canvas), (0, 0, 0, 0))
    x = (args.canvas - resized.width) // 2
    y = args.canvas - args.padding - resized.height if args.anchor == "bottom" else (args.canvas - resized.height) // 2
    canvas.alpha_composite(resized, (x, max(args.padding, y)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
