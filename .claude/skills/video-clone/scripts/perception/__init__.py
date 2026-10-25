"""Perception: measure a film as time series (camera trajectory, easing, tension, rhythm, colour) and compare two films.

Stage 1 of the style compiler (docs/COMPILER.md). Entry points:

    fingerprint.extract(video, shots=…, audio=…, beats=…)   → fingerprint dict (analysis/fingerprint.json)
    distance.style_distance(ref_fp, our_fp, pairs=…)        → scores per component and shot, plus findings
    python .claude/skills/video-clone/scripts/fingerprint.py --help
"""
