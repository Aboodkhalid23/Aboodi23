"""Style update 1 (owner's reference folder): in-scene title placement, face-following stickers."""
import cv2
import numpy as np

from editor.pipeline.masks import image_layout, place_on_face


def _pair(tmp_path, alpha):
    src, cut = tmp_path / "p.jpg", tmp_path / "p_person.png"
    h, w = alpha.shape
    img = np.full((h, w, 3), 120, np.uint8)
    cv2.imwrite(str(src), img)
    cv2.imwrite(str(cut), np.dstack([img, (alpha * 255).astype(np.uint8)]))
    return src, cut


def test_title_goes_behind_a_person_standing_aside(tmp_path):
    a = np.zeros((1080, 1920), np.float32)
    a[300:, 1450:1750] = 1                     # a narrow person on the right
    lay = image_layout(*_pair(tmp_path, a))
    assert lay["titleFront"] is False and 0.1 < lay["titleY"] < 0.9


def test_title_goes_in_front_when_the_person_fills_the_frame(tmp_path):
    lay = image_layout(*_pair(tmp_path, np.ones((1080, 1920), np.float32)))
    assert lay["titleFront"] is True


def test_no_cutout_means_centred_title(tmp_path):
    src, _ = _pair(tmp_path, np.zeros((540, 960), np.float32))
    assert image_layout(src, None) == {"face": None, "titleY": 0.5, "titleFront": False}


def test_stickers_follow_the_face_unless_placed_by_hand():
    face = [0.5, 0.3, 0.2, 0.36]
    st = place_on_face([{"type": "censor", "text": "WHY?"}, {"type": "name_tag", "text": "x"},
                        {"type": "censor", "x": 0.1, "y": 0.1}, {"type": "stamp", "text": "سري"}], face)
    censor, tag, manual, stamp = st
    assert censor["x"] == 0.5 and censor["y"] < 0.3 and censor["w"] > 0.2
    assert tag["y"] > 0.3 + 0.18                 # under the chin
    assert (manual["x"], manual["y"]) == (0.1, 0.1) and "x" not in stamp
    assert place_on_face(st, None) == st
