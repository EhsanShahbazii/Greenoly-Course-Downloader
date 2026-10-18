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


def remux_to_mp4(source: str, destination: str) -> None:
    """Stream-copy the concatenated transport stream into a proper MP4."""
    os.makedirs(os.path.dirname(destination) or ".", exist_ok=True)
    process = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            source,
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            destination,
        ],
        capture_output=True,
    )
    if process.returncode != 0:
        message = process.stderr.decode(errors="ignore").strip()[:300]
        raise RuntimeError(f"ffmpeg remux failed: {message}")


def human_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024 or unit == "GB":
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} GB"
