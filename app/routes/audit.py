"""Operator audit routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import get_current_user
from app.openapi import openapi_error_responses
from domain.schemas import AuditMessageListResponse, AuditMessageResponse, UserResponse
from infra.db.database import get_db
from services.usage_audit import UsageAuditService

router = APIRouter(prefix="/audit", tags=["audit"])


def get_usage_audit_service(
    db: AsyncSession = Depends(get_db),
) -> UsageAuditService:
    return UsageAuditService(db=db)


@router.get(
    "/messages",
    response_model=AuditMessageListResponse,
    summary="Get audit messages",
    description=(
        "Return an operator-facing, reverse-chronological message audit feed with optional "
        "workspace filtering."
    ),
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def get_audit_messages(
    limit: int = Query(default=100),
    group_id: str | None = Query(default=None),
    current_user: UserResponse = Depends(get_current_user),
    service: UsageAuditService = Depends(get_usage_audit_service),
) -> AuditMessageListResponse:
    if current_user.role not in {"owner", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission denied",
        )

    snapshot = await service.list_audit_messages(
        limit=limit,
        group_id=group_id,
    )
    return AuditMessageListResponse(
        limit=snapshot.limit,
        group_id=snapshot.group_id,
        has_more=snapshot.has_more,
        items=[
            AuditMessageResponse(
                message_id=item.message_id,
                chat_jid=item.chat_jid,
                group_id=item.group_id,
                channel=item.channel,
                run_id=item.run_id,
                external_message_id=item.external_message_id,
                sender=item.sender,
                is_from_me=item.is_from_me,
                slot_id=item.slot_id,
                content=item.content,
                timestamp=item.timestamp,
            )
            for item in snapshot.items
        ],
    )


__all__ = ["get_usage_audit_service", "router"]
