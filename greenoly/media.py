"""Segment decryption and MP4 remuxing."""

from __future__ import annotations

import os
import shutil
import subprocess


def require_tools() -> None:
    missing = [tool for tool in ("ffmpeg", "openssl") if shutil.which(tool) is None]
    if missing:
        raise SystemExit(
            "Missing required tools: "
            + ", ".join(missing)
            + "\n  macOS: brew install ffmpeg openssl"
        )


