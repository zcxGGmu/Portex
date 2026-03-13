"""Persistent registered-group helpers for M7.3.1."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.group import RegisteredGroup


class GroupRegistryService:
    """Thin async service around the current registered-group model."""

    def __init__(self, *, db: AsyncSession) -> None:
        self._db = db

    async def list_registered_groups(self) -> list[RegisteredGroup]:
        await self._ensure_schema()
        result = await self._db.execute(
            select(RegisteredGroup).order_by(RegisteredGroup.added_at, RegisteredGroup.folder)
        )
        return list(result.scalars().all())

    async def ensure_registered_group(
        self,
        *,
        jid: str,
        name: str,
        folder: str,
        created_by: str | None = None,
        is_home: bool | None = None,
    ) -> RegisteredGroup:
        await self._ensure_schema()
        existing = await self._db.get(RegisteredGroup, jid)
        if existing is not None:
            existing.name = name
            existing.folder = folder
            if existing.created_by is None and created_by is not None:
                existing.created_by = created_by
            if is_home:
                existing.is_home = True
            await self._db.commit()
            await self._db.refresh(existing)
            return existing

        group = RegisteredGroup(
            jid=jid,
            name=name,
            folder=folder,
            added_at=datetime.utcnow(),
            created_by=created_by,
            is_home=bool(is_home),
        )
        self._db.add(group)
        await self._db.commit()
        await self._db.refresh(group)
        return group

    async def ensure_home_workspace(
        self,
        *,
        user_id: str,
        role: str,
        username: str,
    ) -> RegisteredGroup:
        if role == "owner":
            return await self.ensure_registered_group(
                jid="web:main",
                name="Main",
                folder="main",
                created_by=user_id,
                is_home=True,
            )

        return await self.ensure_registered_group(
            jid=f"web:home-{user_id}",
            name=f"{username} Home",
            folder=f"home-{user_id}",
            created_by=user_id,
            is_home=True,
        )

    async def get_web_workspace_by_folder(self, folder: str) -> RegisteredGroup | None:
        await self._ensure_schema()
        result = await self._db.execute(
            select(RegisteredGroup).where(RegisteredGroup.folder == folder)
        )
        groups = [group for group in result.scalars().all() if group.jid.startswith("web:")]
        if not groups:
            return None

        groups.sort(
            key=lambda group: (
                group.added_at,
                group.jid,
            )
        )
        return groups[0]

    async def _ensure_schema(self) -> None:
        await self._db.execute(
            text(
                "CREATE TABLE IF NOT EXISTS registered_groups ("
                "jid VARCHAR PRIMARY KEY, "
                "name VARCHAR NOT NULL, "
                "folder VARCHAR NOT NULL, "
                "added_at DATETIME NOT NULL, "
                "container_config TEXT, "
                "created_by VARCHAR, "
                "is_home BOOLEAN NOT NULL DEFAULT 0"
                ")"
            )
        )
        await self._db.commit()
        result = await self._db.execute(text("PRAGMA table_info('registered_groups')"))
        columns = {row[1] for row in result.all()}
        if columns and "is_home" not in columns:
            await self._db.execute(
                text(
                    "ALTER TABLE registered_groups "
                    "ADD COLUMN is_home BOOLEAN NOT NULL DEFAULT 0"
                )
            )
            await self._db.commit()


__all__ = ["GroupRegistryService"]
