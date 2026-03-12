from __future__ import annotations

from pathlib import Path
import sys
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
    from services.group_member_service import group_member_service

    auth_service.reset()
    group_member_service.reset()
    with TestClient(app) as client:
        yield client
    auth_service.reset()
    group_member_service.reset()


def _login_headers(api_client: TestClient, username: str, password: str) -> dict[str, str]:
    api_client.post("/auth/register", json={"username": username, "password": password})
    login_response = api_client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def test_post_messages_dispatches_through_real_service_boundary(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from domain.schemas import UnifiedMessage

    dispatched_messages: list[UnifiedMessage] = []

    class FakeDispatchService:
        async def dispatch_inbound_message(self, message: UnifiedMessage):
            dispatched_messages.append(message)
            return type(
                "DispatchResult",
                (),
                {
                    "run_id": "run-http-1",
                    "status": "completed",
                    "final_output": "http reply",
                },
            )()

    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()

    try:
        response = api_client.post(
            "/messages",
            json={"group_id": "group-demo", "content": "hello from http"},
            headers=_login_headers(api_client, "alice", "secret"),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["run_id"] == "run-http-1"
    assert payload["final_output"] == "http reply"
    assert payload["message_id"]
    assert len(dispatched_messages) == 1
    assert dispatched_messages[0].channel == "web"
    assert dispatched_messages[0].group_folder == "group-demo"
    assert dispatched_messages[0].chat_jid == "group-demo"
    assert dispatched_messages[0].content == "hello from http"


def test_post_messages_maps_dispatch_errors_to_http_400(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from services.message_dispatch import MessageDispatchError

    class FailingDispatchService:
        async def dispatch_inbound_message(self, message):
            _ = message
            raise MessageDispatchError("dispatch failed")

    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FailingDispatchService()

    try:
        response = api_client.post(
            "/messages",
            json={"group_id": "group-demo", "content": "hello from http"},
            headers=_login_headers(api_client, "alice", "secret"),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {"detail": "dispatch failed"}
