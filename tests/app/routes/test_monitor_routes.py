from __future__ import annotations

from datetime import datetime, timezone
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


def test_monitor_route_requires_authentication(api_client: TestClient) -> None:
    response = api_client.get("/monitor")

    assert response.status_code == 401


def test_monitor_route_rejects_member_role(api_client: TestClient) -> None:
    headers, _user_id = _login_headers_with_role(api_client, username="member", role="member")

    response = api_client.get("/monitor", headers=headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "permission denied"}


def test_monitor_route_returns_aggregated_status_for_owner(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import monitor as monitor_routes
    from services.execution_coordinator import ExecutionRunSnapshot

    headers, owner_user_id = _login_headers_with_role(api_client, username="owner", role="owner")

    class FakeCoordinator:
        def get_monitor_queue_snapshot(self):
            return [
                type(
                    "QueueItem",
                    (),
                    {
                        "group_id": "project-alpha",
                        "queued_runs": 2,
                        "running_runs": 1,
                        "active_run_id": "run-active",
                        "active_backend": "openai_runtime",
                    },
                )()
            ]

        def list_run_snapshots(self, limit: int = 50):
            assert limit == 50
            return [
                ExecutionRunSnapshot(
                    run_id="run-active",
                    group_folder="project-alpha",
                    chat_jid="web:project-alpha",
                    user_id=owner_user_id,
                    source="web",
                    slot_id="draft",
                    requested_mode="host",
                    status="running",
                    backend="host_process",
                    session_id="project-alpha#slot:draft",
                    created_at=datetime(2026, 3, 14, 8, 0, tzinfo=timezone.utc),
                    started_at=datetime(2026, 3, 14, 8, 0, 1, tzinfo=timezone.utc),
                    finished_at=None,
                    error=None,
                    timeout_ms=None,
                    recovery_attempted=False,
                    recovery_reason=None,
                    recovery_succeeded=None,
                )
            ]

    app.dependency_overrides[monitor_routes.get_execution_coordinator] = lambda: FakeCoordinator()
    app.dependency_overrides[monitor_routes.get_monitor_backend_health] = lambda: [
        {
            "backend": "openai_runtime",
            "status": "ok",
            "detail": "runtime factory available",
        },
        {
            "backend": "docker_container",
            "status": "error",
            "detail": "docker unavailable",
        },
    ]

    try:
        response = api_client.get("/monitor", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["health"]["api_status"] == "ok"
    assert payload["health"]["coordinator_status"] == "ok"
    assert payload["health"]["backends"][1]["status"] == "error"
    assert payload["queue"]["groups"] == [
        {
            "group_id": "project-alpha",
            "queued_runs": 2,
            "running_runs": 1,
            "active_run_id": "run-active",
            "active_backend": "openai_runtime",
        }
    ]
    assert payload["runs"]["items"][0]["run_id"] == "run-active"
    assert payload["runs"]["items"][0]["slot_id"] == "draft"
    assert payload["runs"]["items"][0]["backend"] == "host_process"


def test_monitor_route_returns_idle_state_when_coordinator_is_empty(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import monitor as monitor_routes

    headers, _owner_user_id = _login_headers_with_role(api_client, username="owner", role="owner")

    class EmptyCoordinator:
        def get_monitor_queue_snapshot(self):
            return []

        def list_run_snapshots(self, limit: int = 50):
            assert limit == 50
            return []

    app.dependency_overrides[monitor_routes.get_execution_coordinator] = lambda: EmptyCoordinator()
    app.dependency_overrides[monitor_routes.get_monitor_backend_health] = lambda: []

    try:
        response = api_client.get("/monitor", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["queue"]["groups"] == []
    assert response.json()["runs"]["items"] == []
