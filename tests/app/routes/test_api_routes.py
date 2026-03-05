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
    login_payload = login_response.json()
    assert login_payload["token_type"] == "bearer"
    assert login_payload["access_token"]

    me_response = api_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {login_payload['access_token']}"},
    )
    assert me_response.status_code == 200
    me_payload = me_response.json()
    assert me_payload["id"] == user_id
    assert me_payload["username"] == "alice"
    assert me_payload["role"] == "member"
    assert me_payload["status"] == "active"


def test_groups_and_messages_require_authentication(api_client: TestClient) -> None:
    groups_unauthorized = api_client.get("/groups")
    assert groups_unauthorized.status_code == 401

    messages_unauthorized = api_client.post(
        "/messages",
        json={"group_id": "group-demo", "content": "hello"},
    )
    assert messages_unauthorized.status_code == 401

    api_client.post("/auth/register", json={"username": "bob", "password": "secret"})
    login_response = api_client.post(
        "/auth/login",
        json={"username": "bob", "password": "secret"},
    )
    token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    groups_response = api_client.get("/groups", headers=auth_headers)
    assert groups_response.status_code == 200
    groups_payload = groups_response.json()
    assert len(groups_payload["groups"]) >= 1

    messages_response = api_client.post(
        "/messages",
        json={"group_id": "group-demo", "content": "hello"},
        headers=auth_headers,
    )
    assert messages_response.status_code == 200
    message_payload = messages_response.json()
    assert message_payload["message_id"]
    assert message_payload["status"]


def test_register_duplicate_username_returns_409(api_client: TestClient) -> None:
    first_response = api_client.post(
        "/auth/register",
        json={"username": "charlie", "password": "secret"},
    )
    assert first_response.status_code == 200

    second_response = api_client.post(
        "/auth/register",
        json={"username": "charlie", "password": "secret"},
    )
    assert second_response.status_code == 409


def test_login_failure_returns_401(api_client: TestClient) -> None:
    api_client.post("/auth/register", json={"username": "dora", "password": "secret"})

    failed_login = api_client.post(
        "/auth/login",
        json={"username": "dora", "password": "wrong-password"},
    )
    assert failed_login.status_code == 401
