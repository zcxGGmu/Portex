"""Docker execution placeholders."""

from __future__ import annotations


class DockerExecutor:
    """Minimal placeholder for Docker execution operations."""

    def build(self, image_tag: str) -> str:
        """Return a placeholder build result."""
        return f"build queued for {image_tag}"
