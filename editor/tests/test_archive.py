"""The «أرشيف» look (owner, 2026-10-29: the reels he sent as his target)."""
from PIL import Image

from editor.pipeline import archive


def test_shots_cover_the_whole_talk_without_gaps_or_slivers():
    shots = archive.tidy([{"start": 0.3, "end": 1.4, "kind": "photo"}, {"start": 1.5, "end": 1.7, "kind": "photo"},
                          {"start": 1.6, "end": 4.0, "kind": "face"}, {"start": 4.0, "end": 9.9, "kind": "photo"}], 10.0)
    assert shots[0]["start"] == 0.0 and shots[-1]["end"] == 10.0
    assert all(a["end"] == b["start"] for a, b in zip(shots, shots[1:]))
    assert all(s["end"] - s["start"] >= 0.5 for s in shots)


def test_arabic_word_and_name_tag_are_drawn_shaped():
    w, tag = archive.word_layer("شركة صغيرة"), archive.label_layer("هواوي")
    assert w.mode == "RGBA" and w.width > 200 and tag.width > 150
    assert tag.convert("RGB").getpixel((tag.width // 2, 6))[2] < 60       # yellow, not white


def test_a_photo_shot_moves_and_keeps_the_frame_size():
    img = Image.new("RGB", (1600, 1000), (120, 90, 60))
    frames = list(archive.photo_frames(img, 6, {"word": "هواوي", "print": False}, seed=1))
    assert len(frames) == 6 and frames[0].shape == (archive.H, archive.W, 3)
    prints = list(archive.photo_frames(img, 8, {"label": "رن جنغفي", "print": True}, seed=2))
    assert (prints[0] != prints[-1]).any()                                # the print drops in


def test_plain_search_hits_must_share_a_word_of_the_query(monkeypatch):
    from editor.pipeline.sources import Found
    hits = [Found("Wikimedia Commons", "File:B-2445 at PEK.jpg", "u1", 2000, 1300, "CC", "a", "p"),
            Found("Wikimedia Commons", "File:Shenzhen Futian 1995.jpg", "u2", 2000, 1300, "CC", "a", "p")]
    monkeypatch.setattr("editor.pipeline.sources.find", lambda *a, **k: hits)
    monkeypatch.setattr(archive, "wikipedia_picture", lambda q, s: None)
    got = []

    def fake_download(f, s):
        got.append(f.url)
        raise OSError("stop")
    monkeypatch.setattr("editor.pipeline.sources.download", fake_download)

    class Ep:
        assets = None
    import tempfile
    from pathlib import Path
    Ep.assets = Path(tempfile.mkdtemp())
    shots = [{"kind": "photo", "queries": ["1990s Shenzhen street"]}]
    archive.fetch_pictures(Ep, shots)
    assert got == ["u2"] and shots[0]["kind"] == "face"                   # nothing usable → his face
