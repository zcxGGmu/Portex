from __future__ import annotations

import asyncio
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


def _login_headers_with_user_id(
    api_client: TestClient,
    username: str = "alice",
) -> tuple[dict[str, str], str]:
    register_response = api_client.post(
        "/auth/register",
        json={"username": username, "password": "secret"},
    )
    assert register_response.status_code == 200
    user_id = register_response.json()["user_id"]
    login_response = api_client.post(
        "/auth/login",
        json={"username": username, "password": "secret"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user_id


def _login_headers(api_client: TestClient, username: str = "alice") -> dict[str, str]:
    headers, _ = _login_headers_with_user_id(api_client, username=username)
    return headers


def _seed_shared_workspace(
    *,
    jid: str,
    folder: str,
    owner_id: str,
    member_id: str,
) -> None:
    from infra.db.database import AsyncSessionLocal
    from services.group_member_service import GroupMemberService
    from services.group_registry import GroupRegistryService

    async def _seed() -> None:
        async with AsyncSessionLocal() as session:
            registry = GroupRegistryService(db=session)
            members = GroupMemberService(db=session)
            await registry.ensure_registered_group(
                jid=jid,
                name="Shared Workspace",
                folder=folder,
                created_by=owner_id,
                is_home=False,
            )
            await members.add_member(
                folder,
                member_id,
                added_by=owner_id,
            )

    asyncio.run(_seed())


def test_execution_status_route_requires_authentication(api_client: TestClient) -> None:
    response = api_client.get("/executions/run-missing")

    assert response.status_code == 401


def test_execution_status_route_returns_run_snapshot(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import executions as execution_routes
    from services.execution_coordinator import ExecutionRunSnapshot

    headers, user_id = _login_headers_with_user_id(api_client)

    class FakeCoordinator:
        def get_run_snapshot(self, run_id: str):
            if run_id != "run-visible":
                return None
            return ExecutionRunSnapshot(
                run_id=run_id,
                group_folder="group-demo",
                chat_jid="group-demo",
                user_id=user_id,
                source="web",
                requested_mode="host",
                status="running",
                backend="host_process",
                session_id="group-demo",
                created_at=datetime(2026, 3, 13, 8, 0, tzinfo=timezone.utc),
                started_at=datetime(2026, 3, 13, 8, 0, 1, tzinfo=timezone.utc),
                finished_at=None,
                final_output=None,
                error=None,
                timeout_ms=None,
                recovery_attempted=False,
                recovery_reason=None,
                recovery_succeeded=None,
            )

    app.dependency_overrides[execution_routes.get_execution_coordinator] = lambda: FakeCoordinator()

    try:
        response = api_client.get(
            "/executions/run-visible",
            headers=headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run-visible"
    assert payload["status"] == "running"
    assert payload["backend"] == "host_process"
    assert payload["session_id"] == "group-demo"
    assert payload["recovery"]["attempted"] is False


def test_execution_status_route_returns_404_for_unknown_run(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import executions as execution_routes

    class FakeCoordinator:
        def get_run_snapshot(self, run_id: str):
            _ = run_id
            return None

    app.dependency_overrides[execution_routes.get_execution_coordinator] = lambda: FakeCoordinator()

    try:
        response = api_client.get(
            "/executions/run-missing",
            headers=_login_headers(api_client, username="bob"),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "execution run not found"}


def test_execution_status_route_tolerates_unknown_requested_mode(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import executions as execution_routes
    from services.execution_coordinator import ExecutionRunSnapshot

    headers, user_id = _login_headers_with_user_id(api_client, username="carol")

    class FakeCoordinator:
        def get_run_snapshot(self, run_id: str):
            if run_id != "run-unknown-mode":
                return None
            return ExecutionRunSnapshot(
                run_id=run_id,
                group_folder="group-demo",
                chat_jid="group-demo",
                user_id=user_id,
                source="web",
                requested_mode="unknown",
                status="failed",
                backend=None,
                session_id=None,
                created_at=datetime(2026, 3, 13, 9, 0, tzinfo=timezone.utc),
                started_at=datetime(2026, 3, 13, 9, 0, 1, tzinfo=timezone.utc),
                finished_at=datetime(2026, 3, 13, 9, 0, 2, tzinfo=timezone.utc),
                final_output=None,
                error="unsupported execution mode",
                timeout_ms=None,
                recovery_attempted=False,
                recovery_reason=None,
                recovery_succeeded=None,
            )

    app.dependency_overrides[execution_routes.get_execution_coordinator] = lambda: FakeCoordinator()

    try:
        response = api_client.get(
            "/executions/run-unknown-mode",
            headers=headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run-unknown-mode"
    assert payload["status"] == "failed"
    assert "requested_mode" not in payload


def test_execution_status_route_hides_other_users_runs(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import executions as execution_routes
    from services.execution_coordinator import ExecutionRunSnapshot

    _, owner_user_id = _login_headers_with_user_id(api_client, username="owner")
    viewer_headers, _ = _login_headers_with_user_id(api_client, username="viewer")

    class FakeCoordinator:
        def get_run_snapshot(self, run_id: str):
            if run_id != "run-private":
                return None
            return ExecutionRunSnapshot(
                run_id=run_id,
                group_folder="group-demo",
                chat_jid="group-demo",
                user_id=owner_user_id,
                source="web",
                requested_mode="openai",
                status="completed",
                backend="openai_runtime",
                session_id="group-demo",
                created_at=datetime(2026, 3, 13, 10, 0, tzinfo=timezone.utc),
                started_at=datetime(2026, 3, 13, 10, 0, 1, tzinfo=timezone.utc),
                finished_at=datetime(2026, 3, 13, 10, 0, 2, tzinfo=timezone.utc),
                final_output="done",
                error=None,
                timeout_ms=None,
                recovery_attempted=False,
                recovery_reason=None,
                recovery_succeeded=None,
            )

    app.dependency_overrides[execution_routes.get_execution_coordinator] = lambda: FakeCoordinator()

    try:
        response = api_client.get("/executions/run-private", headers=viewer_headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "execution run not found"}


def test_execution_status_route_allows_shared_workspace_member(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import executions as execution_routes
    from services.execution_coordinator import ExecutionRunSnapshot

    _, owner_id = _login_headers_with_user_id(api_client, username="owner")
    member_headers, member_id = _login_headers_with_user_id(api_client, username="member")
    shared_folder = f"shared-exec-{owner_id[:8]}-{member_id[:8]}"
    _seed_shared_workspace(
        jid=f"web:{shared_folder}",
        folder=shared_folder,
        owner_id=owner_id,
        member_id=member_id,
    )

    class FakeCoordinator:
        def get_run_snapshot(self, run_id: str):
            if run_id != "run-shared-member":
                return None
            return ExecutionRunSnapshot(
                run_id=run_id,
                group_folder=shared_folder,
                chat_jid=f"web:{shared_folder}",
                user_id=owner_id,
                source="web",
                requested_mode="openai",
                status="completed",
                backend="openai_runtime",
                session_id=shared_folder,
                created_at=datetime(2026, 3, 14, 8, 0, tzinfo=timezone.utc),
                started_at=datetime(2026, 3, 14, 8, 0, 1, tzinfo=timezone.utc),
                finished_at=datetime(2026, 3, 14, 8, 0, 2, tzinfo=timezone.utc),
                final_output="shared done",
                error=None,
                timeout_ms=None,
                recovery_attempted=False,
                recovery_reason=None,
                recovery_succeeded=None,
            )

    app.dependency_overrides[execution_routes.get_execution_coordinator] = lambda: FakeCoordinator()

    try:
        response = api_client.get("/executions/run-shared-member", headers=member_headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run-shared-member"
    assert payload["group_folder"] == shared_folder
    assert payload["final_output"] == "shared done"


def test_execution_status_route_hides_inaccessible_shared_workspace_run(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import executions as execution_routes
    from services.execution_coordinator import ExecutionRunSnapshot

    _, owner_id = _login_headers_with_user_id(api_client, username="owner")
    _, member_id = _login_headers_with_user_id(api_client, username="member")
    outsider_headers, outsider_id = _login_headers_with_user_id(api_client, username="outsider")
    shared_folder = f"shared-exec-{owner_id[:8]}-{member_id[:8]}-hidden"
    _seed_shared_workspace(
        jid=f"web:{shared_folder}",
        folder=shared_folder,
        owner_id=owner_id,
        member_id=member_id,
    )

    class FakeCoordinator:
        def get_run_snapshot(self, run_id: str):
            if run_id != "run-shared-hidden":
                return None
            return ExecutionRunSnapshot(
                run_id=run_id,
                group_folder=shared_folder,
                chat_jid=f"web:{shared_folder}",
                user_id=owner_id,
                source="web",
                requested_mode="host",
                status="running",
                backend="host_process",
                session_id=shared_folder,
                created_at=datetime(2026, 3, 14, 9, 0, tzinfo=timezone.utc),
                started_at=datetime(2026, 3, 14, 9, 0, 1, tzinfo=timezone.utc),
                finished_at=None,
                final_output=None,
                error=None,
                timeout_ms=None,
                recovery_attempted=False,
                recovery_reason=None,
                recovery_succeeded=None,
            )

    app.dependency_overrides[execution_routes.get_execution_coordinator] = lambda: FakeCoordinator()

    try:
        response = api_client.get("/executions/run-shared-hidden", headers=outsider_headers)
    finally:
        app.dependency_overrides.clear()

    assert outsider_id not in {owner_id, member_id}
    assert response.status_code == 404
    assert response.json() == {"detail": "execution run not found"}
