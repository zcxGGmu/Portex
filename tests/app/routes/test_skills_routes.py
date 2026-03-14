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
def skills_service(tmp_path: Path):
    from services.skills import SkillsService

    return SkillsService(data_dir=tmp_path / "data")


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


def test_skills_routes_require_authentication(api_client: TestClient) -> None:
    list_response = api_client.get("/skills")
    detail_response = api_client.get("/skills/demo")
    put_response = api_client.put("/skills/demo", json={"content": "# demo"})
    patch_response = api_client.patch("/skills/demo/state", json={"enabled": False})
    delete_response = api_client.delete("/skills/demo")

    assert list_response.status_code == 401
    assert detail_response.status_code == 401
    assert put_response.status_code == 401
    assert patch_response.status_code == 401
    assert delete_response.status_code == 401


def test_skills_routes_support_user_crud_and_state_toggle(
    api_client: TestClient,
    skills_service,
) -> None:
    from app.main import app
    from app.routes import skills as skills_routes

    headers, _user_id = _login_headers(api_client, username="alice")
    app.dependency_overrides[skills_routes.get_skills_service] = lambda: skills_service

    try:
        initial_list = api_client.get("/skills", headers=headers)
        create_response = api_client.put(
            "/skills/writer-guide",
            headers=headers,
            json={"content": "# Writer Guide\nAlways explain tradeoffs."},
        )
        detail_response = api_client.get("/skills/writer-guide", headers=headers)
        disable_response = api_client.patch(
            "/skills/writer-guide/state",
            headers=headers,
            json={"enabled": False},
        )
        enable_response = api_client.patch(
            "/skills/writer-guide/state",
            headers=headers,
            json={"enabled": True},
        )
        delete_response = api_client.delete("/skills/writer-guide", headers=headers)
        final_list = api_client.get("/skills", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert initial_list.status_code == 200
    assert initial_list.json() == {"skills": []}

    assert create_response.status_code == 200
    assert create_response.json()["skill_id"] == "writer-guide"
    assert create_response.json()["enabled"] is True

    assert detail_response.status_code == 200
    assert detail_response.json()["content"] == "# Writer Guide\nAlways explain tradeoffs."

    assert disable_response.status_code == 200
    assert disable_response.json()["enabled"] is False

    assert enable_response.status_code == 200
    assert enable_response.json()["enabled"] is True

    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "deleted"}

    assert final_list.status_code == 200
    assert final_list.json() == {"skills": []}


def test_skills_routes_are_isolated_per_user(api_client: TestClient, skills_service) -> None:
    from app.main import app
    from app.routes import skills as skills_routes

    alice_headers, _alice_id = _login_headers(api_client, username="alice")
    bob_headers, _bob_id = _login_headers(api_client, username="bob")

    app.dependency_overrides[skills_routes.get_skills_service] = lambda: skills_service

    try:
        create_response = api_client.put(
            "/skills/private-skill",
            headers=alice_headers,
            json={"content": "alice-only"},
        )
        bob_get = api_client.get("/skills/private-skill", headers=bob_headers)
        bob_patch = api_client.patch(
            "/skills/private-skill/state",
            headers=bob_headers,
            json={"enabled": False},
        )
        bob_delete = api_client.delete("/skills/private-skill", headers=bob_headers)
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 200
    assert bob_get.status_code == 404
    assert bob_patch.status_code == 404
    assert bob_delete.status_code == 404


def test_skills_routes_map_invalid_skill_id_to_400(api_client: TestClient, skills_service) -> None:
    from app.main import app
    from app.routes import skills as skills_routes

    headers, _user_id = _login_headers(api_client, username="alice")
    app.dependency_overrides[skills_routes.get_skills_service] = lambda: skills_service

    try:
        response = api_client.put(
            "/skills/bad*skill",
            headers=headers,
            json={"content": "invalid id"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid skill id"}
