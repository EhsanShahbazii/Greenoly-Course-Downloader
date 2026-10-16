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


def parse_media_playlist(
    text: str,
    base_url: str,
    headers: dict,
    http: requests.Session,
) -> list[Segment]:
    """Parse a media playlist, resolving byte ranges and AES-128 keys."""
    lines = [line.strip() for line in text.splitlines()]
    segments: list[Segment] = []
    current_key: bytes | None = None
    current_iv: bytes | None = None
    pending_range: tuple[int, int] | None = None
    previous_end = 0
    sequence = 0
    key_cache: dict[str, bytes] = {}

    for line in lines:
        if not line:
            continue
        if line.startswith("#EXT-X-MEDIA-SEQUENCE:"):
            sequence = int(line.split(":", 1)[1])
        elif line.startswith("#EXT-X-KEY:"):
            method = _attr(line, "METHOD")
            if method == "NONE":
                current_key = None
                current_iv = None
                continue
            uri = _attr(line, "URI")
            current_iv = _iv(_attr(line, "IV"), sequence + len(segments))
            if uri:
                key_url = urljoin(base_url, uri)
                if key_url not in key_cache:
                    response = http.get(key_url, headers=headers, timeout=60)
                    response.raise_for_status()
                    key_cache[key_url] = response.content
                current_key = key_cache[key_url]
        elif line.startswith("#EXT-X-BYTERANGE:"):
            spec = line.split(":", 1)[1]
            if "@" in spec:
                length, offset = spec.split("@", 1)
                pending_range = (int(offset), int(length))
            else:
                pending_range = (previous_end, int(spec))
            previous_end = pending_range[0] + pending_range[1]
        elif line.startswith("#"):
            continue
        else:
            offset = pending_range[0] if pending_range else None
            length = pending_range[1] if pending_range else None
            pending_range = None
            segments.append(
                Segment(
                    url=urljoin(base_url, line),
                    offset=offset,
                    length=length,
                    key=current_key,
                    iv=current_iv,
                )
            )
    return segments


def playlist_base(media_text: str, fallback: str) -> str:
    """Absolute URL of the media playlist itself, used to resolve segments."""
    return fallback


