"""Message routes."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.routes.im import get_message_dispatch_service
from app.middleware.auth import get_current_user
from app.openapi import openapi_error_responses
from infra.db.database import get_db
from domain.schemas import SendMessageRequest, SendMessageResponse, UnifiedMessage, UserResponse
from services.group_registry import GroupRegistryService
from services.message_dispatch import MessageDispatchError, MessageDispatchService

router = APIRouter(prefix="/messages", tags=["messages"])


def get_group_registry_service(
    db: AsyncSession = Depends(get_db),
) -> GroupRegistryService:
    return GroupRegistryService(db=db)


async def _resolve_http_message_target(
    *,
    group_id: str,
    current_user: UserResponse,
    group_registry: GroupRegistryService,
) -> tuple[str, str]:
    await group_registry.ensure_home_workspace(
        user_id=current_user.id,
        role=current_user.role,
        username=current_user.username,
    )
    workspace = await group_registry.get_web_workspace_by_folder(group_id)
    if workspace is not None:
        if not await group_registry.user_can_access_group(
            user_id=current_user.id,
            group=workspace,
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="group not found",
            )
        return workspace.jid, workspace.folder
    return group_id, group_id


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
        status.HTTP_404_NOT_FOUND,
    ),
)
async def send_message(
    request: SendMessageRequest,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    dispatch_service: MessageDispatchService = Depends(get_message_dispatch_service),
) -> SendMessageResponse:
    message_id = f"msg-{uuid4().hex[:12]}"
    chat_jid, group_folder = await _resolve_http_message_target(
        group_id=request.group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    normalized_message = UnifiedMessage(
        channel="web",
        chat_jid=chat_jid,
        sender_id=current_user.id,
        group_folder=group_folder,
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


__all__ = ["get_group_registry_service", "router"]
