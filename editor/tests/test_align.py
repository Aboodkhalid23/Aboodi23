import json

import pytest

from editor.pipeline.align import align_to_script, align_words, find_script, script_words
from editor.pipeline.paths import Episode
from editor.pipeline.transcribe import Word, load_words, save_words

from .test_clean import phrase


def test_script_words_strips_markdown():
    text = "# الهوك\n**شركة** [صوت خافت] إيفرغراند (ملاحظة للمصور) كانت > أكبر 🔥 [رابط](http://x.com)\n| جدول |"
    assert script_words(text) == ["شركة", "إيفرغراند", "كانت", "أكبر", "رابط", "جدول"]


def test_align_fixes_misheard_words():
    heard = phrase("شركه ايفر غراند كانت اكبر", 1.0, 3.5)
    fixed, ratio = align_words(heard, ["شركة", "إيفرغراند", "كانت", "أكبر"])
    assert [w.text for w in fixed] == ["شركة", "إيفرغراند", "كانت", "أكبر"]
    assert fixed[0].start == 1.0 and fixed[-1].end == pytest.approx(3.5)
    assert ratio == 1.0


def test_align_keeps_adlib():
    heard = phrase("شركة كانت اكبر والله شي ما يصدگ", 0, 7)
    fixed, ratio = align_words(heard, ["شركة", "كانت", "أكبر"])
    assert [w.text for w in fixed][-4:] == ["والله", "شي", "ما", "يصدگ"]
    assert fixed[-1] == heard[-1]
    assert ratio == pytest.approx(3 / 7)


def test_align_ratio_low_warns(tmp_path, capsys):
    ep = Episode(tmp_path / "ep").ensure()
    script = tmp_path / "02-draft.md"
    script.write_text("شركة إيفرغراند كانت أكبر شركة", encoding="utf-8")
    words = align_to_script(ep, phrase("كلام ثاني تماماً ما بيه علاقة", 0, 5), script)
    assert [w.text for w in words][0] == "كلام"
    assert "الكلام يختلف هواية عن السكربت" in capsys.readouterr().out
    assert (ep.work / "align.json").exists()


def test_find_script_prefers_final(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    (ep.root / "02-draft.md").write_text("x")
    assert find_script(ep).name == "02-draft.md"
    (ep.root / "04-final.md").write_text("x")
    assert find_script(ep).name == "04-final.md"


def test_find_script_uses_studio_final_name(tmp_path):
    """I3: studio writes the fact-checked script as 04-script.md."""
    ep = Episode(tmp_path / "ep").ensure()
    (ep.root / "02-draft.md").write_text("x")
    (ep.root / "04-script.md").write_text("x")
    assert find_script(ep).name == "04-script.md"


def test_align_keeps_heard_words_across_a_pause():
    """C1: a replace span with a pause inside is not stretched over the pause."""
    heard = phrase("شركه ايفر", 0, 1) + phrase("غراند كانت", 3, 4)
    fixed, _ = align_words(heard, ["شركة", "إيفرغراند", "كانت"])
    assert all(w.end - w.start <= 1.0 for w in fixed)
