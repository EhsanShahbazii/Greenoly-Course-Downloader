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


def banner(console: "Console", animate: bool = True) -> None:
    """Print the gradient logo, revealing it line by line."""
    total = len(LOGO)
    for index, line in enumerate(LOGO):
        text = Text()
        for column, char in enumerate(line):
            shade = _gradient_color(index + column / max(len(line), 1), total + 1)
            text.append(char, style=shade)
        console.print(text, highlight=False, soft_wrap=True)
        if animate:
            time.sleep(0.045)

    console.print()
    if animate:
        typed = Text("  ")
        with Live(typed, console=console, refresh_per_second=60, transient=False) as live:
            for char in TAGLINE:
                typed.append(char, style="bold #7ef9c7")
                live.update(typed)
                time.sleep(0.012)
    else:
        console.print(Text("  " + TAGLINE, style="bold #7ef9c7"))
    console.print()


def boot_checks(console: "Console", checks: list[tuple[str, callable]]) -> None:
    """Run a series of checks with a spinner, one line each."""
    for label, check in checks:
        with console.status(f"[#7ef9c7]{label}[/]", spinner="dots12"):
            try:
                detail = check()
            except Exception as exc:  # noqa: BLE001 - reported, not fatal here
                console.print(f"  [red]✖[/] {label} [dim]({exc})[/]")
                continue
        suffix = f" [dim]{detail}[/]" if detail else ""
        console.print(f"  [green]✔[/] {label}{suffix}")
    console.print()


class Reporter:
    """No-op reporter; the base contract for the progress UI."""

    def __enter__(self) -> "Reporter":
        return self

    def __exit__(self, *exc_info) -> None:
        return None

    def cookies_loaded(self, source: str, count: int) -> None: ...

    def course_loaded(self, total: int) -> None: ...

    def lesson_started(self, position: int, total: int, lesson: Lesson) -> None: ...

    def lesson_skipped(self, position: int, total: int, title: str) -> None: ...

    def segments_planned(self, count: int) -> None: ...

    def segment_done(self) -> None: ...

    def lesson_saved(self, path: str, size: int) -> None: ...

    def lesson_failed(self, title: str, error: str) -> None: ...

    def summary(self, failures: list[tuple[str, str]]) -> None: ...


class PlainReporter(Reporter):
    """Minimal line-based output for ``--quiet`` or machines without rich."""

    def cookies_loaded(self, source: str, count: int) -> None:
        print(f"cookies: {count} from {source}")

    def course_loaded(self, total: int) -> None:
        print(f"lessons: {total}")

    def lesson_started(self, position: int, total: int, lesson: Lesson) -> None:
        print(f"[{position}/{total}] {lesson.section} / {lesson.title}", flush=True)

    def lesson_skipped(self, position: int, total: int, title: str) -> None:
        print(f"[{position}/{total}] skip (exists): {title}")

    def lesson_saved(self, path: str, size: int) -> None:
        print(f"    saved: {path} ({human_size(size)})")

    def lesson_failed(self, title: str, error: str) -> None:
        print(f"    FAILED: {title}: {error}")

    def summary(self, failures: list[tuple[str, str]]) -> None:
        if failures:
            print(f"\n{len(failures)} lesson(s) failed:")
            for title, error in failures:
                print(f"  - {title}: {error}")
        else:
            print("\nDone.")


class RichReporter(Reporter):
    """Animated progress bars, per-lesson status and a closing summary."""

    def __init__(self, console: "Console", total_lessons: int = 0) -> None:
        self.console = console
        self.total_lessons = total_lessons
        self.saved = 0
        self.skipped = 0
        self.started_at = time.time()
        self.progress = Progress(
            SpinnerColumn(style="#7ef9c7"),
            TextColumn("[bold #7ef9c7]{task.description}"),
            BarColumn(
                bar_width=None,
                complete_style="#00ff87",
                finished_style="#60efff",
                pulse_style="#00ff87",
            ),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TextColumn("[dim]•[/]"),
            TimeRemainingColumn(),
            console=console,
            expand=True,
        )
        self.course_task = None
        self.segment_task = None
        self._running = False

    def __enter__(self) -> "RichReporter":
        self.progress.start()
        self._running = True
        return self

    def __exit__(self, *exc_info) -> None:
        self._stop()

    def _stop(self) -> None:
        if self._running:
            self.progress.stop()
            self._running = False

    def cookies_loaded(self, source: str, count: int) -> None:
        self.console.print(
            f"[green]✔[/] Cookies: [bold]{count}[/] from [dim]{source}[/]"
        )

    def course_loaded(self, total: int) -> None:
        self.total_lessons = total
        self.course_task = self.progress.add_task(
            "course", total=total, completed=0
        )
        self.console.print(f"[green]✔[/] Lessons found: [bold]{total}[/]\n")

    def lesson_started(self, position: int, total: int, lesson: Lesson) -> None:
        label = lesson.title if len(lesson.title) < 52 else lesson.title[:49] + "…"
        self.progress.update(
            self.course_task,
            description=f"[{position}/{total}] {label}",
            total=total,
        )
        self.segment_task = self.progress.add_task(
            "  segments", total=None, completed=0
        )

    def lesson_skipped(self, position: int, total: int, title: str) -> None:
        self.skipped += 1
        self.progress.update(self.course_task, advance=1)
        self.console.print(f"[dim]⏭  skipped (already exists): {title}[/]")

    def segments_planned(self, count: int) -> None:
        if self.segment_task is not None:
            self.progress.update(self.segment_task, total=count, completed=0)

    def segment_done(self) -> None:
        if self.segment_task is not None:
            self.progress.update(self.segment_task, advance=1)

    def lesson_saved(self, path: str, size: int) -> None:
        self.saved += 1
        if self.segment_task is not None:
            self.progress.remove_task(self.segment_task)
            self.segment_task = None
        self.progress.update(self.course_task, advance=1)
        self.console.print(
            f"[green]✔[/] saved [dim]({human_size(size)})[/] → [bold]{Path(path).name}[/]"
        )

    def lesson_failed(self, title: str, error: str) -> None:
        if self.segment_task is not None:
            self.progress.remove_task(self.segment_task)
            self.segment_task = None
        self.progress.update(self.course_task, advance=1)
        self.console.print(f"[red]✖[/] {title} [dim]{error}[/]")

    def summary(self, failures: list[tuple[str, str]]) -> None:
        self._stop()
        elapsed = time.time() - self.started_at
        table = Table(box=SIMPLE, show_header=False, padding=(0, 2))
        table.add_column(style="bold #7ef9c7")
        table.add_column()
        table.add_row("Downloaded", f"[green]{self.saved}[/]")
        table.add_row("Skipped", f"[yellow]{self.skipped}[/]")
        table.add_row("Failed", f"[red]{len(failures)}[/]")
        table.add_row("Elapsed", f"{elapsed / 60:.1f} min")
        self.console.print()
        self.console.print(
            Panel(
                table,
                title="[bold #7ef9c7]Summary[/]",
                border_style="#00ff87",
                box=ROUNDED,
            )
        )
        if failures:
            self.console.print("[red]Failed lessons:[/]")
            for title, error in failures:
                self.console.print(f"  [red]•[/] {title} [dim]{error}[/]")
            self.console.print(
                "\n[dim]Run again — only the failed lessons will be retried.[/]"
            )


def make_console(quiet: bool = False) -> "Console":
    if not RICH_AVAILABLE:
        raise SystemExit("rich is not installed. pip install -r requirements.txt")
    return Console(quiet=quiet, highlight=False, soft_wrap=True)


def make_reporter(console: "Console", quiet: bool = False) -> Reporter:
    if quiet or not RICH_AVAILABLE:
        return PlainReporter()
    return RichReporter(console)
