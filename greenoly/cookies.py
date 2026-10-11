"""Cookie loading: Netscape files or straight out of the user's browser."""

from __future__ import annotations

import http.cookiejar
from pathlib import Path

import requests

from .config import COOKIE_DOMAIN, SUPPORTED_BROWSERS, USER_AGENT


