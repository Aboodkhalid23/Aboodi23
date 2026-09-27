"""YouTube chapters for the description, on the final timeline (teaser first)."""
from pathlib import Path

from .plan import EditPlan


def _stamp(t: float) -> str:
    t = int(t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def write_chapters(plan: EditPlan, path: Path) -> Path:
    lines = [f"{_stamp(t)} {c['title']}" for t, c in zip(plan.chapter_times(), plan.chapters)]
    Path(path).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return Path(path)
