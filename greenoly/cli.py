"""Command line interface."""

from __future__ import annotations

import argparse
import os
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
    from .media import tool_path

    ffmpeg = tool_path("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("not installed (brew install ffmpeg)")
    output = subprocess.run(
        [ffmpeg, "-version"], capture_output=True, text=True
    ).stdout.splitlines()
    return output[0].split(" ")[2] if output else "ok"


def _check_openssl() -> str:
    from .media import HAS_AES, tool_path

    if HAS_AES:
        return "AES ready (no OpenSSL installation needed)"
    openssl = tool_path("openssl")
    if openssl is None:
        raise RuntimeError("not installed (brew install openssl)")
    output = subprocess.run(
        [openssl, "version"], capture_output=True, text=True
    ).stdout.strip()
    return output.replace("OpenSSL ", "")


def _check_chromium() -> str:
    from .runtime import ensure_chromium

    ensure_chromium()
    return "ready"


def _list_lessons(args, console) -> int:
    from .api import fetch_course_sections, flatten_lessons, resolve_lesson_url
    from .cookies import build_session, resolve_cookies

    cookies, _source = resolve_cookies(
        args.cookies, args.browser, interactive=args.interactive
    )
    http = build_session(cookies)
    lesson_url = resolve_lesson_url(http, args.url)
    lessons = flatten_lessons(fetch_course_sections(http, lesson_url))

    if not RICH_AVAILABLE:
        for lesson in lessons:
            print(f"{lesson.index:03d}  {lesson.section} / {lesson.title}")
        return 0

    from rich.table import Table

    table = Table(title=f"{len(lessons)} lessons", border_style="#00ff87")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Section", style="#7ef9c7")
    table.add_column("Lesson")
    for lesson in lessons:
        table.add_row(str(lesson.index), lesson.section or "-", lesson.title)
    console.print(table)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    interactive = not argv and sys.stdin.isatty()
    try:
        if interactive:
            argv = _prompt_for_url()
        return _execute(argv, interactive)
    except KeyboardInterrupt:
        print("\nInterrupted. Run the same course again to resume.")
        return 130
    except SystemExit as exc:
        if isinstance(exc.code, int) or exc.code is None:
            return exc.code or 0
        print(f"Error: {exc.code}")
        return 1
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        if interactive:
            try:
                input("\nPress Enter to close...")
            except (EOFError, KeyboardInterrupt):
                pass


def _execute(argv: list[str], interactive: bool) -> int:
    if argv == ["--self-test"]:
        from .runtime import self_test

        self_test()
        return 0

    args = build_parser().parse_args(argv)
    args.interactive = interactive
    quiet = args.quiet or not sys.stdout.isatty() or not RICH_AVAILABLE
    console = make_console(quiet=quiet) if RICH_AVAILABLE else None

    if console is not None and not quiet and not args.list:
        banner(console, animate=not args.no_animation)
        boot_checks(
            console,
            [
                ("ffmpeg", _check_ffmpeg),
                ("decryption", _check_openssl),
                ("playwright chromium", _check_chromium),
            ],
        )

    if args.list:
        return _list_lessons(args, console)

    from .config import Settings

    settings = Settings(
        url=args.url,
        output=args.out,
        cookies_file=args.cookies,
        browser=args.browser,
        single=args.single,
        limit=args.limit,
        workers=args.workers,
        max_segments=args.max_segments,
        quality=args.quality,
        retries=args.retries,
        quiet=quiet,
        interactive=interactive,
    )

    try:
        with make_reporter(console, quiet) as reporter:
            code = run(settings, reporter)
    except KeyboardInterrupt:
        _say(console, "\nInterrupted. Run again to resume where it stopped.")
        return 130
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - top level guard
        _say(console, f"Error: {exc}")
        return 1
    return code


def _prompt_for_url() -> list[str]:
    """Guided whole-course download for users opening the launcher."""
    from .cookies import cookie_file_path

    print("\nGreenOly — download a complete course at the best available quality.")
    print("First log in to greenoly.tv in your usual browser.")
    url = input("Paste the lesson or course URL: ").strip()
    if not url:
        raise SystemExit("No URL given.")
    if not url.startswith("https://greenoly.tv/courses/"):
        raise SystemExit("Please paste a https://greenoly.tv/courses/ link.")
    argv = [url]
    print("Cookies: Enter = detect from browsers, or paste/drag a cookies.txt file.")
    cookies = input("Cookies file [automatic]: ").strip()
    if cookies:
        argv.extend(["--cookies", str(cookie_file_path(cookies))])
    default_output = Path.home() / "Downloads" / "GreenOly"
    output = input(f"Save folder [{default_output}]: ").strip()
    destination = cookie_file_path(output) if output else default_output
    argv.extend(["--out", str(destination)])
    print(f"\nDownloading ALL lessons to: {destination}")
    print("Run the same course again to skip completed videos.\n")
    return argv


def _say(console, message: str) -> None:
    if console is None:
        print(message)
    else:
        console.print(message)
