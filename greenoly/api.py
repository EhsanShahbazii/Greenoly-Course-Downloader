"""Course structure discovery on greenoly.tv.

The site is a Next.js app: lesson pages ship their data inside the RSC payload
(a streamed React tree) instead of a JSON API. We fetch the page with the
``RSC: 1`` header and pull the ``sections`` array out of the payload.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import requests

from .config import SITE


@dataclass
class Lesson:
    id: str
    title: str
    section: str
    index: int


def _bracket_match(text: str, start: int) -> int:
    """Return the index just past the JSON array that begins at ``start``."""
    if text[start] != "[":
        raise ValueError("expected '['")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError("unbalanced JSON array")


def _get_rsc(session: requests.Session, url: str) -> str:
    resp = session.get(url, headers={"RSC": "1"}, allow_redirects=True, timeout=60)
    resp.raise_for_status()
    # Without this the Persian titles come back as mojibake.
    resp.encoding = "utf-8"
    return resp.text


