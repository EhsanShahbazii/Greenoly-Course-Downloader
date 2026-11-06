"""Regression coverage for portable startup and browser-cookie fallback."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import requests

from greenoly import cli, runtime
from greenoly.cookies import load_netscape_cookies, resolve_cookies
from greenoly.downloader import _build_headers
from greenoly.media import decrypt_segment


class DecryptionTests(unittest.TestCase):
    def test_aes_cbc_known_vector(self):
        self.assertEqual(
            decrypt_segment(
                bytes.fromhex("7649abac8119b246cee98e9b12e9197d"),
                bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c"),
                bytes.fromhex("000102030405060708090a0b0c0d0e0f"),
            ),
            bytes.fromhex("6bc1bee22e409f96e93d7e117393172a"),
        )

    def test_unencrypted_segment_passes_through(self):
        self.assertEqual(decrypt_segment(b"video data", None, None), b"video data")


class HeaderTests(unittest.TestCase):
    def test_persian_referer_can_be_sent_as_http_header(self):
        url = "https://greenoly.tv/courses/ترکیبیات/lessons/example"
        headers = _build_headers(url)
        headers["Referer"].encode("ascii")
        self.assertEqual(headers, _build_headers(requests.utils.requote_uri(url)))
        self.assertNotIn("%25", headers["Referer"])


class CookieTests(unittest.TestCase):
    def test_httponly_cookie_export_is_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cookies.txt"
            path.write_text(
                "# Netscape HTTP Cookie File\n"
                "#HttpOnly_.greenoly.tv\tTRUE\t/\tTRUE\t0\tsession\ttest-value\n"
            )
            self.assertEqual(load_netscape_cookies(path)[0]["name"], "session")

    def test_automatic_cookie_failure_offers_manual_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cookies with spaces.txt"
            path.write_text(".greenoly.tv\tTRUE\t/\tTRUE\t0\tsession\ttest\n")
            with patch("greenoly.cookies.cookies_from_browser", side_effect=SystemExit("locked")):
                with patch("builtins.input", return_value=f'"{path}"'):
                    cookies, source = resolve_cookies(None, "auto", interactive=True)
            self.assertEqual(cookies[0]["value"], "test")
            self.assertIn("cookies with spaces.txt", source)

    def test_cli_cookie_failure_does_not_prompt(self):
        with patch("greenoly.cookies.cookies_from_browser", side_effect=SystemExit("locked")):
            with patch("builtins.input") as prompt:
                with self.assertRaises(SystemExit):
                    resolve_cookies(None, "auto")
                prompt.assert_not_called()


class StartupTests(unittest.TestCase):
    def test_guided_mode_downloads_whole_course_and_accepts_cookie_file(self):
        with patch("builtins.input", side_effect=[
            "https://greenoly.tv/courses/test", '"/tmp/my cookies.txt"', ""
        ]):
            args = cli.build_parser().parse_args(cli._prompt_for_url())
        self.assertFalse(args.single)
        self.assertEqual(args.cookies, Path("/tmp/my cookies.txt"))
        self.assertEqual(args.out, Path.home() / "Downloads" / "GreenOly")

    def test_startup_failure_keeps_interactive_window_open(self):
        with patch("sys.stdin.isatty", return_value=True):
            with patch("greenoly.cli._prompt_for_url", side_effect=SystemExit("bad URL")):
                with patch("builtins.input", return_value="") as prompt:
                    self.assertEqual(cli.main([]), 1)
                    prompt.assert_called_once_with("\nPress Enter to close...")

    def test_frozen_browser_missing_never_attempts_download(self):
        with patch("greenoly.runtime.chromium_ready", return_value=False):
            with patch("greenoly.runtime.is_frozen", return_value=True):
                with patch("greenoly.runtime.subprocess.run") as run:
                    with self.assertRaisesRegex(SystemExit, "Extract the complete"):
                        runtime.ensure_chromium()
                    run.assert_not_called()

    def test_portable_browser_path_overrides_existing_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            browsers = Path(tmp) / "browsers"
            browsers.mkdir()
            with patch("greenoly.runtime.is_frozen", return_value=True):
                with patch("sys.executable", str(Path(tmp) / "GreenOly")):
                    with patch.dict(os.environ, {"PLAYWRIGHT_BROWSERS_PATH": "/old/cache"}):
                        runtime.configure_browser_path()
                        self.assertEqual(os.environ["PLAYWRIGHT_BROWSERS_PATH"], str(browsers.resolve()))


if __name__ == "__main__":
    unittest.main()
