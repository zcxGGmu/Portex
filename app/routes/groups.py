"""Group routes."""

from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_user
from domain.schemas import GroupListResponse, GroupSummaryResponse, UserResponse

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=GroupListResponse)
async def list_groups(
    current_user: UserResponse = Depends(get_current_user),
) -> GroupListResponse:
    _ = current_user
    return GroupListResponse(
        groups=[GroupSummaryResponse(group_id="group-demo", name="Demo Group")]
    )


__all__ = ["router"]
