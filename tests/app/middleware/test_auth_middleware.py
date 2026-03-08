from __future__ import annotations

from pathlib import Path
import sys

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.middleware.auth import (  # noqa: E402
    get_current_user,
    require_permission,
    require_role,
)
from services.auth import auth_service  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_auth_service() -> None:
    auth_service.reset()
    yield
    auth_service.reset()


@pytest.mark.asyncio
async def test_get_current_user_returns_user_for_valid_token() -> None:
    user = auth_service.register_user("alice", "password123")
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=auth_service.create_access_token(user.id),
    )

    current_user = await get_current_user(credentials=credentials, db=None)
    assert current_user == user


@pytest.mark.asyncio
async def test_get_current_user_raises_401_without_token() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=None, db=None)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_invalid_token() -> None:
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid-token",
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials, db=None)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_require_role_returns_user_for_allowed_role() -> None:
    admin_user = auth_service.register_user("admin", "password123", role="admin")

    dependency = require_role("admin")
    resolved_user = await dependency(current_user=admin_user)

    assert resolved_user == admin_user


@pytest.mark.asyncio
async def test_require_role_raises_403_for_disallowed_role() -> None:
    member_user = auth_service.register_user("member", "password123")

    dependency = require_role("admin")

    with pytest.raises(HTTPException) as exc_info:
        await dependency(current_user=member_user)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_permission_returns_user_for_allowed_permission() -> None:
    admin_user = auth_service.register_user("admin", "password123", role="admin")

    dependency = require_permission("users", "read")
    resolved_user = await dependency(current_user=admin_user)

    assert resolved_user == admin_user


@pytest.mark.asyncio
async def test_require_permission_allows_owner_superset_access() -> None:
    owner_user = auth_service.register_user("owner", "password123", role="owner")

    dependency = require_permission("users", "write")
    resolved_user = await dependency(current_user=owner_user)

    assert resolved_user == owner_user


@pytest.mark.asyncio
async def test_require_permission_raises_403_for_forbidden_permission() -> None:
    member_user = auth_service.register_user("member", "password123")

    dependency = require_permission("users", "read")

    with pytest.raises(HTTPException) as exc_info:
        await dependency(current_user=member_user)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_permission_denies_unknown_role_by_default() -> None:
    guest_user = auth_service.register_user("guest", "password123", role="guest")

    dependency = require_permission("users", "read")

    with pytest.raises(HTTPException) as exc_info:
        await dependency(current_user=guest_user)

    assert exc_info.value.status_code == 403
