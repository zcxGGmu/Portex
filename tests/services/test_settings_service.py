from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def service(tmp_path: Path):
    from services.settings import SettingsService

    return SettingsService(data_dir=tmp_path / "data")


@pytest.mark.asyncio
async def test_get_provider_config_returns_defaults_for_new_user(service) -> None:
    config = await service.get_provider_config("user-1")

    assert config.enabled is False
    assert config.base_url == ""
    assert config.default_model == ""
    assert config.has_api_key is False
    assert config.updated_at is None


@pytest.mark.asyncio
async def test_update_provider_config_persists_per_user(service) -> None:
    updated = await service.update_provider_config(
        "user-1",
        enabled=True,
        base_url="https://example.com/v1",
        default_model="gpt-5.1",
        api_key="sk-demo",
    )
    fetched = await service.get_provider_config("user-1")

    assert updated.enabled is True
    assert updated.base_url == "https://example.com/v1"
    assert updated.default_model == "gpt-5.1"
    assert updated.has_api_key is True
    assert updated.updated_at is not None

    assert fetched.enabled is True
    assert fetched.base_url == "https://example.com/v1"
    assert fetched.default_model == "gpt-5.1"
    assert fetched.has_api_key is True


@pytest.mark.asyncio
async def test_update_channels_config_persists_per_user(service) -> None:
    updated = await service.update_channels_config(
        "user-1",
        feishu_enabled=True,
        feishu_app_id="cli_app_id",
        feishu_app_secret="cli_app_secret",
        feishu_encrypt_key="enc-key",
        feishu_verification_token="verify-token",
        telegram_enabled=True,
        telegram_bot_token="bot-token",
    )
    fetched = await service.get_channels_config("user-1")

    assert updated.feishu_enabled is True
    assert updated.feishu_app_id == "cli_app_id"
    assert updated.feishu_has_app_secret is True
    assert updated.feishu_has_encrypt_key is True
    assert updated.feishu_has_verification_token is True
    assert updated.telegram_enabled is True
    assert updated.telegram_has_bot_token is True
    assert updated.updated_at is not None

    assert fetched.feishu_enabled is True
    assert fetched.feishu_app_id == "cli_app_id"
    assert fetched.feishu_has_app_secret is True
    assert fetched.telegram_enabled is True


@pytest.mark.asyncio
async def test_get_and_update_registration_policy_persists_global_values(service) -> None:
    default_config = await service.get_registration_policy()
    updated = await service.update_registration_policy(
        allow_registration=False,
        require_invite_code=True,
    )
    fetched = await service.get_registration_policy()

    assert default_config.allow_registration is True
    assert default_config.require_invite_code is False
    assert default_config.updated_at is None

    assert updated.allow_registration is False
    assert updated.require_invite_code is True
    assert updated.updated_at is not None

    assert fetched.allow_registration is False
    assert fetched.require_invite_code is True


@pytest.mark.asyncio
async def test_update_appearance_config_persists_global_values(service) -> None:
    updated = await service.update_appearance_config(
        app_name="Portex Ops",
        ai_name="Crab Assistant",
        ai_avatar_emoji="🦀",
        ai_avatar_color="#0ea5e9",
    )
    fetched = await service.get_appearance_config()

    assert updated.app_name == "Portex Ops"
    assert updated.ai_name == "Crab Assistant"
    assert updated.ai_avatar_emoji == "🦀"
    assert updated.ai_avatar_color == "#0ea5e9"
    assert updated.updated_at is not None

    assert fetched.app_name == "Portex Ops"


@pytest.mark.asyncio
async def test_update_system_settings_persists_global_values(service) -> None:
    updated = await service.update_system_settings(
        default_execution_mode="container",
        allow_host_execution=True,
    )
    fetched = await service.get_system_settings()

    assert updated.default_execution_mode == "container"
    assert updated.allow_host_execution is True
    assert updated.updated_at is not None

    assert fetched.default_execution_mode == "container"
    assert fetched.allow_host_execution is True


@pytest.mark.asyncio
async def test_user_settings_are_isolated_per_user(service) -> None:
    await service.update_provider_config(
        "user-1",
        enabled=True,
        base_url="https://provider-a",
        default_model="gpt-a",
        api_key="a-key",
    )

    user_two = await service.get_provider_config("user-2")

    assert user_two.enabled is False
    assert user_two.base_url == ""
    assert user_two.default_model == ""
    assert user_two.has_api_key is False


@pytest.mark.asyncio
async def test_user_settings_reject_invalid_user_id(service) -> None:
    with pytest.raises(ValueError, match="invalid user id"):
        await service.get_provider_config("../bad")


@pytest.mark.asyncio
async def test_user_settings_reject_symlink_escape(service, tmp_path: Path) -> None:
    users_root = tmp_path / "data" / "settings" / "users"
    outside = tmp_path / "outside-user"
    outside.mkdir(parents=True, exist_ok=True)
    users_root.mkdir(parents=True, exist_ok=True)
    (users_root / "user-1").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink traversal detected"):
        await service.get_provider_config("user-1")
