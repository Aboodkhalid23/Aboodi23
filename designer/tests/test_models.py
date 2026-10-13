import hashlib
import http.client
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import models  # noqa: E402

TINY = {"tiny": {"file": "tiny.bin", "url": "https://example.invalid/tiny.bin",
                 "sha256": hashlib.sha256(b"hello").hexdigest()}}


def fake_urlopen(data):
    return mock.MagicMock(__enter__=lambda s: io.BytesIO(data), __exit__=lambda *a: False)


class ModelsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        patches = [mock.patch.object(models, "MODELS_DIR", self.dir), mock.patch.dict(models.MODELS, TINY)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_downloads_and_verifies(self):
        with mock.patch("urllib.request.urlopen", return_value=fake_urlopen(b"hello")):
            p = models.ensure_model("tiny")
        self.assertEqual(p.read_bytes(), b"hello")

    def test_bad_checksum_deletes_file(self):
        with mock.patch("urllib.request.urlopen", return_value=fake_urlopen(b"evil")):
            with self.assertRaisesRegex(models.ModelError, "البصمة"):
                models.ensure_model("tiny")
        self.assertFalse((self.dir / "tiny.bin").exists())
        self.assertFalse((self.dir / "tiny.bin.part").exists())

    def test_existing_good_file_not_downloaded(self):
        (self.dir / "tiny.bin").write_bytes(b"hello")
        with mock.patch("urllib.request.urlopen") as u:
            models.ensure_model("tiny")
        u.assert_not_called()

    def test_existing_bad_file_is_downloaded_again(self):
        (self.dir / "tiny.bin").write_bytes(b"old")
        with mock.patch("urllib.request.urlopen", return_value=fake_urlopen(b"hello")) as u:
            p = models.ensure_model("tiny")
        u.assert_called_once()
        self.assertEqual(p.read_bytes(), b"hello")

    def test_network_error_is_arabic(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("blocked")):
            with self.assertRaisesRegex(models.ModelError, "ما گدرت أنزّل"):
                models.ensure_model("tiny")

    def test_cut_off_download_is_arabic(self):
        cut = mock.MagicMock()
        cut.read.side_effect = http.client.IncompleteRead(b"hel")
        with mock.patch("urllib.request.urlopen",
                        return_value=mock.MagicMock(__enter__=lambda s: cut, __exit__=lambda *a: False)):
            with self.assertRaisesRegex(models.ModelError, "ما گدرت أنزّل"):
                models.ensure_model("tiny")
        self.assertFalse((self.dir / "tiny.bin.part").exists())

    def test_unknown_model(self):
        with self.assertRaisesRegex(models.ModelError, "مو معروف"):
            models.ensure_model("nope")

    def test_real_models_are_pinned(self):
        self.assertEqual(set(models.MODELS) - {"tiny"}, {"upscaler", "face"})
        for name in ("upscaler", "face"):
            self.assertEqual(len(models.MODELS[name]["sha256"]), 64)
            self.assertTrue(models.MODELS[name]["url"].startswith("https://huggingface.co/"))


if __name__ == "__main__":
    unittest.main()
