"""Task routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import require_permission
from domain.models.task import ScheduledTask
from domain.models.task_log import TaskRunLog
from domain.schemas import (
    CreateTaskRequest,
    DeleteTaskResponse,
    TaskListResponse,
    TaskRunLogListResponse,
    TaskRunLogResponse,
    TaskResponse,
)
from services.auth import AuthUser
from services.task_service import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _to_task_response(task: ScheduledTask) -> TaskResponse:
    return TaskResponse.model_validate(task, from_attributes=True)


def _to_task_run_log_response(log: TaskRunLog) -> TaskRunLogResponse:
    return TaskRunLogResponse.model_validate(log, from_attributes=True)


@router.post("", response_model=TaskResponse)
async def create_task(
    request: CreateTaskRequest,
    current_user: AuthUser = Depends(require_permission("tasks", "write")),
) -> TaskResponse:
    _ = current_user
    try:
        task = task_service.create_task(
            group_folder=request.group_folder,
            chat_jid=request.chat_jid,
            prompt=request.prompt,
            schedule_type=request.schedule_type,
            schedule_value=request.schedule_value,
            next_run=request.next_run,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return _to_task_response(task)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user: AuthUser = Depends(require_permission("tasks", "read")),
) -> TaskListResponse:
    _ = current_user
    tasks = [_to_task_response(task) for task in task_service.list_tasks()]
    return TaskListResponse(tasks=tasks)


@router.get("/{task_id}/logs", response_model=TaskRunLogListResponse)
async def list_task_logs(
    task_id: str,
    limit: int = Query(default=20),
    current_user: AuthUser = Depends(require_permission("tasks", "read")),
) -> TaskRunLogListResponse:
    _ = current_user
    task = task_service.get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task not found",
        )

    normalized_limit = min(max(limit, 1), 200)
    logs = [
        _to_task_run_log_response(log)
        for log in task_service.list_logs(task_id, limit=normalized_limit)
    ]
    return TaskRunLogListResponse(logs=logs)


@router.delete("/{task_id}", response_model=DeleteTaskResponse)
async def delete_task(
    task_id: str,
    current_user: AuthUser = Depends(require_permission("tasks", "write")),
) -> DeleteTaskResponse:
    _ = current_user
    if not task_service.delete_task(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task not found",
        )

    return DeleteTaskResponse(status="removed")

__all__ = ["router"]
