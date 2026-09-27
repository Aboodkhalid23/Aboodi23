#!/usr/bin/env python3
"""Initialize the project-local contract for the Xingchen Vox collage branch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def write_new(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()

    if args.width <= 0 or args.height <= 0 or args.fps <= 0:
        parser.error("width, height, and fps must be positive")

    vox = args.project_root.resolve() / "visual" / "vox"
    if vox.exists() and any(vox.iterdir()):
        raise SystemExit(f"refusing to initialize non-empty branch: {vox}")

    for directory in [
        vox / "prompts",
        vox / "lookdev",
        vox / "renders",
        vox / "media" / "images",
        vox / "media" / "source",
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    design = f"""# {args.slug} Vox Collage Design

## Visual thesis

TODO: describe how this subject becomes a specific editorial material world.

## Style DNA

- substrate: TODO
- edge language: TODO
- image treatment: TODO
- palette: substrate / paper / ink / primary accent / optional supporting accent
- shadow logic: TODO
- depth system: plate / distant actors / primary subject / foreground occluder
- grain: TODO
- type roles: display / information / data / subtitles
- annotation: TODO
- motion character: TODO

## Anti-reference

- no repeated generic paper cards
- no generated essential text or numbers
- no decorative evidence graphics
- no Vox logos or copied title packaging
- no caption-only motion through an explanatory interval
- no phone-size semantic subject reduced to a decorative postage stamp
- no unmotivated material-world reset between adjacent scenes

## Mobile and safe regions

- master: {args.width}x{args.height} at {args.fps} fps
- subtitles: project-approved safe region and phone-downsample check
"""

    scene_spec = {
        "schema_version": "1.4.0",
        "project": {
            "slug": args.slug,
            "width": args.width,
            "height": args.height,
            "fps": args.fps,
            "timeline_revision": None,
            "source_master": None,
            "source_master_sha256": None,
            "timeline_fingerprint": None,
            "evidence_input_fingerprint": None,
        },
        "style_ref": "visual/vox/DESIGN.md",
        "scenes": [],
    }
    assets = {"schema_version": "1.4.0", "project_slug": args.slug, "assets": []}

    write_new(vox / "DESIGN.md", design)
    write_new(vox / "scene-spec.json", json.dumps(scene_spec, ensure_ascii=False, indent=2) + "\n")
    write_new(vox / "assets.json", json.dumps(assets, ensure_ascii=False, indent=2) + "\n")

    print(f"Initialized Xingchen Vox collage branch: {vox}")
    print("Next: complete DESIGN.md, add scene contracts, then run validate_vox_branch.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
