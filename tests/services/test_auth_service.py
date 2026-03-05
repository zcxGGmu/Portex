from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.auth import UserAlreadyExistsError, auth_service  # noqa: E402


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
    assert auth_service.get_user_by_id(user.id) == user


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
