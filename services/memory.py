"""User-global memory service backed by per-user ``AGENTS.md`` files."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
USER_MEMORY_FILENAME = "AGENTS.md"


class MemoryService:
    """Manage per-user global memory files under the data directory."""

    def __init__(
        self,
        *,
        data_dir: Path | str | None = None,
        today_func: Callable[[], date] | None = None,
    ) -> None:
        if data_dir is None:
            data_dir = DATA_DIR
        self._data_dir = Path(data_dir)
        self._today_func = today_func or (lambda: datetime.utcnow().date())

    async def get_user_memory(self, user_id: str) -> str:
        memory_path = self._get_user_memory_path(user_id)
        if not memory_path.exists():
            return ""
        return await asyncio.to_thread(memory_path.read_text, encoding="utf-8")

    async def update_user_memory(self, user_id: str, content: str) -> None:
        memory_path = self._get_user_memory_path(user_id)
        await asyncio.to_thread(memory_path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(memory_path.write_text, content, encoding="utf-8")

    async def append_daily_memory(self, group_folder: str, content: str) -> None:
        daily_memory_path = self._get_daily_memory_path(group_folder)
        await asyncio.to_thread(daily_memory_path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(
            self._append_text,
            daily_memory_path,
            f"\n{content}\n",
        )

    def _get_user_memory_path(self, user_id: str) -> Path:
        return self._data_dir / "memory" / "user-global" / user_id / USER_MEMORY_FILENAME

    def _get_daily_memory_path(self, group_folder: str) -> Path:
        return self._data_dir / "memory" / group_folder / f"{self._today_func().isoformat()}.md"

    def _append_text(self, path: Path, content: str) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(content)


memory_service = MemoryService()


__all__ = ["MemoryService", "USER_MEMORY_FILENAME", "memory_service"]
