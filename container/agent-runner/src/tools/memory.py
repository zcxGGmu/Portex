"""Memory tool placeholders."""

from __future__ import annotations

from typing import Any


class MemoryStore:
    """In-memory placeholder store for runner tools."""

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """Set a value in the placeholder memory."""
        self._values[key] = value

    def get(self, key: str) -> Any | None:
        """Get a value from the placeholder memory."""
        return self._values.get(key)
