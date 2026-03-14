"""Filesystem-backed skills service."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil

from infra.exec.security import validate_path


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SKILLS_DIRNAME = "skills"
SKILL_FILENAME = "SKILL.md"
DISABLED_SKILL_FILENAME = "SKILL.md.disabled"
MAX_SKILL_FILE_SIZE_BYTES = 256 * 1024
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True, slots=True)
class SkillEntry:
    skill_id: str
    enabled: bool
    updated_at: datetime
    size: int


@dataclass(frozen=True, slots=True)
class SkillDetail:
    skill_id: str
    enabled: bool
    updated_at: datetime
    size: int
    content: str


class SkillsService:
    """Manage user-owned skills under ``data/skills/{user_id}``."""

    def __init__(
        self,
        *,
        data_dir: str | Path | None = None,
        max_skill_file_size_bytes: int = MAX_SKILL_FILE_SIZE_BYTES,
    ) -> None:
        root = Path(data_dir or DATA_DIR).expanduser().resolve()
        self._skills_root = (root / SKILLS_DIRNAME).resolve()
        self._skills_root.mkdir(parents=True, exist_ok=True)
        self._max_skill_file_size_bytes = max_skill_file_size_bytes

    async def list_user_skills(self, user_id: str) -> list[SkillEntry]:
        return await asyncio.to_thread(self._list_user_skills, user_id)

    async def get_user_skill(self, user_id: str, skill_id: str) -> SkillDetail:
        return await asyncio.to_thread(self._get_user_skill, user_id, skill_id)

    async def upsert_user_skill(self, user_id: str, skill_id: str, content: str) -> SkillDetail:
        return await asyncio.to_thread(self._upsert_user_skill, user_id, skill_id, content)

    async def set_user_skill_enabled(self, user_id: str, skill_id: str, *, enabled: bool) -> SkillDetail:
        return await asyncio.to_thread(self._set_user_skill_enabled, user_id, skill_id, enabled)

    async def delete_user_skill(self, user_id: str, skill_id: str) -> None:
        await asyncio.to_thread(self._delete_user_skill, user_id, skill_id)

    def _list_user_skills(self, user_id: str) -> list[SkillEntry]:
        user_root = self._user_root(user_id)
        entries: list[SkillEntry] = []
        for candidate in sorted(user_root.iterdir(), key=lambda item: item.name.lower()):
            if not candidate.is_dir():
                continue
            if not validate_path(candidate.resolve(strict=False), [user_root]):
                raise ValueError("symlink traversal detected")
            file_path, enabled = self._resolve_skill_file(candidate)
            if file_path is None:
                continue
            entries.append(
                self._build_skill_entry(
                    skill_id=candidate.name,
                    enabled=enabled,
                    file_path=file_path,
                    skill_root=candidate,
                )
            )
        return entries

    def _get_user_skill(self, user_id: str, skill_id: str) -> SkillDetail:
        skill_dir = self._skill_dir(user_id, skill_id)
        if not skill_dir.exists() or not skill_dir.is_dir():
            raise FileNotFoundError("skill not found")

        file_path, enabled = self._resolve_skill_file(skill_dir)
        if file_path is None:
            raise FileNotFoundError("skill not found")
        self._ensure_safe_skill_file(file_path, skill_dir)
        stats = file_path.stat()
        if stats.st_size > self._max_skill_file_size_bytes:
            raise ValueError("skill file exceeds size limit")

        return SkillDetail(
            skill_id=skill_dir.name,
            enabled=enabled,
            updated_at=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc),
            size=stats.st_size,
            content=file_path.read_text(encoding="utf-8"),
        )

    def _upsert_user_skill(self, user_id: str, skill_id: str, content: str) -> SkillDetail:
        encoded = content.encode("utf-8")
        if len(encoded) > self._max_skill_file_size_bytes:
            raise ValueError("skill content exceeds size limit")

        skill_dir = self._skill_dir(user_id, skill_id)
        skill_dir.mkdir(parents=True, exist_ok=True)
        if not validate_path(skill_dir.resolve(strict=False), [self._user_root(user_id)]):
            raise ValueError("symlink traversal detected")

        existing_file, existing_enabled = self._resolve_skill_file(skill_dir)
        if existing_file is not None:
            target = existing_file
            enabled = existing_enabled
        else:
            target = skill_dir / SKILL_FILENAME
            enabled = True

        if target.exists() and target.is_dir():
            raise IsADirectoryError("skill path is a directory")

        target.write_text(content, encoding="utf-8")
        return self._get_user_skill(user_id, skill_id=skill_id)

    def _set_user_skill_enabled(self, user_id: str, skill_id: str, enabled: bool) -> SkillDetail:
        skill_dir = self._skill_dir(user_id, skill_id)
        if not skill_dir.exists() or not skill_dir.is_dir():
            raise FileNotFoundError("skill not found")

        current_file, current_enabled = self._resolve_skill_file(skill_dir)
        if current_file is None:
            raise FileNotFoundError("skill not found")

        if current_enabled != enabled:
            target = skill_dir / (SKILL_FILENAME if enabled else DISABLED_SKILL_FILENAME)
            if target.exists() and target.is_dir():
                raise IsADirectoryError("skill path is a directory")
            if target.exists():
                target.unlink()
            current_file.rename(target)

        return self._get_user_skill(user_id, skill_id)

    def _delete_user_skill(self, user_id: str, skill_id: str) -> None:
        skill_dir = self._skill_dir(user_id, skill_id)
        if not skill_dir.exists() or not skill_dir.is_dir():
            raise FileNotFoundError("skill not found")
        if not validate_path(skill_dir.resolve(strict=False), [self._user_root(user_id)]):
            raise ValueError("symlink traversal detected")
        shutil.rmtree(skill_dir)

    def _user_root(self, user_id: str) -> Path:
        safe_user_id = self._validate_segment(user_id, label="user id")
        user_root = (self._skills_root / safe_user_id).resolve()
        if not validate_path(user_root, [self._skills_root]):
            raise ValueError("invalid user id")
        user_root.mkdir(parents=True, exist_ok=True)
        return user_root

    def _skill_dir(self, user_id: str, skill_id: str) -> Path:
        user_root = self._user_root(user_id)
        safe_skill_id = self._validate_segment(skill_id, label="skill id")
        skill_dir = user_root / safe_skill_id
        if not validate_path(skill_dir.resolve(strict=False), [user_root]):
            raise ValueError("symlink traversal detected")
        return skill_dir

    def _resolve_skill_file(self, skill_dir: Path) -> tuple[Path | None, bool]:
        enabled_path = skill_dir / SKILL_FILENAME
        disabled_path = skill_dir / DISABLED_SKILL_FILENAME

        if enabled_path.exists():
            self._ensure_safe_skill_file(enabled_path, skill_dir)
            return enabled_path, True
        if disabled_path.exists():
            self._ensure_safe_skill_file(disabled_path, skill_dir)
            return disabled_path, False
        return None, False

    def _build_skill_entry(
        self,
        *,
        skill_id: str,
        enabled: bool,
        file_path: Path,
        skill_root: Path,
    ) -> SkillEntry:
        self._ensure_safe_skill_file(file_path, skill_root)
        stats = file_path.stat()
        if stats.st_size > self._max_skill_file_size_bytes:
            raise ValueError("skill file exceeds size limit")

        return SkillEntry(
            skill_id=skill_id,
            enabled=enabled,
            updated_at=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc),
            size=stats.st_size,
        )

    def _ensure_safe_skill_file(self, file_path: Path, skill_root: Path) -> None:
        if not validate_path(file_path.resolve(strict=False), [skill_root]):
            raise ValueError("symlink traversal detected")
        if file_path.name not in {SKILL_FILENAME, DISABLED_SKILL_FILENAME}:
            raise ValueError("unexpected skill file name")

    def _validate_segment(self, value: str, *, label: str) -> str:
        normalized = (value or "").strip()
        if not _SAFE_SEGMENT.fullmatch(normalized):
            raise ValueError(f"invalid {label}")
        return normalized


skills_service = SkillsService()


__all__ = [
    "DISABLED_SKILL_FILENAME",
    "MAX_SKILL_FILE_SIZE_BYTES",
    "SKILL_FILENAME",
    "SkillDetail",
    "SkillEntry",
    "SkillsService",
    "skills_service",
]
