"""Shared path helpers — every task imports this to resolve $ECHOSCROLL_DATA."""

from __future__ import annotations

import os
from pathlib import Path


def data_root() -> Path:
    """Return the data root directory.

    Order of resolution:
      1. $ECHOSCROLL_DATA env var
      2. fallback to ~/echoscroll_data_kit/data
    """
    root = os.environ.get("ECHOSCROLL_DATA")
    if root:
        return Path(root)
    fallback = Path.home() / "echoscroll_data_kit" / "data"
    return fallback


def require_dir(p: Path, hint: str = "") -> Path:
    if not p.exists():
        raise FileNotFoundError(
            f"Expected directory not found: {p}\n"
            f"Hint: {hint or 'check $ECHOSCROLL_DATA or pass --data-root'}"
        )
    return p


def require_file(p: Path, hint: str = "") -> Path:
    if not p.exists():
        raise FileNotFoundError(
            f"Expected file not found: {p}\n"
            f"Hint: {hint or 'check $ECHOSCROLL_DATA or pass --data-root'}"
        )
    return p
