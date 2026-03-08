from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _build_task(
    *,
    task_id: str,
    now: datetime,
    schedule_type: str,
    schedule_value: str | None,
    next_run: datetime | None,
    status: str = "active",
):
    from domain.models.task import ScheduledTask

    return ScheduledTask(
        id=task_id,
        group_folder="group-a",
        chat_jid="chat-a",
        prompt="run task",
        schedule_type=schedule_type,
        schedule_value=schedule_value,
        next_run=next_run,
        status=status,
        created_at=now,
    )


@pytest.mark.asyncio
async def test_run_pending_executes_due_once_task_and_marks_it_completed() -> None:
    from services.scheduler import TaskScheduler

    now = datetime(2026, 3, 8, 12, 0, 0)
    executed_task_ids: list[str] = []

    async def executor(task) -> None:
        executed_task_ids.append(task.id)

    scheduler = TaskScheduler(
        executor=executor,
        now_func=lambda: now,
    )
    task = _build_task(
        task_id="task-once",
        now=now,
        schedule_type="once",
        schedule_value=None,
        next_run=now,
    )
    scheduler.upsert_task(task)

    await scheduler.run_pending()

    assert executed_task_ids == ["task-once"]
    assert task.status == "completed"
    assert task.next_run is None


@pytest.mark.asyncio
async def test_run_pending_executes_due_interval_task_and_advances_next_run() -> None:
    from services.scheduler import TaskScheduler

    now = datetime(2026, 3, 8, 12, 0, 0)
    executed_task_ids: list[str] = []

    async def executor(task) -> None:
        executed_task_ids.append(task.id)

    scheduler = TaskScheduler(
        executor=executor,
        now_func=lambda: now,
    )
    task = _build_task(
        task_id="task-interval",
        now=now,
        schedule_type="interval",
        schedule_value="30",
        next_run=now,
    )
    scheduler.upsert_task(task)

    await scheduler.run_pending()

    assert executed_task_ids == ["task-interval"]
    assert task.status == "active"
    assert task.next_run == now + timedelta(seconds=30)


@pytest.mark.asyncio
async def test_run_pending_executes_due_cron_task_and_advances_next_run() -> None:
    from services.scheduler import TaskScheduler

    now = datetime(2026, 3, 8, 12, 0, 0)
    executed_task_ids: list[str] = []

    async def executor(task) -> None:
        executed_task_ids.append(task.id)

    scheduler = TaskScheduler(
        executor=executor,
        now_func=lambda: now,
    )
    task = _build_task(
        task_id="task-cron",
        now=now,
        schedule_type="cron",
        schedule_value="*/5 * * * *",
        next_run=now,
    )
    scheduler.upsert_task(task)

    await scheduler.run_pending()

    assert executed_task_ids == ["task-cron"]
    assert task.status == "active"
    assert task.next_run == datetime(2026, 3, 8, 12, 5, 0)


@pytest.mark.asyncio
async def test_run_pending_skips_inactive_and_future_tasks() -> None:
    from services.scheduler import TaskScheduler

    now = datetime(2026, 3, 8, 12, 0, 0)
    executed_task_ids: list[str] = []

    async def executor(task) -> None:
        executed_task_ids.append(task.id)

    scheduler = TaskScheduler(
        executor=executor,
        now_func=lambda: now,
    )
    inactive_task = _build_task(
        task_id="task-inactive",
        now=now,
        schedule_type="once",
        schedule_value=None,
        next_run=now,
        status="paused",
    )
    future_task = _build_task(
        task_id="task-future",
        now=now,
        schedule_type="once",
        schedule_value=None,
        next_run=now + timedelta(minutes=5),
    )
    scheduler.upsert_task(inactive_task)
    scheduler.upsert_task(future_task)

    await scheduler.run_pending()

    assert executed_task_ids == []
    assert inactive_task.status == "paused"
    assert future_task.status == "active"
    assert future_task.next_run == now + timedelta(minutes=5)


@pytest.mark.asyncio
async def test_run_pending_keeps_schedule_state_when_executor_fails() -> None:
    from services.scheduler import TaskScheduler

    now = datetime(2026, 3, 8, 12, 0, 0)

    async def executor(_task) -> None:
        raise RuntimeError("boom")

    scheduler = TaskScheduler(
        executor=executor,
        now_func=lambda: now,
    )
    task = _build_task(
        task_id="task-error",
        now=now,
        schedule_type="once",
        schedule_value=None,
        next_run=now,
    )
    scheduler.upsert_task(task)

    await scheduler.run_pending()

    assert task.status == "active"
    assert task.next_run == now


@pytest.mark.asyncio
async def test_start_runs_pending_work_and_stops_cleanly_with_injected_sleep() -> None:
    from services.scheduler import TaskScheduler

    now = datetime(2026, 3, 8, 12, 0, 0)
    executed_task_ids: list[str] = []
    sleep_calls: list[float] = []

    async def executor(task) -> None:
        executed_task_ids.append(task.id)

    async def sleep_func(seconds: float) -> None:
        sleep_calls.append(seconds)
        scheduler.stop()

    scheduler = TaskScheduler(
        executor=executor,
        now_func=lambda: now,
        sleep_func=sleep_func,
        poll_interval_seconds=0.25,
    )
    task = _build_task(
        task_id="task-loop",
        now=now,
        schedule_type="once",
        schedule_value=None,
        next_run=now,
    )
    scheduler.upsert_task(task)

    await scheduler.start()

    assert executed_task_ids == ["task-loop"]
    assert sleep_calls == [0.25]
    assert scheduler.running is False


@pytest.mark.asyncio
async def test_run_pending_does_not_double_execute_task_while_it_is_running() -> None:
    import asyncio

    from services.scheduler import TaskScheduler

    now = datetime(2026, 3, 8, 12, 0, 0)
    started = asyncio.Event()
    release = asyncio.Event()
    executed_task_ids: list[str] = []

    async def executor(task) -> None:
        executed_task_ids.append(task.id)
        started.set()
        await release.wait()

    scheduler = TaskScheduler(
        executor=executor,
        now_func=lambda: now,
    )
    task = _build_task(
        task_id="task-guard",
        now=now,
        schedule_type="interval",
        schedule_value="30",
        next_run=now,
    )
    scheduler.upsert_task(task)

    first_run = asyncio.create_task(scheduler.run_pending())
    await started.wait()
    await scheduler.run_pending()
    release.set()
    await first_run

    assert executed_task_ids == ["task-guard"]
