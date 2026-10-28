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


