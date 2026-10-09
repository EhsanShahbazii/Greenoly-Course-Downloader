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


def fetch_course_sections(session: requests.Session, lesson_url: str) -> list[dict]:
    """Return the raw ``sections`` array of the course that owns ``lesson_url``."""
    text = _get_rsc(session, lesson_url)
    key = '"sections":'
    idx = text.find(key)
    if idx == -1:
        raise RuntimeError("Could not find the course structure in the page response")
    arr_start = text.index("[", idx + len(key))
    arr_end = _bracket_match(text, arr_start)
    return json.loads(text[arr_start:arr_end])


def flatten_lessons(sections: list[dict]) -> list[Lesson]:
    lessons: list[Lesson] = []
    counter = 0
    for section in sections:
        section_title = (section.get("title") or "").strip()
        for raw in section.get("lessons") or []:
            counter += 1
            lessons.append(
                Lesson(
                    id=raw["id"],
                    title=(raw.get("title") or raw["id"]).strip(),
                    section=section_title,
                    index=counter,
                )
            )
    return lessons


def lesson_id_from_url(url: str) -> str:
    match = re.search(r"/lessons/([A-Za-z0-9]+)", url)
    if not match:
        raise SystemExit("Could not find a lesson id in the URL")
    return match.group(1)


def course_base_from_url(url: str) -> str:
    match = re.match(r"(https?://[^/]+/courses/[^/]+)", url)
    if not match:
        raise SystemExit("Could not find the course base URL")
    return match.group(1)


def resolve_lesson_url(session: requests.Session, url: str) -> str:
    """Accept a course URL too, deriving a lesson URL from its first lesson."""
    if "/lessons/" in url:
        return url
    text = _get_rsc(session, url)
    match = re.search(r"/lessons/([A-Za-z0-9]{16,})", text)
    if not match:
        raise SystemExit("Could not find any lesson in the course page")
    return f"{course_base_from_url(url)}/lessons/{match.group(1)}"


def find_lesson(sections: list[dict], lesson_id: str) -> Lesson | None:
    for lesson in flatten_lessons(sections):
        if lesson.id == lesson_id:
            return lesson
    return None


def lesson_page_url(course_base: str, lesson_id: str) -> str:
    return f"{SITE}{course_base.split(SITE, 1)[-1]}/lessons/{lesson_id}"
