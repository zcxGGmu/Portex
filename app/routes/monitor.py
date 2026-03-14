"""Operator monitor routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_user
from app.openapi import openapi_error_responses
from domain.schemas import (
    ExecutionMode,
    ExecutionRecoveryResponse,
    HealthResponse,
    MonitorBackendHealthResponse,
    MonitorHealthResponse,
    MonitorQueueGroupResponse,
    MonitorQueueResponse,
    MonitorResponse,
    MonitorRunListResponse,
    MonitorRunSummaryResponse,
    UserResponse,
)
from services.execution_coordinator import ExecutionCoordinator, ExecutionRunSnapshot
from services.execution_runtime import build_monitor_backend_health, get_execution_coordinator

router = APIRouter(tags=["monitor"])

_ALLOWED_EXECUTION_MODES: set[ExecutionMode] = {"openai", "host", "container"}


def _normalize_requested_mode(requested_mode: str | None) -> ExecutionMode | None:
    if requested_mode in _ALLOWED_EXECUTION_MODES:
        return requested_mode
    return None


def _to_monitor_run_summary(snapshot: ExecutionRunSnapshot) -> MonitorRunSummaryResponse:
    return MonitorRunSummaryResponse(
        run_id=snapshot.run_id,
        group_id=snapshot.group_folder,
        chat_jid=snapshot.chat_jid,
        user_id=snapshot.user_id,
        source=snapshot.source,
        slot_id=snapshot.slot_id,
        status=snapshot.status,
        backend=snapshot.backend,
        requested_mode=_normalize_requested_mode(snapshot.requested_mode),
        created_at=snapshot.created_at,
        started_at=snapshot.started_at,
        finished_at=snapshot.finished_at,
        error=snapshot.error,
        timeout_ms=snapshot.timeout_ms,
        recovery=ExecutionRecoveryResponse(
            attempted=snapshot.recovery_attempted,
            reason=snapshot.recovery_reason,
            succeeded=snapshot.recovery_succeeded,
        ),
    )


def get_monitor_backend_health(
    coordinator: ExecutionCoordinator = Depends(get_execution_coordinator),
) -> list[MonitorBackendHealthResponse]:
    return build_monitor_backend_health(coordinator)


@router.get(
    "/monitor",
    response_model=MonitorResponse,
    summary="Get monitor status",
    description=(
        "Return the current operator-facing monitor payload for queue state, "
        "recent runs, and backend/runtime health."
    ),
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def get_monitor_status(
    current_user: UserResponse = Depends(get_current_user),
    coordinator: ExecutionCoordinator = Depends(get_execution_coordinator),
    backend_health: list[MonitorBackendHealthResponse] = Depends(get_monitor_backend_health),
) -> MonitorResponse:
    if current_user.role not in {"owner", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission denied",
        )

    base_health = HealthResponse()
    return MonitorResponse(
        health=MonitorHealthResponse(
            api_status=base_health.status,
            version=base_health.version,
            coordinator_status="ok",
            backends=backend_health,
        ),
        queue=MonitorQueueResponse(
            groups=[
                MonitorQueueGroupResponse(
                    group_id=item.group_id,
                    queued_runs=item.queued_runs,
                    running_runs=item.running_runs,
                    active_run_id=item.active_run_id,
                    active_backend=item.active_backend,
                )
                for item in coordinator.get_monitor_queue_snapshot()
            ]
        ),
        runs=MonitorRunListResponse(
            items=[
                _to_monitor_run_summary(snapshot)
                for snapshot in coordinator.list_run_snapshots(limit=50)
            ]
        ),
    )


__all__ = [
    "get_execution_coordinator",
    "get_monitor_backend_health",
    "router",
]
