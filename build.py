"""Build a standalone desktop build with PyInstaller.

Produces ``dist/GreenOly`` (folder) and ``dist/GreenOly-<platform>.zip`` with
Chromium, ffmpeg and all Python dependencies inside — the user just unzips and
runs it.

    python build.py
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
APP_NAME = "GreenOly"


def run(command: list[str], env: dict | None = None) -> None:
    print("$", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True, env=env)


def platform_tag() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin":
        return "macos-" + ("arm64" if machine in {"arm64", "aarch64"} else "x64")
    if system == "windows":
        return "windows-x64"
    return "linux-" + ("arm64" if machine in {"arm64", "aarch64"} else "x64")


def main() -> int:
    run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
    run([sys.executable, "-m", "pip", "install", "-q", "pyinstaller>=6.6"])

    # Install Chromium *inside* the package so PyInstaller can bundle it.
    env = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH="0")
    run([sys.executable, "-m", "playwright", "install", "chromium"], env=env)

    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--console",
            "--name",
            APP_NAME,
            "--collect-all",
            "playwright",
            "--collect-all",
            "rich",
            "--collect-all",
            "imageio_ffmpeg",
            "--collect-all",
            "browser_cookie3",
            "--hidden-import",
            "Cryptodome",
            "--hidden-import",
            "cryptography",
            "greenoly.py",
        ]
    )

    bundle = DIST / APP_NAME
    for extra in ("README.md", "requirements.txt"):
        source = ROOT / extra
        if source.exists():
            shutil.copy2(source, bundle / extra)

    tag = platform_tag()
    archive = DIST / f"{APP_NAME}-{tag}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in bundle.rglob("*"):
            zf.write(path, path.relative_to(bundle.parent))

    size_mb = archive.stat().st_size / (1024 * 1024)
    print(f"\nBuilt {archive} ({size_mb:.0f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
