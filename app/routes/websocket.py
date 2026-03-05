"""WebSocket routes."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket import ConnectionManager

router = APIRouter(tags=["websocket"])
manager = ConnectionManager()


@router.websocket("/ws/{group_folder}")
async def websocket_endpoint(websocket: WebSocket, group_folder: str) -> None:
    await manager.connect(websocket, group_folder)
    try:
        while True:
            message = await websocket.receive_text()
            await manager.send_message(message=message, room=group_folder)
    except WebSocketDisconnect:
        manager.disconnect(websocket, group_folder)


__all__ = ["manager", "router"]
