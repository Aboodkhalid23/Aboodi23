"""Part 2: AI scenes, real photos of named people/companies, YouTuber moves, transitions and sound."""
import json
import subprocess

import pytest
import requests

from editor.pipeline.ai import ai_fetch, ai_jobs, log_spend, spent
from editor.pipeline.align import align_words
from editor.pipeline.entities import entity_image, entity_tokens, fetch_entities, load_entities
from editor.pipeline.media import MediaError, probe
from editor.pipeline.paths import Episode
from editor.pipeline.plan import Beat, EditPlan, save_plan
from editor.pipeline.sfx import RECIPES, beat_cues, sfx_path
from editor.pipeline.transcribe import hotwords

from .test_clean import phrase, speech
from .test_compose import corner_rgb, stream_durations


def centre_rgb(path, t):
    """Average colour of the middle of the frame (the vignette darkens corners on purpose)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1",
                          "-vf", "crop=iw/3:ih/3,scale=1:1:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return tuple(raw[:3])


def png_bytes(color="red", size="64x36") -> bytes:
    return subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"color=c={color}:s={size}", "-frames:v", "1",
                           "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout


def write_entities(ep, items):
    (ep.edit / "entities.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


MUSK = {"id": "musk", "name": "إيلون ماسك", "en": "Elon Musk", "kind": "person", "role": "مؤسس تسلا"}


# ---------- sound ----------

def test_every_sfx_renders_at_the_same_peak():
    for name in RECIPES:
        p = sfx_path(name)
        log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(p), "-af", "volumedetect", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        peak = float(log.split("max_volume: ")[1].split(" dB")[0])
        assert -4.5 <= peak <= -1.5, (name, peak)


def test_unknown_sfx_is_a_clear_error():
    with pytest.raises(KeyError):
        sfx_path("explosion")


def test_beat_cues_from_sfx_transitions_and_special_beats():
    beats = [Beat(0, 2, "hook", "face"), Beat(2, 4, "hook", "face_punch", transition="zoom"),
             Beat(4, 6, "hook", "graphic", sfx="riser"), Beat(6, 10, "hook", "face_fx", fx="subscribe")]
    cues = beat_cues(beats, {"fx:subscribe": [(1.6, "click")]})
    assert cues == [(2, "whoosh"), (4, "riser"), (7.6, "click")]


# ---------- AI scenes ----------

def ai_episode(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    beats = [Beat(0, 2, "hook", "face"),
             Beat(2, 4, "hook", "ai_image", prompt="1970s boardroom.", caption="اجتماع"),
             Beat(4, 8.5, "body", "ai_video", prompt="oil refinery at night", caption="مصفاة")]
    save_plan(EditPlan({"primary": "retro-collage", "sections": []}, "", [], beats, ai_budget=10), ep.plan)
    return ep


def test_ai_jobs_add_the_style_suffix_and_track_done(tmp_path):
    ep = ai_episode(tmp_path)
    jobs = ai_jobs(ep)
    assert [(j.beat, j.kind, j.model, j.duration, j.done) for j in jobs] == [
        (1, "ai_image", "nano_banana", 0, False), (2, "ai_video", "veo3_1_lite", 4, False)]
    assert jobs[0].prompt.startswith("1970s boardroom. vintage engraving")
    (ep.assets / "ai_1.png").write_bytes(png_bytes())
    assert ai_jobs(ep)[0].done and json.loads((ep.work / "ai_jobs.json").read_text())[0]["done"]


class OneFile:
    def __init__(self, content, ctype):
        self.content, self.headers, self.status_code = content, {"Content-Type": ctype}, 200

    def raise_for_status(self):
        pass


class Serve:
    def __init__(self, resp=None, fail=False):
        self.resp, self.fail = resp, fail

    def get(self, url, **kw):
        if self.fail:
            raise requests.ConnectionError("403 blocked")
        return self.resp


def test_ai_fetch_saves_and_checks_the_file(tmp_path):
    ep = ai_episode(tmp_path)
    (ep.assets / "ai_1.jpg").write_bytes(b"old")
    out = ai_fetch(ep, 1, "https://cdn.example/x?sig=1", session=Serve(OneFile(png_bytes(), "image/png")))
    assert out.name == "ai_1.png" and not (ep.assets / "ai_1.jpg").exists()
    assert probe(out).width == 64


def test_ai_fetch_rejects_html_and_network_errors(tmp_path):
    ep = ai_episode(tmp_path)
    with pytest.raises(MediaError, match="مو صورة"):
        ai_fetch(ep, 1, "https://cdn.example/x", session=Serve(OneFile(b"<html>denied</html>", "text/html")))
    assert not list(ep.assets.glob("ai_1.*"))
    with pytest.raises(MediaError, match="ما گدرت"):
        ai_fetch(ep, 1, "https://cdn.example/x", session=Serve(fail=True))


def test_ledger_adds_up(tmp_path):
    ep = ai_episode(tmp_path)
    log_spend(ep, 1, "nano_banana", 0.25, "job-1")
    assert log_spend(ep, 2, "veo3_1_lite", 6) == 6.25 == spent(ep)


# ---------- real photos of people / companies ----------

class Wiki:
    """Fake Wikidata + Commons."""
    def __init__(self, claims, licence="CC BY-SA 4.0", search=None):
        self.claims, self.licence, self.search, self.urls = claims, licence, search, []

    def get(self, url, params=None, headers=None, timeout=None):
        self.urls.append((url, params))
        if params and params.get("action") == "wbsearchentities":
            return Data({"search": [{"id": "Q317521"}]})
        if params and params.get("action") == "wbgetclaims":
            return Data({"claims": self.claims})
        if params and params.get("prop") == "imageinfo" and "titles" in params:
            return Data({"query": {"pages": {"1": {"imageinfo": [{"descriptionurl": "https://c/File:x",
                         "extmetadata": {"LicenseShortName": {"value": self.licence}, "Artist": {"value": "Gage"}}}]}}}})
        if params and params.get("generator") == "search":
            return Data(self.search or {})
        return OneFile(png_bytes(), "image/png")


class Data(OneFile):
    def __init__(self, data):
        super().__init__(b"", "application/json")
        self._d = data

    def json(self):
        return self._d


def claim(value):
    return [{"mainsnak": {"datavalue": {"value": value}}}]


def test_person_photo_from_wikidata(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    write_entities(ep, [MUSK])
    s = Wiki({"P18": claim("Elon Musk 2024.jpg")})
    found, missing = fetch_entities(ep, session=s)
    assert found == ["musk"] and missing == []
    assert entity_image(ep, "musk").name == "entity_musk.png"
    assert any("Special:FilePath/Elon_Musk_2024.jpg" in u for u, _ in s.urls)
    credits = json.loads((ep.work / "entity_credits.json").read_text())
    assert "Gage" in credits["musk"] and "CC BY-SA 4.0" in credits["musk"]


def test_company_prefers_logo_and_known_qid_skips_search(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    write_entities(ep, [{"id": "tesla", "name": "تسلا", "en": "Tesla", "kind": "company", "qid": "Q478214"}])
    s = Wiki({"P18": claim("Factory.jpg"), "P154": claim("Tesla logo.svg")}, licence="Public domain")
    fetch_entities(ep, session=s)
    assert not any(p and p.get("action") == "wbsearchentities" for _, p in s.urls)
    assert any("Tesla_logo.svg" in u for u, _ in s.urls)


def test_non_free_photo_is_skipped_and_reported(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    write_entities(ep, [MUSK])
    found, missing = fetch_entities(ep, session=Wiki({"P18": claim("x.jpg")}, licence="Fair use"))
    assert found == [] and "Elon Musk" in missing[0] and "qid" in missing[0]


def test_names_feed_whisper_and_alignment(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    (ep.edit / "vocab.txt").write_text("إيفرغراند\nتسلا\n", encoding="utf-8")
    write_entities(ep, [MUSK])
    assert hotwords(ep) == "إيفرغراند تسلا إيلون ماسك Elon Musk"
    assert entity_tokens(ep) == {"ايلون", "ماسك"}
    assert load_entities(ep)["musk"]["role"] == "مؤسس تسلا"


def test_mispronounced_name_is_corrected_from_the_script():
    heard = phrase("قال موسك انه", 0, 3)       # he says "موسك", the script says "إيلون ماسك"
    script = ["قال", "إيلون", "ماسك", "انه"]
    plain, _ = align_words(heard, script)
    assert [w.text for w in plain] == ["قال", "موسك", "انه"]          # too different for normal words
    report = []
    fixed, _ = align_words(heard, script, names={"ايلون", "ماسك"}, report=report)
    assert [w.text for w in fixed] == script                          # but the script's name wins
    _, _ = align_words(heard, script, report=report)
    assert report and "موسك" in report[0] and "إيلون ماسك" in report[0]


# ---------- transitions (ffmpeg filters) ----------

@pytest.mark.parametrize("name", ["zoom", "flash", "whip", "glitch"])
def test_transition_filters_run_and_keep_size(tmp_path, name):
    from editor.pipeline.compose import Canvas, _transition_filter
    cv = Canvas(320, 180, 30, tmp_path, [])
    out = tmp_path / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=1",
                    "-vf", "null" + _transition_filter(name, cv), "-pix_fmt", "yuv420p", str(out)], check=True)
    info = probe(out)
    assert (info.width, info.height) == (320, 180) and info.duration == pytest.approx(1, abs=0.05)


def test_flash_starts_white(tmp_path):
    from editor.pipeline.compose import Canvas, _transition_filter
    out = tmp_path / "f.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=640x360:r=30:d=1",
                    "-vf", "null" + _transition_filter("flash", Canvas(640, 360, 30, tmp_path, [])),
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    assert min(corner_rgb(out, 0)) > 200 and max(corner_rgb(out, 0.5)) < 30


# ---------- everything together (Remotion + ffmpeg) ----------

@pytest.fixture(scope="module")
def part2(tmp_path_factory):
    from editor.pipeline.clean import clean
    from editor.pipeline.compose import compose
    from editor.pipeline.fetch import fetch
    from editor.pipeline.transcribe import save_words
    from .conftest import make_talking_video
    tmp = tmp_path_factory.mktemp("part2")
    ep = Episode(tmp / "ep").ensure()
    fetch(str(make_talking_video(tmp / "talking.mp4")), ep)
    save_words(speech((0, 4), (7, 12), (13, 20)), ep.transcript)
    total = round(clean(ep), 3)
    (ep.assets / "ai_2.png").write_bytes(png_bytes("blue", "1280x720"))
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=1280x720:r=24:d=1",
                    "-pix_fmt", "yuv420p", str(ep.assets / "ai_3.mp4")], check=True)
    (ep.assets / "entity_musk.png").write_bytes(png_bytes("green", "400x400"))
    write_entities(ep, [MUSK])
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=f=220:r=48000:d=3",
                    "-c:a", "pcm_s16le", str(ep.assets / "music.wav")], check=True)
    beats = [Beat(0, 2, "hook", "face"), Beat(2, 4, "hook", "face_punch", transition="zoom"),
             Beat(4, 6, "hook", "ai_image", prompt="p", caption="صورة", treatment="ken_burns"),
             Beat(6, 8, "hook", "ai_video", prompt="p", caption="فيديو", transition="flash"),
             Beat(8, 10, "hook", "ai_image", prompt="p", caption="ناقصة"),
             Beat(10, 12, "hook", "entity", entity="musk"),
             Beat(12, total, "hook", "face_fx", fx="subscribe", stickers=[{"type": "stamp", "text": "حقيقي", "at": 0.5}])]
    save_plan(EditPlan({"primary": "retro-collage", "sections": []}, "", [], beats), ep.plan)
    compose(ep)
    return ep, total


@pytest.mark.slow
def test_part2_duration_and_sync(part2):
    ep, total = part2
    d = stream_durations(ep.final)
    assert d["video"] == pytest.approx(total, abs=0.1) and abs(d["video"] - d["audio"]) <= 0.1


@pytest.mark.slow
def test_ai_image_and_looped_ai_video_are_on_screen(part2):
    ep, _ = part2
    r, g, b = centre_rgb(ep.final, 5.0)       # blue still, ken burns
    assert b > 150 and r < 80
    r, g, b = centre_rgb(ep.final, 7.6)       # red 1 s clip, looped to fill 2 s
    assert r > 150 and b < 80


@pytest.mark.slow
def test_missing_ai_scene_falls_back_to_caption_card(part2):
    ep, _ = part2
    r, g, b = corner_rgb(ep.final, 9.0)       # paper colour of the text card
    assert r > 180 and g > 170 and b > 150


@pytest.mark.slow
def test_entity_and_face_fx_clips_rendered(part2):
    ep, total = part2
    assert probe(ep.work / "beat_5.mp4").duration == pytest.approx(2, abs=0.05)
    assert probe(ep.work / "fx_6.mp4").duration == pytest.approx(total - 12, abs=0.1)
    scene = sum(corner_rgb(ep.final, 13.5))   # subscribe scene: blurred, darkened copy in the corner
    plain = sum(corner_rgb(ep.work / "face_6.mp4", 1.5))
    assert scene < 0.75 * plain


@pytest.mark.slow
def test_sfx_land_on_their_cues(part2):
    """The subscribe click (12 + 1.6 s) is bright noise: above 5 kHz it stands out from the 1 kHz voice."""
    import array
    ep, _ = part2

    def treble(at):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(at), "-t", "0.08", "-i", str(ep.final), "-vn",
                              "-af", "highpass=f=5000,highpass=f=5000", "-ac", "1", "-f", "s16le", "-"],
                             capture_output=True, check=True).stdout
        a = array.array("h", raw)
        return (sum(x * x for x in a) / max(1, len(a))) ** 0.5
    assert treble(13.58) > 1.5 * treble(13.3)   # same voice either side; only the click differs
