"""Trigger runtime execution and forward stream events."""

from __future__ import annotations

from dataclasses import asdict
import json
from typing import Callable, Protocol
from uuid import uuid4

from infra.runtime.adapter import AgentRuntime, RunEvent, RunRequest


class WebSocketBroadcaster(Protocol):
    async def send_message(self, message: str, room: str) -> None:
        ...


RuntimeFactory = Callable[[str], AgentRuntime]
SessionIdFactory = Callable[[str], str]


def _default_session_id_factory(group_folder: str) -> str:
    return group_folder


def serialize_run_event(event: RunEvent) -> str:
    return json.dumps(asdict(event))


async def trigger_agent_execution(
    group_folder: str,
    message: str,
    user_id: str,
    websocket_manager: WebSocketBroadcaster,
    runtime_factory: RuntimeFactory,
    session_id_factory: SessionIdFactory | None = None,
    request_id: str | None = None,
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
    async for event in runtime.run_streamed(request):
        await websocket_manager.send_message(
            serialize_run_event(event),
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
