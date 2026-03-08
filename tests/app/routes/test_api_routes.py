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


def _login_headers(api_client: TestClient, username: str, password: str) -> dict[str, str]:
    login_response = api_client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_check_endpoint(api_client: TestClient) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_cors_preflight_allows_localhost_5173(api_client: TestClient) -> None:
    response = api_client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


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
    assert me_payload["avatar_emoji"] is None
    assert me_payload["avatar_color"] is None
    assert me_payload["ai_name"] is None
    assert me_payload["ai_avatar_emoji"] is None
    assert me_payload["must_change_password"] is False
    assert me_payload["last_login_at"] is None
    assert me_payload["disable_reason"] is None
    assert me_payload["notes"] is None


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


def test_admin_user_routes_require_authentication(api_client: TestClient) -> None:
    list_response = api_client.get("/admin/users")
    patch_response = api_client.patch("/admin/users/missing-user", json={"role": "admin"})

    assert list_response.status_code == 401
    assert patch_response.status_code == 401


def test_non_admin_cannot_manage_users(api_client: TestClient) -> None:
    api_client.post("/auth/register", json={"username": "member", "password": "secret"})
    member_headers = _login_headers(api_client, "member", "secret")

    list_response = api_client.get("/admin/users", headers=member_headers)
    patch_response = api_client.patch(
        "/admin/users/member-id",
        json={"role": "admin"},
        headers=member_headers,
    )

    assert list_response.status_code == 403
    assert patch_response.status_code == 403


def test_admin_can_list_users(api_client: TestClient) -> None:
    from services.auth import auth_service

    admin_user = auth_service.register_user("admin", "secret", role="admin")
    member_user = auth_service.register_user("member", "secret")
    admin_headers = _login_headers(api_client, "admin", "secret")

    response = api_client.get("/admin/users", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert [user["username"] for user in payload["users"]] == ["admin", "member"]
    assert payload["users"][0]["id"] == admin_user.id
    assert payload["users"][1]["id"] == member_user.id


def test_owner_can_list_users_via_permission_template(api_client: TestClient) -> None:
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    member_user = auth_service.register_user("member", "secret")
    owner_headers = _login_headers(api_client, "owner", "secret")

    response = api_client.get("/admin/users", headers=owner_headers)

    assert response.status_code == 200
    payload = response.json()
    assert [user["username"] for user in payload["users"]] == ["member", "owner"]
    assert payload["users"][0]["id"] == member_user.id
    assert payload["users"][1]["id"] == owner_user.id


def test_admin_can_update_user(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    target_user = auth_service.register_user("member", "secret")
    admin_headers = _login_headers(api_client, "admin", "secret")

    response = api_client.patch(
        f"/admin/users/{target_user.id}",
        json={
            "role": "admin",
            "status": "disabled",
            "avatar_emoji": "🤖",
            "avatar_color": "#00AAFF",
            "ai_name": "Portex",
            "ai_avatar_emoji": "🧠",
            "must_change_password": True,
            "disable_reason": "manual-review",
            "notes": "promoted by admin",
        },
        headers=admin_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == target_user.id
    assert payload["role"] == "admin"
    assert payload["status"] == "disabled"
    assert payload["avatar_emoji"] == "🤖"
    assert payload["avatar_color"] == "#00AAFF"
    assert payload["ai_name"] == "Portex"
    assert payload["ai_avatar_emoji"] == "🧠"
    assert payload["must_change_password"] is True
    assert payload["disable_reason"] == "manual-review"
    assert payload["notes"] == "promoted by admin"


def test_admin_update_missing_user_returns_404(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")

    response = api_client.patch(
        "/admin/users/missing-user-id",
        json={"status": "disabled"},
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_admin_invite_routes_require_authentication(api_client: TestClient) -> None:
    list_response = api_client.get("/admin/invites")
    create_response = api_client.post("/admin/invites", json={})

    assert list_response.status_code == 401
    assert create_response.status_code == 401


def test_non_admin_cannot_manage_invites(api_client: TestClient) -> None:
    api_client.post("/auth/register", json={"username": "member", "password": "secret"})
    member_headers = _login_headers(api_client, "member", "secret")

    list_response = api_client.get("/admin/invites", headers=member_headers)
    create_response = api_client.post(
        "/admin/invites",
        json={"role": "admin"},
        headers=member_headers,
    )

    assert list_response.status_code == 403
    assert create_response.status_code == 403


def test_unknown_role_cannot_list_invites(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("guest", "secret", role="guest")
    guest_headers = _login_headers(api_client, "guest", "secret")

    response = api_client.get("/admin/invites", headers=guest_headers)

    assert response.status_code == 403


def test_admin_can_create_and_list_invites(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")

    create_response = api_client.post(
        "/admin/invites",
        json={"role": "admin", "permission_template": "owner-lite"},
        headers=admin_headers,
    )

    assert create_response.status_code == 200
    created_payload = create_response.json()
    assert created_payload["code"]
    assert created_payload["role"] == "admin"
    assert created_payload["permission_template"] == "owner-lite"
    assert created_payload["used_by"] is None
    assert created_payload["used_at"] is None

    list_response = api_client.get("/admin/invites", headers=admin_headers)

    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert len(list_payload["invites"]) == 1
    assert list_payload["invites"][0]["code"] == created_payload["code"]


def test_register_accepts_valid_invite_and_applies_invite_role(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")
    invite_response = api_client.post(
        "/admin/invites",
        json={"role": "admin"},
        headers=admin_headers,
    )
    invite_code = invite_response.json()["code"]

    register_response = api_client.post(
        "/auth/register",
        json={
            "username": "invited-user",
            "password": "secret",
            "invite_code": invite_code,
        },
    )

    assert register_response.status_code == 200

    login_headers = _login_headers(api_client, "invited-user", "secret")
    me_response = api_client.get("/users/me", headers=login_headers)

    assert me_response.status_code == 200
    assert me_response.json()["role"] == "admin"

    list_response = api_client.get("/admin/invites", headers=admin_headers)
    invite_payload = list_response.json()["invites"][0]
    assert invite_payload["used_by"] == register_response.json()["user_id"]
    assert invite_payload["used_at"] is not None


def test_register_rejects_invalid_invite_code(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")
    api_client.post(
        "/admin/invites",
        json={"role": "member"},
        headers=admin_headers,
    )

    register_response = api_client.post(
        "/auth/register",
        json={
            "username": "bad-invite-user",
            "password": "secret",
            "invite_code": "missing-code",
        },
    )

    assert register_response.status_code == 400


def test_register_rejects_expired_and_used_invite_codes(api_client: TestClient) -> None:
    from datetime import datetime, timedelta, timezone

    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")
    expired_response = api_client.post(
        "/admin/invites",
        json={
            "code": "expired-code",
            "role": "member",
            "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        },
        headers=admin_headers,
    )
    used_response = api_client.post(
        "/admin/invites",
        json={"code": "used-code", "role": "member"},
        headers=admin_headers,
    )
    assert expired_response.status_code == 200
    assert used_response.status_code == 200

    first_register = api_client.post(
        "/auth/register",
        json={
            "username": "first-used-user",
            "password": "secret",
            "invite_code": "used-code",
        },
    )
    assert first_register.status_code == 200

    expired_register = api_client.post(
        "/auth/register",
        json={
            "username": "expired-user",
            "password": "secret",
            "invite_code": "expired-code",
        },
    )
    used_register = api_client.post(
        "/auth/register",
        json={
            "username": "second-used-user",
            "password": "secret",
            "invite_code": "used-code",
        },
    )

    assert expired_register.status_code == 400
    assert used_register.status_code == 400


def test_duplicate_username_does_not_consume_invite_code(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")
    create_response = api_client.post(
        "/admin/invites",
        json={"code": "reusable-check", "role": "member"},
        headers=admin_headers,
    )
    assert create_response.status_code == 200

    register_response = api_client.post(
        "/auth/register",
        json={"username": "plain-user", "password": "secret"},
    )
    assert register_response.status_code == 200

    duplicate_response = api_client.post(
        "/auth/register",
        json={
            "username": "plain-user",
            "password": "new-secret",
            "invite_code": "reusable-check",
        },
    )
    assert duplicate_response.status_code == 409

    list_response = api_client.get("/admin/invites", headers=admin_headers)
    invite_payload = list_response.json()["invites"][0]
    assert invite_payload["used_by"] is None
    assert invite_payload["used_at"] is None
