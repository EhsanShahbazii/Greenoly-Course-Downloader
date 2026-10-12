"""Cookie loading: Netscape files or straight out of the user's browser."""

from __future__ import annotations

import http.cookiejar
from pathlib import Path

import requests

from .config import COOKIE_DOMAIN, SUPPORTED_BROWSERS, USER_AGENT


def load_netscape_cookies(path: str | Path) -> list[dict]:
    """Parse a Netscape ``cookies.txt`` file into Playwright/requests cookies."""
    cookies: list[dict] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 7:
                continue
            domain, _flag, cpath, _secure, _exp, name, value = parts[:7]
            cookies.append(
                {
                    "name": name,
                    "value": value,
                    "domain": domain,
                    "path": cpath or "/",
                }
            )
    return cookies


