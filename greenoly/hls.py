"""HLS manifest parsing (master variants + media playlists)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests


@dataclass
class Variant:
    url: str
    bandwidth: int = 0
    width: int = 0
    height: int = 0

    @property
    def pixels(self) -> int:
        return self.width * self.height


@dataclass
class Segment:
    url: str
    offset: int | None = None
    length: int | None = None
    key: bytes | None = None
    iv: bytes | None = None


def parse_master(text: str, base_url: str) -> list[Variant]:
    """Extract every ``EXT-X-STREAM-INF`` entry of a master playlist."""
    lines = text.splitlines()
    variants: list[Variant] = []
    for i, line in enumerate(lines):
        if not line.startswith("#EXT-X-STREAM-INF"):
            continue
        url = ""
        for follow in lines[i + 1 :]:
            if follow.strip() and not follow.startswith("#"):
                url = urljoin(base_url, follow.strip())
                break
        if not url:
            continue
        resolution = re.search(r"RESOLUTION=(\d+)x(\d+)", line)
        bandwidth = re.search(r"BANDWIDTH=(\d+)", line)
        variants.append(
            Variant(
                url=url,
                bandwidth=int(bandwidth.group(1)) if bandwidth else 0,
                width=int(resolution.group(1)) if resolution else 0,
                height=int(resolution.group(2)) if resolution else 0,
            )
        )
    return variants


def pick_variant(text: str, base_url: str, max_height: int | None = None) -> Variant | None:
    """Best variant, optionally capped to ``max_height`` pixels tall."""
    variants = parse_master(text, base_url)
    if max_height:
        capped = [v for v in variants if 0 < v.height <= max_height]
        if capped:
            variants = capped
    if not variants:
        return None
    variants.sort(key=lambda v: (v.pixels, v.bandwidth), reverse=True)
    return variants[0]


def _attr(line: str, name: str) -> str | None:
    """Read an attribute value, quoted or bare (``IV=0x..`` is often bare)."""
    match = re.search(rf'{name}=(?:"([^"]*)"|([^,]*))', line)
    if not match:
        return None
    value = match.group(1) if match.group(1) is not None else match.group(2)
    return value.strip() or None


def _iv(value: str | None, sequence: int) -> bytes | None:
    if value:
        hexpart = value[2:] if value.lower().startswith("0x") else value
        try:
            return bytes.fromhex(hexpart)
        except ValueError:
            return None
    return sequence.to_bytes(16, "big")


