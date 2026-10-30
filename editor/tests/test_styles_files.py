"""A notes file or a half-written style in the styles folder never stops an episode (2026-10-30: every cut failed)."""
from editor.pipeline import styles


def test_notes_and_broken_styles_are_skipped(tmp_path, monkeypatch):
    d = tmp_path / "styles"
    d.mkdir()
    good = next(p for p in styles._style_files() if p.stem == "noir")
    (d / "noir.md").write_text(good.read_text(encoding="utf-8"), encoding="utf-8")
    (d / "notes.md").write_text("# تحليل\n\n|---|---|\n| a | b |\n", encoding="utf-8")         # not a style
    (d / "half.md").write_text("---\njust a sentence\n---\nnotes", encoding="utf-8")           # a broken style
    monkeypatch.setattr(styles, "STYLES_DIR", d)
    monkeypatch.setattr(styles, "user_styles_dir", lambda: None)
    names = [p.stem for p in styles._style_files()]
    assert "notes" not in names and "noir" in names
    assert "noir:" in styles.styles_summary()                                             # the broken one is skipped


def test_every_style_in_the_repo_opens():
    for p in styles._style_files():
        styles.load_style(p.stem)
