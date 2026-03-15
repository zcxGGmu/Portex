"""Operator usage routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import get_current_user
from app.openapi import openapi_error_responses
from domain.schemas import (
    UsageChannelBreakdownResponse,
    UsageDailyBreakdownResponse,
    UsageStatsResponse,
    UsageSummaryResponse,
    UserResponse,
)
from infra.db.database import get_db
from services.usage_audit import UsageAuditService

router = APIRouter(prefix="/usage", tags=["usage"])


def get_usage_audit_service(
    db: AsyncSession = Depends(get_db),
) -> UsageAuditService:
    return UsageAuditService(db=db)


@router.get(
    "/stats",
    response_model=UsageStatsResponse,
    summary="Get usage statistics",
    description=(
        "Return operator-facing usage statistics aggregated from persisted message records "
        "within the selected day window."
    ),
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def get_usage_stats(
    days: int = Query(default=7),
    current_user: UserResponse = Depends(get_current_user),
    service: UsageAuditService = Depends(get_usage_audit_service),
) -> UsageStatsResponse:
    if current_user.role not in {"owner", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission denied",
        )

    snapshot = await service.get_usage_stats(days=days)
    return UsageStatsResponse(
        days=snapshot.days,
        summary=UsageSummaryResponse(
            total_messages=snapshot.summary.total_messages,
            total_runs=snapshot.summary.total_runs,
            total_user_messages=snapshot.summary.total_user_messages,
            total_assistant_messages=snapshot.summary.total_assistant_messages,
            total_active_days=snapshot.summary.total_active_days,
        ),
        daily=[
            UsageDailyBreakdownResponse(
                date=item.date,
                message_count=item.message_count,
                run_count=item.run_count,
                user_message_count=item.user_message_count,
                assistant_message_count=item.assistant_message_count,
            )
            for item in snapshot.daily
        ],
        channels=[
            UsageChannelBreakdownResponse(
                channel=item.channel,
                message_count=item.message_count,
                run_count=item.run_count,
            )
            for item in snapshot.channels
        ],
    )


__all__ = ["get_usage_audit_service", "router"]
