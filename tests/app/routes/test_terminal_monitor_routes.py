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


def _workspace(*, jid: str, folder: str, name: str):
    class Workspace:
        pass

    workspace = Workspace()
    workspace.jid = jid
    workspace.folder = folder
    workspace.name = name
    workspace.is_home = False
    workspace.added_at = datetime(2026, 3, 16, 9, 0, tzinfo=timezone.utc)
    return workspace


class FakeGroupRegistry:
    def __init__(self, groups: list[object], inaccessible_folders: set[str] | None = None) -> None:
        self.groups = groups
        self.inaccessible_folders = inaccessible_folders or set()

    async def list_registered_groups(self) -> list[object]:
        return list(self.groups)

    async def user_can_access_group(
        self,
        *,
        user_id: str,
        user_role: str | None = None,
        group: object,
    ) -> bool:
        _ = user_id
        _ = user_role
        folder = getattr(group, "folder", "")
        return folder not in self.inaccessible_folders


def _session(
    *,
    session_id: str,
    group_id: str,
    group_folder: str,
    owner_user_id: str,
    status: str,
):
    from services.terminal_sessions import TerminalSessionRecord

    return TerminalSessionRecord(
        session_id=session_id,
        group_id=group_id,
        group_folder=group_folder,
        owner_user_id=owner_user_id,
        backend="docker_container",
        container_name=f"portex-terminal-{group_folder}-1",
        status=status,  # type: ignore[arg-type]
        created_at=datetime(2026, 3, 16, 8, 0, tzinfo=timezone.utc),
        last_attached_at=datetime(2026, 3, 16, 8, 5, tzinfo=timezone.utc),
        reconnect_deadline=datetime(2026, 3, 16, 8, 6, tzinfo=timezone.utc)
        if status == "detached"
        else None,
    )


def test_terminal_overview_route_requires_authentication(api_client: TestClient) -> None:
    response = api_client.get("/terminals")

    assert response.status_code == 401


def test_terminal_overview_route_rejects_member_role(api_client: TestClient) -> None:
    headers, _member_user_id = _login_headers_with_role(api_client, username="member", role="member")

    response = api_client.get("/terminals", headers=headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "permission denied"}


def test_terminal_overview_route_returns_workspace_summaries_sorted_by_session_signal(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import terminals as terminal_routes

    headers, _owner_user_id = _login_headers_with_role(api_client, username="owner", role="owner")

    registry = FakeGroupRegistry(
        groups=[
            _workspace(jid="web:project-empty", folder="project-empty", name="Project Empty"),
            _workspace(jid="web:project-closed", folder="project-closed", name="Project Closed"),
            _workspace(jid="web:project-active", folder="project-active", name="Project Active"),
            _workspace(jid="web:project-hidden", folder="project-hidden", name="Project Hidden"),
        ],
        inaccessible_folders={"project-hidden"},
    )

    class FakeTerminalService:
        def list_sessions(self):
            return [
                _session(
                    session_id="session-active",
                    group_id="project-active",
                    group_folder="project-active",
                    owner_user_id="owner-1",
                    status="attached",
                ),
                _session(
                    session_id="session-closed",
                    group_id="project-closed",
                    group_folder="project-closed",
                    owner_user_id="owner-2",
                    status="closed",
                ),
                _session(
                    session_id="session-hidden",
                    group_id="project-hidden",
                    group_folder="project-hidden",
                    owner_user_id="owner-3",
                    status="detached",
                ),
            ]

    app.dependency_overrides[terminal_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[terminal_routes.get_terminal_session_service] = lambda: FakeTerminalService()

    try:
        response = api_client.get("/terminals", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["group_id"] for item in payload["items"]] == [
        "project-active",
        "project-hidden",
        "project-closed",
        "project-empty",
    ]
    assert payload["items"][0]["chat_accessible"] is True
    assert payload["items"][0]["session"]["status"] == "attached"
    assert payload["items"][1]["chat_accessible"] is False
    assert payload["items"][1]["session"]["status"] == "detached"
    assert payload["items"][2]["session"]["status"] == "closed"
    assert payload["items"][3]["session"] is None

