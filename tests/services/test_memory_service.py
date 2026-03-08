from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _build_service(tmp_path: Path):
    from services import memory as memory_module

    data_dir = tmp_path / "data"
    return memory_module.MemoryService(data_dir=data_dir), data_dir


def _agents_path(data_dir: Path, user_id: str) -> Path:
    return data_dir / "memory" / "user-global" / user_id / "AGENTS.md"


def _claude_path(data_dir: Path, user_id: str) -> Path:
    return data_dir / "memory" / "user-global" / user_id / "CLAUDE.md"


def _daily_path(data_dir: Path, group_folder: str, day: date) -> Path:
    return data_dir / "memory" / group_folder / f"{day.isoformat()}.md"


def _freeze_utc_today(
    monkeypatch: pytest.MonkeyPatch,
    *,
    value: date,
) -> None:
    from services import memory as memory_module

    class _FrozenDateTime:
        @classmethod
        def utcnow(cls) -> datetime:
            return datetime(value.year, value.month, value.day)

    monkeypatch.setattr(memory_module, "datetime", _FrozenDateTime, raising=False)


@pytest.mark.asyncio
async def test_get_user_memory_returns_empty_string_when_agents_file_missing(
    tmp_path: Path,
) -> None:
    service, _data_dir = _build_service(tmp_path)

    content = await service.get_user_memory("user-1")

    assert content == ""


@pytest.mark.asyncio
async def test_update_user_memory_creates_agents_file_in_user_global_directory(
    tmp_path: Path,
) -> None:
    service, data_dir = _build_service(tmp_path)

    await service.update_user_memory("user-1", "first memory entry")

    memory_path = _agents_path(data_dir, "user-1")
    assert memory_path.exists()
    assert memory_path.read_text(encoding="utf-8") == "first memory entry"


@pytest.mark.asyncio
async def test_get_user_memory_reads_back_written_agents_content(
    tmp_path: Path,
) -> None:
    service, _data_dir = _build_service(tmp_path)
    await service.update_user_memory("user-1", "remember this")

    content = await service.get_user_memory("user-1")

    assert content == "remember this"


@pytest.mark.asyncio
async def test_update_user_memory_overwrites_existing_agents_content(
    tmp_path: Path,
) -> None:
    service, data_dir = _build_service(tmp_path)
    await service.update_user_memory("user-1", "old memory")

    await service.update_user_memory("user-1", "new memory")

    memory_path = _agents_path(data_dir, "user-1")
    assert memory_path.read_text(encoding="utf-8") == "new memory"
    assert await service.get_user_memory("user-1") == "new memory"


@pytest.mark.asyncio
async def test_update_user_memory_keeps_agents_files_isolated_per_user(
    tmp_path: Path,
) -> None:
    service, data_dir = _build_service(tmp_path)

    await service.update_user_memory("user-a", "alpha memory")
    await service.update_user_memory("user-b", "beta memory")

    assert _agents_path(data_dir, "user-a").read_text(encoding="utf-8") == "alpha memory"
    assert _agents_path(data_dir, "user-b").read_text(encoding="utf-8") == "beta memory"
    assert await service.get_user_memory("user-a") == "alpha memory"
    assert await service.get_user_memory("user-b") == "beta memory"


@pytest.mark.asyncio
async def test_update_user_memory_does_not_create_legacy_claude_file(
    tmp_path: Path,
) -> None:
    service, data_dir = _build_service(tmp_path)

    await service.update_user_memory("user-1", "agents only")

    assert not _claude_path(data_dir, "user-1").exists()


@pytest.mark.asyncio
async def test_append_daily_memory_creates_expected_dated_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, data_dir = _build_service(tmp_path)
    today = date(2026, 3, 8)
    _freeze_utc_today(monkeypatch, value=today)

    await service.append_daily_memory("group-a", "first entry")

    daily_path = _daily_path(data_dir, "group-a", today)
    assert daily_path.exists()
    assert "first entry" in daily_path.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_append_daily_memory_accumulates_content_in_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, data_dir = _build_service(tmp_path)
    today = date(2026, 3, 8)
    _freeze_utc_today(monkeypatch, value=today)

    await service.append_daily_memory("group-a", "first entry")
    await service.append_daily_memory("group-a", "second entry")

    daily_path = _daily_path(data_dir, "group-a", today)
    content = daily_path.read_text(encoding="utf-8")
    assert content.count("first entry") == 1
    assert content.count("second entry") == 1
    assert content.index("first entry") < content.index("second entry")


@pytest.mark.asyncio
async def test_append_daily_memory_is_isolated_by_group_folder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, data_dir = _build_service(tmp_path)
    today = date(2026, 3, 8)
    _freeze_utc_today(monkeypatch, value=today)

    await service.append_daily_memory("group-a", "alpha")
    await service.append_daily_memory("group-b", "beta")

    group_a_content = _daily_path(data_dir, "group-a", today).read_text(encoding="utf-8")
    group_b_content = _daily_path(data_dir, "group-b", today).read_text(encoding="utf-8")

    assert "alpha" in group_a_content
    assert "beta" not in group_a_content
    assert "beta" in group_b_content
    assert "alpha" not in group_b_content


@pytest.mark.asyncio
async def test_append_daily_memory_does_not_affect_user_agents_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, data_dir = _build_service(tmp_path)
    today = date(2026, 3, 8)
    _freeze_utc_today(monkeypatch, value=today)

    await service.update_user_memory("user-1", "agents only")
    await service.append_daily_memory("group-a", "daily note")

    assert _agents_path(data_dir, "user-1").read_text(encoding="utf-8") == "agents only"
    assert "daily note" in _daily_path(data_dir, "group-a", today).read_text(
        encoding="utf-8"
    )


@pytest.mark.asyncio
async def test_search_memory_returns_matching_markdown_paths_for_target_group(
    tmp_path: Path,
) -> None:
    from services.memory import MemoryService

    data_dir = tmp_path / "data"
    service = MemoryService(data_dir=data_dir)
    match_path = data_dir / "memory" / "group-a" / "2026-03-08.md"
    miss_path = data_dir / "memory" / "group-a" / "2026-03-09.md"
    match_path.parent.mkdir(parents=True, exist_ok=True)
    match_path.write_text("Remember launch checklist", encoding="utf-8")
    miss_path.write_text("unrelated note", encoding="utf-8")

    results = await service.search_memory("group-a", "launch")

    assert results == [str(match_path)]


@pytest.mark.asyncio
async def test_search_memory_is_case_insensitive(tmp_path: Path) -> None:
    from services.memory import MemoryService

    data_dir = tmp_path / "data"
    service = MemoryService(data_dir=data_dir)
    match_path = data_dir / "memory" / "group-a" / "2026-03-08.md"
    match_path.parent.mkdir(parents=True, exist_ok=True)
    match_path.write_text("Remember Launch Checklist", encoding="utf-8")

    results = await service.search_memory("group-a", "launch")

    assert results == [str(match_path)]


@pytest.mark.asyncio
async def test_search_memory_returns_empty_list_for_blank_query(tmp_path: Path) -> None:
    from services.memory import MemoryService

    data_dir = tmp_path / "data"
    service = MemoryService(data_dir=data_dir)

    assert await service.search_memory("group-a", "") == []
    assert await service.search_memory("group-a", "   ") == []


@pytest.mark.asyncio
async def test_search_memory_excludes_other_groups_and_user_agents_files(
    tmp_path: Path,
) -> None:
    from services.memory import MemoryService

    data_dir = tmp_path / "data"
    service = MemoryService(data_dir=data_dir)
    group_match = data_dir / "memory" / "group-a" / "2026-03-08.md"
    other_group = data_dir / "memory" / "group-b" / "2026-03-08.md"
    agents_file = data_dir / "memory" / "user-global" / "user-1" / "AGENTS.md"
    group_match.parent.mkdir(parents=True, exist_ok=True)
    other_group.parent.mkdir(parents=True, exist_ok=True)
    agents_file.parent.mkdir(parents=True, exist_ok=True)
    group_match.write_text("shared keyword", encoding="utf-8")
    other_group.write_text("shared keyword", encoding="utf-8")
    agents_file.write_text("shared keyword", encoding="utf-8")

    results = await service.search_memory("group-a", "shared")

    assert results == [str(group_match)]
