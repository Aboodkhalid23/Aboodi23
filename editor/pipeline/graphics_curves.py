"""Cubic-bezier easing in Python (the same curves the Remotion scenes use)."""


def bezier(x1: float, y1: float, x2: float, y2: float, p: float) -> float:
    """y of the CSS cubic-bezier(x1, y1, x2, y2) at x = p (solved by bisection; p clamped to 0–1)."""
    p = min(1.0, max(0.0, p))
    lo, hi = 0.0, 1.0
    for _ in range(40):
        t = (lo + hi) / 2
        x = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3
        lo, hi = (t, hi) if x < p else (lo, t)
    t = (lo + hi) / 2
    return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3
