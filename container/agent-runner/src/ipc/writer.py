"""IPC writer placeholders."""

from __future__ import annotations

from pathlib import Path


def write_text(path: str, content: str) -> None:
    """Write IPC payload text into a file path."""
    Path(path).write_text(content, encoding="utf-8")
