"""Trigger runtime execution and forward stream events."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
import json
from typing import Awaitable, Callable, Protocol
from uuid import uuid4

from infra.runtime.adapter import AgentRuntime, RunEvent, RunRequest, RunResult
from portex.contracts.events import EventType


class WebSocketBroadcaster(Protocol):
    async def send_message(self, message: str, room: str) -> None:
        ...


RuntimeFactory = Callable[[str], AgentRuntime]
SessionIdFactory = Callable[[str], str]
RunEventHandler = Callable[[RunEvent], Awaitable[None]]


def _default_session_id_factory(group_folder: str) -> str:
    return group_folder


def serialize_run_event(event: RunEvent) -> str:
    return json.dumps(asdict(event))


def _build_timeout_event(run_id: str, timeout_ms: int) -> RunEvent:
    return RunEvent(
        event_type=EventType.RUN_TIMEOUT.value,
        run_id=run_id,
        payload={
            "status": "timeout",
            "timeout_ms": timeout_ms,
        },
    )


class RuntimeReplyCollector:
    def __init__(self, run_id: str) -> None:
        self._run_id = run_id
        self._status: str | None = None
        self._final_output: str | None = None
        self._error: str | None = None
        self._timeout_ms: int | None = None

    async def handle_event(self, event: RunEvent) -> None:
        if event.event_type == EventType.RUN_COMPLETED.value:
            self._status = "completed"
            final_output = event.payload.get("final_output")
            if isinstance(final_output, str) and final_output:
                self._final_output = final_output
            return

        if event.event_type == EventType.RUN_FAILED.value:
            self._status = "failed"
            error = event.payload.get("error") or event.payload.get("status")
            if isinstance(error, str) and error:
                self._error = error
            return

        if event.event_type == EventType.RUN_TIMEOUT.value:
            self._status = "timeout"
            timeout_ms = event.payload.get("timeout_ms")
            if isinstance(timeout_ms, int):
                self._timeout_ms = timeout_ms
            return

    def build_result(self) -> RunResult:
        return RunResult(
            run_id=self._run_id,
            status=self._status or "completed",
            final_output=self._final_output,
            error=self._error,
            timeout_ms=self._timeout_ms,
        )


async def _cleanup_consumer_task(consumer_task: asyncio.Task[None]) -> None:
    if not consumer_task.done():
        consumer_task.cancel()
    await asyncio.gather(consumer_task, return_exceptions=True)


async def run_agent_execution(
    group_folder: str,
    message: str,
    user_id: str,
    runtime_factory: RuntimeFactory,
    event_handler: RunEventHandler | None = None,
    session_id_factory: SessionIdFactory | None = None,
    request_id: str | None = None,
    timeout_ms: int = 300_000,
) -> RunResult:
    run_id = request_id or uuid4().hex
    resolve_session_id = session_id_factory or _default_session_id_factory
    collector = RuntimeReplyCollector(run_id)

    request = RunRequest(
        request_id=run_id,
        group_folder=group_folder,
        message=message,
        session_id=resolve_session_id(group_folder),
        user_id=user_id,
    )

    runtime = runtime_factory(group_folder)

    async def handle_event(event: RunEvent) -> None:
        await collector.handle_event(event)
        if event_handler is not None:
            await event_handler(event)

    async def consume_runtime_events() -> None:
        async for event in runtime.run_streamed(request):
            await handle_event(event)

    consumer_task = asyncio.create_task(
        consume_runtime_events()
    )

    try:
        done, _pending = await asyncio.wait({consumer_task}, timeout=timeout_ms / 1000)
    except asyncio.CancelledError:
        await _cleanup_consumer_task(consumer_task)
        raise

    if consumer_task in done:
        await consumer_task
        return collector.build_result()

    try:
        await runtime.cancel(request.request_id)
    finally:
        await _cleanup_consumer_task(consumer_task)

    await handle_event(_build_timeout_event(run_id, timeout_ms))

    return collector.build_result()


async def trigger_agent_execution(
    group_folder: str,
    message: str,
    user_id: str,
    websocket_manager: WebSocketBroadcaster,
    runtime_factory: RuntimeFactory,
    session_id_factory: SessionIdFactory | None = None,
    request_id: str | None = None,
    timeout_ms: int = 300_000,
) -> str:
    async def broadcast_event(event: RunEvent) -> None:
        await websocket_manager.send_message(
            serialize_run_event(event),
            group_folder,
        )

    result = await run_agent_execution(
        group_folder=group_folder,
        message=message,
        user_id=user_id,
        runtime_factory=runtime_factory,
        event_handler=broadcast_event,
        session_id_factory=session_id_factory,
        request_id=request_id,
        timeout_ms=timeout_ms,
    )
    return result.run_id


__all__ = [
    "RuntimeFactory",
    "RunEventHandler",
    "SessionIdFactory",
    "WebSocketBroadcaster",
    "run_agent_execution",
    "serialize_run_event",
    "trigger_agent_execution",
]
