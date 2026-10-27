"""Command line interface."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .config import (
    DEFAULT_OUTPUT,
    DEFAULT_RETRIES,
    DEFAULT_WORKERS,
    SUPPORTED_BROWSERS,
)
from .downloader import run
from .ui import RICH_AVAILABLE, banner, boot_checks, make_console, make_reporter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="greenoly",
        description="Download GreenOly TV courses at the highest available quality.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  greenoly \"https://greenoly.tv/courses/<slug>/lessons/<id>\" --browser chrome\n"
            "  greenoly \"<lesson-url>\" --cookies greenoly.tv_cookies.txt --out downloads\n"
        ),
    )
    parser.add_argument("url", help="lesson or course URL")
    parser.add_argument(
        "--cookies",
        type=Path,
        help="Netscape cookies.txt file (optional; defaults to reading the browser)",
    )
    parser.add_argument(
        "--browser",
        default="auto",
        choices=("auto",) + SUPPORTED_BROWSERS,
        help="read cookies from this browser (default: auto)",
    )
    parser.add_argument("--out", type=Path, default=Path(DEFAULT_OUTPUT), help="output folder")
    parser.add_argument("--single", action="store_true", help="download only this lesson")
    parser.add_argument("--limit", type=int, help="download only the first N lessons")
    parser.add_argument(
        "--quality",
        default="best",
        help="best, or a height cap such as 720p / 480p",
    )
    parser.add_argument(
        "--workers", type=int, default=DEFAULT_WORKERS, help="parallel segment downloads"
    )
    parser.add_argument(
        "--retries", type=int, default=DEFAULT_RETRIES, help="retries per segment"
    )
    parser.add_argument(
        "--max-segments", type=int, help="debug: limit segments per lesson"
    )
    parser.add_argument("--list", action="store_true", help="only list the lessons")
    parser.add_argument("--quiet", action="store_true", help="plain output, no animation")
    parser.add_argument(
        "--no-animation", action="store_true", help="disable the banner animation"
    )
    parser.add_argument("--version", action="version", version=f"greenoly {__version__}")
    return parser


def _check_ffmpeg() -> str:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("not installed (brew install ffmpeg)")
    output = subprocess.run(
        ["ffmpeg", "-version"], capture_output=True, text=True
    ).stdout.splitlines()
    return output[0].split(" ")[2] if output else "ok"


def _check_openssl() -> str:
    if shutil.which("openssl") is None:
        raise RuntimeError("not installed (brew install openssl)")
    output = subprocess.run(
        ["openssl", "version"], capture_output=True, text=True
    ).stdout.strip()
    return output.replace("OpenSSL ", "")


def _check_chromium() -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        path = playwright.chromium.executable_path
    if not path or not os.path.exists(path):
        raise RuntimeError("python -m playwright install chromium")
    return "ready"


