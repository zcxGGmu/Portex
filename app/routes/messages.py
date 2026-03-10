"""Message routes."""

from uuid import uuid4

from fastapi import APIRouter, Depends, status

from app.middleware.auth import get_current_user
from app.openapi import openapi_error_responses
from domain.schemas import SendMessageRequest, SendMessageResponse, UserResponse

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post(
    "",
    response_model=SendMessageResponse,
    summary="Queue a message",
    description=(
        "Queue a message through the current minimal HTTP placeholder endpoint. The "
        "implementation only returns a queued acknowledgement and does not represent "
        "the full IM delivery pipeline."
    ),
    responses=openapi_error_responses(status.HTTP_401_UNAUTHORIZED),
)
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
