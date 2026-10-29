"""Motion graphics for the archive look (owner, 2026-10-29: "موشن جرافك فاشل… ماكو ولا موشن جرافك")."""
import numpy as np
from PIL import Image

from editor.pipeline import archive, motion

FPS = 24.0


def _all(gen):
    frames = list(gen)
    assert frames and all(f.shape == (motion.H, motion.W, 3) for f in frames)
    return frames


def test_headline_marks_its_key_line_in_yellow():
    frames = _all(motion.headline({"source": "2003", "headline": "موتورولا ترفض صفقة شراء هواوي", "highlight": "ترفض صفقة"}, 30, FPS))
    last = frames[-1].reshape(-1, 3).astype(int)
    yellowish = ((last[:, 0] > 200) & (last[:, 1] > 170) & (last[:, 2] < 120)).sum()
    assert yellowish > 2000                                                 # the marker is on the paper


def test_person_card_writes_the_name_in():
    img = Image.new("RGB", (900, 1100), (150, 140, 130))
    frames = _all(motion.person(img, {"label": "رن جنغفي", "role": "مؤسس هواوي"}, 24, FPS, archive.archive_look))
    assert np.abs(frames[3].astype(int) - frames[-1].astype(int)).mean() > 2


def test_number_counts_up_to_its_value():
    frames = _all(motion.number({"value": "1987", "caption": "سنة التأسيس"}, 30, FPS))
    assert (frames[0] != frames[-1]).any()


def test_map_finds_countries_by_everyday_names_and_skips_unknown_ones():
    assert motion._country("usa")[0] == "United States of America" and motion._country("China")[0] == "China"
    assert motion._country("Atlantis")[0] is None
    _all(motion.world_map({"countries": ["Iraq", "Iran", "Atlantis"], "label": "الحدود"}, 12, FPS))


def test_big_text_shows_word_after_word():
    frames = _all(motion.big_text({"text": "قال جملة غيرت كل شي", "quote": True, "by": "المؤسس"}, 30, FPS))
    assert frames[0].mean() < frames[-1].mean()                             # more words lit at the end
