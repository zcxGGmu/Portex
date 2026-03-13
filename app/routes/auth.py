"""Authentication routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.openapi import openapi_error_responses
from domain.schemas import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from infra.db.database import get_db
from services.auth import InviteCodeUnavailableError, UserAlreadyExistsError, auth_service
from services.group_registry import GroupRegistryService

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_attr(user: Any, field: str) -> Any:
    if isinstance(user, dict):
        return user.get(field)
    return getattr(user, field, None)


def get_group_registry_service(
    db: AsyncSession = Depends(get_db),
) -> GroupRegistryService:
    return GroupRegistryService(db=db)


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="Register a user",
    description=(
        "Create a new user in the current in-memory auth service. If `invite_code` "
        "is provided and valid, the invited role and permission template are applied "
        "during registration."
    ),
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_409_CONFLICT,
    ),
)
async def register(
    request: RegisterRequest,
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
) -> RegisterResponse:
    try:
        user = auth_service.register_user(
            username=request.username,
            password=request.password,
            invite_code=request.invite_code,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="username already exists",
        ) from exc
    except InviteCodeUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invite code is invalid, expired, or already used",
        ) from exc

    await group_registry.ensure_home_workspace(
        user_id=_user_attr(user, "id"),
        role=_user_attr(user, "role"),
        username=_user_attr(user, "username"),
    )
    return RegisterResponse(user_id=_user_attr(user, "id"))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with username and password",
    description=(
        "Exchange username and password credentials for a bearer token that can be "
        "used on the authenticated HTTP routes."
    ),
    responses=openapi_error_responses(status.HTTP_401_UNAUTHORIZED),
)
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


__all__ = ["get_group_registry_service", "router"]
