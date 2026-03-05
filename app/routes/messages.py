"""Message routes."""

from uuid import uuid4

from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_user
from domain.schemas import SendMessageRequest, SendMessageResponse, UserResponse

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> SendMessageResponse:
    _ = (request, current_user)
    return SendMessageResponse(
        message_id=f"msg-{uuid4().hex[:12]}",
        status="queued",
    )


__all__ = ["router"]
