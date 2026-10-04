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


def _solid(path, color, d=1.0):
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color={color}:s=320x180:r=30:d={d}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)


def test_tear_and_burn_wipe_the_new_shot_in_from_the_right(tmp_path):
    from editor.pipeline.media import probe
    from editor.pipeline.wipes import DUR, apply_wipe
    _solid(tmp_path / "old.mp4", "blue"); _solid(tmp_path / "new.mp4", "red")
    for kind in ("tear", "burn"):
        out = apply_wipe(kind, tmp_path / "old.mp4", tmp_path / "new.mp4", tmp_path / f"{kind}.mp4", 320, 180, 30,
                         ["-c:v", "libx264", "-pix_fmt", "yuv420p"])
        assert abs(probe(out).duration - 1.0) < 0.05
        mid = cv2.VideoCapture(str(out))
        mid.set(cv2.CAP_PROP_POS_FRAMES, int(DUR * 30 / 2))
        ok, frame = mid.read()
        assert ok
        left, right = frame[90, 20], frame[90, 300]          # BGR
        assert left[0] > 150 and right[2] > 150              # old blue still on the left, new red on the right


def test_halftone_print_is_grey_inside_with_a_coloured_paper_edge(tmp_path):
    from editor.pipeline.masks import halftone_cutout
    a = np.zeros((540, 960), np.uint8)
    cv2.circle(a, (480, 270), 150, 255, -1)
    img = np.dstack([np.full((540, 960), 40, np.uint8), np.full((540, 960), 160, np.uint8), np.full((540, 960), 220, np.uint8), a])
    cv2.imwrite(str(tmp_path / "c.png"), img)
    out = cv2.imread(str(halftone_cutout(tmp_path / "c.png", (242, 194, 48))), cv2.IMREAD_UNCHANGED)
    inside, edge, outside = out[270, 480], out[270, 480 + 152], out[270, 900]
    assert abs(int(inside[0]) - int(inside[2])) < 3 and inside[3] == 255       # black and white print
    assert edge[3] > 200 and edge[2] > 200 and edge[0] < 90                       # yellow edge (BGR)
    assert outside[3] == 0


def test_plan_accepts_tear_and_burn():
    from editor.pipeline.plan import TRANSITIONS
    from editor.pipeline.sfx import TRANSITION_SFX
    assert {"tear", "burn"} <= set(TRANSITIONS) and TRANSITION_SFX["tear"] == "paper"


def test_ai_look_replaces_the_world_suffix_and_is_validated():
    from editor.pipeline.ai import AI_LOOKS
    from editor.pipeline.plan import Beat, EditPlan, validate_plan
    beats = [Beat(0, 3, "hook", "ai_image", prompt="a lab at night", look="pencil"),
             Beat(3, 6, "hook", "image", query="x", look="pencil"),
             Beat(6, 9, "hook", "image", query="x", treatment="halftone_cutout")]
    plan = EditPlan(style={"primary": "retro-collage"}, style_reason="", teaser=[], beats=beats, end_screen=0)
    errs = " ".join(validate_plan(plan, 9.0))
    assert "beat 1: look" in errs and "beat 2: halftone_cutout" in errs and "beat 0: look" not in errs
    assert "pencil" in AI_LOOKS["pencil"]


def test_camera_moves_dive_into_the_old_shot_and_pan_to_the_new_one(tmp_path):
    from editor.pipeline.wipes import MOVE_DUR, apply_wipe
    _solid(tmp_path / "old.mp4", "blue"); _solid(tmp_path / "new.mp4", "red")
    enc = ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    def frame(path, n):
        cap = cv2.VideoCapture(str(path)); cap.set(cv2.CAP_PROP_POS_FRAMES, n); ok, f = cap.read(); assert ok; return f
    dive = apply_wipe("dive", tmp_path / "old.mp4", tmp_path / "new.mp4", tmp_path / "dive.mp4", 320, 180, 30, enc)
    assert frame(dive, 3)[90, 160][0] > 150 and frame(dive, int(MOVE_DUR * 30) + 2)[90, 160][2] > 150   # old, then new
    pan = apply_wipe("pan", tmp_path / "old.mp4", tmp_path / "new.mp4", tmp_path / "pan.mp4", 320, 180, 30, enc)
    mid = frame(pan, int(MOVE_DUR * 30 / 2) - 1)
    assert mid[90, 5][2] > 150 and mid[90, 315][0] > 150          # new shot comes in from the left, old leaves right


def test_headline_storm_has_a_paper_sound_per_landing_and_chapters_get_riser_and_hit():
    from editor.pipeline.compose import chapter_cues, graphic_cues
    from editor.pipeline.plan import Beat, EditPlan
    b = Beat(10, 14, "body", "graphic", graphic={"type": "headlines", "items": [{"title": "أ"}, {"title": "ب"}, {"title": "ج"}]})
    cues = graphic_cues(b)
    assert [n for _, n in cues] == ["paper"] * 3 and cues[0][0] == 10.15
    plan = EditPlan({"primary": "vox"}, "", [], [Beat(0, 60, "body", "face")], chapters=[{"t": 0, "title": "أ"}, {"t": 30, "title": "ب"}])
    assert chapter_cues(plan) == [(28.8, "riser"), (30.0, "hit")]
