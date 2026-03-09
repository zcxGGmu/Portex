from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.mark.parametrize(
    ("user_role", "group_config", "expected"),
    [
        ("admin", {"host_mode": True}, "host"),
        ("admin", {"host_mode": False}, "container"),
        ("member", {"host_mode": True}, "container"),
        ("guest", {}, "container"),
    ],
)
def test_get_execution_mode_respects_admin_host_mode_rule(
    user_role: str,
    group_config: dict[str, object],
    expected: str,
) -> None:
    from services.execution_mode import get_execution_mode

    assert get_execution_mode(user_role, group_config) == expected


def test_memory_service_builds_expected_user_and_daily_paths(tmp_path: Path) -> None:
    from services.memory import MemoryService, USER_MEMORY_FILENAME

    frozen_day = date(2026, 3, 9)
    data_dir = tmp_path / "data"
    service = MemoryService(data_dir=data_dir, today_func=lambda: frozen_day)

    assert service._get_user_memory_path("user-1") == (
        data_dir / "memory" / "user-global" / "user-1" / USER_MEMORY_FILENAME
    )
    assert service._get_daily_memory_path("group-a") == (
        data_dir / "memory" / "group-a" / "2026-03-09.md"
    )
    assert service._get_group_memory_dir("group-a") == data_dir / "memory" / "group-a"


@pytest.mark.asyncio
async def test_memory_service_search_memory_short_circuits_blank_query(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from services.memory import MemoryService

    service = MemoryService(data_dir=tmp_path / "data")

    def fail_if_called(group_folder: str, query: str) -> list[str]:
        raise AssertionError(f"unexpected scan for {group_folder}:{query}")

    monkeypatch.setattr(service, "_search_group_memory_files", fail_if_called)

    assert await service.search_memory("group-a", "") == []
    assert await service.search_memory("group-a", "   ") == []
