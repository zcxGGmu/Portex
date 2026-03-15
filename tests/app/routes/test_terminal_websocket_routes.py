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


@pytest.fixture
def api_client() -> Iterator[TestClient]:
    from app.main import app
    from services.auth import auth_service

    auth_service.reset()
    with TestClient(app) as client:
        yield client
    auth_service.reset()


def _login_headers(api_client: TestClient, *, username: str, role: str = "owner") -> tuple[dict[str, str], str]:
    from services.auth import auth_service

    user = auth_service.register_user(username, "secret", role=role)
    login_response = api_client.post(
        "/auth/login",
        json={"username": username, "password": "secret"},
    )
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}, user.id


def test_terminal_websocket_emits_ready_output_and_exit(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes
    from services.terminal_sessions import TerminalSessionEvent, TerminalSessionRecord

    headers, owner_id = _login_headers(api_client, username="owner", role="owner")

    class FakeTerminalService:
        async def attach_session(self, session_id: str, *, owner_user_id: str):
            from datetime import datetime, timezone

            assert session_id == "session-1"
            assert owner_user_id == owner_id
            queue: asyncio.Queue[TerminalSessionEvent] = asyncio.Queue()
            queue.put_nowait(TerminalSessionEvent(event_type="terminal.output", data="hello"))
            queue.put_nowait(TerminalSessionEvent(event_type="terminal.exit", exit_code=0))
            return (
                TerminalSessionRecord(
                    session_id="session-1",
                    group_id="project-alpha",
                    group_folder="project-alpha",
                    owner_user_id=owner_id,
                    backend="docker_container",
                    container_name="portex-terminal-project-alpha-1",
                    status="attached",
                    created_at=datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc),
                    last_attached_at=datetime(2026, 3, 15, 12, 1, tzinfo=timezone.utc),
                ),
                queue,
            )

        async def detach_session(self, session_id: str, *, owner_user_id: str):
            assert session_id == "session-1"
            assert owner_user_id == owner_id

        async def send_input(self, session_id: str, *, owner_user_id: str, data: str):
            _ = (session_id, owner_user_id, data)

        async def resize(self, session_id: str, *, owner_user_id: str, cols: int, rows: int):
            _ = (session_id, owner_user_id, cols, rows)

        async def close_session(self, session_id: str, *, owner_user_id: str):
            _ = (session_id, owner_user_id)

    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: FakeTerminalService()

    try:
        with api_client.websocket_connect("/ws/terminals/session-1", headers=headers) as websocket:
            ready_payload = json.loads(websocket.receive_text())
            output_payload = json.loads(websocket.receive_text())
            exit_payload = json.loads(websocket.receive_text())
    finally:
        app.dependency_overrides.clear()

    assert ready_payload["type"] == "terminal.ready"
    assert ready_payload["session_id"] == "session-1"
    assert output_payload == {"type": "terminal.output", "data": "hello"}
    assert exit_payload == {"type": "terminal.exit", "exit_code": 0}


def test_terminal_websocket_forwards_input_resize_and_invalid_message_errors(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes
    from services.terminal_sessions import TerminalSessionRecord

    headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    received_inputs: list[str] = []
    received_resizes: list[tuple[int, int]] = []
    detach_calls: list[str] = []
    detach_event = threading.Event()

    class FakeTerminalService:
        async def attach_session(self, session_id: str, *, owner_user_id: str):
            from datetime import datetime, timezone

            _ = owner_user_id
            queue: asyncio.Queue = asyncio.Queue()
            return (
                TerminalSessionRecord(
                    session_id=session_id,
                    group_id="project-alpha",
                    group_folder="project-alpha",
                    owner_user_id=owner_id,
                    backend="docker_container",
                    container_name="portex-terminal-project-alpha-1",
                    status="attached",
                    created_at=datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc),
                    last_attached_at=datetime(2026, 3, 15, 12, 1, tzinfo=timezone.utc),
                ),
                queue,
            )

        async def detach_session(self, session_id: str, *, owner_user_id: str):
            _ = owner_user_id
            detach_calls.append(session_id)
            detach_event.set()

        async def send_input(self, session_id: str, *, owner_user_id: str, data: str):
            _ = (session_id, owner_user_id)
            received_inputs.append(data)

        async def resize(self, session_id: str, *, owner_user_id: str, cols: int, rows: int):
            _ = (session_id, owner_user_id)
            received_resizes.append((cols, rows))

        async def close_session(self, session_id: str, *, owner_user_id: str):
            _ = (session_id, owner_user_id)

    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: FakeTerminalService()

    try:
        with api_client.websocket_connect("/ws/terminals/session-2", headers=headers) as websocket:
            ready_payload = json.loads(websocket.receive_text())
            assert ready_payload["type"] == "terminal.ready"

            websocket.send_text(json.dumps({"type": "terminal.input", "data": "pwd\n"}))
            websocket.send_text(json.dumps({"type": "terminal.resize", "cols": 120, "rows": 40}))
            websocket.send_text(json.dumps({"type": "unexpected"}))

            error_payload = json.loads(websocket.receive_text())
    finally:
        app.dependency_overrides.clear()

    assert received_inputs == ["pwd\n"]
    assert received_resizes == [(120, 40)]
    assert error_payload["type"] == "terminal.error"
    assert detach_event.wait(1)
    assert detach_calls == ["session-2"]
