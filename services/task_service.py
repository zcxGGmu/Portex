"""Thin task orchestration service backed by the in-memory scheduler."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from domain.models.task import ScheduledTask
from services.scheduler import TaskScheduler


class TaskService:
    """Create, list, and delete scheduled tasks through ``TaskScheduler``."""

    def __init__(self, *, scheduler: TaskScheduler | None = None) -> None:
        self._scheduler = scheduler or TaskScheduler()

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

    def delete_task(self, task_id: str) -> bool:
        return self._scheduler.remove_task(task_id)

    def reset(self) -> None:
        self._scheduler = TaskScheduler()

    def _normalize_schedule_value(
        self,
        *,
        schedule_type: str,
        schedule_value: str | None,
    ) -> str | None:
        if schedule_value is None:
            if schedule_type == "once":
                return None
            return None

        normalized_value = schedule_value.strip()
        if normalized_value == "":
            if schedule_type == "once":
                return None
            return None

        if schedule_type == "once":
            raise ValueError("once tasks do not accept schedule_value")

        return normalized_value

    def _normalize_datetime(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)


task_service = TaskService()


__all__ = ["TaskService", "task_service"]
