#!/usr/bin/env python3
"""Validate the project-local Vox collage scene and asset contracts."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from input_fingerprints import (
    FingerprintError,
    compute_input_fingerprints,
    resolve_input_path,
)


ROLES = {
    "plate",
    "source",
    "cutout",
    "prop",
    "type",
    "data",
    "annotation",
    "occluder",
    "texture",
}
MODES = {"editorial-explainer", "metaphor-broll", "source-collage"}
SOURCE_KINDS = {"source", "local", "generated", "code-native"}
SEMANTIC_ROLES = {"source", "type", "data", "annotation"}
MOTION_TIERS = {"primary", "secondary", "tertiary", "ambient"}
INDEPENDENT_MOTION_ROLES = {"cutout", "prop", "occluder"}


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing required file: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"top-level JSON must be an object: {path}")
        return {}
    return value


def resolve_project_reference(
    project_root: Path,
    reference: Any,
    prefix: str,
    errors: list[str],
) -> tuple[Path | None, str | None]:
    if not isinstance(reference, str) or not reference.strip():
        errors.append(f"{prefix} is missing a project-relative path")
        return None, None
    if re.match(r"^[a-z][a-z0-9+.-]*://", reference, flags=re.IGNORECASE):
        errors.append(f"{prefix} must not use a remote URL: {reference}")
        return None, None

    file_ref, separator, fragment = reference.partition("#")
    relative = Path(file_ref)
    if relative.is_absolute():
        errors.append(f"{prefix} must be project-relative: {reference}")
        return None, fragment if separator else None

    root = project_root.resolve()
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        errors.append(f"{prefix} escapes the project root: {reference}")
        return None, fragment if separator else None
    return resolved, fragment if separator else None


def validate_code_native_reference(
    project_root: Path,
    reference: Any,
    prefix: str,
    errors: list[str],
) -> None:
    path, fragment = resolve_project_reference(project_root, reference, prefix, errors)
    if path is None:
        return
    if not path.is_file():
        errors.append(f"{prefix} file does not exist: {reference}")
        return
    if not fragment:
        return
    try:
        source = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{prefix} cannot inspect fragment {fragment}: {exc}")
        return
    fragment_pattern = re.compile(
        rf"\bid\s*=\s*['\"]{re.escape(fragment)}['\"]"
    )
    if fragment_pattern.search(source) is None:
        errors.append(f"{prefix} fragment does not exist: {reference}")


def probe_media(
    path: Path,
    prefix: str,
    errors: list[str],
    warnings: list[str],
    allow_pending: bool,
    require_audio: bool = False,
) -> dict[str, Any] | None:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        target = warnings if allow_pending else errors
        target.append(f"{prefix} cannot be inspected because ffprobe is unavailable")
        return None
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,width,height",
            "-of",
            "json",
            str(path),
        ],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        errors.append(f"{prefix} is not decodable: {result.stderr.strip() or result.stdout.strip()}")
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        errors.append(f"{prefix} ffprobe output is invalid JSON: {exc}")
        return None
    streams = payload.get("streams", [])
    if not isinstance(streams, list) or not any(
        stream.get("codec_type") == "video" for stream in streams if isinstance(stream, dict)
    ):
        errors.append(f"{prefix} has no visual stream")
        return None
    if require_audio and not any(
        stream.get("codec_type") == "audio" for stream in streams if isinstance(stream, dict)
    ):
        errors.append(f"{prefix} must contain accepted audio")
    return payload


def decode_video(
    path: Path,
    prefix: str,
    errors: list[str],
    warnings: list[str],
    allow_pending: bool,
) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        target = warnings if allow_pending else errors
        target.append(f"{prefix} cannot be fully decoded because ffmpeg is unavailable")
        return
    result = subprocess.run(
        [ffmpeg, "-v", "error", "-i", str(path), "-f", "null", "-"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        errors.append(f"{prefix} full decode failed: {result.stderr.strip() or result.stdout.strip()}")


def record_pending(
    message: str,
    allow_pending: bool,
    errors: list[str],
    warnings: list[str],
) -> None:
    (warnings if allow_pending else errors).append(message)


def scene_timing(scene: dict[str, Any]) -> tuple[float | None, float | None]:
    timing = scene.get("timing")
    if not isinstance(timing, dict):
        return None, None
    start = timing.get("start_sec")
    end = timing.get("end_sec")
    if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
        return None, None
    return float(start), float(end)


def probe_duration(
    path: Path,
    prefix: str,
    errors: list[str],
    warnings: list[str],
    allow_pending: bool,
) -> float | None:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        target = warnings if allow_pending else errors
        target.append(f"{prefix} duration cannot be inspected because ffprobe is unavailable")
        return None
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        errors.append(
            f"{prefix} duration cannot be inspected: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
        return None
    try:
        duration = float(result.stdout.strip())
    except ValueError:
        errors.append(f"{prefix} duration is not numeric: {result.stdout.strip()!r}")
        return None
    if duration <= 0:
        errors.append(f"{prefix} duration must be positive")
        return None
    return duration


def validate_input_identity(
    project_root: Path,
    scene_doc: dict[str, Any],
    scenes: list[Any],
    errors: list[str],
    warnings: list[str],
    allow_pending: bool,
) -> str | None:
    """Bind accepted evidence to the exact master, audio bytes, and scene timing."""

    project = scene_doc.get("project")
    if not isinstance(project, dict):
        errors.append("scene-spec.json project must be an object")
        return None
    master_ref = project.get("source_master")
    if not isinstance(master_ref, str) or not master_ref.strip():
        record_pending(
            "scene-spec project.source_master and input fingerprints are pending",
            allow_pending,
            errors,
            warnings,
        )
        return None
    try:
        current = compute_input_fingerprints(project_root, scene_doc)
    except FingerprintError as exc:
        errors.append(f"cannot compute input fingerprints: {exc}")
        return None

    for field in [
        "source_master_sha256",
        "timeline_fingerprint",
        "evidence_input_fingerprint",
    ]:
        stored = project.get(field)
        if not isinstance(stored, str) or not re.fullmatch(r"[0-9a-f]{64}", stored):
            record_pending(
                f"scene-spec project.{field} is pending; run lock_vox_inputs.py --write",
                allow_pending,
                errors,
                warnings,
            )
        elif stored != current[field]:
            errors.append(
                f"scene-spec project.{field} is stale: "
                f"stored={stored} current={current[field]}"
            )

    master = resolve_input_path(project_root, master_ref, "scene-spec project.source_master")
    master_probe = probe_media(
        master,
        "scene-spec source master",
        errors,
        warnings,
        allow_pending,
        require_audio=True,
    )
    master_duration = (
        probe_duration(
            master,
            "scene-spec source master",
            errors,
            warnings,
            allow_pending,
        )
        if master_probe is not None
        else None
    )
    timings = [scene_timing(scene) for scene in scenes if isinstance(scene, dict)]
    complete_timings = [
        (start, end)
        for start, end in timings
        if start is not None and end is not None
    ]
    timeline_duration: float | None = None
    if complete_timings:
        timeline_duration = max(end for _, end in complete_timings)
    if master_duration is not None and timeline_duration is not None and timeline_duration > 0:
        tolerance = max(1.0, timeline_duration * 0.03)
        if abs(master_duration - timeline_duration) > tolerance:
            errors.append(
                "scene-spec source master duration is grossly out of sync with the scene timeline: "
                f"master={master_duration:.3f}s timeline={timeline_duration:.3f}s"
            )

    audio_inputs = current.get("audio_inputs", [])
    if len(audio_inputs) == 1 and timeline_duration is not None and timeline_duration > 0:
        audio_ref = audio_inputs[0].get("path")
        try:
            audio_path = resolve_input_path(project_root, audio_ref, "shared playable audio")
        except FingerprintError as exc:
            errors.append(str(exc))
        else:
            audio_duration = probe_duration(
                audio_path,
                "shared playable audio",
                errors,
                warnings,
                allow_pending,
            )
            if audio_duration is not None:
                tolerance = max(1.0, timeline_duration * 0.03)
                if abs(audio_duration - timeline_duration) > tolerance:
                    errors.append(
                        "shared playable audio duration is grossly out of sync with the scene "
                        f"timeline: audio={audio_duration:.3f}s timeline={timeline_duration:.3f}s"
                    )

    return current["evidence_input_fingerprint"]


def validate_state_sync(
    project_root: Path,
    scene_doc: dict[str, Any],
    scenes: list[Any],
    errors: list[str],
    warnings: list[str],
    allow_pending: bool,
) -> None:
    """Keep the Vox branch contract synchronized with Lean project state."""

    state_path = project_root / "project-state.json"
    if not state_path.exists():
        return
    state = load_json(state_path, errors)
    if not state:
        return

    project = scene_doc.get("project")
    if not isinstance(project, dict):
        errors.append("scene-spec.json project must be an object")
        return

    metadata = state.get("metadata")
    state_format = metadata.get("format") if isinstance(metadata, dict) else None
    if not isinstance(state_format, dict):
        errors.append("project-state.json metadata.format must be an object")
        return

    for field in ["width", "height", "fps"]:
        spec_value = project.get(field)
        state_value = state_format.get(field)
        if spec_value != state_value:
            errors.append(
                f"scene-spec project.{field} must match project-state metadata.format.{field}: "
                f"{spec_value!r} != {state_value!r}"
            )

    state_project_id = metadata.get("project_id") if isinstance(metadata, dict) else None
    if isinstance(state_project_id, str) and project.get("slug") != state_project_id:
        errors.append(
            "scene-spec project.slug must match project-state metadata.project_id: "
            f"{project.get('slug')!r} != {state_project_id!r}"
        )

    state_revision = state.get("script", {}).get("timeline_revision")
    spec_revision = project.get("timeline_revision")
    if not isinstance(spec_revision, int) or spec_revision < 1:
        record_pending(
            "scene-spec project.timeline_revision must record the current Lean timeline revision",
            allow_pending,
            errors,
            warnings,
        )
    elif spec_revision != state_revision:
        errors.append(
            "scene-spec project.timeline_revision must match project-state "
            f"script.timeline_revision: {spec_revision!r} != {state_revision!r}"
        )

    source_master_ref = project.get("source_master")
    if not isinstance(source_master_ref, str) or not source_master_ref.strip():
        record_pending(
            "scene-spec project.source_master must point to the current assembled master",
            allow_pending,
            errors,
            warnings,
        )
    else:
        source_master, _ = resolve_project_reference(
            project_root,
            source_master_ref,
            "scene-spec project.source_master",
            errors,
        )
        if source_master is not None:
            if not source_master.is_file():
                errors.append(f"scene-spec source master does not exist: {source_master_ref}")
            else:
                probe_media(
                    source_master,
                    "scene-spec source master",
                    errors,
                    warnings,
                    allow_pending,
                    require_audio=True,
                )

    state_scenes = state.get("scenes")
    if not isinstance(state_scenes, list):
        errors.append("project-state.json scenes must be an array")
        return
    spec_scene_objects = [scene for scene in scenes if isinstance(scene, dict)]
    state_scene_objects = [scene for scene in state_scenes if isinstance(scene, dict)]
    spec_ids = [scene.get("scene_id") for scene in spec_scene_objects]
    state_ids = [scene.get("scene_id") for scene in state_scene_objects]
    if spec_ids != state_ids:
        errors.append(
            "scene-spec scene order/ids must exactly match project-state scenes: "
            f"{spec_ids!r} != {state_ids!r}"
        )
        return

    fps = project.get("fps")
    tolerance = 1.0 / float(fps) if isinstance(fps, (int, float)) and fps > 0 else 0.001
    for spec_scene, state_scene in zip(spec_scene_objects, state_scene_objects):
        scene_id = spec_scene.get("scene_id")
        if spec_scene.get("beat_id") != state_scene.get("beat_id"):
            errors.append(
                f"scene {scene_id} beat_id must match project-state: "
                f"{spec_scene.get('beat_id')!r} != {state_scene.get('beat_id')!r}"
            )
        spec_start, spec_end = scene_timing(spec_scene)
        state_start, state_end = scene_timing(state_scene)
        if None in {spec_start, spec_end, state_start, state_end}:
            errors.append(f"scene {scene_id} needs numeric start_sec/end_sec in both state and scene spec")
            continue
        if abs(spec_start - state_start) > tolerance or abs(spec_end - state_end) > tolerance:
            errors.append(
                f"scene {scene_id} timing drifts from project-state by more than one frame: "
                f"spec=({spec_start}, {spec_end}) state=({state_start}, {state_end})"
            )


def validate(project_root: Path, allow_pending: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    vox = project_root.resolve() / "visual" / "vox"
    design_path = vox / "DESIGN.md"
    if not design_path.exists():
        errors.append(f"missing required file: {design_path}")
    else:
        design = design_path.read_text(encoding="utf-8-sig")
        if "TODO" in design:
            warnings.append("DESIGN.md still contains TODO markers")

    scene_doc = load_json(vox / "scene-spec.json", errors)
    asset_doc = load_json(vox / "assets.json", errors)
    assets = asset_doc.get("assets", [])
    if not isinstance(assets, list):
        errors.append("assets.json assets must be an array")
        assets = []

    asset_by_id: dict[str, dict[str, Any]] = {}
    for index, asset in enumerate(assets):
        prefix = f"asset[{index}]"
        if not isinstance(asset, dict):
            errors.append(f"{prefix} must be an object")
            continue
        asset_id = asset.get("id")
        if not isinstance(asset_id, str) or not asset_id:
            errors.append(f"{prefix} missing id")
            continue
        if asset_id in asset_by_id:
            errors.append(f"duplicate asset id: {asset_id}")
        asset_by_id[asset_id] = asset
        if asset.get("role") not in ROLES:
            errors.append(f"{prefix} has invalid role: {asset.get('role')}")
        if asset.get("source_kind") not in SOURCE_KINDS:
            errors.append(f"{prefix} has invalid source_kind: {asset.get('source_kind')}")
        status = asset.get("status")
        if status not in {"planned", "generated", "reviewed", "approved", "blocked"}:
            errors.append(f"{prefix} has invalid status: {status}")
        if not allow_pending and status not in {"approved", "blocked"}:
            warnings.append(f"{prefix} is not approved: {status}")
        if status == "approved" and asset.get("role") == "cutout" and asset.get("alpha_checked") is not True:
            errors.append(f"{prefix} approved cutout must set alpha_checked=true")
        rel_path = asset.get("path")
        if status == "approved" and asset.get("source_kind") != "code-native":
            if not isinstance(rel_path, str) or not rel_path:
                errors.append(f"{prefix} approved file asset is missing path")
            elif not (project_root / rel_path).exists():
                errors.append(f"{prefix} file does not exist: {rel_path}")
        if asset.get("source_kind") == "code-native" and status in {"reviewed", "approved"}:
            validate_code_native_reference(
                project_root,
                rel_path,
                f"{prefix} code-native path",
                errors,
            )

    scenes = scene_doc.get("scenes", [])
    if not isinstance(scenes, list):
        errors.append("scene-spec.json scenes must be an array")
        scenes = []
    if not scenes:
        errors.append("scene-spec.json has no scenes")

    validate_state_sync(
        project_root,
        scene_doc,
        scenes,
        errors,
        warnings,
        allow_pending,
    )
    current_input_fingerprint = validate_input_identity(
        project_root,
        scene_doc,
        scenes,
        errors,
        warnings,
        allow_pending,
    )

    scene_ids: set[str] = set()
    dominant_visuals: list[str] = []
    for index, scene in enumerate(scenes):
        prefix = f"scene[{index}]"
        if not isinstance(scene, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for key in [
            "scene_id",
            "beat_id",
            "mode",
            "knowledge_change",
            "visual_proposition",
            "dominant_visual",
            "motion_action",
            "hero_frame",
            "layers",
            "camera",
            "checkpoints",
        ]:
            if key not in scene:
                errors.append(f"{prefix} missing {key}")
        scene_id = scene.get("scene_id")
        if isinstance(scene_id, str):
            if scene_id in scene_ids:
                errors.append(f"duplicate scene_id: {scene_id}")
            scene_ids.add(scene_id)
        if scene.get("mode") not in MODES:
            errors.append(f"{prefix} has invalid mode: {scene.get('mode')}")
        dominant = scene.get("dominant_visual")
        if isinstance(dominant, str) and dominant:
            dominant_visuals.append(dominant)
        proposition = scene.get("visual_proposition")
        if not isinstance(proposition, str) or len(proposition.strip()) < 8:
            errors.append(f"{prefix} visual_proposition is missing or too vague")
        hero = scene.get("hero_frame")
        if not isinstance(hero, dict) or not hero.get("description"):
            errors.append(f"{prefix} hero_frame needs a description")
        elif not isinstance(hero.get("focal_order"), list) or not hero.get("focal_order"):
            errors.append(f"{prefix} hero_frame needs a focal_order list")
        elif not hero.get("subtitle_safe_region"):
            errors.append(f"{prefix} hero_frame needs subtitle_safe_region")
        if isinstance(hero, dict):
            hero_path_ref = hero.get("path")
            if not hero_path_ref:
                record_pending(
                    f"{prefix} hero_frame.path is pending; contract validation is not visual approval",
                    allow_pending,
                    errors,
                    warnings,
                )
            else:
                hero_path, _ = resolve_project_reference(
                    project_root,
                    hero_path_ref,
                    f"{prefix} hero_frame.path",
                    errors,
                )
                if hero_path is not None:
                    if not hero_path.is_file():
                        errors.append(f"{prefix} hero frame does not exist: {hero_path_ref}")
                    else:
                        hero_probe = probe_media(
                            hero_path,
                            f"{prefix} hero frame",
                            errors,
                            warnings,
                            allow_pending,
                        )
                        if hero_probe is not None:
                            video_stream = next(
                                (
                                    stream
                                    for stream in hero_probe.get("streams", [])
                                    if isinstance(stream, dict) and stream.get("codec_type") == "video"
                                ),
                                {},
                            )
                            expected_width = scene_doc.get("project", {}).get("width")
                            expected_height = scene_doc.get("project", {}).get("height")
                            if (
                                isinstance(expected_width, int)
                                and isinstance(expected_height, int)
                                and (
                                    video_stream.get("width") != expected_width
                                    or video_stream.get("height") != expected_height
                                )
                            ):
                                errors.append(
                                    f"{prefix} hero frame must be {expected_width}x{expected_height}, "
                                    f"got {video_stream.get('width')}x{video_stream.get('height')}"
                                )
                hero_input_fingerprint = hero.get("input_fingerprint")
                if not isinstance(hero_input_fingerprint, str) or not re.fullmatch(
                    r"[0-9a-f]{64}", hero_input_fingerprint
                ):
                    record_pending(
                        f"{prefix} hero_frame.input_fingerprint is pending; old visual evidence "
                        "must not survive an input change",
                        allow_pending,
                        errors,
                        warnings,
                    )
                elif (
                    current_input_fingerprint is not None
                    and hero_input_fingerprint != current_input_fingerprint
                ):
                    errors.append(
                        f"{prefix} hero_frame.input_fingerprint is stale for the current inputs"
                    )

        playable = scene.get("playable_clip")
        if not isinstance(playable, dict):
            record_pending(
                f"{prefix} playable_clip is pending; stills do not approve motion",
                allow_pending,
                errors,
                warnings,
            )
        else:
            clip_ref = playable.get("path")
            clip_path, _ = resolve_project_reference(
                project_root,
                clip_ref,
                f"{prefix} playable_clip.path",
                errors,
            )
            if clip_path is not None:
                if not clip_path.is_file():
                    errors.append(f"{prefix} playable clip does not exist: {clip_ref}")
                else:
                    probe_media(
                        clip_path,
                        f"{prefix} playable clip",
                        errors,
                        warnings,
                        allow_pending,
                        require_audio=True,
                    )
                    decode_video(
                        clip_path,
                        f"{prefix} playable clip",
                        errors,
                        warnings,
                        allow_pending,
                    )
            audio_ref = playable.get("audio_ref")
            if not isinstance(audio_ref, str) or not audio_ref.strip():
                record_pending(
                    f"{prefix} playable_clip.audio_ref is pending",
                    allow_pending,
                    errors,
                    warnings,
                )
            elif not Path(audio_ref).is_absolute() and not (project_root / audio_ref).is_file():
                errors.append(f"{prefix} playable audio does not exist: {audio_ref}")
            elif Path(audio_ref).is_absolute() and not Path(audio_ref).is_file():
                errors.append(f"{prefix} playable audio does not exist: {audio_ref}")
            playable_input_fingerprint = playable.get("input_fingerprint")
            if not isinstance(playable_input_fingerprint, str) or not re.fullmatch(
                r"[0-9a-f]{64}", playable_input_fingerprint
            ):
                record_pending(
                    f"{prefix} playable_clip.input_fingerprint is pending; old motion evidence "
                    "must not survive an input change",
                    allow_pending,
                    errors,
                    warnings,
                )
            elif (
                current_input_fingerprint is not None
                and playable_input_fingerprint != current_input_fingerprint
            ):
                errors.append(
                    f"{prefix} playable_clip.input_fingerprint is stale for the current inputs"
                )
            if playable.get("phone_reviewed") is not True:
                record_pending(
                    f"{prefix} playable_clip.phone_reviewed must be true",
                    allow_pending,
                    errors,
                    warnings,
                )
            else:
                phone_review_ref = playable.get("phone_review_ref")
                if not isinstance(phone_review_ref, str) or not phone_review_ref.strip():
                    record_pending(
                        f"{prefix} playable_clip.phone_review_ref must point to the review artifact",
                        allow_pending,
                        errors,
                        warnings,
                    )
                else:
                    phone_review_path, _ = resolve_project_reference(
                        project_root,
                        phone_review_ref,
                        f"{prefix} playable_clip.phone_review_ref",
                        errors,
                    )
                    if phone_review_path is not None and not phone_review_path.is_file():
                        errors.append(
                            f"{prefix} phone review artifact does not exist: {phone_review_ref}"
                        )
            checkpoint_paths = playable.get("checkpoint_paths")
            if not isinstance(checkpoint_paths, dict):
                record_pending(
                    f"{prefix} playable_clip.checkpoint_paths is pending",
                    allow_pending,
                    errors,
                    warnings,
                )
            else:
                for checkpoint_role in ["entry", "settled", "exit"]:
                    checkpoint_ref = checkpoint_paths.get(checkpoint_role)
                    checkpoint_path, _ = resolve_project_reference(
                        project_root,
                        checkpoint_ref,
                        f"{prefix} checkpoint {checkpoint_role}",
                        errors,
                    )
                    if checkpoint_path is not None and not checkpoint_path.is_file():
                        errors.append(
                            f"{prefix} checkpoint {checkpoint_role} does not exist: {checkpoint_ref}"
                        )
        checkpoints = scene.get("checkpoints")
        if not isinstance(checkpoints, list) or not {"entry", "settled", "exit"}.issubset(set(checkpoints)):
            errors.append(f"{prefix} checkpoints must include entry, settled, and exit")

        transitions = scene.get("transitions")
        if len(scenes) > 1:
            if not isinstance(transitions, dict):
                errors.append(f"{prefix} needs transitions.in and transitions.out")
            else:
                if index > 0 and not isinstance(transitions.get("in"), str):
                    errors.append(f"{prefix} transitions.in must name the incoming anchor or reset")
                if index < len(scenes) - 1 and not isinstance(transitions.get("out"), str):
                    errors.append(f"{prefix} transitions.out must name the outgoing anchor or reset")

        layers = scene.get("layers", [])
        if not isinstance(layers, list) or not layers:
            errors.append(f"{prefix} must contain independent layers")
            continue
        layer_ids: set[str] = set()
        has_semantic_role = False
        independent_start_frames: list[int | float] = []
        for layer_index, layer in enumerate(layers):
            lp = f"{prefix}.layer[{layer_index}]"
            if not isinstance(layer, dict):
                errors.append(f"{lp} must be an object")
                continue
            layer_id = layer.get("id")
            if not isinstance(layer_id, str) or not layer_id:
                errors.append(f"{lp} missing id")
            elif layer_id in layer_ids:
                errors.append(f"{prefix} duplicate layer id: {layer_id}")
            else:
                layer_ids.add(layer_id)
            role = layer.get("role")
            if role not in ROLES:
                errors.append(f"{lp} has invalid role: {role}")
            if role in SEMANTIC_ROLES:
                has_semantic_role = True
            source_kind = layer.get("source_kind")
            if source_kind not in SOURCE_KINDS:
                errors.append(f"{lp} has invalid source_kind: {source_kind}")
            asset_ref = layer.get("asset_ref")
            if asset_ref and asset_ref not in asset_by_id:
                errors.append(f"{lp} references unknown asset: {asset_ref}")
            exact_text = layer.get("exact_text")
            if exact_text and role not in {"type", "data", "annotation"}:
                errors.append(f"{lp} embeds exact_text in non-code visual role {role}")
            if source_kind == "generated" and role in {"source", "data"}:
                errors.append(f"{lp} cannot use generated media as evidence role {role}")
            transform = layer.get("settled")
            if not isinstance(transform, dict):
                errors.append(f"{lp} missing settled transform")
            entrance = layer.get("entrance")
            if not isinstance(entrance, dict) or not entrance.get("verb"):
                errors.append(f"{lp} missing entrance contract")
                continue
            start_frame = entrance.get("start_frame")
            duration_frames = entrance.get("duration_frames")
            if not isinstance(start_frame, (int, float)) or start_frame < 0:
                errors.append(f"{lp} entrance needs a non-negative start_frame")
            if not isinstance(duration_frames, (int, float)) or duration_frames <= 0:
                errors.append(f"{lp} entrance needs a positive duration_frames")
            if role in INDEPENDENT_MOTION_ROLES:
                if layer.get("motion_tier") not in MOTION_TIERS:
                    errors.append(f"{lp} needs motion_tier: primary, secondary, tertiary, or ambient")
                if isinstance(start_frame, (int, float)) and start_frame >= 0:
                    independent_start_frames.append(start_frame)

        if (
            len(independent_start_frames) >= 3
            and len(set(independent_start_frames)) == 1
            and not scene.get("intentional_group_entrance")
        ):
            warnings.append(
                f"{prefix} starts three or more independent actors together; "
                "record intentional_group_entrance or stagger them"
            )

        if scene.get("mode") != "metaphor-broll" and not has_semantic_role:
            warnings.append(f"{prefix} has no source/type/data/annotation layer")

        start_sec, end_sec = scene_timing(scene)
        if start_sec is not None and end_sec is not None and end_sec - start_sec >= 3.0:
            picture_actions = [
                layer
                for layer in layers
                if isinstance(layer, dict)
                and layer.get("role") not in {"type", "data", "annotation"}
                and isinstance(layer.get("entrance"), dict)
                and layer["entrance"].get("verb") not in {None, "hold", "static"}
            ]
            intentional_hold = scene.get("intentional_static_hold")
            has_hold_reason = (
                isinstance(intentional_hold, str) and bool(intentional_hold.strip())
            ) or (
                isinstance(intentional_hold, dict)
                and isinstance(intentional_hold.get("reason"), str)
                and bool(intentional_hold["reason"].strip())
            )
            if not picture_actions and not has_hold_reason:
                record_pending(
                    f"{prefix} risks caption-only motion: add a non-text picture action or "
                    "intentional_static_hold.reason",
                    allow_pending,
                    errors,
                    warnings,
                )

    if len(dominant_visuals) >= 4 and len(set(dominant_visuals)) == 1:
        errors.append("four or more scenes repeat one dominant visual grammar")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a Xingchen Vox branch. Strict mode requires a rendered hero frame, "
            "a decodable playable clip with audio, checkpoint frames, and phone review."
        )
    )
    parser.add_argument("project_root", type=Path)
    parser.add_argument(
        "--allow-pending",
        action="store_true",
        help=(
            "Validate an in-progress contract before render evidence exists. Missing hero/clip "
            "evidence becomes warnings; PASS with warnings is not visual approval."
        ),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    errors, warnings = validate(args.project_root, args.allow_pending)
    result = {"errors": errors, "warnings": warnings, "status": "fail" if errors else "pass"}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for warning in warnings:
            print(f"WARN: {warning}")
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Xingchen Vox branch validation: {result['status'].upper()} errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
