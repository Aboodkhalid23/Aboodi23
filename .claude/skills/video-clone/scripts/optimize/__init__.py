"""Stage 3 of the style compiler (docs/COMPILER.md): search a score's camera and timing for the version closest to the
reference — render-free, with CMA-ES over a bounded space that keeps the director's framing.

    cmaes      the optimizer (unit box, deterministic per seed)
    space      which numbers may change, their bounds, and writing a point back as an edited score
    objective  camera distance per shot + predicted tension at plan peaks + staying near the author's values
    run        the per-project driver (motion_score.py optimize)
"""
