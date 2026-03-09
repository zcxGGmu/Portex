from __future__ import annotations

from pathlib import Path
import sys
from typing import Iterator

from fastapi.testclient import TestClient
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
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


def test_health_check_endpoint(api_client: TestClient) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_register_login_and_get_current_user_flow(api_client: TestClient) -> None:
    register_response = api_client.post(
        "/auth/register",
        json={"username": "alice", "password": "secret"},
    )

    assert register_response.status_code == 200
    user_id = register_response.json()["user_id"]

    login_response = api_client.post(
        "/auth/login",
        json={"username": "alice", "password": "secret"},
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = api_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json() == {
        "id": user_id,
        "username": "alice",
        "role": "member",
        "status": "active",
        "avatar_emoji": None,
        "avatar_color": None,
        "ai_name": None,
        "ai_avatar_emoji": None,
        "must_change_password": False,
        "last_login_at": None,
        "disable_reason": None,
        "notes": None,
    }
