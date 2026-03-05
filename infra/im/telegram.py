"""Telegram IM client placeholders."""

from __future__ import annotations

from .base import IMClient


class TelegramClient(IMClient):
    """Minimal placeholder Telegram client."""

    def send_message(self, channel: str, text: str) -> bool:
        """Pretend to send a Telegram message."""
        _ = (channel, text)
        return True
