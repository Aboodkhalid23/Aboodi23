#!/usr/bin/env python3
"""Extract per-scene playable clips and review frames from one accepted master."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path
from typing import Any

from input_fingerprints import (
    FingerprintError,
    compute_input_fingerprints,
    sha256_file,
)


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"top-level JSON must be an object: {path}")
    return value


def within(root: Path, target: Path, label: str) -> Path:
    resolved = target.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise SystemExit(f"{label} must stay inside project root: {target}") from exc
    return resolved


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def scene_records(
    state: dict[str, Any],
    spec: dict[str, Any],
) -> tuple[int, int, list[dict[str, Any]]]:
    project = spec.get("project")
    metadata = state.get("metadata")
    state_format = metadata.get("format") if isinstance(metadata, dict) else None
    if not isinstance(project, dict) or not isinstance(state_format, dict):
        raise SystemExit("scene spec project and project-state metadata.format are required")

    fps = project.get("fps")
    state_fps = state_format.get("fps")
    if not isinstance(fps, int) or fps <= 0 or fps != state_fps:
        raise SystemExit("scene-spec fps must be a positive integer matching project-state")
    revision = project.get("timeline_revision")
    state_revision = state.get("script", {}).get("timeline_revision")
    if not isinstance(revision, int) or revision < 1 or revision != state_revision:
        raise SystemExit("scene-spec timeline_revision must match project-state")

    spec_scenes = spec.get("scenes")
    state_scenes = state.get("scenes")
    if not isinstance(spec_scenes, list) or not isinstance(state_scenes, list):
        raise SystemExit("both scene spec and project state need scenes arrays")
    if [scene.get("scene_id") for scene in spec_scenes if isinstance(scene, dict)] != [
        scene.get("scene_id") for scene in state_scenes if isinstance(scene, dict)
    ]:
        raise SystemExit("scene-spec scene order/ids must match project-state")

    tolerance = 1.0 / fps
    records: list[dict[str, Any]] = []
    for spec_scene, state_scene in zip(spec_scenes, state_scenes):
        if not isinstance(spec_scene, dict) or not isinstance(state_scene, dict):
            raise SystemExit("scene entries must be objects")
        scene_id = spec_scene.get("scene_id")
        timing = spec_scene.get("timing")
        state_timing = state_scene.get("timing")
        if not isinstance(scene_id, str) or not isinstance(timing, dict) or not isinstance(state_timing, dict):
            raise SystemExit("each scene needs scene_id and timing objects")
        start = timing.get("start_sec")
        end = timing.get("end_sec")
        state_start = state_timing.get("start_sec")
        state_end = state_timing.get("end_sec")
        if not all(isinstance(value, (int, float)) for value in [start, end, state_start, state_end]):
            raise SystemExit(f"scene {scene_id} needs numeric start_sec/end_sec")
        start = float(start)
        end = float(end)
        if start < 0 or end <= start:
            raise SystemExit(f"scene {scene_id} has invalid timing")
        if abs(start - float(state_start)) > tolerance or abs(end - float(state_end)) > tolerance:
            raise SystemExit(f"scene {scene_id} timing drifts from project-state")
        records.append(
            {
                "scene_id": scene_id,
                "beat_id": spec_scene.get("beat_id"),
                "start_sec": start,
                "end_sec": end,
                "duration_sec": round(end - start, 6),
            }
        )
    if not records:
        raise SystemExit("no scenes available for extraction")
    return fps, revision, records


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract H.264/AAC scene clips plus entry, settled, exit, and contact-sheet evidence."
    )
    parser.add_argument("project_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--master", type=Path, help="Override scene-spec project.source_master")
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Validate state/spec synchronization and print the extraction plan without running FFmpeg.",
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    state = load_object(root / "project-state.json")
    spec = load_object(root / "visual" / "vox" / "scene-spec.json")
    fps, revision, records = scene_records(state, spec)

    project = spec["project"]
    master_arg = args.master
    if master_arg is None:
        master_ref = project.get("source_master")
        if not isinstance(master_ref, str) or not master_ref.strip():
            raise SystemExit("scene-spec project.source_master is required")
        master = within(root, root / master_ref, "source master")
    else:
        master = within(root, master_arg if master_arg.is_absolute() else root / master_arg, "source master")
    if not master.is_file():
        raise SystemExit(f"source master not found: {master}")

    try:
        input_identity = compute_input_fingerprints(root, spec)
    except FingerprintError as exc:
        raise SystemExit(f"cannot compute input fingerprints: {exc}") from exc
    for field in [
        "source_master_sha256",
        "timeline_fingerprint",
        "evidence_input_fingerprint",
    ]:
        if project.get(field) != input_identity[field]:
            raise SystemExit(
                f"scene-spec project.{field} is missing or stale; "
                "run lock_vox_inputs.py --write before extracting evidence"
            )
    if sha256_file(master) != input_identity["source_master_sha256"]:
        raise SystemExit(
            "--master does not match the source master locked in scene-spec.json"
        )

    output = within(
        root,
        args.output_dir if args.output_dir.is_absolute() else root / args.output_dir,
        "evidence directory",
    )
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty evidence directory: {output}")

    plan = {
        "schema_version": "1.1.0",
        "source_master": master.relative_to(root).as_posix(),
        "source_master_sha256": input_identity["source_master_sha256"],
        "timeline_revision": revision,
        "timeline_fingerprint": input_identity["timeline_fingerprint"],
        "evidence_input_fingerprint": input_identity["evidence_input_fingerprint"],
        "audio_inputs": input_identity["audio_inputs"],
        "fps": fps,
        "output_dir": output.relative_to(root).as_posix(),
        "scenes": records,
    }
    if args.plan_only:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    probe = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
            "-of",
            "json",
            str(master),
        ]
    )
    metadata = json.loads(probe.stdout)
    duration = float(metadata.get("format", {}).get("duration", 0))
    if not math.isfinite(duration) or duration + (1.0 / fps) < records[-1]["end_sec"]:
        raise SystemExit("source master is shorter than the final scene boundary")
    run(["ffmpeg", "-v", "error", "-i", str(master), "-f", "null", "-"])

    output.mkdir(parents=True, exist_ok=True)
    index_scenes: list[dict[str, Any]] = []
    for record in records:
        scene_id = record["scene_id"]
        scene_dir = output / scene_id
        scene_dir.mkdir(parents=True, exist_ok=False)
        clip = scene_dir / "playable.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-ss",
                f"{record['start_sec']:.6f}",
                "-i",
                str(master),
                "-t",
                f"{record['duration_sec']:.6f}",
                "-map",
                "0:v:0",
                "-map",
                "0:a:0?",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                str(clip),
            ]
        )

        offsets = {
            "entry": min(0.10, record["duration_sec"] * 0.04),
            "settled": record["duration_sec"] * 0.72,
            "exit": max(0.0, record["duration_sec"] - 0.10),
        }
        checkpoint_paths: dict[str, str] = {}
        for role, offset in offsets.items():
            frame = scene_dir / f"{role}.png"
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-ss",
                    f"{record['start_sec'] + offset:.6f}",
                    "-i",
                    str(master),
                    "-frames:v",
                    "1",
                    str(frame),
                ]
            )
            checkpoint_paths[role] = frame.relative_to(root).as_posix()

        contact_sheet = scene_dir / "contact-sheet.jpg"
        sample_rate = 6.0 / record["duration_sec"]
        run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-i",
                str(clip),
                "-vf",
                f"fps={sample_rate:.8f},scale=480:-1,tile=3x2:padding=8:margin=8",
                "-frames:v",
                "1",
                str(contact_sheet),
            ]
        )
        index_scenes.append(
            {
                **record,
                "input_fingerprint": input_identity["evidence_input_fingerprint"],
                "playable_clip": clip.relative_to(root).as_posix(),
                "checkpoint_paths": checkpoint_paths,
                "contact_sheet": contact_sheet.relative_to(root).as_posix(),
            }
        )

    index = {
        **plan,
        "source_metadata": metadata,
        "decode": "pass",
        "scenes": index_scenes,
    }
    index_path = output / "scene-evidence-index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Scene evidence: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
