from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _build_message(channel: str = "feishu"):
    from domain.schemas import UnifiedMessage

    return UnifiedMessage(
        channel=channel,  # type: ignore[arg-type]
        chat_jid=f"{channel}:chat-1",
        sender_id="user-1",
        group_folder="group-a",
        content="hello",
        message_id="msg-1",
        timestamp=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_route_message_dispatches_feishu_messages() -> None:
    from services.message_router import MessageRouter

    received: list[tuple[str, object]] = []

    async def feishu_handler(message: object) -> None:
        received.append(("feishu", message))

    async def telegram_handler(message: object) -> None:
        received.append(("telegram", message))

    async def web_handler(message: object) -> None:
        received.append(("web", message))

    message = _build_message(channel="feishu")
    router = MessageRouter(
        feishu_handler=feishu_handler,
        telegram_handler=telegram_handler,
        web_handler=web_handler,
    )

    await router.route_message(message)

    assert received == [("feishu", message)]


@pytest.mark.asyncio
async def test_route_message_dispatches_telegram_messages() -> None:
    from services.message_router import MessageRouter

    received: list[tuple[str, object]] = []

    async def feishu_handler(message: object) -> None:
        received.append(("feishu", message))

    async def telegram_handler(message: object) -> None:
        received.append(("telegram", message))

    async def web_handler(message: object) -> None:
        received.append(("web", message))

    message = _build_message(channel="telegram")
    router = MessageRouter(
        feishu_handler=feishu_handler,
        telegram_handler=telegram_handler,
        web_handler=web_handler,
    )

    await router.route_message(message)

    assert received == [("telegram", message)]


@pytest.mark.asyncio
async def test_route_message_dispatches_web_messages() -> None:
    from services.message_router import MessageRouter

    received: list[tuple[str, object]] = []

    async def feishu_handler(message: object) -> None:
        received.append(("feishu", message))

    async def telegram_handler(message: object) -> None:
        received.append(("telegram", message))

    async def web_handler(message: object) -> None:
        received.append(("web", message))

    message = _build_message(channel="web")
    router = MessageRouter(
        feishu_handler=feishu_handler,
        telegram_handler=telegram_handler,
        web_handler=web_handler,
    )

    await router.route_message(message)

    assert received == [("web", message)]


@pytest.mark.asyncio
async def test_route_message_raises_for_unknown_channel() -> None:
    from domain.schemas import UnifiedMessage
    from services.message_router import MessageRouter, MessageRouterError

    async def noop_handler(message: object) -> None:
        _ = message

    message = UnifiedMessage.model_construct(
        channel="unknown",
        chat_jid="unknown:chat-1",
        sender_id="user-1",
        group_folder="group-a",
        content="hello",
        message_id="msg-1",
        timestamp=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
    )
    router = MessageRouter(
        feishu_handler=noop_handler,
        telegram_handler=noop_handler,
        web_handler=noop_handler,
    )

    with pytest.raises(MessageRouterError, match="unknown"):
        await router.route_message(message)


@pytest.mark.asyncio
async def test_route_message_propagates_handler_errors() -> None:
    from services.message_router import MessageRouter

    async def failing_handler(message: object) -> None:
        _ = message
        raise RuntimeError("handler exploded")

    async def noop_handler(message: object) -> None:
        _ = message

    router = MessageRouter(
        feishu_handler=failing_handler,
        telegram_handler=noop_handler,
        web_handler=noop_handler,
    )

    with pytest.raises(RuntimeError, match="handler exploded"):
        await router.route_message(_build_message(channel="feishu"))
