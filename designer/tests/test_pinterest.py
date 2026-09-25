import contextlib
import io
import json
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pinterest  # noqa: E402

PAYLOAD = {"resource_response": {"data": {"results": [
    {"id": "111", "title": "Space thumbnail", "description": "black hole",
     "images": {"orig": {"url": "https://i.pinimg.com/originals/a.jpg"}, "236x": {"url": "https://i.pinimg.com/236x/a.jpg"}}},
    {"id": "222", "grid_title": "Shock face", "images": {"736x": {"url": "https://i.pinimg.com/736x/b.jpg"}}},
    {"id": "333", "title": "no image"},
    "not-a-pin",
    {"id": "444", "images": {"474x": {"url": "https://i.pinimg.com/474x/d.jpg"}}},
]}}}


class PinterestTest(unittest.TestCase):
    def test_parse_picks_biggest_image_and_skips_bad_items(self):
        pins = pinterest.parse_results(PAYLOAD, 10)
        self.assertEqual([p["id"] for p in pins], ["111", "222", "444"])
        self.assertEqual(pins[0]["image"], "https://i.pinimg.com/originals/a.jpg")
        self.assertEqual(pins[1]["title"], "Shock face")
        self.assertEqual(pins[0]["link"], "https://www.pinterest.com/pin/111/")

    def test_parse_respects_limit(self):
        self.assertEqual(len(pinterest.parse_results(PAYLOAD, 2)), 2)

    def test_parse_empty_or_odd_payload(self):
        self.assertEqual(pinterest.parse_results({}, 5), [])
        self.assertEqual(pinterest.parse_results({"resource_response": {"data": []}}, 5), [])

    def test_search_url_carries_query(self):
        url = pinterest.search_url("youtube thumbnail", 30)
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        data = json.loads(qs["data"][0])
        self.assertEqual(data["options"]["query"], "youtube thumbnail")
        self.assertEqual(data["options"]["page_size"], 30)

    def test_slug(self):
        self.assertEqual(pinterest.slug("YouTube Thumbnail!"), "youtube-thumbnail")
        self.assertTrue(pinterest.slug("غلاف").startswith("q-"))

    def test_slug_different_arabic_queries_give_different_slugs(self):
        # Minor 8: two Arabic queries must not collapse to the same "search" slug
        # and overwrite each other's saved images.
        a = pinterest.slug("غلاف يوتيوب")
        b = pinterest.slug("غلاف تيك توك")
        self.assertNotEqual(a, b)
        self.assertTrue(a.startswith("q-"))
        self.assertTrue(b.startswith("q-"))

    def test_network_blocked_gives_arabic_error(self):
        buf = io.StringIO()
        with mock.patch.object(pinterest, "fetch_json", side_effect=OSError("blocked")), \
                contextlib.redirect_stdout(buf):
            code = pinterest.main(["youtube thumbnail"])
        self.assertEqual(code, 1)
        self.assertIn("*.pinterest.com", buf.getvalue())

    def test_parse_list_payload_returns_empty(self):
        self.assertEqual(pinterest.parse_results([], 5), [])

    def test_parse_non_dict_resource_response_returns_empty(self):
        self.assertEqual(pinterest.parse_results({"resource_response": "x"}, 5), [])

    def test_parse_skips_item_with_non_dict_images(self):
        payload = {"resource_response": {"data": {"results": [
            {"id": "111", "images": "abc"},
            {"id": "222", "images": {"orig": {"url": "https://i.pinimg.com/originals/a.jpg"}}},
        ]}}}
        pins = pinterest.parse_results(payload, 10)
        self.assertEqual([p["id"] for p in pins], ["222"])

    def test_main_malformed_json_gives_arabic_error(self):
        buf = io.StringIO()
        with mock.patch.object(pinterest, "fetch_json", return_value=[1, 2]), \
                contextlib.redirect_stdout(buf):
            code = pinterest.main(["test"])
        self.assertEqual(code, 1)
        self.assertIn("رد Pinterest مو مفهوم", buf.getvalue())

    def test_download_skips_non_https_and_non_pinimg_urls(self):
        # Minor 7: only https URLs on a pinimg.com host may be fetched.
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "out.jpg"
            with mock.patch.object(pinterest.urllib.request, "urlopen") as urlopen_mock:
                pinterest.download("http://i.pinimg.com/originals/a.jpg", dest)
                pinterest.download("https://evil.example.com/a.jpg", dest)
                pinterest.download("file:///etc/passwd", dest)
            urlopen_mock.assert_not_called()
            self.assertFalse(dest.exists())

    def test_download_allows_https_pinimg(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "out.jpg"
            fake_resp = mock.MagicMock()
            fake_resp.read.return_value = b"data"
            fake_resp.__enter__.return_value = fake_resp
            with mock.patch.object(pinterest.urllib.request, "urlopen", return_value=fake_resp) as urlopen_mock:
                pinterest.download("https://i.pinimg.com/originals/a.jpg", dest)
            urlopen_mock.assert_called_once()
            self.assertEqual(dest.read_bytes(), b"data")

    def test_main_happy_path_writes_index_with_file_field_and_continues_on_error(self):
        valid_payload = {"resource_response": {"data": {"results": [
            {"id": "111", "title": "A", "images": {"orig": {"url": "https://i.pinimg.com/originals/111.jpg"}}},
            {"id": "222", "title": "B", "images": {"orig": {"url": "https://i.pinimg.com/originals/222.jpg"}}},
        ]}}}

        def fake_download(url, dest):
            if "222" in url:
                raise OSError("boom")
            dest.write_bytes(b"fake")

        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            buf = io.StringIO()
            with mock.patch.object(pinterest, "fetch_json", return_value=valid_payload), \
                    mock.patch.object(pinterest, "download", side_effect=fake_download), \
                    mock.patch.object(pinterest, "OUT_DIR", out_dir), \
                    contextlib.redirect_stdout(buf):
                code = pinterest.main(["test query"])
            self.assertEqual(code, 0)
            index_path = out_dir / pinterest.slug("test query") / "index.json"
            data = json.loads(index_path.read_text(encoding="utf-8"))
            self.assertEqual(data[0]["file"], "01-111.jpg")
            self.assertNotIn("file", data[1])
            self.assertIn("انحفظت", buf.getvalue())

    def test_main_write_error_gives_arabic_error(self):
        buf = io.StringIO()
        valid_payload = {"resource_response": {"data": {"results": [
            {"id": "111", "title": "Test", "images": {"orig": {"url": "https://i.pinimg.com/originals/a.jpg"}}},
        ]}}}
        with mock.patch.object(pinterest, "fetch_json", return_value=valid_payload), \
                mock.patch.object(pinterest, "download", return_value=None), \
                mock.patch.object(Path, "mkdir", side_effect=PermissionError("no write")), \
                contextlib.redirect_stdout(buf):
            code = pinterest.main(["test"])
        self.assertEqual(code, 1)
        self.assertIn("ما گدرت أحفظ الصور", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
