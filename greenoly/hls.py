"""HLS manifest parsing (master variants + media playlists)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests


