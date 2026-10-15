from editor.pipeline.compose import paper_cues
from editor.pipeline.graphics import face_paper_job
from editor.pipeline.plan import Beat, paper_errors
from editor.pipeline.styles import load_style


def _beat(papers, **kw):
    return Beat(start=10, end=17, zone="body", kind="face_paper", papers=papers, **kw)


def test_good_papers_pass():
    b = _beat([{"type": "newspaper", "at": 0.3, "title": "عنوان", "query": "ford factory"},
               {"type": "document", "at": 2.5, "title": "تقرير", "lines": ["سطر"]},
               {"type": "number", "at": 4.5, "value": 93, "label": "دقيقة"}])
    assert paper_errors(b) == []


def test_bad_papers_are_explained():
    assert paper_errors(_beat([]))                                                   # none
    assert paper_errors(_beat([{"type": "poster"}]))                                 # unknown type
    assert paper_errors(_beat([{"type": "photo"}]))                                  # photo without a search
    assert paper_errors(_beat([{"type": "quote", "text": "x", "at": 6.9}]))          # lands too late
    assert paper_errors(_beat([{"type": "quote", "text": "x", "at": 1},
                               {"type": "quote", "text": "y", "at": 1.5}]))          # too close together
    assert paper_errors(_beat([{"type": "quote", "text": "x"}], treatment="wall"))   # unknown layout


def test_a_paper_sound_as_each_paper_lands():
    b = _beat([{"type": "quote", "text": "x", "at": 0.5}, {"type": "quote", "text": "y", "at": 3}])
    assert paper_cues(b) == [(10.5, "paper"), (13.0, "paper")]


def test_papers_go_to_the_empty_side_and_desk_when_no_room(tmp_path):
    style = load_style("retro-collage")
    b = _beat([{"type": "photo", "query": "x"}])
    (tmp_path / "public").mkdir()
    face = tmp_path / "face.mp4"
    face.write_bytes(b"0")
    left = face_paper_job(b, style, face, tmp_path / "o.mp4", 30, bundle=tmp_path, face_x=0.3)
    assert left.props["side"] == "right" and left.props["layout"] == "overlay"
    middle = face_paper_job(b, style, face, tmp_path / "o.mp4", 30, bundle=tmp_path, face_x=0.5)
    assert middle.props["layout"] == "desk"
    phone = face_paper_job(b, style, face, tmp_path / "o.mp4", 30, bundle=tmp_path, face_x=0.3, pic_w=0.32)
    assert phone.props["layout"] == "desk"
    assert "query" not in middle.props["papers"][0]


def test_brief_points_at_moments_for_papers():
    from types import SimpleNamespace as W
    from editor.pipeline.brief import find_moments
    said = lambda *ws: [W(text=t, start=i, end=i + 0.4) for i, t in enumerate(ws)]
    out = find_moments([said("نشرت", "الجريدة", "خبر", "غريب"), said("وگال", "المدير", "شي"),
                        said("سنة", "1913", "بدا"), said("هلا", "بيكم")])
    assert [o.split("]")[1].split(":")[0].strip() for o in out] == \
        ["face_paper newspaper", "face_paper quote", "face_paper number", "face_fx tv"]


def test_behind_his_shoulder_is_a_transparent_layer(tmp_path):
    style = load_style("retro-collage")
    (tmp_path / "public").mkdir()
    face = tmp_path / "face.mp4"
    face.write_bytes(b"0")
    b = _beat([{"type": "quote", "text": "x"}], treatment="behind")
    assert paper_errors(b) == []
    job = face_paper_job(b, style, face, tmp_path / "p.mov", 30, bundle=tmp_path, face_x=0.4, layer_only=True)
    assert job.alpha and job.props["layerOnly"] and job.props["layout"] == "overlay"


def test_director_cues_land_on_the_moment_the_sentence_is_said(tmp_path):
    from editor.pipeline.brief import visual_cues
    from editor.pipeline.paths import Episode
    from editor.pipeline.transcribe import Word
    ep = Episode(tmp_path / "ep").ensure()
    (ep.root / "07-visuals.md").write_text("- «فورد شغل أول خط تجميع» → face_paper newspaper: فورد | خط تجميع\n"
                                           "- «جملة ما انگالت أبد هنا» → image: x\n", encoding="utf-8")
    text = "هلا بيكم سنة 1913 فورد شغّل أول خط تجميع بالعالم"
    words = [Word(w, i * 0.5, i * 0.5 + 0.4) for i, w in enumerate(text.split())]
    cues = visual_cues(ep, words)
    assert len(cues) == 1 and cues[0].startswith("[00:02.0] face_paper newspaper")
