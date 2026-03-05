from __future__ import annotations

from pathlib import Path
import sys

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.middleware.auth import get_current_user  # noqa: E402
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
