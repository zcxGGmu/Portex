from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace
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


def _login_headers_with_role(
    api_client: TestClient,
    *,
    username: str,
    role: str = "member",
) -> tuple[dict[str, str], str]:
    from services.auth import auth_service

    user = auth_service.register_user(username, "secret", role=role)
    login_response = api_client.post(
        "/auth/login",
        json={"username": username, "password": "secret"},
    )
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}, user.id


def test_usage_and_audit_routes_require_authentication(api_client: TestClient) -> None:
    usage_response = api_client.get("/usage/stats")
    audit_response = api_client.get("/audit/messages")

    assert usage_response.status_code == 401
    assert audit_response.status_code == 401


def test_usage_and_audit_routes_reject_member_role(api_client: TestClient) -> None:
    headers, _user_id = _login_headers_with_role(api_client, username="member", role="member")

    usage_response = api_client.get("/usage/stats", headers=headers)
    audit_response = api_client.get("/audit/messages", headers=headers)

    assert usage_response.status_code == 403
    assert usage_response.json() == {"detail": "permission denied"}
    assert audit_response.status_code == 403
    assert audit_response.json() == {"detail": "permission denied"}


def test_owner_can_read_usage_and_audit_payloads(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import audit as audit_routes
    from app.routes import usage as usage_routes

    headers, _owner_user_id = _login_headers_with_role(api_client, username="owner", role="owner")

    captured_calls: dict[str, tuple[int, str | None] | int] = {}

    class FakeUsageAuditService:
        async def get_usage_stats(self, *, days: int = 7):
            captured_calls["usage_days"] = days
            return SimpleNamespace(
                days=days,
                summary=SimpleNamespace(
                    total_messages=12,
                    total_runs=4,
                    total_user_messages=7,
                    total_assistant_messages=5,
                    total_active_days=3,
                ),
                daily=[
                    SimpleNamespace(
                        date="2026-03-15",
                        message_count=5,
                        run_count=2,
                        user_message_count=3,
                        assistant_message_count=2,
                    )
                ],
                channels=[
                    SimpleNamespace(channel="web", message_count=8, run_count=3),
                    SimpleNamespace(channel="telegram", message_count=4, run_count=1),
                ],
            )

        async def list_audit_messages(self, *, limit: int = 100, group_id: str | None = None):
            captured_calls["audit_args"] = (limit, group_id)
            return SimpleNamespace(
                limit=limit,
                group_id=group_id,
                has_more=False,
                items=[
                    SimpleNamespace(
                        message_id="msg-1",
                        chat_jid="web:project-alpha",
                        group_id="project-alpha",
                        channel="web",
                        run_id="run-1",
                        external_message_id="out-1",
                        sender="portex",
                        is_from_me=True,
                        slot_id="main",
                        content="reply",
                        timestamp=datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc),
                    )
                ],
            )

    fake_service = FakeUsageAuditService()
    app.dependency_overrides[usage_routes.get_usage_audit_service] = lambda: fake_service
    app.dependency_overrides[audit_routes.get_usage_audit_service] = lambda: fake_service

    try:
        usage_response = api_client.get("/usage/stats?days=14", headers=headers)
        audit_response = api_client.get(
            "/audit/messages?limit=25&group_id=project-alpha",
            headers=headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert usage_response.status_code == 200
    usage_payload = usage_response.json()
    assert usage_payload["days"] == 14
    assert usage_payload["summary"]["total_messages"] == 12
    assert usage_payload["daily"][0]["run_count"] == 2
    assert usage_payload["channels"][1]["channel"] == "telegram"

    assert audit_response.status_code == 200
    audit_payload = audit_response.json()
    assert audit_payload["limit"] == 25
    assert audit_payload["group_id"] == "project-alpha"
    assert audit_payload["has_more"] is False
    assert audit_payload["items"][0]["run_id"] == "run-1"

    assert captured_calls["usage_days"] == 14
    assert captured_calls["audit_args"] == (25, "project-alpha")
