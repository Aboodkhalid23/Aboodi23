from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
INIT = SKILL / "scripts" / "init_vox_branch.py"
VALIDATE = SKILL / "scripts" / "validate_vox_branch.py"
BUILD = SKILL / "scripts" / "build_scene_evidence.py"
LOCK = SKILL / "scripts" / "lock_vox_inputs.py"


def valid_scene() -> dict:
    return {
        "scene_id": "s01",
        "beat_id": "b01",
        "mode": "editorial-explainer",
        "knowledge_change": "A small action propagates into a system-wide effect.",
        "visual_proposition": "One red paper dot triggers a field of twenty-four cut-paper echoes.",
        "dominant_visual": "propagation-field",
        "motion_action": "build",
        "hero_frame": {
            "description": "One dot on the left, a visible spreading field on the right.",
            "focal_order": ["trigger dot", "spreading field", "thesis label"],
            "subtitle_safe_region": "bottom 173 pixels remain clear",
        },
        "layers": [
            {
                "id": "substrate",
                "role": "plate",
                "source_kind": "code-native",
                "settled": {"x": 960, "y": 540, "scale": 1, "rotation": 0},
                "entrance": {"verb": "hold", "start_frame": 0, "duration_frames": 1},
            },
            {
                "id": "thesis",
                "role": "type",
                "source_kind": "code-native",
                "exact_text": "不是加法，是扩散",
                "settled": {"x": 1300, "y": 820, "scale": 1, "rotation": -1},
                "entrance": {"verb": "slap", "start_frame": 60, "duration_frames": 14},
            },
        ],
        "camera": {"kind": "locked", "from": 1, "to": 1},
        "timing": {"start_sec": 0.0, "end_sec": 4.0},
        "checkpoints": ["entry", "settled", "exit"],
    }


def write_lean_state(root: Path, *, end_sec: float = 4.0, revision: int = 3) -> None:
    state = {
        "metadata": {
            "project_id": "smoke",
            "format": {"width": 1920, "height": 1080, "fps": 30},
        },
        "script": {"timeline_revision": revision},
        "scenes": [
            {
                "scene_id": "s01",
                "beat_id": "b01",
                "timing": {"start_sec": 0.0, "end_sec": end_sec},
            }
        ],
    }
    (root / "project-state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class ScriptTests(unittest.TestCase):
    def test_initialize_then_validate_contract(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            init = subprocess.run(
                [sys.executable, str(INIT), str(root), "--slug", "smoke"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(init.returncode, 0, init.stderr)

            empty = subprocess.run(
                [sys.executable, str(VALIDATE), str(root)],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(empty.returncode, 0)
            self.assertIn("has no scenes", empty.stdout)

            spec_path = root / "visual" / "vox" / "scene-spec.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["scenes"] = [valid_scene()]
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

            valid = subprocess.run(
                [sys.executable, str(VALIDATE), str(root), "--allow-pending"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
            self.assertIn("hero_frame.path is pending", valid.stdout)
            self.assertIn("playable_clip is pending", valid.stdout)
            self.assertIn("risks caption-only motion", valid.stdout)

    def test_rejects_exact_text_in_cutout(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subprocess.run(
                [sys.executable, str(INIT), str(root), "--slug", "bad"],
                check=True,
                text=True,
                capture_output=True,
            )
            scene = valid_scene()
            scene["layers"][1]["role"] = "cutout"
            spec_path = root / "visual" / "vox" / "scene-spec.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["scenes"] = [scene]
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

            invalid = subprocess.run(
                [sys.executable, str(VALIDATE), str(root), "--allow-pending"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("embeds exact_text", invalid.stdout)

    def test_rejects_missing_code_native_fragment(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subprocess.run(
                [sys.executable, str(INIT), str(root), "--slug", "fragment"],
                check=True,
                text=True,
                capture_output=True,
            )
            code_path = root / "visual" / "vox" / "media" / "code" / "hero.html"
            code_path.parent.mkdir(parents=True, exist_ok=True)
            code_path.write_text('<svg><g id="real-fragment"></g></svg>', encoding="utf-8")

            assets_path = root / "visual" / "vox" / "assets.json"
            assets = json.loads(assets_path.read_text(encoding="utf-8"))
            assets["assets"] = [
                {
                    "id": "substrate",
                    "role": "plate",
                    "source_kind": "code-native",
                    "path": "visual/vox/media/code/hero.html#missing-fragment",
                    "status": "reviewed",
                }
            ]
            assets_path.write_text(
                json.dumps(assets, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            scene = valid_scene()
            scene["layers"][0]["asset_ref"] = "substrate"
            spec_path = root / "visual" / "vox" / "scene-spec.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["scenes"] = [scene]
            spec_path.write_text(
                json.dumps(spec, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            invalid = subprocess.run(
                [sys.executable, str(VALIDATE), str(root), "--allow-pending"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("fragment does not exist", invalid.stdout)

    def test_strict_mode_requires_rendered_review_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subprocess.run(
                [sys.executable, str(INIT), str(root), "--slug", "strict"],
                check=True,
                text=True,
                capture_output=True,
            )
            spec_path = root / "visual" / "vox" / "scene-spec.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["scenes"] = [valid_scene()]
            spec_path.write_text(
                json.dumps(spec, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            invalid = subprocess.run(
                [sys.executable, str(VALIDATE), str(root)],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("hero_frame.path is pending", invalid.stdout)
            self.assertIn("playable_clip is pending", invalid.stdout)

    def test_rejects_scene_timing_drift_from_lean_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subprocess.run(
                [sys.executable, str(INIT), str(root), "--slug", "smoke"],
                check=True,
                text=True,
                capture_output=True,
            )
            spec_path = root / "visual" / "vox" / "scene-spec.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["project"]["timeline_revision"] = 3
            spec["scenes"] = [valid_scene()]
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
            write_lean_state(root, end_sec=5.0)

            invalid = subprocess.run(
                [sys.executable, str(VALIDATE), str(root), "--allow-pending"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("timing drifts from project-state", invalid.stdout)

    def test_scene_evidence_plan_uses_synced_state_and_spec(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subprocess.run(
                [sys.executable, str(INIT), str(root), "--slug", "smoke"],
                check=True,
                text=True,
                capture_output=True,
            )
            master = root / "renders" / "master.mp4"
            master.parent.mkdir(parents=True, exist_ok=True)
            master.write_bytes(b"plan-only fixture")

            spec_path = root / "visual" / "vox" / "scene-spec.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["project"]["timeline_revision"] = 3
            spec["project"]["source_master"] = "renders/master.mp4"
            spec["scenes"] = [valid_scene()]
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
            write_lean_state(root)

            locked = subprocess.run(
                [sys.executable, str(LOCK), str(root), "--write"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(locked.returncode, 0, locked.stdout + locked.stderr)

            planned = subprocess.run(
                [
                    sys.executable,
                    str(BUILD),
                    str(root),
                    "visual/vox/evidence-v1",
                    "--plan-only",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
            plan = json.loads(planned.stdout)
            self.assertEqual(plan["timeline_revision"], 3)
            self.assertEqual(len(plan["source_master_sha256"]), 64)
            self.assertEqual(len(plan["timeline_fingerprint"]), 64)
            self.assertEqual(len(plan["evidence_input_fingerprint"]), 64)
            self.assertEqual(plan["scenes"][0]["scene_id"], "s01")
            self.assertFalse((root / "visual" / "vox" / "evidence-v1").exists())

    def test_input_lock_detects_changed_audio_and_master(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subprocess.run(
                [sys.executable, str(INIT), str(root), "--slug", "identity"],
                check=True,
                text=True,
                capture_output=True,
            )
            master = root / "renders" / "master.mp4"
            master.parent.mkdir(parents=True, exist_ok=True)
            master.write_bytes(b"master-v1")
            audio = root / "audio" / "narration.wav"
            audio.parent.mkdir(parents=True, exist_ok=True)
            audio.write_bytes(b"audio-v1")

            spec_path = root / "visual" / "vox" / "scene-spec.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["project"]["timeline_revision"] = 1
            spec["project"]["source_master"] = "renders/master.mp4"
            scene = valid_scene()
            scene["playable_clip"] = {"audio_ref": "audio/narration.wav"}
            spec["scenes"] = [scene]
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

            locked = subprocess.run(
                [sys.executable, str(LOCK), str(root), "--write"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(locked.returncode, 0, locked.stdout + locked.stderr)
            checked = subprocess.run(
                [sys.executable, str(LOCK), str(root), "--check"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

            audio.write_bytes(b"audio-v2")
            stale_audio = subprocess.run(
                [sys.executable, str(LOCK), str(root), "--check"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(stale_audio.returncode, 0)
            self.assertIn("timeline_fingerprint", stale_audio.stdout)
            self.assertIn("evidence_input_fingerprint", stale_audio.stdout)

            subprocess.run(
                [sys.executable, str(LOCK), str(root), "--write"],
                check=True,
                text=True,
                capture_output=True,
            )
            master.write_bytes(b"master-v2")
            stale_master = subprocess.run(
                [sys.executable, str(LOCK), str(root), "--check"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(stale_master.returncode, 0)
            self.assertIn("source_master_sha256", stale_master.stdout)
            self.assertIn("evidence_input_fingerprint", stale_master.stdout)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_rejects_gross_shared_audio_duration_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subprocess.run(
                [sys.executable, str(INIT), str(root), "--slug", "duration"],
                check=True,
                text=True,
                capture_output=True,
            )
            master = root / "renders" / "master.mp4"
            master.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=black:s=1920x1080:r=30:d=4",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:duration=4",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-shortest",
                    str(master),
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            audio = root / "audio" / "old-narration.wav"
            audio.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=330:duration=8",
                    str(audio),
                ],
                check=True,
                text=True,
                capture_output=True,
            )

            spec_path = root / "visual" / "vox" / "scene-spec.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["project"]["timeline_revision"] = 1
            spec["project"]["source_master"] = "renders/master.mp4"
            scene = valid_scene()
            scene["playable_clip"] = {
                "path": "renders/master.mp4",
                "audio_ref": "audio/old-narration.wav",
                "phone_reviewed": False,
            }
            spec["scenes"] = [scene]
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
            subprocess.run(
                [sys.executable, str(LOCK), str(root), "--write"],
                check=True,
                text=True,
                capture_output=True,
            )
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["scenes"][0]["playable_clip"]["input_fingerprint"] = spec["project"][
                "evidence_input_fingerprint"
            ]
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

            invalid = subprocess.run(
                [sys.executable, str(VALIDATE), str(root), "--allow-pending"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("shared playable audio duration is grossly out of sync", invalid.stdout)


if __name__ == "__main__":
    unittest.main()
