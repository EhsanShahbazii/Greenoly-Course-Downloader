"""Segment decryption and MP4 remuxing.

Decryption prefers the ``cryptography`` package (fast, pure wheels, no external
binary) and falls back to the ``openssl`` CLI. ffmpeg is always required for the
final remux and is looked up next to the executable so a bundled build works.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    HAS_CRYPTOGRAPHY = True
    CRYPTOGRAPHY_IMPORT_ERROR = None
except ImportError as exc:  # pragma: no cover - fallback path
    HAS_CRYPTOGRAPHY = False
    CRYPTOGRAPHY_IMPORT_ERROR = str(exc)


def tool_path(name: str) -> str | None:
    """Find a tool on PATH or shipped next to the (frozen) executable."""
    found = shutil.which(name)
    if found and not getattr(sys, "frozen", False):
        return found
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.dirname(sys.executable))
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        candidates.append(bundle)
    for folder in candidates:
        for suffix in ("", ".exe"):
            candidate = os.path.join(folder, name + suffix)
            if os.path.exists(candidate):
                return candidate
    if name == "ffmpeg":
        # imageio-ffmpeg ships a static ffmpeg for macOS/Windows/Linux, which is
        # what makes the standalone builds work without installing anything.
        try:
            import imageio_ffmpeg

            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:  # noqa: BLE001 - optional dependency
            return found
    return found


def require_tools() -> None:
    required = ["ffmpeg"]
    if not HAS_CRYPTOGRAPHY:
        required.append("openssl")
    missing = [tool for tool in required if tool_path(tool) is None]
    if missing:
        raise SystemExit(
            "Missing required tools: "
            + ", ".join(missing)
            + "\n  macOS: brew install ffmpeg\n  Windows: winget install Gyan.FFmpeg"
        )


def decrypt_segment(encrypted: bytes, key: bytes | None, iv: bytes | None) -> bytes:
    """AES-128-CBC decrypt one HLS segment."""
    if not key:
        return encrypted
    if HAS_CRYPTOGRAPHY:
        decryptor = Cipher(
            algorithms.AES(key), modes.CBC(iv or bytes(16))
        ).decryptor()
        return decryptor.update(encrypted) + decryptor.finalize()
    openssl = tool_path("openssl")
    if openssl is None:
        raise RuntimeError("Neither cryptography nor openssl is available")
    process = subprocess.run(
        [
            openssl,
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
    ffmpeg = tool_path("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg not found")
    process = subprocess.run(
        [
            ffmpeg,
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
