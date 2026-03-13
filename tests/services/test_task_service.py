from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _build_service(*, now: datetime, executor=None, execution_coordinator=None, task_log_service=None):
    from services.scheduler import TaskScheduler
    from services.task_service import TaskService

    scheduler = TaskScheduler(now_func=lambda: now)
    service = TaskService(
        scheduler=scheduler,
        executor=executor,
        execution_coordinator=execution_coordinator,
        task_log_service=task_log_service,
        run_at_now_func=lambda: now,
    )
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


def test_create_task_normalizes_aware_next_run_to_internal_utc_naive() -> None:
    now = datetime(2026, 3, 8, 12, 0, 0)
    service, _scheduler = _build_service(now=now)

    task = service.create_task(
        group_folder="group-a",
        chat_jid="chat-a",
        prompt="run once with timezone",
        schedule_type="once",
        schedule_value=None,
        next_run=datetime(2026, 3, 8, 12, 5, 0, tzinfo=timezone(timedelta(hours=8))),
    )

    assert task.next_run == datetime(2026, 3, 8, 4, 5, 0)
    assert task.next_run.tzinfo is None


def test_create_task_persists_execution_mode() -> None:
    now = datetime(2026, 3, 8, 12, 0, 0)
    service, _scheduler = _build_service(now=now)

    task = service.create_task(
        group_folder="group-a",
        chat_jid="chat-a",
        prompt="run in host mode",
        execution_mode="host",
        schedule_type="once",
        schedule_value=None,
        next_run=now + timedelta(minutes=5),
    )

    assert task.execution_mode == "host"


@pytest.mark.asyncio
async def test_run_pending_records_success_log_for_due_task() -> None:
    from services.task_log_service import TaskLogService

    now = datetime(2026, 3, 8, 12, 0, 0)
    executed_task_ids: list[str] = []
    log_service = TaskLogService()

    async def executor(task) -> None:
        executed_task_ids.append(task.id)

    service, _scheduler = _build_service(
        now=now,
        executor=executor,
        task_log_service=log_service,
    )
    task = service.create_task(
        group_folder="group-a",
        chat_jid="chat-a",
        prompt="run once",
        schedule_type="once",
        schedule_value=None,
        next_run=now,
    )

    await service.run_pending()

    assert executed_task_ids == [task.id]
    logs = log_service.list_logs(task.id)
    assert len(logs) == 1
    assert logs[0].task_id == task.id
    assert logs[0].status == "success"


@pytest.mark.asyncio
async def test_run_pending_records_error_log_when_executor_fails() -> None:
    from services.task_log_service import TaskLogService

    now = datetime(2026, 3, 8, 12, 0, 0)
    log_service = TaskLogService()

    async def executor(_task) -> None:
        raise RuntimeError("boom")

    service, _scheduler = _build_service(
        now=now,
        executor=executor,
        task_log_service=log_service,
    )
    task = service.create_task(
        group_folder="group-a",
        chat_jid="chat-a",
        prompt="run once",
        schedule_type="once",
        schedule_value=None,
        next_run=now,
    )

    await service.run_pending()

    logs = log_service.list_logs(task.id)
    assert len(logs) == 1
    assert logs[0].status == "error"
    assert logs[0].result is None
    assert logs[0].error == "boom"


@pytest.mark.asyncio
async def test_run_pending_submits_due_task_through_execution_coordinator() -> None:
    from services.execution_coordinator import ExecutionHandle, ExecutionResult
    from services.task_log_service import TaskLogService

    now = datetime(2026, 3, 8, 12, 0, 0)
    log_service = TaskLogService()
    submit_calls: list[object] = []
    wait_calls: list[str] = []

    class FakeCoordinator:
        async def submit_execution(self, request):
            submit_calls.append(request)
            return ExecutionHandle(
                run_id=request.request_id or "run-scheduled",
                group_folder=request.group_folder,
                status="queued",
            )

        async def wait_for_run(self, run_id: str):
            wait_calls.append(run_id)
            return ExecutionResult(
                run_id=run_id,
                status="completed",
                group_folder="group-a",
                backend="host_process",
                session_id="group-a",
                final_output="scheduled reply",
            )

    service, _scheduler = _build_service(
        now=now,
        execution_coordinator=FakeCoordinator(),
        task_log_service=log_service,
    )
    task = service.create_task(
        group_folder="group-a",
        chat_jid="chat-a",
        prompt="run scheduled task",
        execution_mode="host",
        schedule_type="once",
        schedule_value=None,
        next_run=now,
    )

    await service.run_pending()

    assert submit_calls[0].source == "scheduled"
    assert submit_calls[0].requested_mode == "host"
    assert wait_calls == [submit_calls[0].request_id]
    logs = log_service.list_logs(task.id)
    assert logs[0].status == "success"
    assert logs[0].result == "scheduled reply"


@pytest.mark.asyncio
async def test_run_pending_records_timeout_log_for_coordinator_timeout() -> None:
    from services.execution_coordinator import ExecutionHandle, ExecutionResult
    from services.task_log_service import TaskLogService

    now = datetime(2026, 3, 8, 12, 0, 0)
    log_service = TaskLogService()

    class FakeCoordinator:
        async def submit_execution(self, request):
            return ExecutionHandle(
                run_id=request.request_id or "run-timeout",
                group_folder=request.group_folder,
                status="queued",
            )

        async def wait_for_run(self, run_id: str):
            return ExecutionResult(
                run_id=run_id,
                status="timeout",
                group_folder="group-a",
                backend="openai_runtime",
                session_id="group-a",
                timeout_ms=10,
            )

    service, _scheduler = _build_service(
        now=now,
        execution_coordinator=FakeCoordinator(),
        task_log_service=log_service,
    )
    task = service.create_task(
        group_folder="group-a",
        chat_jid="chat-a",
        prompt="timeout scheduled task",
        schedule_type="once",
        schedule_value=None,
        next_run=now,
    )

    await service.run_pending()

    logs = log_service.list_logs(task.id)
    assert logs[0].status == "timeout"
    assert logs[0].error == "execution timed out"
    assert task.status == "active"
    assert task.next_run == now


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
