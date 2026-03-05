"""WebSocket connection manager for room-based broadcasting."""

from __future__ import annotations

from collections.abc import Iterable
from fastapi import WebSocket


class ConnectionManager:
    """Manage active websocket connections grouped by room."""

    def __init__(self) -> None:
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str) -> None:
        await websocket.accept()
        room_connections = self.active_connections.setdefault(room, set())
        room_connections.add(websocket)

    def disconnect(self, websocket: WebSocket, room: str) -> None:
        room_connections = self.active_connections.get(room)
        if room_connections is None:
            return

        room_connections.discard(websocket)
        if not room_connections:
            self.active_connections.pop(room, None)

    async def send_message(self, message: str, room: str) -> None:
        for connection in self._room_connections(room):
            await connection.send_text(message)

    def connection_count(self, room: str) -> int:
        return len(self.active_connections.get(room, set()))

    def reset(self) -> None:
        self.active_connections.clear()

    def _room_connections(self, room: str) -> Iterable[WebSocket]:
        return tuple(self.active_connections.get(room, set()))


__all__ = ["ConnectionManager"]
