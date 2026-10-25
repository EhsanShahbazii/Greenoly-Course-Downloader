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


