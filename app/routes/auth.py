"""Authentication routes."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from domain.schemas import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from services.auth import UserAlreadyExistsError, auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_attr(user: Any, field: str) -> Any:
    if isinstance(user, dict):
        return user.get(field)
    return getattr(user, field, None)


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


__all__ = ["router"]
