"""Execution status query routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import get_current_user
from app.openapi import openapi_error_responses
from infra.db.database import get_db
from domain.schemas import (
    ExecutionMode,
    ExecutionRecoveryResponse,
    ExecutionRunStatusResponse,
    UserResponse,
)
from services.execution_coordinator import ExecutionCoordinator, ExecutionRunSnapshot
from services.group_registry import GroupRegistryService
from services.execution_runtime import get_execution_coordinator

router = APIRouter(prefix="/executions", tags=["executions"])

_ALLOWED_EXECUTION_MODES: set[ExecutionMode] = {"openai", "host", "container"}


def get_group_registry_service(
    db: AsyncSession = Depends(get_db),
) -> GroupRegistryService:
    return GroupRegistryService(db=db)


def _normalize_requested_mode(requested_mode: str | None) -> ExecutionMode | None:
    if requested_mode in _ALLOWED_EXECUTION_MODES:
        return requested_mode
    return None


def _to_execution_status_response(snapshot: ExecutionRunSnapshot) -> ExecutionRunStatusResponse:
    return ExecutionRunStatusResponse(
        run_id=snapshot.run_id,
        status=snapshot.status,
        group_folder=snapshot.group_folder,
        chat_jid=snapshot.chat_jid,
        user_id=snapshot.user_id,
        source=snapshot.source,
        slot_id=snapshot.slot_id,
        requested_mode=_normalize_requested_mode(snapshot.requested_mode),
        backend=snapshot.backend,
        session_id=snapshot.session_id,
        created_at=snapshot.created_at,
        started_at=snapshot.started_at,
        finished_at=snapshot.finished_at,
        final_output=snapshot.final_output,
        error=snapshot.error,
        timeout_ms=snapshot.timeout_ms,
        recovery=ExecutionRecoveryResponse(
            attempted=snapshot.recovery_attempted,
            reason=snapshot.recovery_reason,
            succeeded=snapshot.recovery_succeeded,
        ),
    )


async def _can_read_execution_snapshot(
    current_user: UserResponse,
    snapshot: ExecutionRunSnapshot,
    group_registry: GroupRegistryService,
) -> bool:
    workspace = await group_registry.get_web_workspace_by_folder(snapshot.group_folder)
    if workspace is not None:
        return await group_registry.user_can_access_group(
            user_id=current_user.id,
            group=workspace,
        )
    if current_user.role in {"owner", "admin"}:
        return True
    return snapshot.user_id == current_user.id


@router.get(
    "/{run_id}",
    response_model=ExecutionRunStatusResponse,
    response_model_exclude_none=True,
    summary="Get execution run status",
    description=(
        "Return the current execution status snapshot for one run id. "
        "The snapshot includes minimal recovery signals from coordinator-owned "
        "session lifecycle handling."
    ),
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def get_execution_status(
    run_id: str,
    current_user: UserResponse = Depends(get_current_user),
    coordinator: ExecutionCoordinator = Depends(get_execution_coordinator),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
) -> ExecutionRunStatusResponse:
    _ = current_user
    snapshot = coordinator.get_run_snapshot(run_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="execution run not found",
        )
    if not await _can_read_execution_snapshot(current_user, snapshot, group_registry):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="execution run not found",
        )

    return _to_execution_status_response(snapshot)


__all__ = ["get_execution_coordinator", "get_group_registry_service", "router"]
