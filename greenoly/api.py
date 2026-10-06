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


