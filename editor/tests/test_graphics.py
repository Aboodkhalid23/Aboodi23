import subprocess

import pytest

from editor.pipeline.graphics import render_face_frame_bg, render_graphic
from editor.pipeline.media import probe
from editor.pipeline.plan import Beat
from editor.pipeline.styles import load_style

GRAPHICS = {
    "number": {"type": "number", "value": 3000000000, "label": "دولار ديون"},
    "headline": {"type": "headline", "outlet": "Reuters", "title": "شركة إيفرغراند تعلن إفلاسها رسمياً",
                 "highlight": "إفلاسها"},
    "quote": {"type": "quote", "text": "ما كنا نتوقع هذا اليوم يجي", "who": "مدير الشركة"},
    "map": {"type": "map", "country": "CHN", "label": "الصين"},
    "timeline": {"type": "timeline", "items": [{"year": "1996", "label": "التأسيس"},
                                               {"year": "2017", "label": "القمة"},
                                               {"year": "2021", "label": "الانهيار"}]},
    "chart": {"type": "chart", "unit": "مليار", "bars": [{"label": "2019", "value": 120},
                                                        {"label": "2021", "value": 300}]},
    "text": {"type": "text", "text": "شركة إيفرغراند"},
}


@pytest.mark.slow
@pytest.mark.parametrize("gtype", [*GRAPHICS, "image"])
def test_render_each_graphic_type(gtype, tmp_path):
    if gtype == "image":
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        "testsrc2=size=1600x900", "-frames:v", "1", str(tmp_path / "img_3.png")], check=True)
        beat = Beat(0, 2, "body", "image", query="x", treatment="paper_cutout")
        out = render_graphic(beat, load_style("vox"), tmp_path / "beat_3.mp4", public_dir=tmp_path, index=3)
    else:
        beat = Beat(0, 2, "body", "graphic", graphic=GRAPHICS[gtype])
        out = render_graphic(beat, load_style("vox"), tmp_path / "g.mp4")
    info = probe(out)
    assert (info.width, info.height) == (1920, 1080)
    assert info.duration == pytest.approx(2.0, abs=0.1)


@pytest.mark.slow
def test_render_face_frame_bg(tmp_path):
    out = render_face_frame_bg(load_style("vox"), tmp_path / "frame.png")
    assert out.exists() and out.stat().st_size > 1000


@pytest.mark.slow
def test_bundle_built_once(tmp_path):
    """I-4: the Remotion project is bundled once, not once per graphic."""
    from editor.pipeline.graphics import ensure_bundle
    b = ensure_bundle(tmp_path / "bundle")
    stamp = (b / "index.html").stat().st_mtime
    assert ensure_bundle(tmp_path / "bundle") == b
    assert (b / "index.html").stat().st_mtime == stamp
    assert (b / "public" / "paper-noise.png").exists()
