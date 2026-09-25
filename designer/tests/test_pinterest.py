import contextlib
import io
import json
import sys
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
        self.assertEqual(pinterest.slug("غلاف"), "search")

    def test_network_blocked_gives_arabic_error(self):
        buf = io.StringIO()
        with mock.patch.object(pinterest, "fetch_json", side_effect=OSError("blocked")), \
                contextlib.redirect_stdout(buf):
            code = pinterest.main(["youtube thumbnail"])
        self.assertEqual(code, 1)
        self.assertIn("*.pinterest.com", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
