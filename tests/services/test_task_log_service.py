from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_record_log_and_list_logs_returns_most_recent_first() -> None:
    from services.task_log_service import TaskLogService

    service = TaskLogService()
    now = datetime(2026, 3, 8, 12, 0, 0)

    older = service.record_log(
        task_id="task-1",
        run_at=now,
        duration_ms=150,
        status="success",
        result="ok",
    )
    newer = service.record_log(
        task_id="task-1",
        run_at=now + timedelta(minutes=1),
        duration_ms=25,
        status="error",
        result="boom",
    )

    logs = service.list_logs("task-1")

    assert [log.id for log in logs] == [newer.id, older.id]


def test_list_logs_applies_limit_per_task() -> None:
    from services.task_log_service import TaskLogService

    service = TaskLogService()
    now = datetime(2026, 3, 8, 12, 0, 0)

    service.record_log(
        task_id="task-1",
        run_at=now,
        duration_ms=10,
        status="success",
        result=None,
    )
    second = service.record_log(
        task_id="task-1",
        run_at=now + timedelta(seconds=1),
        duration_ms=20,
        status="success",
        result=None,
    )
    service.record_log(
        task_id="task-2",
        run_at=now + timedelta(seconds=2),
        duration_ms=30,
        status="success",
        result=None,
    )

    logs = service.list_logs("task-1", limit=1)

    assert [log.id for log in logs] == [second.id]
