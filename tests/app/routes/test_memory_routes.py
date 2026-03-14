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


def _login_headers(
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


def test_memory_routes_require_authentication(api_client: TestClient) -> None:
    global_get_response = api_client.get("/memory/global")
    global_put_response = api_client.put("/memory/global", json={"content": "hello"})
    list_response = api_client.get("/memory/workspaces/project-alpha/files")
    read_response = api_client.get(
        "/memory/workspaces/project-alpha/file",
        params={"path": "2026-03-15.md"},
    )
    write_response = api_client.put(
        "/memory/workspaces/project-alpha/file",
        json={"path": "2026-03-15.md", "content": "hello"},
    )
    search_response = api_client.get(
        "/memory/workspaces/project-alpha/search",
        params={"q": "hello"},
    )

    assert global_get_response.status_code == 401
    assert global_put_response.status_code == 401
    assert list_response.status_code == 401
    assert read_response.status_code == 401
    assert write_response.status_code == 401
    assert search_response.status_code == 401


def test_global_memory_route_reads_and_updates_current_user_memory(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    from app.main import app
    from app.routes import memory as memory_routes
    from services.memory import MemoryService

    headers, _user_id = _login_headers(api_client, username="alice")
    memory_service = MemoryService(data_dir=tmp_path / "data")

    app.dependency_overrides[memory_routes.get_memory_service] = lambda: memory_service

    try:
        initial_response = api_client.get("/memory/global", headers=headers)
        update_response = api_client.put(
            "/memory/global",
            headers=headers,
            json={"content": "Always reply in concise bullet points."},
        )
        current_response = api_client.get("/memory/global", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert initial_response.status_code == 200
    assert initial_response.json() == {"content": "", "updated_at": None, "size": 0}
    assert update_response.status_code == 200
    assert update_response.json()["content"] == "Always reply in concise bullet points."
    assert update_response.json()["size"] == len(
        "Always reply in concise bullet points.".encode("utf-8")
    )
    assert update_response.json()["updated_at"] is not None
    assert current_response.status_code == 200
    assert current_response.json()["content"] == "Always reply in concise bullet points."


def test_workspace_memory_routes_allow_member_read_write_and_search(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    from app.main import app
    from app.routes import memory as memory_routes
    from services.memory import MemoryService

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
    memory_service = MemoryService(data_dir=tmp_path / "data")
    seed_path = tmp_path / "data" / "memory" / "project-alpha" / "2026-03-15.md"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text("existing note", encoding="utf-8")

    app.dependency_overrides[memory_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[memory_routes.get_memory_service] = lambda: memory_service

    try:
        list_response = api_client.get(
            "/memory/workspaces/project-alpha/files",
            headers=member_headers,
        )
        missing_read_response = api_client.get(
            "/memory/workspaces/project-alpha/file",
            headers=member_headers,
            params={"path": "notes/today.md"},
        )
        write_response = api_client.put(
            "/memory/workspaces/project-alpha/file",
            headers=member_headers,
            json={"path": "notes/today.md", "content": "project launch checklist"},
        )
        read_response = api_client.get(
            "/memory/workspaces/project-alpha/file",
            headers=member_headers,
            params={"path": "notes/today.md"},
        )
        search_response = api_client.get(
            "/memory/workspaces/project-alpha/search",
            headers=member_headers,
            params={"q": "launch"},
        )
    finally:
        app.dependency_overrides.clear()

    assert list_response.status_code == 200
    assert list_response.json()["files"][0]["path"] == "2026-03-15.md"
    assert missing_read_response.status_code == 200
    assert missing_read_response.json() == {
        "path": "notes/today.md",
        "content": "",
        "updated_at": None,
        "size": 0,
    }
    assert write_response.status_code == 200
    assert write_response.json()["content"] == "project launch checklist"
    assert write_response.json()["updated_at"] is not None
    assert read_response.status_code == 200
    assert read_response.json()["content"] == "project launch checklist"
    assert search_response.status_code == 200
    assert search_response.json()["hits"] == [{"path": "notes/today.md"}]


def test_workspace_memory_routes_return_404_for_inaccessible_workspace(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    from app.main import app
    from app.routes import memory as memory_routes
    from services.memory import MemoryService

    owner_headers, owner_id = _login_headers(api_client, username="owner", role="owner")
    _ = owner_headers
    outsider_headers, _outsider_id = _login_headers(api_client, username="outsider", role="member")
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
    memory_service = MemoryService(data_dir=tmp_path / "data")

    app.dependency_overrides[memory_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[memory_routes.get_memory_service] = lambda: memory_service

    try:
        list_response = api_client.get(
            "/memory/workspaces/project-alpha/files",
            headers=outsider_headers,
        )
        read_response = api_client.get(
            "/memory/workspaces/project-alpha/file",
            headers=outsider_headers,
            params={"path": "2026-03-15.md"},
        )
        write_response = api_client.put(
            "/memory/workspaces/project-alpha/file",
            headers=outsider_headers,
            json={"path": "notes/today.md", "content": "x"},
        )
        search_response = api_client.get(
            "/memory/workspaces/project-alpha/search",
            headers=outsider_headers,
            params={"q": "hello"},
        )
    finally:
        app.dependency_overrides.clear()

    assert list_response.status_code == 404
    assert read_response.status_code == 404
    assert write_response.status_code == 404
    assert search_response.status_code == 404


def test_workspace_memory_routes_map_safety_guards_to_400(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    from app.main import app
    from app.routes import memory as memory_routes
    from services.memory import MemoryService

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
    memory_service = MemoryService(data_dir=tmp_path / "data")
    outside_root = tmp_path / "data" / "outside"
    outside_root.mkdir(parents=True, exist_ok=True)
    (outside_root / "secret.md").write_text("secret", encoding="utf-8")
    workspace_root = tmp_path / "data" / "memory" / "project-alpha"
    workspace_root.mkdir(parents=True, exist_ok=True)
    (workspace_root / "link.md").symlink_to(outside_root / "secret.md")

    app.dependency_overrides[memory_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[memory_routes.get_memory_service] = lambda: memory_service

    try:
        traversal_response = api_client.get(
            "/memory/workspaces/project-alpha/file",
            headers=owner_headers,
            params={"path": "../escape.md"},
        )
        symlink_response = api_client.get(
            "/memory/workspaces/project-alpha/file",
            headers=owner_headers,
            params={"path": "link.md"},
        )
        extension_response = api_client.put(
            "/memory/workspaces/project-alpha/file",
            headers=owner_headers,
            json={"path": "notes.txt", "content": "hello"},
        )
    finally:
        app.dependency_overrides.clear()

    assert traversal_response.status_code == 400
    assert traversal_response.json() == {"detail": "path traversal detected"}
    assert symlink_response.status_code == 400
    assert symlink_response.json() == {"detail": "symlink traversal detected"}
    assert extension_response.status_code == 400
    assert extension_response.json() == {"detail": "only markdown memory files are supported"}
