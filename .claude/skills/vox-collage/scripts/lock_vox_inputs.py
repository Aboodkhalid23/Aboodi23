#!/usr/bin/env python3
"""Print, check, or write deterministic Vox input fingerprints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from input_fingerprints import FingerprintError, compute_input_fingerprints


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"top-level JSON must be an object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lock the current audio, scene timing, and source master identities."
    )
    parser.add_argument("project_root", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="Write the three current fingerprints into scene-spec.json.",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="Fail when the stored fingerprints do not match the current inputs.",
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    spec_path = root / "visual" / "vox" / "scene-spec.json"
    spec = load_object(spec_path)
    try:
        current = compute_input_fingerprints(root, spec)
    except FingerprintError as exc:
        raise SystemExit(str(exc)) from exc

    project = spec.get("project")
    if not isinstance(project, dict):
        raise SystemExit("scene-spec project must be an object")
    stored = {
        key: project.get(key)
        for key in [
            "source_master_sha256",
            "timeline_fingerprint",
            "evidence_input_fingerprint",
        ]
    }
    expected = {key: current[key] for key in stored}

    if args.check:
        mismatches = [
            key for key, value in expected.items() if stored.get(key) != value
        ]
        if mismatches:
            print(json.dumps({"status": "stale", "mismatches": mismatches}, indent=2))
            return 1
        print(json.dumps({"status": "locked", **expected}, indent=2))
        return 0

    if args.write:
        project.update(expected)
        spec_path.write_text(
            json.dumps(spec, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Updated input fingerprints: {spec_path}")

    print(
        json.dumps(
            {
                **expected,
                "audio_inputs": current["audio_inputs"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
