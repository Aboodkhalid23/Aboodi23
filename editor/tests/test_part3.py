"""Round 3: variety of looks, colour grade, AI music bed, CC0 sound library, source check."""
import json
import subprocess

import pytest

from editor.pipeline.grade import LOOKS, correction, grade_filter
from editor.pipeline.music import audio_duration, bed_filter, music_fetch, music_jobs, segments
from editor.pipeline.paths import Episode
from editor.pipeline.plan import Beat, EditPlan, save_plan, validate_plan
from editor.pipeline.sfx import names, sfx_path, variants
from editor.pipeline.styles import load_style
from editor.pipeline.vary import assign_variety

from .test_part2 import OneFile, Serve


def tone(path, f=330, d=3.0):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=f={f}:r=48000:d={d}",
                    "-c:a", "libmp3lame", str(path)], check=True)
    return path


# ---------- variety ----------

def test_pictures_and_text_cards_never_repeat_back_to_back():
    style = load_style("retro-collage")
    beats = []
    for i in range(8):
        beats.append(Beat(i * 10, i * 10 + 5, "body", "image", query="x", caption="س"))
        beats.append(Beat(i * 10 + 5, i * 10 + 10, "body", "graphic", graphic={"type": "text", "text": "ن"}))
    plan = assign_variety(EditPlan({"primary": "retro-collage"}, "", [], beats), style)
    looks = [b.treatment for b in plan.beats if b.kind == "image"]
    texts = [b.graphic["variant"] for b in plan.beats if b.kind == "graphic"]
    assert all(a != b for a, b in zip(looks, looks[1:])) and set(looks) == set(style.image_treatments)
    assert all(a != b for a, b in zip(texts, texts[1:])) and set(texts) == set(style.text_variants)


def test_variety_keeps_choices_the_plan_made():
    style = load_style("retro-collage")
    beats = [Beat(0, 5, "body", "image", treatment="crt"), Beat(5, 10, "body", "ai_image"),
             Beat(10, 15, "body", "graphic", graphic={"type": "text", "text": "x", "variant": "ransom"})]
    plan = assign_variety(EditPlan({"primary": "retro-collage"}, "", [], beats), style)
    assert plan.beats[0].treatment == "crt" and plan.beats[1].treatment not in (None, "crt")
    assert plan.beats[2].graphic["variant"] == "ransom"


# ---------- colour ----------

STATS = {"YLOW": 24.0, "YAVG": 104.0, "YHIGH": 201.0, "UAVG": 127.7, "VAVG": 128.0, "SATAVG": 3.7}


def test_correction_is_gentle_and_bounded():
    c = correction(STATS)
    assert c.startswith("colorlevels=")
    dark = correction({**STATS, "YAVG": 40.0, "YLOW": 16.0, "YHIGH": 120.0, "VAVG": 150.0})
    gamma = float(dark.split("eq=gamma=")[1].split(",")[0])
    assert gamma <= 1.15 ** 0.5 + 1e-3                                  # never a wild exposure jump
    assert "colorbalance=rm=-0.060" in dark                              # red cast pulled back, capped


@pytest.mark.parametrize("look", list(LOOKS))
def test_every_look_runs(tmp_path, look):
    out = tmp_path / f"{look}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=0.5",
                    "-vf", "null" + grade_filter(correction(STATS), look), "-pix_fmt", "yuv420p", str(out)], check=True)
    assert out.stat().st_size > 0


def test_unknown_look_is_rejected_by_validator():
    from .test_plan import build
    plan, clean = build()
    plan.grade = "cinematic"                 # film looks are gone: natural colours only
    assert any(e.startswith("grade:") for e in validate_plan(plan, clean))
    plan.grade, plan.beats[3].grade = None, "none"
    assert validate_plan(plan, clean) == []


# ---------- music ----------

def music_episode(tmp_path, cues):
    ep = Episode(tmp_path / "ep").ensure()
    save_plan(EditPlan({"primary": "retro-collage"}, "", [], [Beat(0, 100, "body", "face")], music=cues), ep.plan)
    return ep


def test_music_jobs_pick_duration_and_instrumental(tmp_path):
    ep = music_episode(tmp_path, [{"t": 0, "prompt": "tense pulse", "mood": "mysterious"},
                                  {"t": 70, "prompt": "hopeful piano"}])
    jobs = music_jobs(ep, 300.0)
    assert [(j["cue"], j["seconds"], j["settings"]["duration"]) for j in jobs] == [(0, 70.0, "90"), (1, 230.0, "180")]
    assert jobs[0]["settings"]["song_type"] == "instrumental" and "no vocals" in jobs[0]["prompt"].lower()
    assert jobs[0]["settings"]["song_mood"] == "mysterious" and not jobs[0]["done"]


def test_music_cues_validated():
    from .test_plan import build
    plan, clean = build()
    plan.music = [{"t": 5, "prompt": "x"}]
    assert "music 0" in validate_plan(plan, clean)[0]
    plan.music = [{"t": 0, "prompt": "x"}, {"t": 10, "prompt": "y"}]
    assert "20" in validate_plan(plan, clean)[0]
    plan.music = [{"t": 0, "prompt": "x"}, {"t": 40, "prompt": "y"}]
    assert validate_plan(plan, clean) == []


def test_music_fetch_checks_it_is_audio(tmp_path):
    ep = music_episode(tmp_path, [{"t": 0, "prompt": "x"}])
    good = tone(tmp_path / "t.mp3").read_bytes()
    out = music_fetch(ep, 0, "https://cdn/x.mp3", session=Serve(OneFile(good, "audio/mpeg")))
    assert out.name == "music_0.mp3" and audio_duration(out) == pytest.approx(3, abs=0.1)
    from editor.pipeline.media import MediaError
    with pytest.raises(MediaError):
        music_fetch(ep, 0, "https://cdn/x", session=Serve(OneFile(b"<html>", "text/html")))


def test_short_track_is_looped_with_crossfades_to_fill_its_segment(tmp_path):
    t = tone(tmp_path / "a.mp3", d=5.0)
    args, graph = bed_filter([(0, t, 0.0, 12.0)], 0, -24)
    assert args.count("-i") == 4 and graph.count("acrossfade") == 3   # 5 s track, 2 s overlaps → 4 copies ≥ 14 s
    out = tmp_path / "bed.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args, "-filter_complex", graph, "-map", "[mus]", str(out)], check=True)
    assert audio_duration(out) == pytest.approx(14, abs=0.2)


def test_segments_cover_the_timeline():
    plan = EditPlan({"primary": "vox"}, "", [], [], music=[{"t": 0, "prompt": "a"}, {"t": 50, "prompt": "b"}])
    assert segments(plan, 120) == [(0, 0, 50), (1, 50, 120)]


# ---------- sounds ----------

def test_cc0_library_has_takes_and_synth_fills_the_rest():
    assert {"click", "pop", "ding", "hit", "glitch", "tick", "switch", "whoosh", "swoosh", "riser", "boom"} <= set(names())
    assert len(variants("pop")) >= 2 and variants("whoosh") == []
    assert sfx_path("pop", 0) != sfx_path("pop", 1)
    assert sfx_path("pop", 0) == sfx_path("pop", len(variants("pop")))   # wraps around


# ---------- source check ----------

class FakeModel:
    def transcribe(self, path, **kw):
        class S:
            text = " هلا بيكم اليوم "
        return [S()], None


def test_check_reports_length_frames_and_first_words(tmp_path):
    from editor.pipeline.check import check_source
    from editor.pipeline.fetch import fetch
    from .conftest import make_talking_video
    ep = Episode(tmp_path / "ep").ensure()
    fetch(str(make_talking_video(tmp_path / "talk.mp4")), ep)
    d = check_source(ep, model=FakeModel())
    assert d["length"] == "0:20" and d["first_words"] == "هلا بيكم اليوم" and d["name"] == "talk.mp4"
    assert (ep.work / "source_check.jpg").exists()
    assert json.loads((ep.work / "source_check.json").read_text())["width"] == 1280


def test_new_link_is_fetched_again_not_the_old_video(tmp_path):
    from editor.pipeline.fetch import fetch
    from editor.pipeline.media import probe
    from .conftest import make_talking_video
    from .test_fetch import synth
    ep = Episode(tmp_path / "ep").ensure()
    fetch(str(make_talking_video(tmp_path / "old.mp4")), ep)
    assert probe(ep.source).duration == pytest.approx(20, abs=0.1)
    fetch(str(synth(tmp_path / "new.mp4", size="1280x720", dur=3)), ep)
    assert probe(ep.source).duration == pytest.approx(3, abs=0.1)
    assert json.loads((ep.work / "source.json").read_text())["name"] == "new.mp4"


def test_natural_grade_has_no_vignette_grain_or_colour_cast():
    f = grade_filter(correction(STATS), "natural")
    assert "vignette" not in f and "noise" not in f and "colorbalance=rs" not in f and "curves" not in f
    assert grade_filter(correction(STATS), "none") == ""


# ---------- subtitles ----------

def test_srt_follows_the_final_timeline_with_teaser_first(tmp_path):
    from editor.pipeline.subtitles import write_srt
    from editor.pipeline.transcribe import Word, save_words
    ep = Episode(tmp_path / "ep").ensure()
    save_words([Word("شركة", 0.0, 0.5), Word("كبيرة", 0.5, 1.0), Word("انهارت", 3.0, 3.6), Word("فجأة", 3.6, 4.2)],
               ep.clean_words)
    save_plan(EditPlan({"primary": "vox"}, "", [(3.0, 4.2)], [Beat(0, 5.4, "hook", "face")]), ep.plan)
    text = write_srt(ep).read_text(encoding="utf-8")
    blocks = [b.splitlines() for b in text.strip().split("\n\n")]
    assert blocks[0][1:] == ["00:00:00,000 --> 00:00:01,200", "انهارت فجأة"]          # the teaser shot
    assert blocks[1][1:] == ["00:00:01,200 --> 00:00:02,200", "شركة كبيرة"]           # then the episode
    assert blocks[2][1] == "00:00:04,200 --> 00:00:05,400"


def test_long_phrases_split_into_short_lines():
    from editor.pipeline.subtitles import MAX_CHARS, cues
    from editor.pipeline.transcribe import Word
    words = [Word("كلمة" + str(i), i * 0.3, i * 0.3 + 0.28) for i in range(40)]
    out = cues(words)
    assert len(out) > 3 and all(len(t) <= MAX_CHARS for _, _, t in out)


# ---------- custom scenes ----------

def test_custom_scene_must_exist_and_maps_to_its_composition(tmp_path):
    from editor.pipeline.graphics import custom_scenes, graphic_job, write_registry, CUSTOM_DIR
    from .test_plan import build
    plan, clean = build()
    plan.beats[18].graphic = {"type": "custom", "scene": "NoSuchScene"}
    assert any("NoSuchScene" in e for e in validate_plan(plan, clean))
    plan.beats[18].graphic = {"type": "custom", "scene": "StepFlow", "steps": ["أ", "ب"]}
    assert validate_plan(plan, clean) == []
    write_registry()
    assert "StepFlow" in custom_scenes() and "['StepFlow'" in (CUSTOM_DIR / "registry.ts").read_text()
    bundle = tmp_path / "b"
    (bundle / "public").mkdir(parents=True)
    job = graphic_job(plan.beats[18], load_style("vox"), tmp_path / "x.mp4", bundle=bundle)
    assert job.comp == "custom-StepFlow" and job.props["steps"] == ["أ", "ب"] and "scene" not in job.props
