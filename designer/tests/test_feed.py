import contextlib
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feed  # noqa: E402


def fake_yt_dlp(entries=None, error=None, fail_times=None):
    """yt_dlp وهمي: error يفشل دائماً، وfail_times يفشل أول N مرات وبعدها ينجح."""
    mod = types.ModuleType("yt_dlp")
    mod.utils = types.SimpleNamespace(DownloadError=type("DownloadError", (Exception,), {}))
    mod.calls = []
    state = {"fails": fail_times or 0}

    class YDL:
        def __init__(self, opts):
            self.opts = opts
            mod.calls.append(opts)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, url, download=False):
            if error:
                raise mod.utils.DownloadError(error)
            if state["fails"]:
                state["fails"] -= 1
                raise mod.utils.DownloadError("HTTP Error 403: Forbidden")
            return {"entries": entries}
    mod.YoutubeDL = YDL
    return mod


class FeedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.thumb = self.dir / "t.jpg"
        Image.new("RGB", (1280, 720), (200, 40, 40)).save(self.thumb)

    def item(self, title="عنوان تجريبي طويل شوية حتى ينقسم سطرين بالشاشة الصغيرة"):
        return {"thumb": self.thumb, "title": title, "channel": "قناة", "meta": "1.2 مليون مشاهدة", "duration": "25:00"}

    def test_interleave_positions(self):
        self.assertEqual(feed.interleave(list("ABC"), list("abcdef")), list("aAbcBdeCf"))

    def test_interleave_few_others(self):
        self.assertEqual(feed.interleave(list("ABC"), ["a"]), ["a", "A", "B", "C"])

    def test_formats(self):
        self.assertEqual([feed.fmt_views(v) for v in (1234567, 350000, 900, None)],
                         ["1.2 مليون مشاهدة", "350 ألف مشاهدة", "900 مشاهدة", ""])
        self.assertEqual([feed.fmt_duration(s) for s in (1500, 3723, None)], ["25:00", "1:02:03", ""])

    def test_phone_screen(self):
        img = feed.phone_screen([self.item() for _ in range(9)], dark=True)
        self.assertEqual(img.width, 720)
        self.assertGreater(img.height, 9 * 405)
        self.assertEqual(img.getpixel((2, 2)), (15, 15, 15))
        light = feed.phone_screen([self.item("Evergrande: مؤبد")], dark=False)
        self.assertEqual(light.getpixel((2, 2)), (255, 255, 255))

    def test_meta_line_channel_on_right_views_on_left(self):
        d = feed.ImageDraw.Draw(Image.new("RGB", (720, 100)))
        font = feed.load_font(feed.FONT, 22)
        layout = dict(feed._meta_layout(d, 600, "Preet Banerjee", "8 ألف مشاهدة", font))
        self.assertGreater(layout["Preet Banerjee"], layout["·"])
        self.assertGreater(layout["·"], layout["8 ألف مشاهدة"])

    def test_meta_line_without_views(self):
        d = feed.ImageDraw.Draw(Image.new("RGB", (720, 100)))
        layout = feed._meta_layout(d, 600, "قناتك", "", feed.load_font(feed.FONT, 22))
        self.assertEqual([t for t, _ in layout], ["قناتك"])

    def test_make_feed_offline(self):
        comps = [{"id": f"abcdefghij{i}", "title": "منافس", "channel": "قناة", "views": 1000, "duration": 600}
                 for i in range(6)]
        with mock.patch.object(feed, "fetch_thumb", return_value=self.thumb):
            img = feed.make_feed([self.thumb] * 3, "عنواننا", comps, self.dir)
        self.assertEqual(img.width, 2 * 720 + 3 * 40)

    def test_partial_search_results(self):
        entries = [None, {"id": "abcdefghijk", "title": "x"}, {"title": "بدون رقم"}]
        with mock.patch.dict(sys.modules, {"yt_dlp": fake_yt_dlp(entries)}):
            res = feed.search("evergrande", 6)
        self.assertEqual(res, [{"id": "abcdefghijk", "title": "x", "channel": "", "views": None, "duration": None}])

    def test_search_error_is_arabic(self):
        with mock.patch.dict(sys.modules, {"yt_dlp": fake_yt_dlp(error="blocked")}), \
                mock.patch.object(feed.time, "sleep"):
            with self.assertRaisesRegex(feed.FeedError, "ما گدرت أبحث بيوتيوب"):
                feed.search("evergrande")

    def test_search_retries_with_wait_after_blocks(self):
        fake = fake_yt_dlp([{"id": "abcdefghijk", "title": "x"}], fail_times=2)
        with mock.patch.dict(sys.modules, {"yt_dlp": fake}), mock.patch.object(feed.time, "sleep") as sleep:
            res = feed.search("evergrande")
        self.assertEqual(len(res), 1)
        self.assertEqual(len(fake.calls), 3)
        self.assertEqual(sleep.call_count, 2)

    def test_search_silences_yt_dlp_messages(self):
        fake = fake_yt_dlp(error="blocked")
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with mock.patch.dict(sys.modules, {"yt_dlp": fake}), contextlib.redirect_stdout(buf_out), \
                contextlib.redirect_stderr(buf_err), mock.patch.object(feed.time, "sleep"):
            with self.assertRaises(feed.FeedError):
                feed.search("evergrande")
        logger = fake.calls[0]["logger"]
        for level in ("debug", "info", "warning", "error"):
            getattr(logger, level)("English noise")
        self.assertEqual(buf_out.getvalue() + buf_err.getvalue(), "")

    def test_search_cached_saves_then_reuses(self):
        found = [{"id": "abcdefghijk", "title": "x", "channel": "c", "views": 5, "duration": 60}]
        with mock.patch.object(feed, "search", return_value=found) as s:
            self.assertEqual(feed.search_cached("evergrande", 6, self.dir), found)
            self.assertEqual(feed.search_cached("evergrande", 6, self.dir), found)
        s.assert_called_once()
        self.assertTrue((self.dir / "search.json").exists())

    def test_search_cached_never_mixes_topics(self):
        # "كأس العالم 2026" و"انتخابات 2026" ينطون نفس المجلد (2026)، فلازم الكاش يعرف البحث
        a = [{"id": "aaaaaaaaaaa", "title": "كأس", "channel": "c", "views": 5, "duration": 60}]
        b = [{"id": "bbbbbbbbbbb", "title": "انتخابات", "channel": "c", "views": 5, "duration": 60}]
        with mock.patch.object(feed, "search", side_effect=[a, b]) as s:
            self.assertEqual(feed.search_cached("كأس العالم 2026", 6, self.dir), a)
            self.assertEqual(feed.search_cached("انتخابات 2026", 6, self.dir), b)
        self.assertEqual(s.call_count, 2)

    def test_search_cached_ignores_broken_cache(self):
        (self.dir / "search.json").write_text("{broken", encoding="utf-8")
        with mock.patch.object(feed, "search", return_value=[]) as s:
            self.assertEqual(feed.search_cached("evergrande", 6, self.dir), [])
        s.assert_called_once()

    def test_bad_video_id_rejected(self):
        with self.assertRaises(feed.FeedError):
            feed.fetch_thumb("../etc/pass", self.dir)

    def test_fetch_thumb_uses_cache(self):
        cached = self.dir / "abcdefghijk.jpg"
        Image.new("RGB", (16, 9)).save(cached)
        with mock.patch("urllib.request.urlopen") as u:
            self.assertEqual(feed.fetch_thumb("abcdefghijk", self.dir), cached)
        u.assert_not_called()

    def test_cli_search_failure(self):
        buf = io.StringIO()
        with mock.patch.object(feed, "search_cached", side_effect=feed.FeedError("ما گدرت أبحث بيوتيوب (x).")), \
                contextlib.redirect_stdout(buf):
            code = feed.main(["evergrande", "--ours", str(self.thumb), "--title", "ع", "-o", str(self.dir / "f.jpg")])
        self.assertEqual(code, 1)
        self.assertIn("✗ خطأ", buf.getvalue())

    def test_cli_without_ours_shows_competitors_only(self):
        """قبل الأفكار: المصمم يشوف أغلفة المنافسين بس (بدون أغلفتنا)."""
        comps = [{"id": f"abcdefghij{i}", "title": "منافس", "channel": "قناة", "views": 1000, "duration": 600}
                 for i in range(4)]
        out = self.dir / "before.jpg"
        buf = io.StringIO()
        with mock.patch.object(feed, "search_cached", return_value=comps), \
                mock.patch.object(feed, "fetch_thumb", return_value=self.thumb), contextlib.redirect_stdout(buf):
            code = feed.main(["evergrande", "--title", "ع", "-o", str(out)])
        self.assertEqual(code, 0, buf.getvalue())
        self.assertTrue(out.exists())

    def test_cli_zero_competitors_warns(self):
        buf = io.StringIO()
        with mock.patch.object(feed, "search_cached", return_value=[]), contextlib.redirect_stdout(buf):
            code = feed.main(["evergrande", "--ours", str(self.thumb), "--title", "ع", "-o", str(self.dir / "f.jpg")])
        self.assertEqual(code, 0)
        self.assertIn("⚠️", buf.getvalue())
        self.assertNotIn("✓", buf.getvalue())

    def test_video_id_rejects_trailing_newline(self):
        self.assertIsNone(feed.VIDEO_ID.match("abcdefghijk\n"))

    def test_cli_bad_out_extension_arabic(self):
        buf = io.StringIO()
        with mock.patch.object(feed, "search_cached", return_value=[]), contextlib.redirect_stdout(buf):
            code = feed.main(["evergrande", "--ours", str(self.thumb), "--title", "ع", "-o", str(self.dir / "f")])
        self.assertEqual(code, 1)
        self.assertIn("✗ خطأ", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
