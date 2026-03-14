"""User-global memory service backed by per-user ``AGENTS.md`` files."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from infra.exec.security import validate_path


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
USER_MEMORY_FILENAME = "AGENTS.md"
MAX_GROUP_MEMORY_FILE_SIZE_BYTES = 1 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class GroupMemoryFileEntry:
    path: str
    name: str
    updated_at: datetime
    size: int


@dataclass(frozen=True, slots=True)
class GroupMemoryFileContent:
    path: str
    content: str
    updated_at: datetime | None
    size: int


class MemoryService:
    """Manage per-user global memory files under the data directory."""

    def __init__(
        self,
        *,
        data_dir: Path | str | None = None,
        today_func: Callable[[], date] | None = None,
        max_group_memory_file_size_bytes: int = MAX_GROUP_MEMORY_FILE_SIZE_BYTES,
    ) -> None:
        if data_dir is None:
            data_dir = DATA_DIR
        self._data_dir = Path(data_dir)
        self._today_func = today_func or (lambda: datetime.utcnow().date())
        self._user_memory_cache: dict[str, str] = {}
        self._max_group_memory_file_size_bytes = max_group_memory_file_size_bytes

    async def get_user_memory(self, user_id: str) -> str:
        if user_id in self._user_memory_cache:
            return self._user_memory_cache[user_id]

        memory_path = self._get_user_memory_path(user_id)
        if not memory_path.exists():
            self._user_memory_cache[user_id] = ""
            return ""

        content = await asyncio.to_thread(memory_path.read_text, encoding="utf-8")
        self._user_memory_cache[user_id] = content
        return content

    async def update_user_memory(self, user_id: str, content: str) -> None:
        memory_path = self._get_user_memory_path(user_id)
        await asyncio.to_thread(memory_path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(memory_path.write_text, content, encoding="utf-8")
        self._user_memory_cache[user_id] = content

    async def append_daily_memory(self, group_folder: str, content: str) -> None:
        daily_memory_path = self._get_daily_memory_path(group_folder)
        await asyncio.to_thread(daily_memory_path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(
            self._append_text,
            daily_memory_path,
            f"\n{content}\n",
        )

    async def search_memory(self, group_folder: str, query: str) -> list[str]:
        normalized_query = query.strip().lower()
        if normalized_query == "":
            return []
        return await asyncio.to_thread(
            self._search_group_memory_files,
            group_folder,
            normalized_query,
        )

    async def list_group_memory_files(self, group_folder: str) -> list[GroupMemoryFileEntry]:
        return await asyncio.to_thread(self._list_group_memory_files, group_folder)

    async def get_group_memory_file(
        self,
        group_folder: str,
        relative_path: str,
    ) -> GroupMemoryFileContent:
        return await asyncio.to_thread(
            self._get_group_memory_file,
            group_folder,
            relative_path,
        )

    async def update_group_memory_file(
        self,
        group_folder: str,
        relative_path: str,
        content: str,
    ) -> GroupMemoryFileContent:
        return await asyncio.to_thread(
            self._update_group_memory_file,
            group_folder,
            relative_path,
            content,
        )

    def get_user_memory_metadata(self, user_id: str) -> tuple[datetime | None, int]:
        memory_path = self._get_user_memory_path(user_id)
        if not memory_path.exists():
            return None, 0
        stats = memory_path.stat()
        return datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc), stats.st_size

    def _get_user_memory_path(self, user_id: str) -> Path:
        return self._data_dir / "memory" / "user-global" / user_id / USER_MEMORY_FILENAME

    def _get_daily_memory_path(self, group_folder: str) -> Path:
        return self._get_group_memory_dir(group_folder) / f"{self._today_func().isoformat()}.md"

    def _get_group_memory_dir(self, group_folder: str) -> Path:
        memory_root = (self._data_dir / "memory").resolve()
        candidate = (memory_root / group_folder).resolve()
        if not validate_path(candidate, [memory_root]):
            raise ValueError("invalid group memory root")
        return candidate

    def _append_text(self, path: Path, content: str) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(content)

    def _search_group_memory_files(self, group_folder: str, query: str) -> list[str]:
        memory_dir = self._get_group_memory_dir(group_folder)
        if not memory_dir.exists():
            return []

        matches: list[str] = []
        for path in sorted(memory_dir.rglob("*.md")):
            if not path.is_file():
                continue
            if not validate_path(path.resolve(strict=False), [memory_dir]):
                raise ValueError("symlink traversal detected")
            content = path.read_text(encoding="utf-8")
            if query in content.lower():
                matches.append(path.relative_to(memory_dir).as_posix())
        return matches

    def _list_group_memory_files(self, group_folder: str) -> list[GroupMemoryFileEntry]:
        memory_dir = self._get_group_memory_dir(group_folder)
        if not memory_dir.exists():
            return []

        entries: list[GroupMemoryFileEntry] = []
        for path in sorted(memory_dir.rglob("*.md")):
            if not path.is_file():
                continue
            if not validate_path(path.resolve(strict=False), [memory_dir]):
                raise ValueError("symlink traversal detected")
            stats = path.stat()
            entries.append(
                GroupMemoryFileEntry(
                    path=path.relative_to(memory_dir).as_posix(),
                    name=path.name,
                    updated_at=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc),
                    size=stats.st_size,
                )
            )
        return entries

    def _get_group_memory_file(self, group_folder: str, relative_path: str) -> GroupMemoryFileContent:
        memory_dir, candidate, normalized_path = self._resolve_group_memory_file(
            group_folder,
            relative_path,
        )
        if not candidate.exists():
            return GroupMemoryFileContent(
                path=normalized_path,
                content="",
                updated_at=None,
                size=0,
            )
        if candidate.is_dir():
            raise IsADirectoryError("path is a directory")

        stats = candidate.stat()
        if stats.st_size > self._max_group_memory_file_size_bytes:
            raise ValueError("memory file exceeds size limit")
        return GroupMemoryFileContent(
            path=normalized_path,
            content=candidate.read_text(encoding="utf-8"),
            updated_at=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc),
            size=stats.st_size,
        )

    def _update_group_memory_file(
        self,
        group_folder: str,
        relative_path: str,
        content: str,
    ) -> GroupMemoryFileContent:
        memory_dir, candidate, normalized_path = self._resolve_group_memory_file(
            group_folder,
            relative_path,
        )
        encoded = content.encode("utf-8")
        if len(encoded) > self._max_group_memory_file_size_bytes:
            raise ValueError("memory content exceeds size limit")
        if candidate.exists() and candidate.is_dir():
            raise IsADirectoryError("path is a directory")

        candidate.parent.mkdir(parents=True, exist_ok=True)
        if not validate_path(candidate.parent.resolve(strict=False), [memory_dir]):
            raise ValueError("symlink traversal detected")
        candidate.write_text(content, encoding="utf-8")
        stats = candidate.stat()
        return GroupMemoryFileContent(
            path=normalized_path,
            content=content,
            updated_at=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc),
            size=stats.st_size,
        )

    def _resolve_group_memory_file(
        self,
        group_folder: str,
        relative_path: str,
    ) -> tuple[Path, Path, str]:
        memory_dir = self._get_group_memory_dir(group_folder)
        normalized_path = self._normalize_group_memory_relative_path(relative_path)
        candidate = memory_dir / normalized_path
        if not validate_path(candidate.resolve(strict=False), [memory_dir]):
            if ".." in Path(relative_path).parts:
                raise ValueError("path traversal detected")
            raise ValueError("symlink traversal detected")
        return memory_dir, candidate, normalized_path

    def _normalize_group_memory_relative_path(self, relative_path: str) -> str:
        normalized = (relative_path or "").strip().strip("/")
        if normalized in {"", "."}:
            raise ValueError("memory file path is required")
        normalized = Path(normalized).as_posix()
        if Path(normalized).suffix.lower() != ".md":
            raise ValueError("only markdown memory files are supported")
        return normalized


memory_service = MemoryService()


__all__ = [
    "GroupMemoryFileContent",
    "GroupMemoryFileEntry",
    "MAX_GROUP_MEMORY_FILE_SIZE_BYTES",
    "MemoryService",
    "USER_MEMORY_FILENAME",
    "memory_service",
]
