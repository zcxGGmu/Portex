"""WebSocket routes."""

from __future__ import annotations

import asyncio
import json
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket import ConnectionManager
from infra.runtime.adapter import RunEvent
from infra.runtime.openai import OpenAIAgentsRuntime
from services.agent_trigger import serialize_run_event, trigger_agent_execution

router = APIRouter(tags=["websocket"])
manager = ConnectionManager()
DEFAULT_WEBSOCKET_USER_ID = "websocket-user"


def create_runtime() -> OpenAIAgentsRuntime:
    return OpenAIAgentsRuntime(tools=[])


def _parse_cancel_run_id(message: str) -> str | None:
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    if payload.get("type") != "cancel":
        return None

    run_id = payload.get("run_id")
    return run_id if isinstance(run_id, str) and run_id else None


def _is_run_started_message(message: str) -> bool:
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        return False

    return isinstance(payload, dict) and payload.get("event_type") == "run.started"


class ConnectionScopedBroadcaster:
    def __init__(self, websocket: WebSocket, room_manager: ConnectionManager) -> None:
        self.websocket = websocket
        self.room_manager = room_manager

    async def send_message(self, message: str, room: str) -> None:
        if _is_run_started_message(message):
            await self.websocket.send_text(message)
            return
        await self.room_manager.send_message(message, room)


async def _cleanup_task(task: asyncio.Task[None] | None) -> None:
    if task is None:
        return
    if not task.done():
        task.cancel()
    await asyncio.gather(task, return_exceptions=True)


@router.websocket("/ws/{group_folder}")
async def websocket_endpoint(websocket: WebSocket, group_folder: str) -> None:
    await manager.connect(websocket, group_folder)
    runtime = create_runtime()
    broadcaster = ConnectionScopedBroadcaster(websocket, manager)
    active_run_id: str | None = None
    active_task: asyncio.Task[None] | None = None

    async def execute_message(message: str, run_id: str) -> None:
        nonlocal active_run_id, active_task

        try:
            await trigger_agent_execution(
                group_folder=group_folder,
                message=message,
                user_id=DEFAULT_WEBSOCKET_USER_ID,
                websocket_manager=broadcaster,
                runtime_factory=lambda _group: runtime,
                request_id=run_id,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await manager.send_message(
                serialize_run_event(
                    RunEvent(
                        event_type="run.failed",
                        run_id=run_id,
                        payload={"error": str(exc)},
                    )
                ),
                group_folder,
            )
        finally:
            if active_run_id == run_id:
                active_run_id = None
            if active_task is asyncio.current_task():
                active_task = None

    try:
        while True:
            message = await websocket.receive_text()
            cancel_run_id = _parse_cancel_run_id(message)
            if cancel_run_id is not None:
                if active_run_id == cancel_run_id:
                    await runtime.cancel(cancel_run_id)
                    await _cleanup_task(active_task)
                    active_task = None
                    active_run_id = None
                    await websocket.send_text(
                        serialize_run_event(
                            RunEvent(
                                event_type="run.failed",
                                run_id=cancel_run_id,
                                payload={"status": "cancelled"},
                            )
                        )
                    )
                continue

            if not message.strip():
                continue

            if active_task is not None and not active_task.done():
                continue

            run_id = uuid4().hex
            active_run_id = run_id
            active_task = asyncio.create_task(execute_message(message, run_id))
    except WebSocketDisconnect:
        pass
    finally:
        if active_run_id is not None:
            await runtime.cancel(active_run_id)
        await _cleanup_task(active_task)
        manager.disconnect(websocket, group_folder)


__all__ = ["manager", "router"]
