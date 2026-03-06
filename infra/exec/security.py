"""Filesystem safety helpers for execution infrastructure."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path


def validate_path(path: str | Path, allowed_roots: Sequence[str | Path]) -> bool:
    """Return whether a path resolves under any allowed root."""
    candidate = Path(path).resolve()

    for root in allowed_roots:
        resolved_root = Path(root).resolve()
        try:
            candidate.relative_to(resolved_root)
        except ValueError:
            continue
        return True

    return False


__all__ = ["validate_path"]
