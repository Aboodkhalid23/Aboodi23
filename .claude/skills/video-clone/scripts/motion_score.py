#!/usr/bin/env python3
"""Motion Score: the film's camera and timing as data — validate, compile for the engine, transfer the reference's
camera, predict the measured result before rendering (score/, docs/COMPILER.md).

    python motion_score.py from-ref projects/<id>                    # camera moves transferred from the reference
    python motion_score.py validate projects/<id>/build/score
    python motion_score.py compile  projects/<id>/build/score --out projects/<id>/build/src/score.js
    python motion_score.py predict  projects/<id>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from score.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
