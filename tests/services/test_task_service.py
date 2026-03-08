from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import re
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _build_service(*, now: datetime):
    from services.scheduler import TaskScheduler
    from services.task_service import TaskService

    scheduler = TaskScheduler(now_func=lambda: now)
    service = TaskService(scheduler=scheduler)
    return service, scheduler


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


def test_create_task_generates_active_once_task_with_hex_id() -> None:
    now = datetime(2026, 3, 8, 12, 0, 0)
    service, _scheduler = _build_service(now=now)

    task = service.create_task(
        group_folder="group-a",
        chat_jid="chat-a",
        prompt="run once",
        schedule_type="once",
        schedule_value=None,
        next_run=now + timedelta(minutes=5),
    )

    assert re.fullmatch(r"task-[0-9a-f]+", task.id)
    assert task.status == "active"


def test_create_task_initializes_missing_interval_next_run_via_scheduler() -> None:
    now = datetime(2026, 3, 8, 12, 0, 0)
    service, _scheduler = _build_service(now=now)

    task = service.create_task(
        group_folder="group-a",
        chat_jid="chat-a",
        prompt="run every 30 seconds",
        schedule_type="interval",
        schedule_value="30",
        next_run=None,
    )

    assert task.next_run == now + timedelta(seconds=30)
    assert task.status == "active"


def test_list_tasks_returns_tasks_in_scheduler_order() -> None:
    now = datetime(2026, 3, 8, 12, 0, 0)
    service, scheduler = _build_service(now=now)

    scheduler.upsert_task(
        _build_task(
            task_id="task-b",
            now=now,
            schedule_type="once",
            schedule_value=None,
            next_run=now + timedelta(minutes=2),
        )
    )
    scheduler.upsert_task(
        _build_task(
            task_id="task-c",
            now=now,
            schedule_type="once",
            schedule_value=None,
            next_run=now + timedelta(minutes=1),
        )
    )
    scheduler.upsert_task(
        _build_task(
            task_id="task-a",
            now=now,
            schedule_type="once",
            schedule_value=None,
            next_run=now + timedelta(minutes=1),
        )
    )

    tasks = service.list_tasks()

    assert [task.id for task in tasks] == ["task-a", "task-c", "task-b"]


def test_delete_task_returns_true_for_existing_task_and_false_for_missing_task() -> None:
    now = datetime(2026, 3, 8, 12, 0, 0)
    service, scheduler = _build_service(now=now)

    task = service.create_task(
        group_folder="group-a",
        chat_jid="chat-a",
        prompt="delete me",
        schedule_type="once",
        schedule_value=None,
        next_run=now + timedelta(minutes=5),
    )

    assert service.delete_task(task.id) is True
    assert service.delete_task(task.id) is False
    assert scheduler.list_tasks() == []


@pytest.mark.parametrize(
    ("schedule_type", "schedule_value", "next_run"),
    [
        ("once", None, None),
        ("interval", "0", None),
        ("interval", "-5", None),
    ],
)
def test_create_task_raises_value_error_for_invalid_schedule_combinations(
    schedule_type: str,
    schedule_value: str | None,
    next_run: datetime | None,
) -> None:
    now = datetime(2026, 3, 8, 12, 0, 0)
    service, _scheduler = _build_service(now=now)

    with pytest.raises(ValueError):
        service.create_task(
            group_folder="group-a",
            chat_jid="chat-a",
            prompt="invalid task",
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            next_run=next_run,
        )
