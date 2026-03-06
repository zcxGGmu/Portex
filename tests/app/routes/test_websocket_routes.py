from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
import threading
from typing import Iterator

from fastapi.testclient import TestClient
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class DummyWebSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.messages: list[str] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_text(self, message: str) -> None:
        self.messages.append(message)


@pytest.fixture
def api_client() -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.mark.asyncio
async def test_connection_manager_tracks_connect_and_disconnect() -> None:
    from app.websocket import ConnectionManager

    manager = ConnectionManager()
    socket = DummyWebSocket()

    await manager.connect(socket, "room-1")

    assert socket.accepted is True
    assert manager.active_connections["room-1"] == {socket}

    manager.disconnect(socket, "room-1")

    assert "room-1" not in manager.active_connections


@pytest.mark.asyncio
async def test_connection_manager_sends_to_only_target_room() -> None:
    from app.websocket import ConnectionManager

    manager = ConnectionManager()
    room_a_socket_1 = DummyWebSocket()
    room_a_socket_2 = DummyWebSocket()
    room_b_socket = DummyWebSocket()

    await manager.connect(room_a_socket_1, "room-a")
    await manager.connect(room_a_socket_2, "room-a")
    await manager.connect(room_b_socket, "room-b")

    await manager.send_message("hello", "room-a")

    assert room_a_socket_1.messages == ["hello"]
    assert room_a_socket_2.messages == ["hello"]
    assert room_b_socket.messages == []


def test_websocket_endpoint_starts_background_execution_for_text_message(api_client: TestClient) -> None:
    from app.routes import websocket as websocket_routes

    recorded_calls: list[dict[str, str]] = []

    async def fake_trigger_agent_execution(
        *,
        group_folder: str,
        message: str,
        user_id: str,
        websocket_manager: object,
        runtime_factory: object,
        session_id_factory: object | None = None,
        request_id: str | None = None,
        timeout_ms: int = 300_000,
    ) -> str:
        _ = (runtime_factory, session_id_factory, timeout_ms)
        recorded_calls.append(
            {
                "group_folder": group_folder,
                "message": message,
                "user_id": user_id,
                "request_id": request_id or "",
            }
        )
        await websocket_manager.send_message(
            json.dumps({"event_type": "run.started", "run_id": request_id, "payload": {"status": "started"}}),
            group_folder,
        )
        return request_id or "missing"

    class FakeRuntime:
        async def cancel(self, run_id: str) -> None:
            _ = run_id

    class FixedUUID:
        hex = "run-fixed"

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(websocket_routes, "trigger_agent_execution", fake_trigger_agent_execution, raising=False)
    monkeypatch.setattr(websocket_routes, "create_runtime", lambda: FakeRuntime(), raising=False)
    monkeypatch.setattr(websocket_routes, "uuid4", lambda: FixedUUID(), raising=False)

    try:
        with api_client.websocket_connect("/ws/group-1") as ws_1:
            ws_1.send_text("ping")

            payload = json.loads(ws_1.receive_text())
            assert payload["event_type"] == "run.started"
            assert recorded_calls == [
                {
                    "group_folder": "group-1",
                    "message": "ping",
                    "user_id": "websocket-user",
                    "request_id": "run-fixed",
                }
            ]
    finally:
        monkeypatch.undo()


def test_websocket_endpoint_cancels_active_run_from_same_socket(api_client: TestClient) -> None:
    from app.routes import websocket as websocket_routes

    cancel_event = threading.Event()

    class FakeRuntime:
        def __init__(self) -> None:
            self.cancelled_run_ids: list[str] = []

        async def cancel(self, run_id: str) -> None:
            self.cancelled_run_ids.append(run_id)
            cancel_event.set()

    runtime = FakeRuntime()

    async def fake_trigger_agent_execution(
        *,
        group_folder: str,
        message: str,
        user_id: str,
        websocket_manager: object,
        runtime_factory: object,
        session_id_factory: object | None = None,
        request_id: str | None = None,
        timeout_ms: int = 300_000,
    ) -> str:
        _ = (group_folder, message, user_id, runtime_factory, session_id_factory, timeout_ms)
        await asyncio.to_thread(cancel_event.wait)
        return request_id or "missing"

    class FixedUUID:
        hex = "run-cancel"

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(websocket_routes, "trigger_agent_execution", fake_trigger_agent_execution, raising=False)
    monkeypatch.setattr(websocket_routes, "create_runtime", lambda: runtime, raising=False)
    monkeypatch.setattr(websocket_routes, "uuid4", lambda: FixedUUID(), raising=False)

    try:
        with api_client.websocket_connect("/ws/group-1") as ws:
            ws.send_text("ping")
            ws.send_text(json.dumps({"type": "cancel", "run_id": "run-cancel"}))
            assert cancel_event.wait(1)
            assert runtime.cancelled_run_ids == ["run-cancel"]
            payload = json.loads(ws.receive_text())
            assert payload["event_type"] == "run.failed"
            assert payload["payload"] == {"status": "cancelled"}
    finally:
        monkeypatch.undo()
