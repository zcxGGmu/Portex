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


def _workspace(*, jid: str, folder: str, name: str, created_by: str | None, is_home: bool = False):
    class Workspace:
        pass

    workspace = Workspace()
    workspace.jid = jid
    workspace.folder = folder
    workspace.name = name
    workspace.created_by = created_by
    workspace.is_home = is_home
    return workspace


class FakeGroupRegistry:
    def __init__(self, groups) -> None:
        self.groups = list(groups)

    async def get_web_workspace_by_folder(self, folder: str):
        for group in self.groups:
            if group.folder == folder and group.jid.startswith("web:"):
                return group
        return None

    async def user_can_access_group(self, *, user_id: str, user_role: str | None = None, group):
        if group.is_home:
            if group.jid == "web:main" and group.folder == "main" and user_role == "owner":
                return True
            return group.created_by == user_id
        return group.created_by == user_id or user_id in getattr(group, "member_ids", set())


def test_file_routes_require_authentication(api_client: TestClient) -> None:
    list_response = api_client.get("/groups/project-alpha/files")
    upload_response = api_client.post("/groups/project-alpha/files")
    content_response = api_client.get("/groups/project-alpha/files/content/readme.txt")
    delete_response = api_client.delete("/groups/project-alpha/files/readme.txt")

    assert list_response.status_code == 401
    assert upload_response.status_code == 401
    assert content_response.status_code == 401
    assert delete_response.status_code == 401


def test_list_files_route_returns_workspace_entries(api_client: TestClient, tmp_path: Path) -> None:
    from app.main import app
    from app.routes import files as file_routes
    from services.workspace_files import WorkspaceFileService

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    member_headers, member_id = _login_headers(api_client, username="member")

    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_id,
            )
        ]
    )
    registry.groups[0].member_ids = {member_id}
    service = WorkspaceFileService(data_root=tmp_path / "data")
    service.save_upload("project-alpha", "", "readme.txt", b"hello")

    app.dependency_overrides[file_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[file_routes.get_workspace_file_service] = lambda: service

    try:
        response = api_client.get("/groups/project-alpha/files", headers=member_headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_path"] == ""
    assert payload["entries"][0]["name"] == "readme.txt"


def test_member_cannot_upload_file(api_client: TestClient, tmp_path: Path) -> None:
    from app.main import app
    from app.routes import files as file_routes
    from services.workspace_files import WorkspaceFileService

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    _ = owner_headers
    member_headers, member_id = _login_headers(api_client, username="member")

    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_id,
            )
        ]
    )
    registry.groups[0].member_ids = {member_id}
    service = WorkspaceFileService(data_root=tmp_path / "data")

    app.dependency_overrides[file_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[file_routes.get_workspace_file_service] = lambda: service

    try:
        response = api_client.post(
            "/groups/project-alpha/files",
            headers=member_headers,
            files={"files": ("notes.txt", b"hello", "text/plain")},
            data={"path": ""},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_owner_can_upload_and_read_text_file(api_client: TestClient, tmp_path: Path) -> None:
    from app.main import app
    from app.routes import files as file_routes
    from services.workspace_files import WorkspaceFileService

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_id,
            )
        ]
    )
    service = WorkspaceFileService(data_root=tmp_path / "data")

    app.dependency_overrides[file_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[file_routes.get_workspace_file_service] = lambda: service

    try:
        upload_response = api_client.post(
            "/groups/project-alpha/files",
            headers=owner_headers,
            files={"files": ("notes.txt", b"hello", "text/plain")},
            data={"path": ""},
        )
        content_response = api_client.get(
            "/groups/project-alpha/files/content/notes.txt",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert upload_response.status_code == 200
    assert upload_response.json()["files"] == ["notes.txt"]
    assert content_response.status_code == 200
    assert content_response.json()["content"] == "hello"


def test_owner_can_delete_file(api_client: TestClient, tmp_path: Path) -> None:
    from app.main import app
    from app.routes import files as file_routes
    from services.workspace_files import WorkspaceFileService

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_id,
            )
        ]
    )
    service = WorkspaceFileService(data_root=tmp_path / "data")
    service.save_upload("project-alpha", "", "notes.txt", b"hello")

    app.dependency_overrides[file_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[file_routes.get_workspace_file_service] = lambda: service

    try:
        response = api_client.delete(
            "/groups/project-alpha/files/notes.txt",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}
