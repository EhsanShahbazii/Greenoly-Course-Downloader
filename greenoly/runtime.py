"""Use the browser shipped beside the executable, or the source install cache."""

from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path


def configure_browser_path() -> None:
    if is_frozen():
        bundled = Path(sys.executable).resolve().parent / "browsers"
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(bundled)


def chromium_path() -> str | None:
    configure_browser_path()
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
    if is_frozen():
        raise SystemExit(
            "Bundled Chromium is missing. Extract the complete release archive, "
            "including the browsers folder, and try again."
        )
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


def self_test() -> None:
    """Exercise the shipped browser, crypto and ffmpeg without network access."""
    from playwright.sync_api import sync_playwright
    from .media import AES_IMPORT_ERROR, HAS_AES, decrypt_segment, tool_path

    if not HAS_AES:
        raise RuntimeError(f"AES backend could not load: {AES_IMPORT_ERROR}")
    decrypted = decrypt_segment(
        bytes.fromhex("3ad77bb40d7a3660a89ecaf32466ef97"),
        bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c"),
        bytes(16),
    )
    if decrypted != bytes.fromhex("6bc1bee22e409f96e93d7e117393172a"):
        raise RuntimeError("AES decryption self-test failed")
    ensure_chromium()
    if is_frozen():
        bundled = Path(sys.executable).resolve().parent / "browsers"
        if not Path(chromium_path()).resolve().is_relative_to(bundled):
            raise RuntimeError("Chromium is not using the portable browser folder")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_content("<title>GreenOly browser ready</title>")
            assert page.title() == "GreenOly browser ready"
        finally:
            browser.close()
    ffmpeg = tool_path("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is missing")
    if is_frozen() and not Path(ffmpeg).resolve().is_relative_to(Path(sys.executable).resolve().parent):
        raise RuntimeError("ffmpeg is not using the portable bundle")
    subprocess.run([ffmpeg, "-version"], check=True, stdout=subprocess.DEVNULL)
    print("PASS: bundled Chromium, AES and ffmpeg (no network needed)")
