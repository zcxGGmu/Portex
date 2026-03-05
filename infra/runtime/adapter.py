"""Runtime adapter abstractions."""

from __future__ import annotations

from typing import Any, Protocol


class RuntimeAdapter(Protocol):
    """Minimal runtime adapter protocol."""

    def run(self, prompt: str) -> dict[str, Any]:
        """Run a prompt through the runtime backend."""
        ...
