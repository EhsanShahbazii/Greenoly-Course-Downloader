"""Runtime prerequisites for the standalone build.

Chromium cannot be shipped inside the PyInstaller bundle on macOS (code-signing
fails on the Chrome for Testing app), so it is downloaded once on first run and
then reused from the Playwright cache.
"""

from __future__ import annotations

import subprocess
import sys


def chromium_path() -> str | None:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            path = playwright.chromium.executable_path
    except Exception:  # noqa: BLE001 - driver not available yet
        return None
    return path or None


def chromium_ready() -> bool:
    import os

    path = chromium_path()
    return bool(path and os.path.exists(path))


def _driver_command() -> list[str]:
    from playwright._impl._driver import compute_driver_executable

    driver = compute_driver_executable()
    if isinstance(driver, (tuple, list)):
        return [str(part) for part in driver]
    return [str(driver)]


def ensure_chromium(on_progress=None) -> str:
    """Install Chromium if missing and return its executable path."""
    if chromium_ready():
        return chromium_path() or ""
    if on_progress:
        on_progress("Downloading Chromium (one time, ~150 MB)...")
    try:
        subprocess.run(
            [*_driver_command(), "install", "chromium"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:  # noqa: BLE001 - surface a readable message
        raise SystemExit(
            "Could not download Chromium automatically.\n"
            f"  {exc}\n"
            "  Run: python -m playwright install chromium"
        ) from exc
    if not chromium_ready():
        raise SystemExit("Chromium is still missing after installation")
    return chromium_path() or ""


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))
