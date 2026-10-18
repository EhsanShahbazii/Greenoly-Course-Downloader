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


def decrypt_segment(encrypted: bytes, key: bytes | None, iv: bytes | None) -> bytes:
    """AES-128-CBC decrypt one HLS segment with the openssl CLI."""
    if not key:
        return encrypted
    process = subprocess.run(
        [
            "openssl",
            "enc",
            "-d",
            "-aes-128-cbc",
            "-K",
            key.hex(),
            "-iv",
            (iv or bytes(16)).hex(),
        ],
        input=encrypted,
        capture_output=True,
    )
    if process.returncode != 0:
        message = process.stderr.decode(errors="ignore")[:200]
        raise RuntimeError(f"openssl failed: {message}")
    return process.stdout


def concat_files(paths: list[str], destination: str) -> None:
    with open(destination, "wb") as out:
        for path in paths:
            with open(path, "rb") as handle:
                shutil.copyfileobj(handle, out)


