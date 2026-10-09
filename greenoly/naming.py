"""Filesystem-safe naming helpers."""

from __future__ import annotations

import re

from .api import Lesson

_BAD_CHARS = re.compile(r'[\\/:*?"<>|\r\n\t]+')
_SPACES = re.compile(r"\s+")


