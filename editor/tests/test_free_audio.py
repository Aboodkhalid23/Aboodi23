"""Free music and sound effects (owner's rule: no credits on sound), and AI only when nothing real exists."""
import json
import subprocess

from editor.pipeline import free_audio as FA
from editor.pipeline.paths import Episode
from editor.pipeline.plan import Beat, EditPlan, save_plan


def mp3(path, d=2.0):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=f=220:d={d}", "-c:a", "libmp3lame",
                    str(path)], check=True)
    return path.read_bytes()


class Openverse:
    """Fake Openverse audio search + file server."""
    def __init__(self, audio: bytes, results):
        self.audio, self.results, self.asked = audio, results, []

    def get(self, url, params=None, headers=None, timeout=None):
        outer = self
        class R:
            status_code = 200
            content = outer.audio
            def raise_for_status(self): pass
            def json(self): return {"results": outer.results}
        if params:
            self.asked.append(dict(params))
        return R()


def track(title, secs, lic="by", genres=("filmscore",), url=None):
    return {"title": title, "url": url or f"https://a/{title}.mp3", "duration": secs * 1000, "license": lic,
            "license_version": "3.0", "creator": "Someone", "foreign_landing_url": "https://jamendo/x", "genres": list(genres)}


def test_tracks_too_short_or_with_vocals_lose(tmp_path):
    s = Openverse(b"", [track("Short", 30), track("My Song feat. X", 200), track("Score", 200)])
    got = FA.find_tracks(["cinematic"], s)
    assert [t.title for t in got] == ["Score", "My Song feat. X"]
    assert s.asked[0]["license"] == "cc0,by"                       # never share-alike or non-commercial


def test_free_music_fills_the_bed_and_credits_it(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    save_plan(EditPlan({"primary": "retro-collage"}, "", [], [Beat(0, 10, "body", "face")]), ep.plan)
    s = Openverse(mp3(tmp_path / "x.mp3"), [track("Score", 200)])
    assert FA.free_music(ep, 10.0, s) == []
    assert (ep.assets / "music.mp3").exists()
    cred = json.loads((ep.work / "music_credits.json").read_text())
    assert cred["bed"]["credit"].startswith("Music: Score — Someone — CC BY 3.0")


def test_sound_effects_are_cc0_from_freesound_and_kept(tmp_path):
    s = Openverse(mp3(tmp_path / "x.mp3", 0.5), [dict(track("Typewriter", 1, "cc0"), id="abc123456789")])
    got = FA.fetch_sfx("typewriter", tmp_path / "lib", s)
    assert got and got[0].parent.name == "typewriter" and (tmp_path / "lib/typewriter/SOURCE.txt").exists()
    assert s.asked[0]["license"] == "cc0" and s.asked[0]["source"] == "freesound"


def test_a_picture_nobody_has_becomes_an_ai_image_only_then(tmp_path, monkeypatch):
    from editor.pipeline import sources
    from editor.pipeline.wikimedia import collect_images
    monkeypatch.setattr(sources, "find", lambda *a, **k: [])
    ep = Episode(tmp_path / "ep").ensure()
    plan = EditPlan({"primary": "retro-collage"}, "", [], [
        Beat(0, 4, "body", "image", query="secret 1920 meeting", caption="اجتماع سري", prompt="a secret meeting in 1920"),
        Beat(4, 8, "body", "image", query="nothing", caption="ولا شي")])
    collect_images(plan, ep, session=object())
    assert plan.beats[0].kind == "ai_image" and plan.beats[1].kind == "graphic"
