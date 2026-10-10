"""Filesystem-safe naming helpers."""

from __future__ import annotations

import re

from .api import Lesson

_BAD_CHARS = re.compile(r'[\\/:*?"<>|\r\n\t]+')
_SPACES = re.compile(r"\s+")


def safe_name(name: str, maxlen: int = 120) -> str:
    """Strip characters that are illegal on macOS/Windows/Linux filesystems."""
    cleaned = _BAD_CHARS.sub(" ", name or "")
    cleaned = _SPACES.sub(" ", cleaned).strip().strip(".")
    return (cleaned or "untitled")[:maxlen]


def lesson_filename(lesson: Lesson) -> str:
    """``001 - Intro.mp4`` — numbered so the order matches the course."""
    return f"{lesson.index:03d} - {safe_name(lesson.title)}.mp4"


def section_folder(name: str) -> str:
    return safe_name(name) if name else "."
