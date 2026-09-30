"""Style library: editor/styles/<name>.md with YAML front matter."""
from dataclasses import dataclass
from pathlib import Path

import yaml

STYLES_DIR = Path(__file__).resolve().parent.parent / "styles"


@dataclass
class Style:
    name: str
    summary: str
    fits: list[str]
    palette: dict[str, str]
    fonts: dict[str, str]
    texture: str
    image_treatment: str
    transition: str
    beat_seconds: float
    music_mood: str
    sfx: list[str]
    ai_suffix: str
    notes: str = ""


def _style_files() -> list[Path]:
    return sorted(p for p in STYLES_DIR.glob("*.md") if p.name not in ("README.md", "performance.md", "channel-system.md"))


def load_style(name: str) -> Style:
    path = STYLES_DIR / f"{name}.md"
    if path not in _style_files():
        raise KeyError(f"ستايل '{name}' مو موجود بـ editor/styles")
    _, front, notes = path.read_text(encoding="utf-8").split("---", 2)
    return Style(**yaml.safe_load(front), notes=notes.strip())


def styles_summary() -> str:
    return "\n".join(f"{s.name}: {s.summary}" for s in map(lambda p: load_style(p.stem), _style_files()))
