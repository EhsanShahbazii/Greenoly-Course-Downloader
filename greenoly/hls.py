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


