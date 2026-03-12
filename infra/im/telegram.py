"""Telegram client foundation for Bot API update polling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import escape
import re
from uuid import uuid4

import httpx

from domain.schemas import UnifiedMessage
from .base import IMClient


class TelegramClientError(RuntimeError):
    """Raised when the Telegram client cannot complete an operation."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


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
    timestamp: datetime = field(default_factory=_utcnow, compare=False)

    def to_unified_message(self, group_folder: str | None = None) -> UnifiedMessage:
        """Convert the Telegram event into the minimal cross-channel message DTO."""
        return UnifiedMessage(
            channel="telegram",
            chat_jid=f"telegram:{self.chat_id}",
            sender_id=self.sender_id,
            group_folder=group_folder,
            content=self.text or "",
            message_id=self.message_id,
            timestamp=self.timestamp,
        )


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
            timestamp=self._extract_timestamp(message),
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

    async def send_text_message(self, chat_id: str, text: str) -> dict[str, object]:
        """Send a minimal text reply through the Telegram Bot API."""
        client = self.http_client or httpx.AsyncClient()
        close_client = self.http_client is None
        try:
            try:
                response = await client.post(
                    f"{self.base_url.rstrip('/')}/bot{self.bot_token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": self.markdown_to_html(text),
                        "parse_mode": "HTML",
                    },
                )
                payload = response.json()
            except Exception as exc:  # pragma: no cover - exercised via fake clients in tests
                raise TelegramClientError(str(exc) or "failed to send Telegram message") from exc
        finally:
            if close_client:
                await client.aclose()

        if not isinstance(payload, dict):
            raise TelegramClientError("invalid Telegram response payload")
        if payload.get("ok") is not True:
            raise TelegramClientError(str(payload.get("description", "failed to send Telegram message")))
        return payload

    def send_message(self, channel: str, text: str) -> bool:
        """Guard the legacy IM protocol until Telegram send support exists."""
        _ = (channel, text)
        raise TelegramClientError("Telegram send_message is not implemented yet")

    def markdown_to_html(self, text: str) -> str:
        """Convert a narrow Markdown subset into Telegram-safe HTML."""
        replacements: dict[str, str] = {}

        def store_replacement(prefix: str, replacement: str) -> str:
            token = f"@@PORTEX_{prefix}_{uuid4().hex}@@"
            replacements[token] = replacement
            return token

        def replace_code_block(match: re.Match[str]) -> str:
            content = match.group(1)
            return store_replacement(
                "CODE_BLOCK",
                f"<pre><code>{escape(content)}</code></pre>",
            )

        def replace_markdown_link(match: re.Match[str]) -> str:
            return store_replacement("MARKDOWN_LINK", escape(match.group(0)))

        def replace_inline_code(match: re.Match[str]) -> str:
            return store_replacement("INLINE_CODE", f"<code>{match.group(1)}</code>")

        def replace_unsupported_emphasis(match: re.Match[str]) -> str:
            return store_replacement("UNSUPPORTED", match.group(0))

        rendered = re.sub(
            r"```(?:[^\n`]*)\n?(.*?)```",
            replace_code_block,
            text,
            flags=re.DOTALL,
        )
        rendered = re.sub(r"\[[^\]]+\]\([^)]+\)", replace_markdown_link, rendered)
        rendered = escape(rendered)
        rendered = re.sub(r"`([^`\n]+?)`", replace_inline_code, rendered)
        for pattern in (
            r"\*\*\*.*?\*\*\*",
            r"\*[^*\n]*\*\*.*?\*\*[^*\n]*\*",
            r"\*\*[^*\n]*\*.*?\*[^*\n]*\*\*",
        ):
            rendered = re.sub(pattern, replace_unsupported_emphasis, rendered)
        rendered = re.sub(r"\*\*([^*\n]+)\*\*", r"<b>\1</b>", rendered)
        rendered = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", rendered)

        for token, replacement in replacements.items():
            rendered = rendered.replace(token, replacement)
        return rendered

    def _extract_timestamp(self, message: dict[str, object]) -> datetime:
        value = message.get("date")
        if value is None:
            return _utcnow()
        if isinstance(value, bool):
            raise TelegramClientError("invalid Telegram message timestamp")
        if isinstance(value, str):
            try:
                numeric = float(value)
            except ValueError as exc:
                raise TelegramClientError("invalid Telegram message timestamp") from exc
        elif isinstance(value, (int, float)):
            numeric = float(value)
        else:
            raise TelegramClientError("invalid Telegram message timestamp")

        if abs(numeric) >= 1_000_000_000_000:
            numeric /= 1000.0
        return datetime.fromtimestamp(numeric, tz=timezone.utc)


__all__ = ["TelegramClient", "TelegramClientError", "TelegramMessageEvent"]
