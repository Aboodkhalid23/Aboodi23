import pytest

from editor.pipeline.styles import load_style, styles_summary


def test_load_vox():
    s = load_style("vox")
    assert s.palette["accent"] == "#FFD400"
    assert s.image_treatment == "paper_cutout"
    assert s.fonts["title"] == "Cairo"


def test_missing_style_arabic_error():
    with pytest.raises(KeyError) as err:
        load_style("nope")
    assert "ستايل" in str(err.value)


def test_summary_lists_vox():
    assert any(ln.startswith("vox:") for ln in styles_summary().splitlines())
