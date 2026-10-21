"""Terminal experience: banner, animations, progress bars and summaries."""

from __future__ import annotations

import time
from pathlib import Path

from .api import Lesson
from .media import human_size

try:  # rich is optional at runtime, but strongly recommended
    from rich.box import SIMPLE, ROUNDED
    from rich.console import Console, Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback path
    RICH_AVAILABLE = False


LOGO = [
    " ██████╗ ██████╗ ███████╗███████╗███╗   ██╗ ██████╗ ██╗  ██╗   ██╗",
    "██╔════╝ ██╔══██╗██╔════╝██╔════╝████╗  ██║██╔═══██╗██║  ╚██╗ ██╔╝",
    "██║  ███╗██████╔╝█████╗  █████╗  ██╔██╗ ██║██║   ██║██║   ╚████╔╝ ",
    "██║   ██║██╔══██╗██╔══╝  ██╔══╝  ██║╚██╗██║██║   ██║██║    ╚██╔╝  ",
    "╚██████╔╝██║  ██║███████╗███████╗██║ ╚████║╚██████╔╝███████╗██║   ",
    " ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝   ",
]

TAGLINE = "GreenOly course downloader • max quality • auto-organized folders"

_GRADIENT = [
    (0x00, 0xFF, 0x87),
    (0x22, 0xE5, 0x9A),
    (0x3E, 0xD6, 0xB4),
    (0x4F, 0xCB, 0xD9),
    (0x60, 0xC8, 0xF0),
    (0x60, 0xEF, 0xFF),
]


