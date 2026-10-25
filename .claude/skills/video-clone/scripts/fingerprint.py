#!/usr/bin/env python3
"""Style Fingerprint of a film, and how far our film is from the reference (perception/, docs/COMPILER.md).

    python fingerprint.py project projects/<id>          # the usual call: reference vs out/video.mp4, findings printed
    python fingerprint.py extract <video> --out fp.json [--shots report.json|plan.json] [--plot fp.png]
    python fingerprint.py compare ref.json ours.json --out style_distance.json [--plan plan.json]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from perception.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
