import contextlib
import copy
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import concepts  # noqa: E402
from concepts import ConceptError  # noqa: E402

BASE = {
    "id": "A1", "angle": "metaphor", "idea": "زر نووي وإصبع روبوت", "text": None,
    "subject": {"outfit": "olive military shirt", "expression": "tense, mouth closed", "action": "leans over the desk"},
    "hero": "a robotic finger above a red nuclear button",
    "setting": "dark war room with blue world-map screens",
    "camera": "wide_close",
    "layout": {"face": "right", "hero": "left", "text_zone": None},
    "palette": ["#0B1A2A", "#E3262B", "#2EC4FF"],
    "scores": {"clarity": 8, "curiosity": 8, "emotion": 8, "novelty": 8, "honesty": 8, "producible": 8, "face": 8},
    "why": "الذكاء الاصطناعي يقرر الحرب",
}


def card(cid="A1", score=8, angle="metaphor", expression="tense", color="#0B1A2A", text=None, **over):
    c = copy.deepcopy(BASE)
    c["id"], c["angle"] = cid, angle
    c["subject"]["expression"] = expression
    c["palette"][0] = color
    c["scores"] = {k: score for k in concepts.WEIGHTS}
    if text:
        c["text"] = text
        c["layout"]["text_zone"] = "top_left"
    c.update(over)
    return c


class ScoreTest(unittest.TestCase):
    def test_score_all_tens_is_100(self):
        self.assertEqual(concepts.score(card(score=10)), 100.0)

    def test_score_weights(self):
        c = card(score=0)
        c["scores"]["clarity"] = 10
        self.assertEqual(concepts.score(c), 18.2)


class ValidateTest(unittest.TestCase):
    def assertInvalid(self, cards, *parts):
        with self.assertRaises(ConceptError) as ctx:
            concepts.validate(cards)
        for part in parts:
            self.assertIn(part, str(ctx.exception))

    def test_valid_card_passes(self):
        concepts.validate([card()])

    def test_missing_field(self):
        c = card("A3")
        del c["hero"]
        self.assertInvalid([c], "A3", "hero")
        c = card("A4")
        del c["subject"]["expression"]
        self.assertInvalid([c], "A4", "expression")
        c = card("A5")
        del c["scores"]["face"]
        self.assertInvalid([c], "A5", "face")

    def test_score_out_of_range(self):
        c = card()
        c["scores"]["clarity"] = 11
        self.assertInvalid([c], "clarity")

    def test_score_as_string(self):
        c = card()
        c["scores"]["clarity"] = "9"
        self.assertInvalid([c], "clarity")

    def test_text_too_long(self):
        self.assertInvalid([card(text="واحد اثنين\nثلاثة أربعة خمسة")], "4")
        self.assertInvalid([card(text="واحد\nاثنين\nثلاثة")], "سطر")

    def test_text_needs_zone_and_no_text_has_none(self):
        c = card(text="نهاية\nالعالم؟")
        c["layout"]["text_zone"] = None
        self.assertInvalid([c], "text_zone")
        c = card()
        c["layout"]["text_zone"] = "top_left"
        self.assertInvalid([c], "text_zone")

    def test_bad_palette(self):
        self.assertInvalid([card(palette=["#FFF", "#000000"])], "palette")
        self.assertInvalid([card(palette=["#000000"] * 5)], "palette")
        self.assertInvalid([card(palette=["#000000"])], "palette")

    def test_unknown_angle_camera_layout(self):
        self.assertInvalid([card(angle="x")], "angle")
        self.assertInvalid([card(camera="drone")], "camera")
        c = card()
        c["layout"]["face"] = "up"
        self.assertInvalid([c], "face")

    def test_duplicate_ids(self):
        self.assertInvalid([card("A1"), card("A1", angle="scale")], "A1", "مكرر")

    def test_unknown_font(self):
        self.assertInvalid([card(text="نهاية\nالعالم؟", font="Nope")], "Nope")
        self.assertInvalid([card(text="نهاية\nالعالم؟", font="Cairo", font_latin="Nope")], "Nope")

    def test_arabic_text_in_latin_only_font(self):
        self.assertInvalid([card(text="نهاية\nالعالم؟", font="Anton")], "Anton", "font_latin")
        concepts.validate([card(text="300\nBILLION", font="Anton")])

    def test_not_a_list(self):
        self.assertInvalid({"id": "A1"}, "قائمة")
        self.assertInvalid([], "فارغ")


class SelectTest(unittest.TestCase):
    def ids(self, picked):
        return [p["id"] for p in picked]

    def test_select_two_without_text_one_with(self):
        cards = [
            card("n1", 10, "metaphor", "calm", "#8B0000"),
            card("n2", 9, "scale", "worried", "#003366"),
            card("n3", 7, "mystery", "smirk", "#004D00"),
            card("t1", 8, "villain", "angry", "#4B0082", text="نهاية\nالعالم؟"),
            card("t2", 6, "pov", "shocked", "#663300", text="انت\nالهدف!"),
            card("n4", 9.5, "metaphor", "doubt", "#330066"),
        ]
        picked, notes = concepts.select(cards)
        self.assertEqual(self.ids(picked), ["n1", "n2", "t1"])
        self.assertEqual([p["label"] for p in picked], ["A", "B", "C"])
        self.assertEqual([p["score"] for p in picked], [100.0, 90.0, 80.0])
        self.assertEqual(notes, [])

    def test_select_distinct_angles_expressions_colors(self):
        cards = [
            card("na", 10, "metaphor", "calm", "#8B0000"),
            card("nb", 9.5, "metaphor", "worried", "#003366"),
            card("nc", 9, "metaphor", "smirk", "#004D00"),
            card("nd", 6, "scale", "doubt", "#4B0082"),
            card("te", 7, "metaphor", "angry", "#663300", text="نهاية\nالعالم؟"),
            card("tf", 5, "villain", "shocked", "#006666", text="انت\nالهدف!"),
        ]
        picked, notes = concepts.select(cards)
        self.assertEqual(self.ids(picked), ["na", "nd", "tf"])
        self.assertEqual(notes, [])

    def test_gray_dominant_skips_hue_rule(self):
        cards = [
            card("n1", 10, "metaphor", "calm", "#111111"),
            card("n2", 9, "scale", "worried", "#8B0000"),
            card("t1", 8, "villain", "angry", "#003366", text="نهاية\nالعالم؟"),
        ]
        picked, notes = concepts.select(cards)
        self.assertEqual(self.ids(picked), ["n1", "n2", "t1"])
        self.assertEqual(notes, [])

    def test_relax_with_note(self):
        cards = [
            card("n1", 10, "metaphor", "calm", "#8B0000"),
            card("n2", 9, "scale", "worried", "#8B0000"),
            card("t1", 8, "villain", "angry", "#8B0000", text="نهاية\nالعالم؟"),
        ]
        picked, notes = concepts.select(cards)
        self.assertEqual(len(picked), 3)
        self.assertEqual(len(notes), 1)
        self.assertIn("اللون", notes[0])

    def test_same_expression_ignores_case_and_spaces(self):
        cards = [
            card("n1", 10, "metaphor", "Calm", "#8B0000"),
            card("n2", 9, "scale", " calm ", "#003366"),
            card("n3", 5, "mystery", "smirk", "#004D00"),
            card("t1", 8, "villain", "angry", "#4B0082", text="نهاية\nالعالم؟"),
        ]
        picked, _ = concepts.select(cards)
        self.assertEqual(self.ids(picked), ["n1", "t1", "n3"])

    def test_not_enough_no_text_cards(self):
        cards = [card("n1"), card("t1", angle="scale", text="نهاية\nالعالم؟"),
                 card("t2", angle="pov", text="انت\nالهدف!")]
        with self.assertRaisesRegex(ConceptError, "بدون كتابة"):
            concepts.select(cards)

    def test_not_enough_text_cards(self):
        cards = [card("n1"), card("n2", angle="scale"), card("n3", angle="pov")]
        with self.assertRaisesRegex(ConceptError, "بكتابة"):
            concepts.select(cards)


class PromptTest(unittest.TestCase):
    def test_prompt_starts_with_identity_and_ends_no_text(self):
        p = concepts.build_prompt(card())
        self.assertTrue(p.startswith(
            "Cinematic photorealistic YouTube thumbnail photo. Main subject: the man in the reference image."))
        self.assertIn("Preserve his exact facial identity", p.split("\n")[1])
        self.assertTrue(p.endswith("No text, no letters, no captions, no logos, no watermark."))

    def test_prompt_wide_close_line(self):
        self.assertIn("wide-angle lens", concepts.build_prompt(card(camera="wide_close")))
        self.assertNotIn("wide-angle lens", concepts.build_prompt(card(camera="standard")))

    def test_prompt_top_down(self):
        self.assertIn("top-down", concepts.build_prompt(card(camera="top_down")).lower())

    def test_prompt_text_zone_line(self):
        p = concepts.build_prompt(card(text="نهاية\nالعالم؟"))
        self.assertIn("upper-left", p)
        self.assertIn("empty for a headline", p)
        self.assertNotIn("headline", concepts.build_prompt(card()))

    def test_prompt_uses_card_fields_and_colors(self):
        c = card()
        p = concepts.build_prompt(c)
        for value in (c["subject"]["outfit"], c["subject"]["expression"], c["subject"]["action"],
                      c["hero"], c["setting"]):
            self.assertIn(value, p)
        self.assertIn("red", p)
        self.assertIn("right third", p)

    def test_color_name_grays_and_light_colors(self):
        self.assertEqual(concepts.color_name("#2A2A2A"), "charcoal")
        self.assertEqual(concepts.color_name("#C9D1D9"), "silver")
        self.assertEqual(concepts.color_name("#111111"), "black")
        self.assertEqual(concepts.color_name("#9BE7FF"), "light blue")
        self.assertEqual(concepts.color_name("#00FF9C"), "spring green")
        self.assertEqual(concepts.color_name("#0B1A2A"), "dark navy")

    def test_offscreen_prompt_looks_away(self):
        p = concepts.build_prompt(card(angle="offscreen"))
        self.assertNotIn("into the camera", p)
        self.assertIn("outside the frame", p)
        self.assertIn("into the camera", concepts.build_prompt(card(angle="metaphor")))

    def test_wide_close_foreground_only_when_hero_in_foreground(self):
        side = card(camera="wide_close")
        self.assertNotIn("foreground", concepts.build_prompt(side))
        front = card(camera="wide_close")
        front["layout"]["hero"] = "foreground"
        self.assertIn("foreground", concepts.build_prompt(front))

    def test_color_name(self):
        self.assertEqual(concepts.color_name("#E3262B"), "red")
        self.assertEqual(concepts.color_name("#2EC4FF"), "cyan")
        self.assertEqual(concepts.color_name("#FFC400"), "yellow")


def six_cards():
    return [
        card("n1", 10, "metaphor", "calm", "#8B0000"),
        card("n2", 9, "scale", "worried", "#003366"),
        card("n3", 7, "mystery", "smirk", "#004D00"),
        card("t1", 8, "villain", "angry", "#4B0082", text="نهاية\n300 BILLION", font="Kufam", font_latin="Anton"),
        card("t2", 6, "pov", "shocked", "#663300", text="انت\nالهدف!"),
        card("n4", 9.5, "metaphor", "doubt", "#330066"),
    ]


class SketchTest(unittest.TestCase):
    def test_sketch_size_and_no_crash_without_text(self):
        img = concepts.draw_sketch(card(), 80.0)
        self.assertEqual(img.size, (1280, 720))
        self.assertEqual(img.mode, "RGB")

    def test_sketch_with_text_differs(self):
        plain = concepts.draw_sketch(card(), 80.0)
        texted = concepts.draw_sketch(card(text="نهاية\nالعالم؟"), 80.0)
        self.assertTrue(plain.tobytes() != texted.tobytes())

    def test_sketch_every_layout(self):
        for face in concepts.FACE_POS:
            for hero in concepts.HERO_POS:
                for camera in concepts.CAMERAS:
                    c = card(camera=camera)
                    c["layout"].update(face=face, hero=hero)
                    self.assertEqual(concepts.draw_sketch(c, 50.0).size, (1280, 720))

    def test_face_labels_visible_above_foreground_hero(self):
        def white(img):
            r, g, b = img.crop((700, 66, 1280, 660)).split()
            return sum(ImageChops.darker(ImageChops.darker(r, g), b).histogram()[236:])
        base = card(camera="wide_close")
        base["layout"]["hero"] = "foreground"
        labelled = dict(base, expression_ar="هادي وواثق، عابس شوية")
        gained = white(concepts.draw_sketch(labelled, 80.0)) - white(concepts.draw_sketch(base, 80.0))
        self.assertGreater(gained, 900)

    def test_board_rows(self):
        cards = [card(f"c{i}", angle="scale") for i in range(9)]
        board = concepts.draw_board(cards, {"c0", "c3"})
        rows = 3
        self.assertEqual(board.size, (4 * concepts.TILE[0] + 5 * concepts.GAP,
                                      concepts.BOARD_HEADER + rows * (concepts.TILE[1] + concepts.GAP) + concepts.GAP))


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.json = self.dir / "concepts.json"
        self.json.write_text(json.dumps(six_cards(), ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            code = concepts.main([str(a) for a in args])
        return code, buf.getvalue()

    def test_cli_writes_outputs(self):
        code, out = self.run_cli(self.json, "-o", self.dir)
        self.assertEqual(code, 0, out)
        picked = json.loads((self.dir / "picked.json").read_text(encoding="utf-8"))
        self.assertEqual([p["id"] for p in picked["picked"]], ["n1", "n2", "t1"])
        self.assertEqual(picked["notes"], [])
        for p in picked["picked"]:
            self.assertIn("No text, no letters", p["prompt"])
            with Image.open(self.dir / f"sketch-{p['id']}.jpg") as im:
                self.assertEqual(im.size, (1280, 720))
        with Image.open(self.dir / "board.jpg") as im:
            im.load()
        self.assertIn("الدرجة", out)
        self.assertIn("✓", out)

    def test_cli_creates_missing_out_dir(self):
        out_dir = self.dir / "new" / "deep"
        code, out = self.run_cli(self.json, "-o", out_dir)
        self.assertEqual(code, 0, out)
        self.assertTrue((out_dir / "picked.json").exists())

    def test_cli_bad_inputs(self):
        bad_syntax = self.dir / "bad.json"
        bad_syntax.write_text("[{", encoding="utf-8")
        not_list = self.dir / "obj.json"
        not_list.write_text("{}", encoding="utf-8")
        empty = self.dir / "empty.json"
        empty.write_text("[]", encoding="utf-8")
        for path in (self.dir / "missing.json", bad_syntax, not_list, empty):
            with self.subTest(path=path.name):
                code, out = self.run_cli(path, "-o", self.dir / "out")
                self.assertEqual(code, 1)
                self.assertIn("✗ خطأ:", out)
                self.assertNotIn("Traceback", out)


@unittest.skipUnless(shutil.which("git"), "git مو موجود")
class GitignoreTest(unittest.TestCase):
    def ignored(self, path: str) -> bool:
        root = Path(__file__).resolve().parents[2]
        return subprocess.run(["git", "check-ignore", "-q", path], cwd=root).returncode == 0

    def test_sketches_not_ignored(self):
        for folder in ("designs/x", "episodes/x/design"):
            with self.subTest(folder=folder):
                self.assertFalse(self.ignored(f"{folder}/sketch-A1.jpg"))
                self.assertFalse(self.ignored(f"{folder}/board.jpg"))
                self.assertTrue(self.ignored(f"{folder}/scene-A.png"))
                self.assertTrue(self.ignored(f"{folder}/thumb-A.jpg"))


if __name__ == "__main__":
    unittest.main()
