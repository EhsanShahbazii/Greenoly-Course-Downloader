"""Unit tests for manifest parsing and naming (no network needed)."""

from __future__ import annotations

import unittest

from greenoly.api import Lesson
from greenoly.hls import parse_master, parse_media_playlist, pick_variant
from greenoly.naming import lesson_filename, safe_name

MASTER = """#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
360/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720
720/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1200000,RESOLUTION=854x480
480/index.m3u8
"""

MEDIA = """#EXTM3U
#EXT-X-TARGETDURATION:6
#EXT-X-MEDIA-SEQUENCE:7
#EXT-X-KEY:METHOD=AES-128,URI="key.bin",IV=0x00000000000000000000000000000001
#EXTINF:6.0,
#EXT-X-BYTERANGE:1000@0
seg.ts
#EXTINF:6.0,
#EXT-X-BYTERANGE:500
seg.ts
"""


class FakeResponse:
    content = b"0" * 16

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def get(self, url, headers=None, timeout=None):
        return FakeResponse()


class MasterPlaylistTests(unittest.TestCase):
    def test_parses_all_variants(self) -> None:
        variants = parse_master(MASTER, "https://cdn.example/")
        self.assertEqual(len(variants), 3)
        self.assertEqual(variants[0].url, "https://cdn.example/360/index.m3u8")
        self.assertEqual(variants[1].height, 720)

    def test_picks_highest_by_default(self) -> None:
        best = pick_variant(MASTER, "https://cdn.example/")
        self.assertIsNotNone(best)
        self.assertEqual(best.height, 720)

    def test_respects_height_cap(self) -> None:
        capped = pick_variant(MASTER, "https://cdn.example/", max_height=480)
        self.assertIsNotNone(capped)
        self.assertEqual(capped.height, 480)

    def test_falls_back_when_cap_matches_nothing(self) -> None:
        capped = pick_variant(MASTER, "https://cdn.example/", max_height=120)
        self.assertEqual(capped.height, 720)


class MediaPlaylistTests(unittest.TestCase):
    def test_byteranges_and_key(self) -> None:
        segments = parse_media_playlist(
            MEDIA, "https://cdn.example/720/", {}, FakeSession()
        )
        self.assertEqual(len(segments), 2)
        self.assertEqual((segments[0].offset, segments[0].length), (0, 1000))
        self.assertEqual((segments[1].offset, segments[1].length), (1000, 500))
        self.assertEqual(segments[0].key, b"0" * 16)
        self.assertEqual(segments[0].iv, bytes(15) + b"\x01")
        self.assertEqual(segments[0].url, "https://cdn.example/720/seg.ts")


class NamingTests(unittest.TestCase):
    def test_strips_illegal_characters(self) -> None:
        self.assertEqual(safe_name('درس ۱: مقدمه/بخش'), "درس ۱ مقدمه بخش")

    def test_numbers_files(self) -> None:
        lesson = Lesson(id="x", title="معرفی دوره", section="مقدمه", index=3)
        self.assertEqual(lesson_filename(lesson), "003 - معرفی دوره.mp4")


if __name__ == "__main__":
    unittest.main()
