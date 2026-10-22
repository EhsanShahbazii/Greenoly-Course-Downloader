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


def _lerp(start: tuple[int, int, int], end: tuple[int, int, int], t: float) -> str:
    rgb = tuple(round(a + (b - a) * t) for a, b in zip(start, end))
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _gradient_color(index: int, total: int) -> str:
    if total <= 1:
        return _lerp(_GRADIENT[0], _GRADIENT[-1], 0.0)
    position = index / (total - 1)
    span = len(_GRADIENT) - 1
    segment = min(int(position * span), span - 1)
    local = position * span - segment
    return _lerp(_GRADIENT[segment], _GRADIENT[segment + 1], local)


