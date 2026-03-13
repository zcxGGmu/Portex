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


@pytest.mark.asyncio
async def test_dispatch_inbound_message_uses_execution_coordinator_when_configured() -> None:
    from services.execution_coordinator import ExecutionHandle, ExecutionResult
    from services.message_dispatch import MessageDispatchService, ResolvedMessageTarget

    submit_calls: list[object] = []
    wait_calls: list[str] = []
    store_calls: list[dict[str, object]] = []
    routed_messages: list[object] = []

    class FakeCoordinator:
        async def submit_execution(self, request):
            submit_calls.append(request)
            return ExecutionHandle(
                run_id=request.request_id or "run-coordinator",
                group_folder=request.group_folder,
                status="queued",
            )

        async def wait_for_run(self, run_id: str):
            wait_calls.append(run_id)
            return ExecutionResult(
                run_id=run_id,
                status="completed",
                group_folder="resolved-group",
                backend="openai_runtime",
                session_id="resolved-group",
                final_output="reply from coordinator",
            )

    def resolver(message):
        return ResolvedMessageTarget(group_folder="resolved-group", chat_jid=message.chat_jid)

    async def store_message(**kwargs):
        store_calls.append(kwargs)
        return SimpleNamespace(id=f"db-{len(store_calls)}")

    class Router:
        async def route_message(self, message):
            routed_messages.append(message)

    service = MessageDispatchService(
        target_resolver=resolver,
        execution_coordinator=FakeCoordinator(),
        store_message=store_message,
        message_router=Router(),
    )

    result = await service.dispatch_inbound_message(_build_message(group_folder=None))

    assert result.run_id == submit_calls[0].request_id
    assert result.status == "completed"
    assert len(submit_calls) == 1
    assert submit_calls[0].group_folder == "resolved-group"
    assert submit_calls[0].prompt == "hello from telegram"
    assert submit_calls[0].source == "im"
    assert submit_calls[0].request_id == result.run_id
    assert wait_calls == [result.run_id]
    assert len(store_calls) == 2
    assert store_calls[0]["run_id"] == result.run_id
    assert store_calls[1]["run_id"] == result.run_id
    assert routed_messages[0].content == "reply from coordinator"


@pytest.mark.asyncio
async def test_dispatch_inbound_message_persists_inbound_before_coordinator_submission() -> None:
    from services.execution_coordinator import ExecutionHandle, ExecutionResult
    from services.message_dispatch import MessageDispatchService, ResolvedMessageTarget

    stored_before_submit = False
    store_calls: list[dict[str, object]] = []

    class FakeCoordinator:
        async def submit_execution(self, request):
            assert stored_before_submit is True
            return ExecutionHandle(
                run_id=request.request_id or "run-coordinator",
                group_folder=request.group_folder,
                status="queued",
            )

        async def wait_for_run(self, run_id: str):
            return ExecutionResult(
                run_id=run_id,
                status="completed",
                group_folder="resolved-group",
                backend="openai_runtime",
                session_id="resolved-group",
                final_output="reply from coordinator",
            )

    def resolver(message):
        return ResolvedMessageTarget(group_folder="resolved-group", chat_jid=message.chat_jid)

    async def store_message(**kwargs):
        nonlocal stored_before_submit
        store_calls.append(kwargs)
        if kwargs["is_from_me"] is False:
            stored_before_submit = True
        return SimpleNamespace(id=f"db-{len(store_calls)}")

    class Router:
        async def route_message(self, message):
            _ = message

    service = MessageDispatchService(
        target_resolver=resolver,
        execution_coordinator=FakeCoordinator(),
        store_message=store_message,
        message_router=Router(),
    )

    await service.dispatch_inbound_message(_build_message(group_folder=None))

    assert store_calls[0]["is_from_me"] is False


@pytest.mark.asyncio
async def test_dispatch_inbound_message_propagates_explicit_execution_mode() -> None:
    from services.execution_coordinator import ExecutionHandle, ExecutionResult
    from services.message_dispatch import MessageDispatchService, ResolvedMessageTarget

    submit_calls: list[object] = []

    class FakeCoordinator:
        async def submit_execution(self, request):
            submit_calls.append(request)
            return ExecutionHandle(
                run_id=request.request_id or "run-coordinator",
                group_folder=request.group_folder,
                status="queued",
            )

        async def wait_for_run(self, run_id: str):
            return ExecutionResult(
                run_id=run_id,
                status="completed",
                group_folder="resolved-group",
                backend="host_process",
                session_id="resolved-group",
                final_output="reply from coordinator",
            )

    def resolver(message):
        return ResolvedMessageTarget(group_folder="resolved-group", chat_jid=message.chat_jid)

    async def store_message(**kwargs):
        return SimpleNamespace(id="db-message")

    class Router:
        async def route_message(self, message):
            _ = message

    service = MessageDispatchService(
        target_resolver=resolver,
        execution_coordinator=FakeCoordinator(),
        store_message=store_message,
        message_router=Router(),
    )

    await service.dispatch_inbound_message(
        _build_message(group_folder=None),
        execution_mode="host",
    )

    assert submit_calls[0].requested_mode == "host"
