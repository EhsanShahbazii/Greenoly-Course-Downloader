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


def _jar_to_dicts(jar: http.cookiejar.CookieJar, domain: str) -> list[dict]:
    cookies: list[dict] = []
    for cookie in jar:
        host = (cookie.domain or "").lstrip(".")
        if domain and domain not in host:
            continue
        cookies.append(
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain or domain,
                "path": cookie.path or "/",
            }
        )
    return cookies


