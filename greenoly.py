#!/usr/bin/env python3
"""Launcher: ``python greenoly.py <url>``."""

from __future__ import annotations

import sys

from greenoly.cli import main

if __name__ == "__main__":
    sys.exit(main())
