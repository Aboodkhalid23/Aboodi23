"""All file locations of one episode's edit."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Episode:
    root: Path

    def __post_init__(self):
        self.root = Path(self.root)

    @property
    def edit(self) -> Path: return self.root / "edit"
    @property
    def work(self) -> Path: return self.edit / "work"
    @property
    def assets(self) -> Path: return self.edit / "assets"
    @property
    def source(self) -> Path: return self.work / "source.mp4"
    @property
    def transcript(self) -> Path: return self.edit / "transcript.json"
    @property
    def cuts(self) -> Path: return self.edit / "cuts.json"
    @property
    def clean_video(self) -> Path: return self.work / "clean.mp4"
    @property
    def clean_words(self) -> Path: return self.edit / "clean_words.json"
    @property
    def plan_input(self) -> Path: return self.work / "plan_input.txt"
    @property
    def plan(self) -> Path: return self.edit / "edit_plan.json"
    @property
    def fallbacks(self) -> Path: return self.work / "fallbacks.json"
    @property
    def credits(self) -> Path: return self.edit / "credits.txt"
    @property
    def format_file(self) -> Path: return self.work / "format.json"
    @property
    def final(self) -> Path: return self.edit / "final.mp4"

    def ensure(self) -> "Episode":
        for d in (self.edit, self.work, self.assets):
            d.mkdir(parents=True, exist_ok=True)
        return self
