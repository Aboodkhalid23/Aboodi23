#!/usr/bin/env python3
"""Compute deterministic input identities for one Vox collage scene contract."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


class FingerprintError(ValueError):
    """Raised when a declared input cannot be fingerprinted safely."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_input_path(project_root: Path, reference: Any, label: str) -> Path:
    if not isinstance(reference, str) or not reference.strip():
        raise FingerprintError(f"{label} is missing")
    if re.match(r"^[a-z][a-z0-9+.-]*://", reference, flags=re.IGNORECASE):
        raise FingerprintError(f"{label} must not use a remote URL: {reference}")

    path = Path(reference)
    if not path.is_absolute():
        root = project_root.resolve()
        path = (root / path).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise FingerprintError(f"{label} escapes the project root: {reference}") from exc
    else:
        path = path.resolve()
    if not path.is_file():
        raise FingerprintError(f"{label} does not exist: {reference}")
    return path


def canonical_scene_records(scene_doc: dict[str, Any]) -> list[dict[str, Any]]:
    scenes = scene_doc.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise FingerprintError("scene-spec needs at least one scene before inputs can be locked")

    records: list[dict[str, Any]] = []
    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise FingerprintError(f"scene[{index}] must be an object")
        timing = scene.get("timing")
        if not isinstance(timing, dict):
            raise FingerprintError(f"scene[{index}] timing is missing")
        start = timing.get("start_sec")
        end = timing.get("end_sec")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            raise FingerprintError(f"scene[{index}] needs numeric start_sec/end_sec")
        records.append(
            {
                "scene_id": scene.get("scene_id"),
                "beat_id": scene.get("beat_id"),
                "start_sec": float(start),
                "end_sec": float(end),
            }
        )
    return records


def audio_input_records(
    project_root: Path,
    scene_doc: dict[str, Any],
) -> list[dict[str, str]]:
    refs: set[str] = set()
    for scene in scene_doc.get("scenes", []):
        if not isinstance(scene, dict):
            continue
        playable = scene.get("playable_clip")
        if not isinstance(playable, dict):
            continue
        reference = playable.get("audio_ref")
        if isinstance(reference, str) and reference.strip():
            refs.add(reference)

    records: list[dict[str, str]] = []
    for reference in sorted(refs):
        path = resolve_input_path(project_root, reference, f"playable audio {reference}")
        records.append({"path": reference, "sha256": sha256_file(path)})
    return records


def compute_input_fingerprints(
    project_root: Path,
    scene_doc: dict[str, Any],
) -> dict[str, Any]:
    project = scene_doc.get("project")
    if not isinstance(project, dict):
        raise FingerprintError("scene-spec project must be an object")

    master_ref = project.get("source_master")
    master = resolve_input_path(project_root, master_ref, "scene-spec project.source_master")
    master_sha256 = sha256_file(master)
    scenes = canonical_scene_records(scene_doc)
    audio_inputs = audio_input_records(project_root, scene_doc)
    timeline_payload = {
        "schema": "vox-timeline-inputs/v1",
        "fps": project.get("fps"),
        "timeline_revision": project.get("timeline_revision"),
        "scenes": scenes,
        "audio_inputs": audio_inputs,
    }
    canonical = json.dumps(
        timeline_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    timeline_fingerprint = hashlib.sha256(canonical).hexdigest()
    evidence_payload = (
        "vox-evidence-inputs/v1\n"
        f"{master_sha256}\n"
        f"{timeline_fingerprint}\n"
    ).encode("utf-8")
    evidence_input_fingerprint = hashlib.sha256(evidence_payload).hexdigest()
    return {
        "source_master": master_ref,
        "source_master_sha256": master_sha256,
        "timeline_fingerprint": timeline_fingerprint,
        "evidence_input_fingerprint": evidence_input_fingerprint,
        "audio_inputs": audio_inputs,
        "timeline_payload": timeline_payload,
    }
