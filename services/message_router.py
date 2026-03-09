"""Minimal message routing orchestration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from domain.schemas import UnifiedMessage

MessageHandler = Callable[[UnifiedMessage], Awaitable[None]]


class MessageRouterError(RuntimeError):
    """Raised when a message cannot be routed to a downstream handler."""


class MessageRouter:
    """Route unified messages to injected channel handlers."""

    def __init__(
        self,
        *,
        feishu_handler: MessageHandler,
        telegram_handler: MessageHandler,
        web_handler: MessageHandler,
    ) -> None:
        self._handlers: dict[str, MessageHandler] = {
            "feishu": feishu_handler,
            "telegram": telegram_handler,
            "web": web_handler,
        }

    async def route_message(self, message: UnifiedMessage) -> None:
        handler = self._handlers.get(message.channel)
        if handler is None:
            raise MessageRouterError(f"unsupported message channel: {message.channel}")
        await handler(message)


__all__ = ["MessageRouter", "MessageRouterError"]
