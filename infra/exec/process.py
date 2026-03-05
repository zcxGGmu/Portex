"""Process execution placeholders."""

from __future__ import annotations


class ProcessExecutor:
    """Minimal placeholder for local process execution operations."""

    def run(self, command: list[str]) -> int:
        """Return a placeholder process exit code."""
        _ = command
        return 0
