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


def _fetch_segment(
    segment: Segment,
    index: int,
    headers: dict,
    local: threading.local,
    retries: int,
    tmpdir: str,
) -> tuple[int, str]:
    request_headers = dict(headers)
    if segment.offset is not None and segment.length is not None:
        end = segment.offset + segment.length - 1
        request_headers["Range"] = f"bytes={segment.offset}-{end}"

    payload: bytes | None = None
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = _thread_session(local).get(
                segment.url, headers=request_headers, timeout=120
            )
            response.raise_for_status()
            payload = response.content
            break
        except Exception as exc:  # noqa: BLE001 - the CDN resets connections
            last_error = exc
            time.sleep(min(1.5 * (attempt + 1), 8))
    if payload is None:
        raise RuntimeError(f"segment {index} failed after {retries} tries: {last_error}")

    data = decrypt_segment(payload, segment.key, segment.iv)
    path = os.path.join(tmpdir, f"{index:05d}.ts")
    with open(path, "wb") as handle:
        handle.write(data)
    return index, path


