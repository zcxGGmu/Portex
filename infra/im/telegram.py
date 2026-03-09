"""Telegram client foundation for Bot API update polling."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from .base import IMClient


class TelegramClientError(RuntimeError):
    """Raised when the Telegram client cannot complete an operation."""


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
            response = await client.get(
                f"{self.base_url.rstrip('/')}/bot{self.bot_token}/getUpdates",
                params=params,
            )
            payload = response.json()
        finally:
            if close_client:
                await client.aclose()

        if payload.get("ok") is not True:
            raise TelegramClientError(
                str(payload.get("description", "failed to fetch Telegram updates"))
            )

        result = payload.get("result")
        if not isinstance(result, list):
            raise TelegramClientError("Telegram response missing result list")
        return result


__all__ = ["TelegramClient", "TelegramClientError"]
