"""WebSocket routes."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket import ConnectionManager
from infra.runtime.adapter import RunEvent
from portex.contracts.events import EventType
from services.agent_trigger import serialize_run_event
from services.execution_coordinator import ExecutionRequest, ExecutionResult
from services.execution_runtime import get_execution_coordinator

router = APIRouter(tags=["websocket"])
manager = ConnectionManager()
DEFAULT_WEBSOCKET_USER_ID = "websocket-user"


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
    broadcaster = ConnectionScopedBroadcaster(websocket, manager)
    coordinator = get_execution_coordinator()
    active_run_id: str | None = None
    active_task: asyncio.Task[None] | None = None
    terminal_event_seen = False

    async def broadcast_event(event: RunEvent) -> None:
        nonlocal terminal_event_seen
        if event.event_type in {
            EventType.RUN_COMPLETED.value,
            EventType.RUN_FAILED.value,
            EventType.RUN_TIMEOUT.value,
        }:
            terminal_event_seen = True
        await broadcaster.send_message(
            serialize_run_event(event),
            group_folder,
        )

    async def emit_terminal_event(result: ExecutionResult) -> None:
        if terminal_event_seen and result.status in {"completed", "failed", "timeout"}:
            return

        if result.status == "cancelled":
            await websocket.send_text(
                serialize_run_event(
                    RunEvent(
                        event_type=EventType.RUN_FAILED.value,
                        run_id=result.run_id,
                        payload={"status": "cancelled"},
                    )
                )
            )
            return

        if result.status == "timeout":
            await broadcaster.send_message(
                serialize_run_event(
                    RunEvent(
                        event_type=EventType.RUN_TIMEOUT.value,
                        run_id=result.run_id,
                        payload={"status": "timeout", "timeout_ms": result.timeout_ms},
                    )
                ),
                group_folder,
            )
            return

        if result.status == "completed":
            if result.backend == "openai_runtime":
                return
            await broadcaster.send_message(
                serialize_run_event(
                    RunEvent(
                        event_type=EventType.RUN_COMPLETED.value,
                        run_id=result.run_id,
                        payload={
                            "status": "response.completed",
                            "final_output": result.final_output,
                        },
                    )
                ),
                group_folder,
            )
            return

        if result.status == "failed":
            await broadcaster.send_message(
                serialize_run_event(
                    RunEvent(
                        event_type=EventType.RUN_FAILED.value,
                        run_id=result.run_id,
                        payload={"error": result.error or "execution failed"},
                    )
                ),
                group_folder,
            )

    async def wait_for_result(run_id: str) -> None:
        nonlocal active_run_id, active_task

        try:
            result = await coordinator.wait_for_run(run_id)
            await emit_terminal_event(result)
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
                    await coordinator.cancel(cancel_run_id)
                    await _cleanup_task(active_task)
                    active_task = None
                    active_run_id = None
                    terminal_event_seen = True
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

            terminal_event_seen = False
            handle = await coordinator.submit_execution(
                ExecutionRequest(
                    group_folder=group_folder,
                    chat_jid=group_folder,
                    user_id=DEFAULT_WEBSOCKET_USER_ID,
                    prompt=message,
                    source="web",
                    request_metadata={"event_handler": broadcast_event},
                )
            )
            active_run_id = handle.run_id
            active_task = asyncio.create_task(wait_for_result(handle.run_id))
    except WebSocketDisconnect:
        pass
    finally:
        if active_run_id is not None:
            await coordinator.cancel(active_run_id)
        await _cleanup_task(active_task)
        manager.disconnect(websocket, group_folder)


__all__ = ["manager", "router"]
