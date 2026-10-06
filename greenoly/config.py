"""Static configuration, endpoints and the settings object."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

SITE = "https://greenoly.tv"
VOD_HOST = "https://vod.greenoly.org/"
PLAYER_ENDPOINT = SITE + "/api/courses/lessons/{lesson_id}/player"
COOKIE_DOMAIN = "greenoly.tv"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36"
)

DEFAULT_OUTPUT = "downloads"
DEFAULT_WORKERS = 6
DEFAULT_RETRIES = 6

PLAYLIST_TIMEOUT_MS = 45_000
PLAYER_SETTLE_MS = 6_000

SUPPORTED_BROWSERS = (
    "chrome",
    "brave",
    "edge",
    "chromium",
    "firefox",
    "safari",
    "opera",
    "vivaldi",
)


