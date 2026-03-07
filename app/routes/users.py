"""User routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import get_current_user, require_role
from domain.schemas import UpdateUserRequest, UserListResponse, UserResponse
from infra.db.database import get_db
from services.auth import AuthUser, UserNotFoundError, auth_service

router = APIRouter(tags=["users"])


def _to_user_response(user: AuthUser) -> UserResponse:
    return UserResponse.model_validate(user, from_attributes=True)


@router.get("/users/me", response_model=UserResponse)
async def get_me(current_user: AuthUser = Depends(get_current_user)) -> UserResponse:
    return _to_user_response(current_user)


@router.get("/admin/users", response_model=UserListResponse, tags=["admin"])
async def list_users(
    current_user: AuthUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    _ = current_user
    _ = db  # Reserved for future DB-backed user listing.
    return UserListResponse(users=[_to_user_response(user) for user in auth_service.list_users()])


@router.patch("/admin/users/{user_id}", response_model=UserResponse, tags=["admin"])
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: AuthUser = Depends(require_role("admin")),
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


__all__ = ["router"]
