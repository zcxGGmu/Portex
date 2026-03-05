"""Feishu IM client placeholders."""

from __future__ import annotations

from .base import IMClient


class FeishuClient(IMClient):
    """Minimal placeholder Feishu client."""

    def send_message(self, channel: str, text: str) -> bool:
        """Pretend to send a Feishu message."""
        _ = (channel, text)
        return True
