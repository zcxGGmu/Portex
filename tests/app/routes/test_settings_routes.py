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
def settings_service(tmp_path: Path):
    from services.settings import SettingsService

    return SettingsService(data_dir=tmp_path / "data")


class _NoopGroupRegistry:
    async def ensure_home_workspace(
        self,
        *,
        user_id: str,
        role: str,
        username: str,
    ):
        _ = (user_id, role, username)
        return None


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


def test_settings_routes_require_authentication(api_client: TestClient) -> None:
    responses = [
        api_client.get("/settings/provider"),
        api_client.put("/settings/provider", json={"enabled": False, "base_url": "", "default_model": ""}),
        api_client.get("/settings/channels"),
        api_client.put(
            "/settings/channels",
            json={
                "feishu_enabled": False,
                "feishu_app_id": "",
                "feishu_app_secret": "",
                "feishu_encrypt_key": "",
                "feishu_verification_token": "",
                "telegram_enabled": False,
                "telegram_bot_token": "",
            },
        ),
        api_client.get("/settings/registration"),
        api_client.put(
            "/settings/registration",
            json={"allow_registration": True, "require_invite_code": False},
        ),
        api_client.get("/settings/appearance"),
        api_client.put(
            "/settings/appearance",
            json={
                "app_name": "Portex",
                "ai_name": "Portex",
                "ai_avatar_emoji": "🤖",
                "ai_avatar_color": "#0ea5e9",
            },
        ),
        api_client.get("/settings/system"),
        api_client.put(
            "/settings/system",
            json={"default_execution_mode": "openai", "allow_host_execution": False},
        ),
    ]

    for response in responses:
        assert response.status_code == 401


def test_member_can_manage_provider_and_channels(
    api_client: TestClient,
    settings_service,
) -> None:
    from app.main import app
    from app.routes import settings as settings_routes

    headers, _user_id = _login_headers(api_client, username="alice", role="member")
    app.dependency_overrides[settings_routes.get_settings_service] = lambda: settings_service

    try:
        provider_initial = api_client.get("/settings/provider", headers=headers)
        provider_update = api_client.put(
            "/settings/provider",
            headers=headers,
            json={
                "enabled": True,
                "base_url": "https://provider.example/v1",
                "default_model": "gpt-5.1",
                "api_key": "sk-user-1",
            },
        )
        channels_update = api_client.put(
            "/settings/channels",
            headers=headers,
            json={
                "feishu_enabled": True,
                "feishu_app_id": "cli_app_id",
                "feishu_app_secret": "cli_app_secret",
                "feishu_encrypt_key": "encrypt-key",
                "feishu_verification_token": "verify-token",
                "telegram_enabled": True,
                "telegram_bot_token": "telegram-token",
            },
        )
        channels_get = api_client.get("/settings/channels", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert provider_initial.status_code == 200
    assert provider_initial.json()["enabled"] is False
    assert provider_initial.json()["has_api_key"] is False

    assert provider_update.status_code == 200
    assert provider_update.json()["enabled"] is True
    assert provider_update.json()["base_url"] == "https://provider.example/v1"
    assert provider_update.json()["default_model"] == "gpt-5.1"
    assert provider_update.json()["has_api_key"] is True

    assert channels_update.status_code == 200
    assert channels_update.json()["feishu_enabled"] is True
    assert channels_update.json()["feishu_app_id"] == "cli_app_id"
    assert channels_update.json()["feishu_has_app_secret"] is True
    assert channels_update.json()["telegram_enabled"] is True
    assert channels_update.json()["telegram_has_bot_token"] is True

    assert channels_get.status_code == 200
    assert channels_get.json()["feishu_enabled"] is True


def test_global_settings_enforce_role_permissions(
    api_client: TestClient,
    settings_service,
) -> None:
    from app.main import app
    from app.routes import settings as settings_routes

    member_headers, _member_id = _login_headers(api_client, username="member", role="member")
    admin_headers, _admin_id = _login_headers(api_client, username="admin", role="admin")
    owner_headers, _owner_id = _login_headers(api_client, username="owner", role="owner")

    app.dependency_overrides[settings_routes.get_settings_service] = lambda: settings_service

    try:
        member_get = api_client.get("/settings/registration", headers=member_headers)
        admin_get = api_client.get("/settings/registration", headers=admin_headers)
        admin_put = api_client.put(
            "/settings/registration",
            headers=admin_headers,
            json={"allow_registration": False, "require_invite_code": True},
        )
        owner_put = api_client.put(
            "/settings/registration",
            headers=owner_headers,
            json={"allow_registration": False, "require_invite_code": True},
        )
        owner_get_appearance = api_client.put(
            "/settings/appearance",
            headers=owner_headers,
            json={
                "app_name": "Portex Ops",
                "ai_name": "Ops Assistant",
                "ai_avatar_emoji": "🦀",
                "ai_avatar_color": "#2563eb",
            },
        )
        owner_get_system = api_client.put(
            "/settings/system",
            headers=owner_headers,
            json={"default_execution_mode": "container", "allow_host_execution": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert member_get.status_code == 403
    assert member_get.json() == {"detail": "permission denied"}

    assert admin_get.status_code == 200
    assert admin_put.status_code == 403
    assert admin_put.json() == {"detail": "permission denied"}

    assert owner_put.status_code == 200
    assert owner_put.json()["allow_registration"] is False
    assert owner_put.json()["require_invite_code"] is True

    assert owner_get_appearance.status_code == 200
    assert owner_get_appearance.json()["app_name"] == "Portex Ops"

    assert owner_get_system.status_code == 200
    assert owner_get_system.json()["default_execution_mode"] == "container"


def test_registration_policy_is_enforced_by_register_route(
    api_client: TestClient,
    settings_service,
) -> None:
    from app.main import app
    from app.routes import auth as auth_routes
    from app.routes import settings as settings_routes

    owner_headers, _owner_id = _login_headers(api_client, username="owner", role="owner")

    app.dependency_overrides[settings_routes.get_settings_service] = lambda: settings_service
    app.dependency_overrides[auth_routes.get_settings_service] = lambda: settings_service
    app.dependency_overrides[auth_routes.get_group_registry_service] = lambda: _NoopGroupRegistry()

    try:
        set_invite_required = api_client.put(
            "/settings/registration",
            headers=owner_headers,
            json={"allow_registration": True, "require_invite_code": True},
        )
        missing_invite = api_client.post(
            "/auth/register",
            json={"username": "no-invite", "password": "secret"},
        )

        invite_response = api_client.post(
            "/admin/invites",
            headers=owner_headers,
            json={"role": "member", "code": "invite-1"},
        )
        with_invite = api_client.post(
            "/auth/register",
            json={"username": "with-invite", "password": "secret", "invite_code": "invite-1"},
        )

        set_registration_disabled = api_client.put(
            "/settings/registration",
            headers=owner_headers,
            json={"allow_registration": False, "require_invite_code": False},
        )
        disabled_register = api_client.post(
            "/auth/register",
            json={"username": "blocked", "password": "secret"},
        )
    finally:
        app.dependency_overrides.clear()

    assert set_invite_required.status_code == 200
    assert missing_invite.status_code == 400
    assert missing_invite.json() == {"detail": "invite code is required by registration policy"}

    assert invite_response.status_code == 200
    assert with_invite.status_code == 200

    assert set_registration_disabled.status_code == 200
    assert disabled_register.status_code == 403
    assert disabled_register.json() == {"detail": "registration is disabled"}
