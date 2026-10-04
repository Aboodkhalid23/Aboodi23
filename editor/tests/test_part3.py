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


# ---------- real articles ----------

def test_article_beat_needs_url_quote_and_fallback_title():
    from .test_plan import build
    plan, clean = build()
    plan.beats[18].graphic = {"type": "article", "url": "https://x.com/a", "quote": "the line"}
    assert any("article" in e for e in validate_plan(plan, clean))
    plan.beats[18].graphic["title"] = "عنوان الخبر"
    assert validate_plan(plan, clean) == []


def test_article_screenshot_or_headline_fallback(tmp_path, monkeypatch):
    from editor.pipeline import articles
    ep = Episode(tmp_path / "ep").ensure()
    beats = [Beat(0, 5, "body", "graphic", graphic={"type": "article", "url": "https://ok.com/a", "quote": "q", "title": "ع"}),
             Beat(5, 10, "body", "graphic", graphic={"type": "article", "url": "https://blocked.com/b", "quote": "q",
                                                     "title": "عنوان", "outlet": "Reuters"})]
    plan = EditPlan({"primary": "vox"}, "", [], beats)

    def fake_shoot(url, quote, out):
        if "blocked" in url:
            return {"error": "net::ERR_BLOCKED"}
        out.write_bytes(b"png")
        return {"ok": True, "found": True, "rects": [[320, 200, 640, 40]], "width": 3200, "height": 2000, "site": "ok.com"}
    monkeypatch.setattr(articles, "shoot", fake_shoot)
    fb = articles.collect_articles(plan, ep)
    meta = json.loads((ep.assets / "article_0.json").read_text())
    assert meta["rects"] == [[0.1, 0.1, 0.2, 0.02]] and meta["url"] == "https://ok.com/a"
    assert fb[0]["beat"] == 1 and plan.beats[1].graphic == {"type": "headline", "outlet": "Reuters", "title": "عنوان",
                                                              "highlight": ""}


# ---------- archive footage ----------

class Archive:
    """Fake archive.org: one film, served as a real small mp4."""
    def __init__(self, video: bytes, commons_down=True):
        self.video, self.commons_down = video, commons_down

    def get(self, url, params=None, headers=None, timeout=None, stream=False):
        import requests
        if "commons.wikimedia.org" in url:
            if self.commons_down:
                raise requests.ConnectionError("429")
        if "advancedsearch" in url:
            return Data({"response": {"docs": [{"identifier": "oldfilm", "title": "Old Film"}]}})
        if "/metadata/" in url:
            return Data({"metadata": {}, "files": [{"name": "oldfilm.mp4", "format": "h.264", "size": "1000"}]})
        return Stream(self.video)


class Data:
    def __init__(self, d):
        self._d = d

    def json(self):
        return self._d

    def raise_for_status(self):
        pass


class Stream(Data):
    def __init__(self, content):
        super().__init__(None)
        self.content = content

    def iter_content(self, n):
        yield self.content

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_footage_from_the_archive_is_cut_to_the_beat_and_credited(tmp_path):
    from editor.pipeline.footage import collect_footage
    from editor.pipeline.media import probe
    film = tmp_path / "film.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=640x480:r=24:d=12", "-pix_fmt", "yuv420p",
                    str(film)], check=True)
    ep = Episode(tmp_path / "ep").ensure()
    plan = EditPlan({"primary": "vox"}, "", [], [Beat(0, 4, "body", "footage", query="factory", caption="مصنع"),
                                                Beat(4, 8, "body", "footage", query="factory", caption="مصنع")])
    fb, credits = collect_footage(plan, ep, session=Archive(film.read_bytes()))
    assert probe(ep.assets / "footage_0.mp4").duration == pytest.approx(4.5, abs=0.2)
    assert credits[0].startswith("Old Film — Internet Archive — Public domain")
    # the same film is not used twice in a row: the second beat falls back to its caption card
    assert fb[0]["beat"] == 1 and plan.beats[1].kind == "graphic" and plan.beats[1].graphic["text"] == "مصنع"



# ---------- end screen ----------

def test_end_screen_length_is_validated():
    from .test_plan import build
    plan, clean = build()
    plan.end_screen = 30
    assert any(e.startswith("end_screen") for e in validate_plan(plan, clean))
    plan.end_screen = 0
    assert validate_plan(plan, clean) == []


@pytest.mark.slow
def test_end_screen_is_appended_with_sound_running_to_the_end(tmp_path):
    from editor.pipeline.clean import clean
    from editor.pipeline.compose import compose
    from editor.pipeline.fetch import fetch
    from editor.pipeline.media import probe
    from editor.pipeline.transcribe import save_words
    from .conftest import make_talking_video
    from .test_clean import speech
    from .test_compose import stream_durations
    ep = Episode(tmp_path / "ep").ensure()
    fetch(str(make_talking_video(tmp_path / "t.mp4")), ep)
    save_words(speech((0, 4)), ep.transcript)
    total = round(clean(ep), 3)
    save_plan(EditPlan({"primary": "retro-collage"}, "", [], [Beat(0, total, "hook", "face")], end_screen=5), ep.plan)
    d = stream_durations(compose(ep))
    assert d["video"] == pytest.approx(total + 5, abs=0.1) and abs(d["video"] - d["audio"]) <= 0.1
    assert probe(ep.work / "end_screen.mp4").duration == pytest.approx(5, abs=0.05)


# ---------- presenter cut-out ----------

@pytest.mark.slow
def test_cutout_puts_the_scene_behind_and_keeps_length(tmp_path):
    """No person in a test pattern: the whole frame must become the background scene, at the right length."""
    from editor.pipeline.cutout import cutout_clip
    from editor.pipeline.media import probe
    face, bg, out = tmp_path / "f.mp4", tmp_path / "bg.png", tmp_path / "o.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=640x360:r=30:d=1", "-pix_fmt", "yuv420p",
                    str(face)], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0x2060C0:s=640x360", "-frames:v", "1",
                    str(bg)], check=True)
    cutout_clip(face, bg, out, 640, 360, 30, 45, ["-c:v", "libx264", "-pix_fmt", "yuv420p"], shift=0.1)
    assert probe(out).duration == pytest.approx(1.5, abs=0.05)          # held the last frame to fill 45 frames
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.5", "-i", str(out), "-frames:v", "1", "-vf",
                          "scale=1:1:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    r, g, b = raw[:3]
    assert b > 150 and r < 80   # mostly the blue background scene



# ---------- shorts ----------

def test_shorts_are_validated():
    from .test_plan import build
    plan, clean = build()
    plan.shorts = [{"from": 10, "to": 20, "title": "هوك"}]           # too short for a Short
    assert any(e.startswith("short 1") for e in validate_plan(plan, clean))
    plan.shorts = [{"from": 10, "to": 40}]                          # no title
    assert any(e.startswith("short 1") for e in validate_plan(plan, clean))
    plan.shorts = [{"from": 10, "to": 40, "title": "هوك"}]
    assert validate_plan(plan, clean) == []


def test_short_pieces_crop_faces_and_frame_graphics():
    from editor.pipeline.shorts import _pieces
    beats = [Beat(0, 5, "body", "face"), Beat(5, 10, "body", "graphic"), Beat(10, 15, "body", "face_punch"),
             Beat(15, 20, "body", "face_fx", fx="subscribe")]
    assert _pieces(beats, 3, 17) == [(3, 5, True), (5, 10, False), (10, 15, True), (15, 17, False)]
