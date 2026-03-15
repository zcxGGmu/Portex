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

    auth_service.reset()
    with TestClient(app) as client:
        yield client
    auth_service.reset()


def _login_headers(api_client: TestClient, *, username: str, role: str = "member") -> tuple[dict[str, str], str]:
    from services.auth import auth_service

    user = auth_service.register_user(username, "secret", role=role)
    login_response = api_client.post(
        "/auth/login",
        json={"username": username, "password": "secret"},
    )
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}, user.id


def _workspace(*, jid: str, folder: str, name: str, created_by: str):
    class Workspace:
        pass

    workspace = Workspace()
    workspace.jid = jid
    workspace.folder = folder
    workspace.name = name
    workspace.created_by = created_by
    workspace.is_home = False
    return workspace


class FakeGroupRegistry:
    def __init__(self, groups) -> None:
        self.groups = list(groups)

    async def get_web_workspace_by_folder(self, folder: str):
        for group in self.groups:
            if group.folder == folder:
                return group
        return None

    async def user_can_access_group(self, *, user_id: str, user_role: str | None = None, group):
        _ = user_role
        return group.created_by == user_id or user_id in getattr(group, "member_ids", set())


def test_terminal_routes_require_authentication(api_client: TestClient) -> None:
    create_response = api_client.post("/terminals/project-alpha/sessions", json={})
    get_response = api_client.get("/terminals/project-alpha/sessions/current")
    delete_response = api_client.delete("/terminals/project-alpha/sessions/current")

    assert create_response.status_code == 401
    assert get_response.status_code == 401
    assert delete_response.status_code == 401


def test_member_cannot_create_terminal_session(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    _ = owner_headers
    member_headers, member_id = _login_headers(api_client, username="member")
    registry = FakeGroupRegistry(
        [_workspace(jid="web:project-alpha", folder="project-alpha", name="Project Alpha", created_by=owner_id)]
    )
    registry.groups[0].member_ids = {member_id}

    class FakeTerminalService:
        async def create_session(self, **kwargs):
            _ = kwargs
            raise AssertionError("create_session should not be called for forbidden members")

    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: FakeTerminalService()

    try:
        response = api_client.post(
            "/terminals/project-alpha/sessions",
            headers=member_headers,
            json={},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_owner_can_create_read_and_delete_terminal_session(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes
    from services.terminal_sessions import TerminalSessionRecord

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    registry = FakeGroupRegistry(
        [_workspace(jid="web:project-alpha", folder="project-alpha", name="Project Alpha", created_by=owner_id)]
    )

    class FakeTerminalService:
        def __init__(self) -> None:
            from datetime import datetime, timezone

            self.record = TerminalSessionRecord(
                session_id="terminal-session-1",
                group_id="project-alpha",
                group_folder="project-alpha",
                owner_user_id=owner_id,
                backend="docker_container",
                container_name="portex-terminal-project-alpha-1",
                status="created",
                created_at=datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc),
            )
            self.closed = False

        async def create_session(self, **kwargs):
            _ = kwargs
            return self.record

        def get_current_session(self, group_folder: str):
            assert group_folder == "project-alpha"
            return self.record

        async def close_session_by_group(self, group_folder: str, *, owner_user_id: str):
            assert group_folder == "project-alpha"
            assert owner_user_id == owner_id
            self.closed = True
            return self.record

    service = FakeTerminalService()

    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: service

    try:
        create_response = api_client.post(
            "/terminals/project-alpha/sessions",
            headers=owner_headers,
            json={},
        )
        get_response = api_client.get(
            "/terminals/project-alpha/sessions/current",
            headers=owner_headers,
        )
        delete_response = api_client.delete(
            "/terminals/project-alpha/sessions/current",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 200
    assert create_response.json()["session_id"] == "terminal-session-1"
    assert get_response.status_code == 200
    assert get_response.json()["backend"] == "docker_container"
    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "closed"}
    assert service.closed is True


def test_create_terminal_session_returns_404_for_inaccessible_workspace(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    _ = owner_id
    registry = FakeGroupRegistry([])

    class FakeTerminalService:
        async def create_session(self, **kwargs):
            _ = kwargs
            raise AssertionError("create_session should not be called when workspace is missing")

    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: FakeTerminalService()

    try:
        response = api_client.post(
            "/terminals/project-alpha/sessions",
            headers=owner_headers,
            json={},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_create_terminal_session_maps_conflict_and_backend_errors(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes
    from services.terminal_sessions import (
        TerminalBackendDisabledError,
        TerminalSessionConflictError,
    )

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    registry = FakeGroupRegistry(
        [_workspace(jid="web:project-alpha", folder="project-alpha", name="Project Alpha", created_by=owner_id)]
    )

    class FakeConflictService:
        async def create_session(self, **kwargs):
            _ = kwargs
            raise TerminalSessionConflictError("active terminal session already owned by another user")

        def get_current_session(self, group_folder: str):
            _ = group_folder
            return None

    class FakeDisabledService:
        async def create_session(self, **kwargs):
            _ = kwargs
            raise TerminalBackendDisabledError("host_process backend is disabled for terminal sessions")

        def get_current_session(self, group_folder: str):
            _ = group_folder
            return None

    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: FakeConflictService()

    try:
        conflict_response = api_client.post(
            "/terminals/project-alpha/sessions",
            headers=owner_headers,
            json={},
        )
    finally:
        app.dependency_overrides.clear()

    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: FakeDisabledService()

    try:
        disabled_response = api_client.post(
            "/terminals/project-alpha/sessions",
            headers=owner_headers,
            json={"requested_mode": "host"},
        )
    finally:
        app.dependency_overrides.clear()

    assert conflict_response.status_code == 409
    assert disabled_response.status_code == 422
