import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from editor.pipeline.deliver import prepare_delivery
from editor.pipeline.paths import Episode
from editor.pipeline.plan import Beat, EditPlan, save_plan
from editor.pipeline.transcribe import save_words

from .test_clean import speech

REPO = Path(__file__).resolve().parents[2]


def cli(*args, env=None):
    return subprocess.run([sys.executable, "-m", "editor.pipeline", *map(str, args)], cwd=REPO,
                          capture_output=True, text=True, env={**os.environ, **(env or {})})


@pytest.mark.slow
def test_cli_prep_and_render_end_to_end(talking_video, tmp_path):
    ep = Episode(tmp_path / "ep")
    fake = tmp_path / "fake_transcript.json"
    save_words(speech((0, 4), (7, 12), (13, 20)), fake)  # cleans to 496 frames
    r = cli("prep", ep.root, "--source", talking_video, env={"EDITOR_FAKE_TRANSCRIPT": str(fake)})
    assert r.returncode == 0, r.stdout + r.stderr
    assert ep.plan_input.exists()
    kinds = ["face", "face_zoom_in", "image", "face_zoom_out", "graphic", "face", "face_zoom_in", "face_framed"]
    beats = [Beat(2.0 * i, 2.0 * (i + 1), "hook", k) for i, k in enumerate(kinds)]
    beats[-1].end = 496 / 30
    beats[2].query = "Evergrande Group headquarters"
    beats[4].graphic = {"type": "number", "value": 300, "label": "مليار دولار"}
    save_plan(EditPlan({"primary": "vox", "sections": []}, "اختبار", [], beats), ep.plan)
    r = cli("render", ep.root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert ep.final.exists()


def test_cli_validate_exit_code(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    ep.cuts.write_text("[[0, 10]]")
    save_plan(EditPlan({"primary": "vox", "sections": []}, "", [], [Beat(0, 9, "hook", "face")]), ep.plan)
    r = cli("validate", ep.root)
    assert r.returncode == 2
    assert "beat 0:" in r.stdout


def test_cli_bad_source_is_arabic(tmp_path):
    r = cli("fetch", tmp_path / "ep", "--source", "https://example.com/v.mp4")
    assert r.returncode == 1
    assert "الرابط مو رابط گوگل درايف" in r.stdout


def test_prepare_delivery_recompresses(talking_video, tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    shutil.copyfile(talking_video, ep.final)
    size_mb = ep.final.stat().st_size / 1e6
    assert prepare_delivery(ep, max_mb=size_mb * 10) == ep.final
    out = prepare_delivery(ep, max_mb=size_mb * 0.8)
    assert out.name == "final_small.mp4"
    assert out.stat().st_size < ep.final.stat().st_size
