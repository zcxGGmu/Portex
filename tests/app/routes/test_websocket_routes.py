from __future__ import annotations

from pathlib import Path
import sys
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


def test_websocket_endpoint_broadcasts_messages_to_room(api_client: TestClient) -> None:
    with (
        api_client.websocket_connect("/ws/group-1") as ws_1,
        api_client.websocket_connect("/ws/group-1") as ws_2,
    ):
        ws_1.send_text("ping")

        assert ws_2.receive_text() == "ping"
