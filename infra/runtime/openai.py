"""OpenAI runtime adapter placeholders."""

from __future__ import annotations

from typing import Any

from .adapter import RuntimeAdapter


class OpenAIRuntimeAdapter(RuntimeAdapter):
    """Minimal placeholder implementation for an OpenAI runtime adapter."""

    def run(self, prompt: str) -> dict[str, Any]:
        """Return a placeholder runtime result."""
        return {"status": "placeholder", "prompt": prompt}
