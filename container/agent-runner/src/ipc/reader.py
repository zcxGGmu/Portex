"""IPC reader placeholders."""

from __future__ import annotations

from pathlib import Path


def read_text(path: str) -> str:
    """Read IPC payload text from a file path."""
    return Path(path).read_text(encoding="utf-8")
