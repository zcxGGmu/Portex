"""Persistent registered-group helpers for M7.3.1."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.group import RegisteredGroup


class GroupRegistryService:
    """Thin async service around the current registered-group model."""

    def __init__(self, *, db: AsyncSession) -> None:
        self._db = db

    async def list_registered_groups(self) -> list[RegisteredGroup]:
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
    ) -> RegisteredGroup:
        existing = await self._db.get(RegisteredGroup, jid)
        if existing is not None:
            existing.name = name
            existing.folder = folder
            if created_by is not None:
                existing.created_by = created_by
            await self._db.commit()
            await self._db.refresh(existing)
            return existing

        group = RegisteredGroup(
            jid=jid,
            name=name,
            folder=folder,
            added_at=datetime.utcnow(),
            created_by=created_by,
        )
        self._db.add(group)
        await self._db.commit()
        await self._db.refresh(group)
        return group


__all__ = ["GroupRegistryService"]
