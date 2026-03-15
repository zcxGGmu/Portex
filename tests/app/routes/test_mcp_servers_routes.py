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


@pytest.fixture
def mcp_servers_service(tmp_path: Path):
    from services.mcp_servers import McpServersService

    return McpServersService(data_dir=tmp_path / "data")


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


def test_mcp_servers_routes_require_authentication(api_client: TestClient) -> None:
    list_response = api_client.get("/mcp-servers")
    detail_response = api_client.get("/mcp-servers/demo")
    put_response = api_client.put(
        "/mcp-servers/demo",
        json={"transport": "stdio", "command": "python"},
    )
    patch_response = api_client.patch(
        "/mcp-servers/demo/state",
        json={"enabled": False},
    )
    delete_response = api_client.delete("/mcp-servers/demo")

    assert list_response.status_code == 401
    assert detail_response.status_code == 401
    assert put_response.status_code == 401
    assert patch_response.status_code == 401
    assert delete_response.status_code == 401


def test_mcp_servers_routes_support_user_crud_and_state_toggle(
    api_client: TestClient,
    mcp_servers_service,
) -> None:
    from app.main import app
    from app.routes import mcp_servers as mcp_servers_routes

    headers, _user_id = _login_headers(api_client, username="alice")
    app.dependency_overrides[mcp_servers_routes.get_mcp_servers_service] = lambda: mcp_servers_service

    try:
        initial_list = api_client.get("/mcp-servers", headers=headers)
        create_response = api_client.put(
            "/mcp-servers/local-cli",
            headers=headers,
            json={
                "transport": "stdio",
                "command": "uvx",
                "args": ["mcp-server-sqlite"],
                "env": {"MCP_ROOT": "/workspace"},
                "description": "Local stdio MCP",
            },
        )
        detail_response = api_client.get("/mcp-servers/local-cli", headers=headers)
        disable_response = api_client.patch(
            "/mcp-servers/local-cli/state",
            headers=headers,
            json={"enabled": False},
        )
        update_response = api_client.put(
            "/mcp-servers/local-cli",
            headers=headers,
            json={
                "transport": "http",
                "url": "https://example.com/mcp",
                "headers": {"Authorization": "Bearer demo"},
            },
        )
        delete_response = api_client.delete("/mcp-servers/local-cli", headers=headers)
        final_list = api_client.get("/mcp-servers", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert initial_list.status_code == 200
    assert initial_list.json() == {"servers": []}

    assert create_response.status_code == 200
    assert create_response.json()["server_id"] == "local-cli"
    assert create_response.json()["transport"] == "stdio"
    assert create_response.json()["enabled"] is True

    assert detail_response.status_code == 200
    assert detail_response.json()["command"] == "uvx"

    assert disable_response.status_code == 200
    assert disable_response.json()["enabled"] is False

    assert update_response.status_code == 200
    assert update_response.json()["transport"] == "http"
    assert update_response.json()["enabled"] is False

    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "deleted"}

    assert final_list.status_code == 200
    assert final_list.json() == {"servers": []}


def test_mcp_servers_routes_are_isolated_per_user(api_client: TestClient, mcp_servers_service) -> None:
    from app.main import app
    from app.routes import mcp_servers as mcp_servers_routes

    alice_headers, _alice_id = _login_headers(api_client, username="alice")
    bob_headers, _bob_id = _login_headers(api_client, username="bob")

    app.dependency_overrides[mcp_servers_routes.get_mcp_servers_service] = lambda: mcp_servers_service

    try:
        create_response = api_client.put(
            "/mcp-servers/private-server",
            headers=alice_headers,
            json={"transport": "stdio", "command": "python"},
        )
        bob_get = api_client.get("/mcp-servers/private-server", headers=bob_headers)
        bob_patch = api_client.patch(
            "/mcp-servers/private-server/state",
            headers=bob_headers,
            json={"enabled": False},
        )
        bob_delete = api_client.delete("/mcp-servers/private-server", headers=bob_headers)
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 200
    assert bob_get.status_code == 404
    assert bob_patch.status_code == 404
    assert bob_delete.status_code == 404


def test_mcp_servers_routes_map_invalid_payload_to_400(api_client: TestClient, mcp_servers_service) -> None:
    from app.main import app
    from app.routes import mcp_servers as mcp_servers_routes

    headers, _user_id = _login_headers(api_client, username="alice")
    app.dependency_overrides[mcp_servers_routes.get_mcp_servers_service] = lambda: mcp_servers_service

    try:
        bad_id_response = api_client.put(
            "/mcp-servers/bad*id",
            headers=headers,
            json={"transport": "stdio", "command": "python"},
        )
        bad_payload_response = api_client.put(
            "/mcp-servers/invalid-stdio",
            headers=headers,
            json={"transport": "stdio"},
        )
    finally:
        app.dependency_overrides.clear()

    assert bad_id_response.status_code == 400
    assert bad_id_response.json() == {"detail": "invalid server id"}
    assert bad_payload_response.status_code == 400
    assert bad_payload_response.json() == {"detail": "command is required for stdio transport"}
