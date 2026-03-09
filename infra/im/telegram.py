"""Telegram client foundation for Bot API update polling."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from .base import IMClient


class TelegramClientError(RuntimeError):
    """Raised when the Telegram client cannot complete an operation."""


@dataclass(slots=True)
class TelegramMessageEvent:
    """Normalized Telegram message update payload."""

    event_type: str
    chat_id: str
    message_id: str
    sender_id: str
    message_type: str
    text: str | None
    raw_event: dict[str, object]


@dataclass(slots=True)
class TelegramClient(IMClient):
    """Minimal Telegram client skeleton for `getUpdates` polling."""

    bot_token: str
    base_url: str = "https://api.telegram.org"
    http_client: httpx.AsyncClient | object | None = None

    async def get_updates(
        self,
        offset: int = 0,
        timeout: int = 60,
        allowed_updates: list[str] | None = None,
    ) -> list[dict[str, object]]:
        """Fetch raw Telegram updates with the smallest useful Bot API contract."""
        params: dict[str, object] = {
            "offset": offset,
            "timeout": timeout,
        }
        if allowed_updates is not None:
            params["allowed_updates"] = allowed_updates

        client = self.http_client or httpx.AsyncClient()
        close_client = self.http_client is None
        try:
            try:
                response = await client.get(
                    f"{self.base_url.rstrip('/')}/bot{self.bot_token}/getUpdates",
                    params=params,
                )
                payload = response.json()
            except Exception as exc:  # pragma: no cover - exercised via fake clients in tests
                raise TelegramClientError(str(exc) or "failed to fetch Telegram updates") from exc
        finally:
            if close_client:
                await client.aclose()

        if not isinstance(payload, dict):
            raise TelegramClientError("invalid Telegram response payload")
        if payload.get("ok") is not True:
            raise TelegramClientError(
                str(payload.get("description", "failed to fetch Telegram updates"))
            )

        result = payload.get("result")
        if not isinstance(result, list):
            raise TelegramClientError("Telegram response missing result list")
        return result

    def handle_update(self, update: dict[str, object]) -> TelegramMessageEvent | None:
        """Normalize a Telegram update into a message event when applicable."""
        message = update.get("message")
        if message is None:
            return None
        if not isinstance(message, dict):
            raise TelegramClientError("invalid Telegram message payload")

        chat = message.get("chat")
        if not isinstance(chat, dict):
            raise TelegramClientError("invalid Telegram chat payload")

        sender = message.get("from")
        if not isinstance(sender, dict):
            raise TelegramClientError("invalid Telegram sender payload")

        chat_id = self._extract_required_identifier(chat.get("id"), "chat")
        message_id = self._extract_required_identifier(message.get("message_id"), "message")
        sender_id = self._extract_required_identifier(sender.get("id"), "sender")

        return TelegramMessageEvent(
            event_type="message",
            chat_id=chat_id,
            message_id=message_id,
            sender_id=sender_id,
            message_type=self._extract_message_type(message),
            text=self._extract_text(message),
            raw_event=message,
        )

    def _extract_required_identifier(self, value: object, field_name: str) -> str:
        if isinstance(value, bool):
            raise TelegramClientError(f"invalid Telegram {field_name} payload")
        if isinstance(value, int):
            return str(value)
        if isinstance(value, str) and value:
            return value
        raise TelegramClientError(f"invalid Telegram {field_name} payload")

    def _extract_message_type(self, message: dict[str, object]) -> str:
        if "text" in message:
            return "text"

        for candidate in ("photo", "document", "voice", "sticker", "video", "audio", "animation"):
            if candidate in message:
                return candidate
        return "unknown"

    def _extract_text(self, message: dict[str, object]) -> str | None:
        text = message.get("text")
        if isinstance(text, str) and text:
            return text
        return None

    def send_message(self, channel: str, text: str) -> bool:
        """Guard the legacy IM protocol until Telegram send support exists."""
        _ = (channel, text)
        raise TelegramClientError("Telegram send_message is not implemented yet")


__all__ = ["TelegramClient", "TelegramClientError", "TelegramMessageEvent"]
