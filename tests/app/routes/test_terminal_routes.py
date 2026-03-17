from __future__ import annotations

import asyncio
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


class _RouteFakeBridge:
    def __init__(self) -> None:
        self._event_handler = None

    async def start(self, on_event) -> None:
        self._event_handler = on_event

    async def send_input(self, data: str) -> None:
        _ = data

    async def resize(self, *, cols: int, rows: int) -> None:
        _ = (cols, rows)

    async def close(self) -> None:
        return None


def test_terminal_routes_require_authentication(api_client: TestClient) -> None:
    create_response = api_client.post("/terminals/project-alpha/sessions", json={})
    get_response = api_client.get("/terminals/project-alpha/sessions/current")
    history_response = api_client.get("/terminals/project-alpha/sessions/current/history")
    timeline_response = api_client.get("/terminals/project-alpha/sessions/history")
    search_response = api_client.get("/terminals/project-alpha/sessions/history/search?q=error")
    detail_response = api_client.get("/terminals/project-alpha/sessions/history/test-session")
    delete_response = api_client.delete("/terminals/project-alpha/sessions/current")
    force_delete_response = api_client.delete("/terminals/project-alpha/sessions/force")

    assert create_response.status_code == 401
    assert get_response.status_code == 401
    assert history_response.status_code == 401
    assert timeline_response.status_code == 401
    assert search_response.status_code == 401
    assert detail_response.status_code == 401
    assert delete_response.status_code == 401
    assert force_delete_response.status_code == 401


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
        force_response = api_client.delete(
            "/terminals/project-alpha/sessions/force",
            headers=member_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert force_response.status_code == 403


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


def test_operator_can_force_close_terminal_session(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    registry = FakeGroupRegistry(
        [_workspace(jid="web:project-alpha", folder="project-alpha", name="Project Alpha", created_by=owner_id)]
    )

    class FakeTerminalService:
        def __init__(self) -> None:
            self.force_closed = False

        async def force_close_session_by_group(self, group_folder: str):
            assert group_folder == "project-alpha"
            self.force_closed = True

    service = FakeTerminalService()
    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: service

    try:
        response = api_client.delete(
            "/terminals/project-alpha/sessions/force",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "closed"}
    assert service.force_closed is True


def test_owner_can_read_terminal_session_history(api_client: TestClient) -> None:
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
                status="attached",
                created_at=datetime(2026, 3, 16, 9, 0, tzinfo=timezone.utc),
            )

        async def get_history_by_group(self, group_folder: str):
            assert group_folder == "project-alpha"
            return SimpleNamespace(
                record=self.record,
                output="line1\nline2\n",
                output_bytes=12,
                history_max_bytes=32768,
                truncated=False,
            )

    service = FakeTerminalService()
    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: service

    try:
        response = api_client.get(
            "/terminals/project-alpha/sessions/current/history",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["output"] == "line1\nline2\n"
    assert response.json()["output_bytes"] == 12
    assert response.json()["history_max_bytes"] == 32768
    assert response.json()["truncated"] is False
    assert response.json()["session"]["session_id"] == "terminal-session-1"


def test_terminal_history_route_returns_404_when_session_is_missing(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes
    from services.terminal_sessions import TerminalSessionNotFoundError

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    registry = FakeGroupRegistry(
        [_workspace(jid="web:project-alpha", folder="project-alpha", name="Project Alpha", created_by=owner_id)]
    )

    class FakeTerminalService:
        async def get_history_by_group(self, group_folder: str):
            _ = group_folder
            raise TerminalSessionNotFoundError("terminal session not found")

    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: FakeTerminalService()

    try:
        response = api_client.get(
            "/terminals/project-alpha/sessions/current/history",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "terminal session not found"


def test_owner_can_read_terminal_history_timeline(api_client: TestClient) -> None:
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
                session_id="terminal-session-2",
                group_id="project-alpha",
                group_folder="project-alpha",
                owner_user_id=owner_id,
                backend="docker_container",
                container_name="portex-terminal-project-alpha-2",
                status="closed",
                created_at=datetime(2026, 3, 16, 10, 0, tzinfo=timezone.utc),
            )
            self.snapshot_at = datetime(2026, 3, 16, 10, 30, tzinfo=timezone.utc)
            self.last_call: tuple[str, int, int, str | None, str | None, str | None] | None = None

        async def list_history_timeline_by_group(
            self,
            group_folder: str,
            *,
            limit: int,
            offset: int,
            status: str | None,
            owner_user_id: str | None,
            session_id_prefix: str | None,
        ):
            self.last_call = (group_folder, limit, offset, status, owner_user_id, session_id_prefix)
            return SimpleNamespace(
                limit=limit,
                offset=offset,
                has_more=True,
                items=[
                    SimpleNamespace(
                        record=self.record,
                        snapshot_at=self.snapshot_at,
                        output_bytes=18,
                        history_max_bytes=32768,
                        truncated=False,
                    )
                ],
            )

    service = FakeTerminalService()
    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: service

    try:
        response = api_client.get(
            "/terminals/project-alpha/sessions/history?limit=1&offset=2&status=closed&owner_user_id="
            f"{owner_id}&session_id_prefix=terminal-",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["limit"] == 1
    assert response.json()["offset"] == 2
    assert response.json()["has_more"] is True
    assert response.json()["items"][0]["session"]["session_id"] == "terminal-session-2"
    assert response.json()["items"][0]["snapshot_at"] == "2026-03-16T10:30:00Z"
    assert service.last_call == ("project-alpha", 1, 2, "closed", owner_id, "terminal-")


def test_terminal_history_timeline_route_returns_404_when_workspace_has_no_history(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes
    from services.terminal_sessions import TerminalSessionNotFoundError

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    registry = FakeGroupRegistry(
        [_workspace(jid="web:project-alpha", folder="project-alpha", name="Project Alpha", created_by=owner_id)]
    )

    class FakeTerminalService:
        async def list_history_timeline_by_group(
            self,
            group_folder: str,
            *,
            limit: int,
            offset: int,
            status: str | None,
            owner_user_id: str | None,
            session_id_prefix: str | None,
        ):
            _ = (group_folder, limit, offset, status, owner_user_id, session_id_prefix)
            raise TerminalSessionNotFoundError("terminal session not found")

    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: FakeTerminalService()

    try:
        response = api_client.get(
            "/terminals/project-alpha/sessions/history",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "terminal session not found"


def test_owner_can_search_terminal_history_output(api_client: TestClient) -> None:
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
                session_id="terminal-session-search",
                group_id="project-alpha",
                group_folder="project-alpha",
                owner_user_id=owner_id,
                backend="docker_container",
                container_name="portex-terminal-project-alpha-search",
                status="closed",
                created_at=datetime(2026, 3, 17, 10, 0, tzinfo=timezone.utc),
            )
            self.last_call: tuple[str, str, int, int] | None = None

        async def search_history_by_group(
            self,
            group_folder: str,
            *,
            query: str,
            limit: int,
            offset: int,
        ):
            from datetime import datetime, timezone

            self.last_call = (group_folder, query, limit, offset)
            return SimpleNamespace(
                query=query,
                limit=limit,
                offset=offset,
                total=1,
                has_more=False,
                items=[
                    SimpleNamespace(
                        record=self.record,
                        snapshot_at=datetime(2026, 3, 17, 10, 5, tzinfo=timezone.utc),
                        match_count=2,
                        snippets=["...ERROR one...", "...error two..."],
                        snippet_matches=[
                            SimpleNamespace(
                                text="...ERROR one...",
                                match_index=0,
                                match_offset=120,
                            ),
                            SimpleNamespace(
                                text="...error two...",
                                match_index=1,
                                match_offset=256,
                            ),
                        ],
                    )
                ],
            )

    service = FakeTerminalService()
    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: service

    try:
        response = api_client.get(
            "/terminals/project-alpha/sessions/history/search?q=error&limit=1&offset=0",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "error"
    assert payload["limit"] == 1
    assert payload["offset"] == 0
    assert payload["total"] == 1
    assert payload["has_more"] is False
    assert payload["items"][0]["session"]["session_id"] == "terminal-session-search"
    assert payload["items"][0]["match_count"] == 2
    assert payload["items"][0]["snippets"] == ["...ERROR one...", "...error two..."]
    assert payload["items"][0]["snippet_matches"] == [
        {
            "text": "...ERROR one...",
            "match_index": 0,
            "match_offset": 120,
        },
        {
            "text": "...error two...",
            "match_index": 1,
            "match_offset": 256,
        },
    ]
    assert service.last_call == ("project-alpha", "error", 1, 0)


def test_terminal_history_search_route_returns_empty_page_when_no_match(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    registry = FakeGroupRegistry(
        [_workspace(jid="web:project-alpha", folder="project-alpha", name="Project Alpha", created_by=owner_id)]
    )

    class FakeTerminalService:
        async def search_history_by_group(
            self,
            group_folder: str,
            *,
            query: str,
            limit: int,
            offset: int,
        ):
            _ = (group_folder, query, limit, offset)
            return SimpleNamespace(
                query=query,
                limit=limit,
                offset=offset,
                total=0,
                has_more=False,
                items=[],
            )

    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: FakeTerminalService()

    try:
        response = api_client.get(
            "/terminals/project-alpha/sessions/history/search?q=not-found",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_terminal_history_search_route_returns_404_when_workspace_has_no_history(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes
    from services.terminal_sessions import TerminalSessionNotFoundError

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    registry = FakeGroupRegistry(
        [_workspace(jid="web:project-alpha", folder="project-alpha", name="Project Alpha", created_by=owner_id)]
    )

    class FakeTerminalService:
        async def search_history_by_group(
            self,
            group_folder: str,
            *,
            query: str,
            limit: int,
            offset: int,
        ):
            _ = (group_folder, query, limit, offset)
            raise TerminalSessionNotFoundError("terminal session not found")

    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: FakeTerminalService()

    try:
        response = api_client.get(
            "/terminals/project-alpha/sessions/history/search?q=error",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "terminal session not found"


def test_owner_can_read_terminal_history_detail(api_client: TestClient) -> None:
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
                session_id="terminal-session-3",
                group_id="project-alpha",
                group_folder="project-alpha",
                owner_user_id=owner_id,
                backend="docker_container",
                container_name="portex-terminal-project-alpha-3",
                status="closed",
                created_at=datetime(2026, 3, 16, 11, 0, tzinfo=timezone.utc),
            )
            self.last_call: tuple[str, str] | None = None

        async def get_history_snapshot_by_group(self, group_folder: str, session_id: str):
            from datetime import datetime, timezone

            self.last_call = (group_folder, session_id)
            return SimpleNamespace(
                record=self.record,
                snapshot_at=datetime(2026, 3, 16, 11, 5, tzinfo=timezone.utc),
                output="pwd\n",
                output_bytes=4,
                history_max_bytes=32768,
                truncated=False,
            )

    service = FakeTerminalService()
    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: service

    try:
        response = api_client.get(
            "/terminals/project-alpha/sessions/history/terminal-session-3",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["session"]["session_id"] == "terminal-session-3"
    assert response.json()["snapshot_at"] == "2026-03-16T11:05:00Z"
    assert response.json()["output"] == "pwd\n"
    assert service.last_call == ("project-alpha", "terminal-session-3")


def test_terminal_history_detail_route_returns_404_when_session_is_missing(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes
    from services.terminal_sessions import TerminalSessionNotFoundError

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    registry = FakeGroupRegistry(
        [_workspace(jid="web:project-alpha", folder="project-alpha", name="Project Alpha", created_by=owner_id)]
    )

    class FakeTerminalService:
        async def get_history_snapshot_by_group(self, group_folder: str, session_id: str):
            _ = (group_folder, session_id)
            raise TerminalSessionNotFoundError("terminal session not found")

    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: FakeTerminalService()

    try:
        response = api_client.get(
            "/terminals/project-alpha/sessions/history/missing-session",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "terminal session not found"


def test_get_current_terminal_session_reads_recovered_active_session(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes
    from services.terminal_sessions import TerminalSessionService

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    persist_root = tmp_path / "terminal-history"

    async def _seed_active_session() -> str:
        first_service = TerminalSessionService(
            bridge_factory=lambda **_: _RouteFakeBridge(),
            reconnect_timeout_seconds=10.0,
            history_persist_root=persist_root,
        )
        session = await first_service.create_session(
            group_id="project-alpha",
            group_folder="project-alpha",
            owner_user_id=owner_id,
            requested_mode="container",
        )
        return session.session_id

    expected_session_id = asyncio.run(_seed_active_session())

    recovered_service = TerminalSessionService(
        bridge_factory=lambda **_: _RouteFakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
        recover_active_sessions=True,
    )
    registry = FakeGroupRegistry(
        [_workspace(jid="web:project-alpha", folder="project-alpha", name="Project Alpha", created_by=owner_id)]
    )
    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: recovered_service

    try:
        response = api_client.get(
            "/terminals/project-alpha/sessions/current",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["session_id"] == expected_session_id
    assert response.json()["status"] == "detached"


def test_create_terminal_session_returns_409_for_recovered_other_owner_active_session(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes
    from services.terminal_sessions import TerminalSessionService

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    other_headers, other_id = _login_headers(api_client, username="other-owner", role="owner")
    _ = owner_headers
    persist_root = tmp_path / "terminal-history"

    async def _seed_active_session() -> None:
        first_service = TerminalSessionService(
            bridge_factory=lambda **_: _RouteFakeBridge(),
            reconnect_timeout_seconds=10.0,
            history_persist_root=persist_root,
        )
        await first_service.create_session(
            group_id="project-alpha",
            group_folder="project-alpha",
            owner_user_id=owner_id,
            requested_mode="container",
        )

    asyncio.run(_seed_active_session())

    recovered_service = TerminalSessionService(
        bridge_factory=lambda **_: _RouteFakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
        recover_active_sessions=True,
    )
    registry = FakeGroupRegistry(
        [_workspace(jid="web:project-alpha", folder="project-alpha", name="Project Alpha", created_by=owner_id)]
    )
    registry.groups[0].member_ids = {other_id}
    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: recovered_service

    try:
        response = api_client.post(
            "/terminals/project-alpha/sessions",
            headers=other_headers,
            json={},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
