"""In-memory task execution log service."""

from __future__ import annotations

from datetime import datetime, timezone

from domain.models.task_log import TaskRunLog


class TaskLogService:
    """Store task execution logs in memory for the current process."""

    def __init__(self) -> None:
        self._next_id = 1
        self._logs_by_task_id: dict[str, list[TaskRunLog]] = {}

    def record_log(
        self,
        *,
        task_id: str,
        run_at: datetime,
        duration_ms: int,
        status: str,
        result: str | None,
        error: str | None = None,
    ) -> TaskRunLog:
        log = TaskRunLog(
            id=self._next_id,
            task_id=task_id,
            run_at=self._normalize_datetime(run_at),
            duration_ms=duration_ms,
            status=status,
            result=result,
            error=error,
        )
        self._next_id += 1
        self._logs_by_task_id.setdefault(task_id, []).append(log)
        return log

    def list_logs(self, task_id: str, limit: int = 20) -> list[TaskRunLog]:
        logs = self._logs_by_task_id.get(task_id, [])
        ordered_logs = sorted(
            logs,
            key=lambda log: (log.run_at, log.id),
            reverse=True,
        )
        return ordered_logs[:limit]

    def reset(self) -> None:
        self._next_id = 1
        self._logs_by_task_id.clear()

    def _normalize_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)


task_log_service = TaskLogService()


__all__ = ["TaskLogService", "task_log_service"]
