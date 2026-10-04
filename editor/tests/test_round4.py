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
    p.beats[0] = Beat(0, 5, "body", "face_cutout", treatment="scene", caption="مزرعة")
    p.beats[1] = Beat(5, 10, "body", "face_cutout", treatment="title")
    p.beats[2] = Beat(10, 15, "body", "face_cutout", treatment="space")
    e = errs(p)
    assert "beat 0: face_cutout scene يحتاج query" in e and "beat 1: face_cutout title يحتاج title" in e
    assert "beat 2: face_cutout شكله" in e


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


def test_words_go_behind_him_and_scene_puts_him_in_the_place(tmp_path):
    from editor.pipeline.cutout import cutout_clip
    _video(tmp_path / "face.mp4", "blue")
    _video(tmp_path / "words.mp4", "white")            # the words cover the whole frame here
    enc = ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    out = cutout_clip(tmp_path / "face.mp4", None, tmp_path / "t.mp4", 320, 180, 30, 15, enc, mode="title",
                      text=tmp_path / "words.mp4", text_rgb=(255, 0, 0), matter=Box())
    ok, f = cv2.VideoCapture(str(out)).read()
    assert f[90, 20][2] > 200 and f[90, 160][0] > 200        # red words at the side, he (blue) in front of them
    cv2.imwrite(str(tmp_path / "farm.png"), np.full((180, 320, 3), (0, 200, 0), np.uint8))
    out = cutout_clip(tmp_path / "face.mp4", tmp_path / "farm.png", tmp_path / "s.mp4", 320, 180, 30, 15, enc,
                      mode="scene", matter=Box())
    ok, f = cv2.VideoCapture(str(out)).read()
    assert f[90, 20][1] > 150 and f[90, 160][0] > 150        # the green place around him, he stays himself


def test_thumbnail_words_are_few():
    p = long_plan([{"from": 30.0 * k + 10, "to": 30.0 * k + 40, "title": "هوك"} for k in range(5)])
    p.thumbnail = {"text": "سر الخلية العصبية الي محد يعرفه"}
    assert "thumbnail:" in errs(p)
    p.thumbnail = {"text": "سر الخلية", "highlight": "سر"}
    assert "thumbnail:" not in errs(p)
