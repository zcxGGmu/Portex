"""User routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import get_current_user, require_permission
from app.openapi import openapi_error_responses
from domain.schemas import (
    CreateInviteCodeRequest,
    InviteCodeListResponse,
    InviteCodeResponse,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
)
from infra.db.database import get_db
from services.auth import (
    AuthInviteCode,
    AuthUser,
    InviteCodeAlreadyExistsError,
    UserNotFoundError,
    auth_service,
)

router = APIRouter(tags=["users"])


def _to_user_response(user: AuthUser) -> UserResponse:
    return UserResponse.model_validate(user, from_attributes=True)


def _to_invite_response(invite: AuthInviteCode) -> InviteCodeResponse:
    return InviteCodeResponse.model_validate(invite, from_attributes=True)


@router.get(
    "/users/me",
    response_model=UserResponse,
    summary="Get the current user",
    description="Return the authenticated user resolved from the current bearer token.",
    responses=openapi_error_responses(status.HTTP_401_UNAUTHORIZED),
)
async def get_me(current_user: AuthUser = Depends(get_current_user)) -> UserResponse:
    return _to_user_response(current_user)


@router.get(
    "/admin/users",
    response_model=UserListResponse,
    tags=["admin"],
    summary="List users",
    description=(
        "List users from the current in-memory auth service. Access requires the "
        "`users:read` permission template."
    ),
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def list_users(
    current_user: AuthUser = Depends(require_permission("users", "read")),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    _ = current_user
    _ = db  # Reserved for future DB-backed user listing.
    return UserListResponse(users=[_to_user_response(user) for user in auth_service.list_users()])


@router.patch(
    "/admin/users/{user_id}",
    response_model=UserResponse,
    tags=["admin"],
    summary="Update a user",
    description=(
        "Update mutable fields on a user record in the current in-memory auth "
        "service. Access requires the `users:write` permission template."
    ),
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: AuthUser = Depends(require_permission("users", "write")),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    _ = current_user
    _ = db  # Reserved for future DB-backed user updates.
    try:
        updated_user = auth_service.update_user(
            user_id,
            **request.model_dump(exclude_unset=True),
        )
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user not found",
        ) from exc
    return _to_user_response(updated_user)


@router.get(
    "/admin/invites",
    response_model=InviteCodeListResponse,
    tags=["admin"],
    summary="List invite codes",
    description=(
        "List invite codes from the current in-memory invite store. Each invite is "
        "single-use and may optionally expire."
    ),
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def list_invite_codes(
    current_user: AuthUser = Depends(require_permission("users", "read")),
    db: AsyncSession = Depends(get_db),
) -> InviteCodeListResponse:
    _ = current_user
    _ = db  # Reserved for future DB-backed invite listing.
    return InviteCodeListResponse(
        invites=[_to_invite_response(invite) for invite in auth_service.list_invite_codes()]
    )


@router.post(
    "/admin/invites",
    response_model=InviteCodeResponse,
    tags=["admin"],
    summary="Create an invite code",
    description=(
        "Create a single-use invite code. The invite can assign a role, an optional "
        "permission template, and an optional expiration timestamp."
    ),
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_409_CONFLICT,
    ),
)
async def create_invite_code(
    request: CreateInviteCodeRequest,
    current_user: AuthUser = Depends(require_permission("users", "write")),
    db: AsyncSession = Depends(get_db),
) -> InviteCodeResponse:
    _ = db  # Reserved for future DB-backed invite creation.
    try:
        invite = auth_service.create_invite_code(
            created_by=current_user.id,
            role=request.role,
            permission_template=request.permission_template,
            expires_at=request.expires_at,
            code=request.code,
        )
    except InviteCodeAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="invite code already exists",
        ) from exc
    return _to_invite_response(invite)


__all__ = ["router"]
