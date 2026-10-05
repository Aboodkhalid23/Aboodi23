"""Owner's round 4: reliable cuts (test_clean), top quality, 5 edited reels, precise cut-out with 3 looks."""
import subprocess

import cv2
import numpy as np

from editor.pipeline.plan import Beat, EditPlan, validate_plan


def long_plan(shorts, face_only=False):
    beats, t = [], 0.0
    while t < 600:
        kind = "face" if face_only or int(t) % 10 < 5 else "image"
        beats.append(Beat(t, t + 5, "body", kind, query="x" if kind == "image" else None, caption="ص"))
        t += 5
    return EditPlan({"primary": "retro-collage"}, "", [], beats, shorts=shorts, end_screen=0)


def errs(plan):
    return " ".join(validate_plan(plan, 600.0))


def test_a_long_episode_needs_five_reels_with_editing_in_them():
    five = [{"from": 30.0 * k + 10, "to": 30.0 * k + 40, "title": "هوك"} for k in range(5)]
    assert "shorts:" not in errs(long_plan(five)) and "short 1" not in errs(long_plan(five))
    assert "5 شورتس" in errs(long_plan(five[:3]))
    assert "short 1: لازم بيه مونتاج" in errs(long_plan(five, face_only=True))


def test_cutout_looks_are_checked():
    p = long_plan([])
    p.beats[1] = Beat(5, 10, "body", "face_cutout", treatment="title")
    p.beats[2] = Beat(10, 15, "body", "face_cutout", treatment="scene")
    e = errs(p)
    assert "beat 1: face_cutout title يحتاج title" in e and "beat 2: face_cutout شكله" in e


def test_stray_bits_of_the_room_are_dropped_from_the_matte():
    from editor.pipeline.cutout import Matter
    a = np.zeros((400, 400), np.float32)
    a[100:400, 120:280] = 1          # him
    a[20:50, 20:50] = 1              # a lamp the model caught
    out = Matter.clean(a)
    assert out[200, 200] > 0.9 and out[35, 35] < 0.1


class Box:
    """A fake matter: the person is the middle third of the picture."""
    kind = "test"
    @staticmethod
    def clean(a):
        return a
    def __call__(self, rgb):
        h, w = rgb.shape[:2]
        m = np.zeros((h, w), np.float32); m[:, w // 3: 2 * w // 3] = 1
        return m
    def close(self):
        pass


def _video(path, color, d=0.5, s="320x180"):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color={color}:s={s}:r=30:d={d}", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(path)], check=True)


def test_words_go_behind_him(tmp_path):
    from editor.pipeline.cutout import cutout_clip
    _video(tmp_path / "face.mp4", "blue")
    _video(tmp_path / "words.mp4", "white")            # the words cover the whole frame here
    enc = ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    out = cutout_clip(tmp_path / "face.mp4", None, tmp_path / "t.mp4", 320, 180, 30, 15, enc, mode="title",
                      text=tmp_path / "words.mp4", text_rgb=(255, 0, 0), matter=Box())
    ok, f = cv2.VideoCapture(str(out)).read()
    assert f[90, 20][2] > 200 and f[90, 160][0] > 200        # red words at the side, he (blue) in front of them


def test_reel_pieces_kinetic_timing_and_new_transitions(tmp_path):
    import numpy as np
    from editor.pipeline.compose import kinetic_times
    from editor.pipeline.paths import Episode
    from editor.pipeline.transcribe import Word, save_words
    from editor.pipeline.wipes import move_frame
    ep = Episode(tmp_path / "ep").ensure()
    save_words([Word("هيچ", 10.2, 10.5), Word("إهانة", 10.6, 11.0), Word("وحدة", 11.1, 11.4)], ep.clean_words)
    p = EditPlan({"primary": "vox"}, "", [], [Beat(10, 13, "body", "graphic", graphic={"type": "kinetic", "text": "هيچ اهانه وحده غيرت"})])
    assert kinetic_times(ep, p, p.beats[0]) == [0.2, 0.6, 1.1, None]
    assert "kinetic" not in " ".join(validate_plan(p, 13.0))
    old, new = np.zeros((40, 60, 3), np.uint8), np.full((40, 60, 3), 200, np.uint8)
    closed = move_frame("shutter", old, new, 0.4, 0.05)
    assert closed.mean() > 60 and move_frame("shutter", old, new, 1.0, 0.05).mean() > 190   # metal, then the new shot
    half = move_frame("slide", old, new, 0.5, 0.05)
    assert half[-1].mean() > 190 and half[0].mean() < 50                                 # new sheet from the bottom
