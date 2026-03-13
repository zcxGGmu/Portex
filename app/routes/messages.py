"""Message routes."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.routes.im import get_message_dispatch_service
from app.middleware.auth import get_current_user
from app.openapi import openapi_error_responses
from domain.schemas import SendMessageRequest, SendMessageResponse, UnifiedMessage, UserResponse
from services.message_dispatch import MessageDispatchError, MessageDispatchService

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post(
    "",
    response_model=SendMessageResponse,
    response_model_exclude_none=True,
    summary="Dispatch a message",
    description=(
        "Dispatch an authenticated HTTP message through the current runtime chain. "
        "The request is normalized into the same dispatch boundary used by the "
        "current IM adapters."
    ),
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
    ),
)
async def send_message(
    request: SendMessageRequest,
    current_user: UserResponse = Depends(get_current_user),
    dispatch_service: MessageDispatchService = Depends(get_message_dispatch_service),
) -> SendMessageResponse:
    message_id = f"msg-{uuid4().hex[:12]}"
    normalized_message = UnifiedMessage(
        channel="web",
        chat_jid=request.group_id,
        sender_id=current_user.id,
        group_folder=request.group_id,
        content=request.content,
        message_id=message_id,
        timestamp=datetime.now(timezone.utc),
    )

    try:
        dispatch_kwargs: dict[str, str] = {}
        if request.execution_mode is not None:
            dispatch_kwargs["execution_mode"] = request.execution_mode
        result = await dispatch_service.dispatch_inbound_message(
            normalized_message,
            **dispatch_kwargs,
        )
    except MessageDispatchError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return SendMessageResponse(
        message_id=message_id,
        run_id=result.run_id,
        status=result.status,
        final_output=result.final_output,
    )


__all__ = ["router"]
