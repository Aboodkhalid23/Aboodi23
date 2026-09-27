#!/usr/bin/env python3
"""Copy neutral Vox collage primitives into an existing Remotion project."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def copy_new(source: Path, target: Path) -> None:
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing path: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("remotion_root", type=Path)
    parser.add_argument("--with-demo", action="store_true")
    parser.add_argument("--project-slug", default="xingchen-vox-collage-demo")
    args = parser.parse_args()

    root = args.remotion_root.resolve()
    if not (root / "package.json").exists() or not (root / "src").is_dir():
        parser.error("target must be an existing Remotion project with package.json and src/")

    asset_root = Path(__file__).resolve().parents[1] / "assets" / "remotion-template"
    primitive_target = root / "src" / "vox-collage"
    copy_new(asset_root / "vox-collage", primitive_target)
    print(f"Installed neutral primitives: {primitive_target}")

    if args.with_demo:
        demo_target = root / "src" / "projects" / args.project_slug
        copy_new(asset_root / "demo", demo_target)
        print(f"Installed demo entry: {demo_target / 'index.tsx'}")
        print(f"Render composition: XingchenVoxCollageDemo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
