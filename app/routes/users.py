"""User routes."""

from fastapi import APIRouter, Depends

from app.routes.auth import get_current_user
from domain.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user


__all__ = ["router"]
