from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _build_message(*, group_folder: str | None = "group-explicit"):
    from domain.schemas import UnifiedMessage

    return UnifiedMessage(
        channel="telegram",
        chat_jid="telegram:chat-1",
        sender_id="user-1",
        group_folder=group_folder,
        content="hello from telegram",
        message_id="external-msg-1",
        timestamp=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_dispatch_inbound_message_uses_explicit_group_folder() -> None:
    from infra.runtime.adapter import RunResult
    from services.message_dispatch import DispatchResult, MessageDispatchService, ResolvedMessageTarget

    resolver_calls: list[object] = []
    trigger_calls: list[dict[str, object]] = []
    store_calls: list[dict[str, object]] = []
    routed_messages: list[object] = []

    def resolver(message):
        resolver_calls.append(message)
        return ResolvedMessageTarget(group_folder="resolved-group", chat_jid=message.chat_jid)

    async def runtime_trigger(**kwargs):
        trigger_calls.append(kwargs)
        return RunResult(
            run_id=kwargs["request_id"],
            status="completed",
            final_output="agent reply",
        )

    async def store_message(**kwargs):
        store_calls.append(kwargs)
        return SimpleNamespace(id=f"db-{len(store_calls)}")

    class Router:
        async def route_message(self, message):
            routed_messages.append(message)

    service = MessageDispatchService(
        target_resolver=resolver,
        runtime_trigger=runtime_trigger,
        store_message=store_message,
        message_router=Router(),
    )

    result = await service.dispatch_inbound_message(_build_message())

    assert isinstance(result, DispatchResult)
    assert result.status == "completed"
    assert result.group_folder == "group-explicit"
    assert result.inbound_message_id == "db-1"
    assert result.outbound_message_id == "db-2"
    assert result.final_output == "agent reply"
    assert resolver_calls == []
    assert trigger_calls[0]["group_folder"] == "group-explicit"
    assert trigger_calls[0]["request_id"] == result.run_id
    assert store_calls[0]["group_folder"] == "group-explicit"
    assert store_calls[0]["run_id"] == result.run_id
    assert store_calls[0]["external_message_id"] == "external-msg-1"
    assert store_calls[0]["is_from_me"] is False
    assert store_calls[1]["is_from_me"] is True
    assert routed_messages[0].content == "agent reply"
    assert routed_messages[0].group_folder == "group-explicit"


@pytest.mark.asyncio
async def test_dispatch_inbound_message_uses_resolver_when_group_folder_missing() -> None:
    from infra.runtime.adapter import RunResult
    from services.message_dispatch import MessageDispatchService, ResolvedMessageTarget

    resolver_calls: list[object] = []
    trigger_calls: list[dict[str, object]] = []

    def resolver(message):
        resolver_calls.append(message)
        return ResolvedMessageTarget(group_folder="resolved-group", chat_jid=message.chat_jid)

    async def runtime_trigger(**kwargs):
        trigger_calls.append(kwargs)
        return RunResult(
            run_id=kwargs["request_id"],
            status="completed",
            final_output="agent reply",
        )

    async def store_message(**kwargs):
        return SimpleNamespace(id="db-message")

    class Router:
        async def route_message(self, message):
            _ = message

    service = MessageDispatchService(
        target_resolver=resolver,
        runtime_trigger=runtime_trigger,
        store_message=store_message,
        message_router=Router(),
    )

    result = await service.dispatch_inbound_message(_build_message(group_folder=None))

    assert result.group_folder == "resolved-group"
    assert len(resolver_calls) == 1
    assert trigger_calls[0]["group_folder"] == "resolved-group"


@pytest.mark.asyncio
async def test_dispatch_inbound_message_does_not_send_fake_success_reply_on_runtime_failure() -> None:
    from infra.runtime.adapter import RunResult
    from services.message_dispatch import MessageDispatchService, ResolvedMessageTarget

    store_calls: list[dict[str, object]] = []
    routed_messages: list[object] = []

    def resolver(message):
        return ResolvedMessageTarget(group_folder="resolved-group", chat_jid=message.chat_jid)

    async def runtime_trigger(**kwargs):
        return RunResult(
            run_id=kwargs["request_id"],
            status="failed",
            error="runtime exploded",
        )

    async def store_message(**kwargs):
        store_calls.append(kwargs)
        return SimpleNamespace(id="db-inbound")

    class Router:
        async def route_message(self, message):
            routed_messages.append(message)

    service = MessageDispatchService(
        target_resolver=resolver,
        runtime_trigger=runtime_trigger,
        store_message=store_message,
        message_router=Router(),
    )

    result = await service.dispatch_inbound_message(_build_message(group_folder=None))

    assert result.status == "failed"
    assert result.outbound_message_id is None
    assert result.error == "runtime exploded"
    assert len(store_calls) == 1
    assert routed_messages == []
