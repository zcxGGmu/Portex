"""Thin task orchestration service backed by the in-memory scheduler."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from uuid import uuid4

from domain.models.task import ScheduledTask
from services.scheduler import TaskScheduler
from services.task_log_service import TaskLogService, task_log_service as global_task_log_service

TaskExecutor = Callable[[ScheduledTask], Awaitable[object | None]]


async def _noop_task_executor(task: ScheduledTask) -> None:
    _ = task


class TaskService:
    """Create, list, and delete scheduled tasks through ``TaskScheduler``."""

    def __init__(
        self,
        *,
        scheduler: TaskScheduler | None = None,
        executor: TaskExecutor | None = None,
        task_log_service: TaskLogService | None = None,
        run_at_now_func: Callable[[], datetime] | None = None,
        perf_counter_func: Callable[[], float] | None = None,
    ) -> None:
        self._executor = executor or _noop_task_executor
        self._task_log_service = task_log_service or global_task_log_service
        self._run_at_now_func = run_at_now_func or datetime.utcnow
        self._perf_counter = perf_counter_func or time.perf_counter
        self._scheduler = scheduler or TaskScheduler()
        self._scheduler.set_executor(self._execute_task)

    def create_task(
        self,
        *,
        group_folder: str,
        chat_jid: str,
        prompt: str,
        schedule_type: str,
        schedule_value: str | None = None,
        next_run: datetime | None = None,
    ) -> ScheduledTask:
        normalized_schedule_value = self._normalize_schedule_value(
            schedule_type=schedule_type,
            schedule_value=schedule_value,
        )
        normalized_next_run = self._normalize_datetime(next_run)
        task = ScheduledTask(
            id=f"task-{uuid4().hex}",
            group_folder=group_folder,
            chat_jid=chat_jid,
            prompt=prompt,
            schedule_type=schedule_type,
            schedule_value=normalized_schedule_value,
            next_run=normalized_next_run,
            status="active",
            created_at=datetime.utcnow(),
        )
        return self._scheduler.upsert_task(task)

    def list_tasks(self) -> list[ScheduledTask]:
        return self._scheduler.list_tasks()

    def get_task(self, task_id: str) -> ScheduledTask | None:
        for task in self._scheduler.list_tasks():
            if task.id == task_id:
                return task
        return None

    def delete_task(self, task_id: str) -> bool:
        return self._scheduler.remove_task(task_id)

    def list_logs(self, task_id: str, limit: int = 20):
        return self._task_log_service.list_logs(task_id, limit=limit)

    async def run_pending(self) -> None:
        await self._scheduler.run_pending()

    def reset(self) -> None:
        self._scheduler = TaskScheduler()
        self._scheduler.set_executor(self._execute_task)
        self._task_log_service.reset()

    def _normalize_schedule_value(
        self,
        *,
        schedule_type: str,
        schedule_value: str | None,
    ) -> str | None:
        if schedule_type == "once":
            if schedule_value is None or schedule_value.strip() == "":
                return None
            raise ValueError("once tasks do not accept schedule_value")

        if schedule_value is None:
            return None

        normalized_value = schedule_value.strip()
        if normalized_value == "":
            return None

        return normalized_value

    def _normalize_datetime(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    async def _execute_task(self, task: ScheduledTask) -> None:
        run_at = self._normalize_datetime(self._run_at_now_func())
        started_at = self._perf_counter()
        try:
            result = await self._executor(task)
        except Exception as exc:
            self._task_log_service.record_log(
                task_id=task.id,
                run_at=run_at or datetime.utcnow(),
                duration_ms=self._duration_ms(started_at),
                status="error",
                result=None,
                error=str(exc),
            )
            raise

        self._task_log_service.record_log(
            task_id=task.id,
            run_at=run_at or datetime.utcnow(),
            duration_ms=self._duration_ms(started_at),
            status="success",
            result=None if result is None else str(result),
            error=None,
        )

    def _duration_ms(self, started_at: float) -> int:
        return max(0, int((self._perf_counter() - started_at) * 1000))


task_service = TaskService()


__all__ = ["TaskService", "task_service"]
