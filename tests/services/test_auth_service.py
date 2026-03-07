from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.auth import UserAlreadyExistsError, UserNotFoundError, auth_service  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_auth_service() -> None:
    auth_service.reset()
    yield
    auth_service.reset()


def test_register_user_success_and_get_user_by_id() -> None:
    user = auth_service.register_user("alice", "password123")

    assert user.id
    assert user.username == "alice"
    assert user.role == "member"
    assert user.status == "active"
    assert user.avatar_emoji is None
    assert user.avatar_color is None
    assert user.ai_name is None
    assert user.ai_avatar_emoji is None
    assert user.must_change_password is False
    assert user.last_login_at is None
    assert user.disable_reason is None
    assert user.notes is None
    assert auth_service.get_user_by_id(user.id) == user


def test_register_user_accepts_explicit_role() -> None:
    admin_user = auth_service.register_user("admin", "password123", role="admin")

    assert admin_user.role == "admin"


def test_list_users_returns_deterministic_username_order() -> None:
    auth_service.register_user("zoe", "password123")
    auth_service.register_user("alice", "password123")

    assert [user.username for user in auth_service.list_users()] == ["alice", "zoe"]


def test_update_user_updates_selected_fields() -> None:
    user = auth_service.register_user("alice", "password123")

    updated_user = auth_service.update_user(
        user.id,
        role="admin",
        status="disabled",
        avatar_emoji="🤖",
        avatar_color="#00AAFF",
        ai_name="Portex",
        ai_avatar_emoji="🧠",
        must_change_password=True,
        disable_reason="manual-review",
        notes="promoted by admin",
    )

    assert updated_user.role == "admin"
    assert updated_user.status == "disabled"
    assert updated_user.avatar_emoji == "🤖"
    assert updated_user.avatar_color == "#00AAFF"
    assert updated_user.ai_name == "Portex"
    assert updated_user.ai_avatar_emoji == "🧠"
    assert updated_user.must_change_password is True
    assert updated_user.disable_reason == "manual-review"
    assert updated_user.notes == "promoted by admin"
    assert auth_service.get_user_by_id(user.id) == updated_user


def test_update_user_raises_for_missing_user() -> None:
    with pytest.raises(UserNotFoundError):
        auth_service.update_user("missing-user-id", role="admin")


def test_register_user_duplicate_raises() -> None:
    auth_service.register_user("alice", "password123")

    with pytest.raises(UserAlreadyExistsError):
        auth_service.register_user("alice", "new-password")


def test_authenticate_user_success_and_failure_paths() -> None:
    registered = auth_service.register_user("alice", "password123")

    assert auth_service.authenticate_user("alice", "password123") == registered
    assert auth_service.authenticate_user("alice", "bad-password") is None
    assert auth_service.authenticate_user("bob", "password123") is None


def test_create_and_decode_access_token() -> None:
    user = auth_service.register_user("alice", "password123")
    token = auth_service.create_access_token(user.id)

    assert isinstance(token, str)
    assert auth_service.decode_access_token(token) == user.id
    assert auth_service.decode_access_token("not-a-jwt-token") is None


def test_reset_clears_all_state() -> None:
    user = auth_service.register_user("alice", "password123")
    token = auth_service.create_access_token(user.id)

    assert auth_service.get_user_by_id(user.id) == user
    assert auth_service.decode_access_token(token) == user.id

    auth_service.reset()

    assert auth_service.get_user_by_id(user.id) is None
    assert auth_service.authenticate_user("alice", "password123") is None
