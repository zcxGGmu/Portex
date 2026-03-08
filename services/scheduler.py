"""Task scheduler service."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

from croniter import croniter

from domain.models.task import ScheduledTask

Executor = Callable[[ScheduledTask], Awaitable[None]]
SleepFunc = Callable[[float], Awaitable[None]]
NowFunc = Callable[[], datetime]


async def _noop_executor(task: ScheduledTask) -> None:
    _ = task


class TaskScheduler:
    """Minimal async task scheduler for cron, interval, and once tasks."""

    def __init__(
        self,
        *,
        executor: Executor | None = None,
        poll_interval_seconds: float = 60.0,
        sleep_func: SleepFunc | None = None,
        now_func: NowFunc | None = None,
    ) -> None:
        self._executor = executor or _noop_executor
        self._poll_interval_seconds = poll_interval_seconds
        self._sleep_func = sleep_func or asyncio.sleep
        self._now_func = now_func or datetime.utcnow
        self._tasks: dict[str, ScheduledTask] = {}
        self._running_task_ids: set[str] = set()
        self.running = False

    def upsert_task(self, task: ScheduledTask) -> ScheduledTask:
        self._validate_task(task)
        self._initialize_next_run(task)
        self._tasks[task.id] = task
        return task

    def remove_task(self, task_id: str) -> bool:
        return self._tasks.pop(task_id, None) is not None

    def list_tasks(self) -> list[ScheduledTask]:
        return sorted(
            self._tasks.values(),
            key=lambda task: (task.next_run or datetime.max, task.id),
        )

    async def run_pending(self) -> None:
        now = self._now_func()
        due_tasks = [
            task
            for task in self._tasks.values()
            if self._is_due(task, now) and task.id not in self._running_task_ids
        ]
        due_tasks.sort(key=lambda task: (task.next_run or datetime.max, task.id))

        for task in due_tasks:
            await self._execute_task(task)

    async def start(self) -> None:
        if self.running:
            return

        self.running = True
        try:
            while self.running:
                await self.run_pending()
                if not self.running:
                    break
                await self._sleep_func(self._poll_interval_seconds)
        finally:
            self.running = False

    def stop(self) -> None:
        self.running = False

    def _is_due(self, task: ScheduledTask, now: datetime) -> bool:
        return task.status == "active" and task.next_run is not None and task.next_run <= now

    async def _execute_task(self, task: ScheduledTask) -> None:
        if task.id in self._running_task_ids:
            return

        self._running_task_ids.add(task.id)
        try:
            await self._executor(task)
        except Exception:
            return
        else:
            self._mark_task_after_success(task)
        finally:
            self._running_task_ids.discard(task.id)

    def _mark_task_after_success(self, task: ScheduledTask) -> None:
        if task.schedule_type == "once":
            task.status = "completed"
            task.next_run = None
            return

        task.next_run = self._compute_next_run(task)

    def _compute_next_run(self, task: ScheduledTask) -> datetime | None:
        anchor = task.next_run or self._now_func()

        if task.schedule_type == "interval":
            interval_seconds = self._parse_interval_seconds(task.schedule_value)
            next_run = anchor
            interval = timedelta(seconds=interval_seconds)
            now = self._now_func()
            while next_run <= now:
                next_run += interval
            return next_run

        if task.schedule_type == "cron":
            expression = self._parse_cron_expression(task.schedule_value)
            return croniter(expression, anchor).get_next(datetime)

        if task.schedule_type == "once":
            return None

        raise ValueError(f"unsupported schedule type: {task.schedule_type}")

    def _validate_task(self, task: ScheduledTask) -> None:
        if task.schedule_type not in {"cron", "interval", "once"}:
            raise ValueError(f"unsupported schedule type: {task.schedule_type}")

        if task.schedule_type == "interval":
            self._parse_interval_seconds(task.schedule_value)
            return

        if task.schedule_type == "cron":
            expression = self._parse_cron_expression(task.schedule_value)
            croniter(expression, task.next_run or self._now_func())
            return

        if task.next_run is None:
            raise ValueError("once tasks require next_run")

    def _initialize_next_run(self, task: ScheduledTask) -> None:
        if task.status != "active" or task.next_run is not None:
            return

        if task.schedule_type == "interval":
            interval_seconds = self._parse_interval_seconds(task.schedule_value)
            task.next_run = self._now_func() + timedelta(seconds=interval_seconds)
            return

        if task.schedule_type == "cron":
            expression = self._parse_cron_expression(task.schedule_value)
            task.next_run = croniter(expression, self._now_func()).get_next(datetime)

    def _parse_interval_seconds(self, schedule_value: str | None) -> int:
        if schedule_value is None:
            raise ValueError("interval tasks require schedule_value")

        try:
            interval_seconds = int(schedule_value)
        except ValueError as exc:
            raise ValueError(f"invalid interval schedule: {schedule_value}") from exc

        if interval_seconds <= 0:
            raise ValueError(f"invalid interval schedule: {schedule_value}")
        return interval_seconds

    def _parse_cron_expression(self, schedule_value: str | None) -> str:
        if schedule_value is None or schedule_value.strip() == "":
            raise ValueError("cron tasks require schedule_value")
        return schedule_value


SchedulerService = TaskScheduler

__all__ = ["SchedulerService", "TaskScheduler"]
