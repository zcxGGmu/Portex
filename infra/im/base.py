"""IM channel base abstractions."""

from __future__ import annotations

from typing import Protocol


class IMClient(Protocol):
    """Minimal IM client protocol."""

    def send_message(self, channel: str, text: str) -> bool:
        """Send a message to the target channel."""
        ...
