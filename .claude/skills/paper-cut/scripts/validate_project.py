#!/usr/bin/env python3
"""Validate Paper Cut state and asset contracts without invoking providers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


STAGES = {"intake", "storyboard-review", "asset-review", "asset-production", "assembly", "qa", "preview-review", "preview", "delivery"}
ROLES = {"background", "subject", "prop", "texture", "type", "typography", "audio", "reference"}
STATUSES = {"planned", "generated", "processed", "approved", "approved-for-preview", "approved-for-revision", "rejected", "superseded"}


def load(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"missing file: {path.name}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.name}: {exc}") from None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir", type=Path)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    errors: list[str] = []
    try:
        project = load(root / "paper-cut-project.json")
        manifest = load(root / "assets-manifest.json")
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    if not isinstance(project, dict) or not isinstance(manifest, dict):
        print("root JSON values must be objects", file=sys.stderr)
        return 1

    if project.get("schemaVersion") != 1:
        errors.append("paper-cut-project.json schemaVersion must be 1")
    if project.get("stage") not in STAGES:
        errors.append(f"invalid stage: {project.get('stage')!r}")
    video = project.get("video")
    if not isinstance(video, dict):
        errors.append("video must be an object")
    else:
        for key in ("width", "height", "fps", "durationSeconds"):
            value = video.get(key)
            if not isinstance(value, (int, float)) or value <= 0:
                errors.append(f"video.{key} must be positive")

    scenes = project.get("scenes", [])
    if not isinstance(scenes, list):
        errors.append("scenes must be an array")
        scenes = []
    scene_ids: set[str] = set()
    last_start = -1.0
    max_end = 0.0
    for index, scene in enumerate(scenes):
        prefix = f"scenes[{index}]"
        if not isinstance(scene, dict):
            errors.append(f"{prefix} must be an object")
            continue
        scene_id, start, duration = scene.get("id"), scene.get("start"), scene.get("duration")
        if not isinstance(scene_id, str) or not scene_id:
            errors.append(f"{prefix}.id must be a non-empty string")
        elif scene_id in scene_ids:
            errors.append(f"duplicate scene id: {scene_id}")
        else:
            scene_ids.add(scene_id)
        if not isinstance(start, (int, float)) or start < 0:
            errors.append(f"{prefix}.start must be non-negative")
            continue
        if start < last_start:
            errors.append(f"{prefix}.start is not monotonic")
        last_start = float(start)
        if not isinstance(duration, (int, float)) or duration <= 0:
            errors.append(f"{prefix}.duration must be positive")
            continue
        max_end = max(max_end, float(start + duration))
    if isinstance(video, dict) and isinstance(video.get("durationSeconds"), (int, float)) and max_end > video["durationSeconds"] + 0.05:
        errors.append("scene timing exceeds video.durationSeconds")

    assets = manifest.get("assets", [])
    if manifest.get("schemaVersion") != 1 or not isinstance(assets, list):
        errors.append("assets-manifest.json must have schemaVersion 1 and an assets array")
        assets = []
    asset_ids: set[str] = set()
    for index, asset in enumerate(assets):
        prefix = f"assets[{index}]"
        if not isinstance(asset, dict):
            errors.append(f"{prefix} must be an object")
            continue
        asset_id = asset.get("id")
        if not isinstance(asset_id, str) or not asset_id:
            errors.append(f"{prefix}.id must be a non-empty string")
        elif asset_id in asset_ids:
            errors.append(f"duplicate asset id: {asset_id}")
        else:
            asset_ids.add(asset_id)
        if asset.get("role") not in ROLES:
            errors.append(f"{prefix}.role is invalid")
        if asset.get("status") not in STATUSES:
            errors.append(f"{prefix}.status is invalid")
        for scene_id in asset.get("sceneIds", []):
            if scene_id not in scene_ids:
                errors.append(f"{prefix} references unknown scene {scene_id!r}")
        for key in ("sourcePath", "processedPath"):
            relative = asset.get(key)
            if relative and asset.get("status") in {"generated", "processed", "approved", "approved-for-preview", "approved-for-revision"}:
                if not (root / relative).exists() and not (root / "hyperframes" / relative).exists():
                    errors.append(f"{prefix}.{key} does not exist: {relative}")

    for required in ("video-script.md", "storyboard.md"):
        if not (root / required).is_file():
            errors.append(f"missing file: {required}")
    if not (root / "index.html").is_file() and not (root / "hyperframes" / "index.html").is_file():
        errors.append("missing HyperFrames index.html")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"valid": True, "scenes": len(scenes), "assets": len(assets)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
