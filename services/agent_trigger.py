"""Trigger runtime execution and forward stream events."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
import json
from typing import Callable, Protocol
from uuid import uuid4

from infra.runtime.adapter import AgentRuntime, RunEvent, RunRequest
from portex.contracts.events import EventType


class WebSocketBroadcaster(Protocol):
    async def send_message(self, message: str, room: str) -> None:
        ...


RuntimeFactory = Callable[[str], AgentRuntime]
SessionIdFactory = Callable[[str], str]


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


async def _broadcast_runtime_events(
    runtime: AgentRuntime,
    request: RunRequest,
    websocket_manager: WebSocketBroadcaster,
) -> None:
    async for event in runtime.run_streamed(request):
        await websocket_manager.send_message(
            serialize_run_event(event),
            request.group_folder,
        )


async def _cleanup_consumer_task(consumer_task: asyncio.Task[None]) -> None:
    if not consumer_task.done():
        consumer_task.cancel()
    await asyncio.gather(consumer_task, return_exceptions=True)


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
    run_id = request_id or uuid4().hex
    resolve_session_id = session_id_factory or _default_session_id_factory

    request = RunRequest(
        request_id=run_id,
        group_folder=group_folder,
        message=message,
        session_id=resolve_session_id(group_folder),
        user_id=user_id,
    )

    runtime = runtime_factory(group_folder)
    consumer_task = asyncio.create_task(
        _broadcast_runtime_events(
            runtime=runtime,
            request=request,
            websocket_manager=websocket_manager,
        )
    )

    try:
        done, _pending = await asyncio.wait({consumer_task}, timeout=timeout_ms / 1000)
    except asyncio.CancelledError:
        await _cleanup_consumer_task(consumer_task)
        raise

    if consumer_task in done:
        await consumer_task
        return run_id

    try:
        await runtime.cancel(request.request_id)
    finally:
        await _cleanup_consumer_task(consumer_task)

    await websocket_manager.send_message(
        serialize_run_event(_build_timeout_event(run_id, timeout_ms)),
        group_folder,
    )

    return run_id


__all__ = [
    "RuntimeFactory",
    "SessionIdFactory",
    "WebSocketBroadcaster",
    "serialize_run_event",
    "trigger_agent_execution",
]
