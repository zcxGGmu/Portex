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
async def test_get_user_memory_caches_missing_agents_file_lookup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, _data_dir = _build_service(tmp_path)

    class _MissingMemoryPath:
        def __init__(self) -> None:
            self.exists_calls = 0

        def exists(self) -> bool:
            self.exists_calls += 1
            return False

        def read_text(self, *, encoding: str) -> str:
            raise AssertionError("read_text should not be called for a missing file")

    memory_path = _MissingMemoryPath()
    monkeypatch.setattr(service, "_get_user_memory_path", lambda user_id: memory_path)

    first = await service.get_user_memory("user-1")
    second = await service.get_user_memory("user-1")

    assert first == ""
    assert second == ""
    assert memory_path.exists_calls == 1


@pytest.mark.asyncio
async def test_get_user_memory_caches_existing_agents_file_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, _data_dir = _build_service(tmp_path)

    class _ExistingMemoryPath:
        def __init__(self) -> None:
            self.read_text_calls = 0

        def exists(self) -> bool:
            return True

        def read_text(self, *, encoding: str) -> str:
            self.read_text_calls += 1
            return "remember this"

    memory_path = _ExistingMemoryPath()
    monkeypatch.setattr(service, "_get_user_memory_path", lambda user_id: memory_path)

    first = await service.get_user_memory("user-1")
    second = await service.get_user_memory("user-1")

    assert first == "remember this"
    assert second == "remember this"
    assert memory_path.read_text_calls == 1


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
async def test_update_user_memory_refreshes_cached_content_after_external_stale_write(
    tmp_path: Path,
) -> None:
    service, data_dir = _build_service(tmp_path)
    memory_path = _agents_path(data_dir, "user-1")
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text("old", encoding="utf-8")

    assert await service.get_user_memory("user-1") == "old"

    await service.update_user_memory("user-1", "new")
    memory_path.write_text("stale", encoding="utf-8")

    assert await service.get_user_memory("user-1") == "new"


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

    assert results == ["2026-03-08.md"]


@pytest.mark.asyncio
async def test_search_memory_is_case_insensitive(tmp_path: Path) -> None:
    from services.memory import MemoryService

    data_dir = tmp_path / "data"
    service = MemoryService(data_dir=data_dir)
    match_path = data_dir / "memory" / "group-a" / "2026-03-08.md"
    match_path.parent.mkdir(parents=True, exist_ok=True)
    match_path.write_text("Remember Launch Checklist", encoding="utf-8")

    results = await service.search_memory("group-a", "launch")

    assert results == ["2026-03-08.md"]


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

    assert results == ["2026-03-08.md"]


@pytest.mark.asyncio
async def test_list_group_memory_files_returns_markdown_files_only(
    tmp_path: Path,
) -> None:
    service, data_dir = _build_service(tmp_path)
    group_root = data_dir / "memory" / "group-a"
    (group_root / "nested").mkdir(parents=True, exist_ok=True)
    (group_root / "2026-03-08.md").write_text("daily", encoding="utf-8")
    (group_root / "nested" / "notes.md").write_text("nested", encoding="utf-8")
    (group_root / "ignore.txt").write_text("ignored", encoding="utf-8")

    files = await service.list_group_memory_files("group-a")

    assert [entry.path for entry in files] == ["2026-03-08.md", "nested/notes.md"]
    assert [entry.name for entry in files] == ["2026-03-08.md", "notes.md"]
    assert all(entry.size > 0 for entry in files)
    assert all(entry.updated_at is not None for entry in files)


@pytest.mark.asyncio
async def test_list_group_memory_files_rejects_symlink_escape(
    tmp_path: Path,
) -> None:
    service, data_dir = _build_service(tmp_path)
    group_root = data_dir / "memory" / "group-a"
    outside_root = data_dir / "outside"
    outside_root.mkdir(parents=True, exist_ok=True)
    (outside_root / "secret.md").write_text("secret", encoding="utf-8")
    group_root.mkdir(parents=True, exist_ok=True)
    (group_root / "link.md").symlink_to(outside_root / "secret.md")

    with pytest.raises(ValueError, match="symlink traversal detected"):
        await service.list_group_memory_files("group-a")


@pytest.mark.asyncio
async def test_get_group_memory_file_returns_empty_for_missing_but_valid_path(
    tmp_path: Path,
) -> None:
    service, _data_dir = _build_service(tmp_path)

    memory_file = await service.get_group_memory_file("group-a", "2026-03-08.md")

    assert memory_file.path == "2026-03-08.md"
    assert memory_file.content == ""
    assert memory_file.size == 0
    assert memory_file.updated_at is None


@pytest.mark.asyncio
async def test_update_group_memory_file_writes_and_get_reads_back(
    tmp_path: Path,
) -> None:
    service, _data_dir = _build_service(tmp_path)

    updated = await service.update_group_memory_file("group-a", "notes/today.md", "remember this")
    fetched = await service.get_group_memory_file("group-a", "notes/today.md")

    assert updated.path == "notes/today.md"
    assert updated.content == "remember this"
    assert updated.size == len("remember this".encode("utf-8"))
    assert updated.updated_at is not None
    assert fetched.path == "notes/today.md"
    assert fetched.content == "remember this"
    assert fetched.size == len("remember this".encode("utf-8"))
    assert fetched.updated_at is not None


@pytest.mark.asyncio
async def test_group_memory_file_rejects_path_traversal(
    tmp_path: Path,
) -> None:
    service, _data_dir = _build_service(tmp_path)

    with pytest.raises(ValueError, match="path traversal detected"):
        await service.get_group_memory_file("group-a", "../escape.md")

    with pytest.raises(ValueError, match="path traversal detected"):
        await service.update_group_memory_file("group-a", "../escape.md", "x")


@pytest.mark.asyncio
async def test_group_memory_file_rejects_symlink_escape_for_direct_read(
    tmp_path: Path,
) -> None:
    service, data_dir = _build_service(tmp_path)
    group_root = data_dir / "memory" / "group-a"
    outside_root = data_dir / "outside"
    outside_root.mkdir(parents=True, exist_ok=True)
    (outside_root / "secret.md").write_text("secret", encoding="utf-8")
    group_root.mkdir(parents=True, exist_ok=True)
    (group_root / "link.md").symlink_to(outside_root / "secret.md")

    with pytest.raises(ValueError, match="symlink traversal detected"):
        await service.get_group_memory_file("group-a", "link.md")


@pytest.mark.asyncio
async def test_group_memory_file_rejects_non_markdown_extension(
    tmp_path: Path,
) -> None:
    service, _data_dir = _build_service(tmp_path)

    with pytest.raises(ValueError, match="only markdown memory files are supported"):
        await service.get_group_memory_file("group-a", "notes.txt")

    with pytest.raises(ValueError, match="only markdown memory files are supported"):
        await service.update_group_memory_file("group-a", "notes.txt", "x")
