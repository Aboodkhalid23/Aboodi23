from editor.pipeline.chapters import write_chapters
from editor.pipeline.plan import Beat, EditPlan, validate_plan

from .test_plan import build


def with_chapters(chapters, teaser=((10.0, 12.0), (20.0, 22.0), (40.0, 42.0))):
    plan, clean = build()
    plan.teaser = list(teaser)
    plan.chapters = chapters
    return plan, clean


def test_chapter_times_shift_by_teaser(tmp_path):
    plan, _ = with_chapters([{"t": 0, "title": "البداية"}, {"t": 30, "title": "الصعود"}, {"t": 64, "title": "الانهيار"}])
    text = write_chapters(plan, tmp_path / "chapters.txt").read_text(encoding="utf-8")
    assert text.splitlines() == ["00:00 البداية", "00:36 الصعود", "01:10 الانهيار"]


def test_valid_chapters_pass():
    plan, clean = with_chapters([{"t": 0, "title": "أ"}, {"t": 20, "title": "ب"}, {"t": 40, "title": "ج"}])
    assert validate_plan(plan, clean) == []


def test_first_chapter_must_be_zero():
    plan, clean = with_chapters([{"t": 5, "title": "أ"}, {"t": 20, "title": "ب"}, {"t": 40, "title": "ج"}])
    errs = validate_plan(plan, clean)
    assert len(errs) == 1 and errs[0].startswith("chapter 0:")


def test_chapters_too_close():
    plan, clean = with_chapters([{"t": 0, "title": "أ"}, {"t": 20, "title": "ب"}, {"t": 25, "title": "ج"}])
    errs = validate_plan(plan, clean)
    assert len(errs) == 1 and errs[0].startswith("chapter 2:")


def test_too_few_chapters():
    plan, clean = with_chapters([{"t": 0, "title": "أ"}, {"t": 20, "title": "ب"}])
    assert any("3" in e for e in validate_plan(plan, clean))


def test_hour_format(tmp_path):
    plan = EditPlan({"primary": "vox"}, "", [], [Beat(0, 5, "hook", "face")],
                    chapters=[{"t": 0, "title": "أ"}, {"t": 1800, "title": "ب"}, {"t": 3700, "title": "ج"}])
    lines = write_chapters(plan, tmp_path / "c.txt").read_text(encoding="utf-8").splitlines()
    assert lines[1:] == ["30:00 ب", "1:01:40 ج"]
