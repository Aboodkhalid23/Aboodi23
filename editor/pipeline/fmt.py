"""The episode's output canvas (resolution + fps), decided once from the raw footage."""
import json
from dataclasses import asdict, dataclass

from .media import MediaInfo
from .paths import Episode


@dataclass(frozen=True)
class Format:
    width: int
    height: int
    fps: int


def decide_format(info: MediaInfo, max_height: int | None = None) -> Format:
    h = info.height if info.width >= info.height else 0
    height = 2160 if h >= 2160 else 1440 if h >= 1440 else 1080
    if max_height:
        height = max(1080, min(height, max_height))
    return Format(height * 16 // 9, height, 60 if info.fps >= 50 else 30)


def save_format(ep: Episode, fmt: Format) -> None:
    ep.format_file.write_text(json.dumps(asdict(fmt)), encoding="utf-8")


def load_format(ep: Episode) -> Format:
    if not ep.format_file.exists():
        return Format(1920, 1080, 30)
    return Format(**json.loads(ep.format_file.read_text(encoding="utf-8")))
