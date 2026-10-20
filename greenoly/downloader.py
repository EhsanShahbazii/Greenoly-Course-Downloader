"""The download engine: segments, lessons and whole courses."""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from .api import (
    Lesson,
    course_base_from_url,
    fetch_course_sections,
    find_lesson,
    flatten_lessons,
    lesson_id_from_url,
    resolve_lesson_url,
)
from .browser import CapturedPlaylist, capture_playlist
from .config import USER_AGENT, Settings
from .cookies import build_session, resolve_cookies
from .hls import Segment, parse_media_playlist
from .media import concat_files, decrypt_segment, remux_to_mp4, require_tools
from .naming import lesson_filename, section_folder
from .ui import Reporter


def _thread_session(local: threading.local) -> requests.Session:
    session = getattr(local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        local.session = session
    return session


