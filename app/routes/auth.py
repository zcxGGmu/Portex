"""Authentication routes and auth dependency."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from domain.schemas import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
)
from services.auth import UserAlreadyExistsError, auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


def _user_attr(user: Any, field: str) -> Any:
    if isinstance(user, dict):
        return user.get(field)
    return getattr(user, field, None)


def _unauthorized_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or missing token",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest) -> RegisterResponse:
    try:
        user = auth_service.register_user(
            username=request.username,
            password=request.password,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="username already exists",
        ) from exc

    return RegisterResponse(user_id=_user_attr(user, "id"))


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    user = auth_service.authenticate_user(
        username=request.username,
        password=request.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid username or password",
        )

    access_token = auth_service.create_access_token(_user_attr(user, "id"))
    return TokenResponse(access_token=access_token)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UserResponse:
    if credentials is None:
        raise _unauthorized_error()

    user_id = auth_service.decode_access_token(credentials.credentials)
    if user_id is None:
        raise _unauthorized_error()

    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise _unauthorized_error()

    return UserResponse(
        id=_user_attr(user, "id"),
        username=_user_attr(user, "username"),
        role=_user_attr(user, "role"),
        status=_user_attr(user, "status"),
    )


__all__ = ["get_current_user", "router"]
