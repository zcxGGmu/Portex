"""Auth dependency middleware."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from infra.db.database import get_db
from services.auth import AuthUser, auth_service

security = HTTPBearer(auto_error=False)


def _unauthorized_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or missing token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AuthUser:
    if credentials is None:
        raise _unauthorized_error()

    user_id = auth_service.decode_access_token(credentials.credentials)
    if user_id is None:
        raise _unauthorized_error()

    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise _unauthorized_error()

    _ = db  # Reserved for future DB-backed user lookup.
    return user


__all__ = ["get_current_user", "security"]
