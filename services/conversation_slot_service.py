"""Persistent conversation-slot helpers for M7.3.5."""

from __future__ import annotations

import re

from sqlalchemy import case, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.conversation_slot import ConversationSlot

_SLOT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class ConversationSlotService:
    """Thin async service around the current conversation-slot model."""

    def __init__(self, *, db: AsyncSession) -> None:
        self._db = db

    async def ensure_main_slot(
        self,
        workspace_folder: str,
        *,
        created_by: str | None = None,
    ) -> ConversationSlot:
        await self._ensure_schema()
        existing = await self.get_slot(workspace_folder, "main")
        if existing is not None:
            if existing.created_by is None and created_by is not None:
                existing.created_by = created_by
                await self._db.commit()
                await self._db.refresh(existing)
            return existing

        slot = ConversationSlot(
            workspace_folder=workspace_folder,
            slot_id="main",
            title="Main",
            created_by=created_by,
        )
        self._db.add(slot)
        await self._db.commit()
        await self._db.refresh(slot)
        return slot

    async def create_slot(
        self,
        *,
        workspace_folder: str,
        slot_id: str,
        title: str,
        created_by: str | None = None,
    ) -> ConversationSlot:
        await self._ensure_schema()
        if slot_id == "main":
            raise ValueError("slot_id 'main' is reserved")
        if not _SLOT_ID_PATTERN.fullmatch(slot_id):
            raise ValueError("invalid slot_id")
        existing = await self.get_slot(workspace_folder, slot_id)
        if existing is not None:
            return existing

        slot = ConversationSlot(
            workspace_folder=workspace_folder,
            slot_id=slot_id,
            title=title,
            created_by=created_by,
        )
        self._db.add(slot)
        await self._db.commit()
        await self._db.refresh(slot)
        return slot

    async def list_slots(self, workspace_folder: str) -> list[ConversationSlot]:
        await self._ensure_schema()
        result = await self._db.execute(
            select(ConversationSlot)
            .where(ConversationSlot.workspace_folder == workspace_folder)
            .order_by(
                case((ConversationSlot.slot_id == "main", 0), else_=1),
                ConversationSlot.slot_id,
            )
        )
        return list(result.scalars().all())

    async def get_slot(
        self,
        workspace_folder: str,
        slot_id: str,
    ) -> ConversationSlot | None:
        await self._ensure_schema()
        result = await self._db.execute(
            select(ConversationSlot).where(
                ConversationSlot.workspace_folder == workspace_folder,
                ConversationSlot.slot_id == slot_id,
            )
        )
        return result.scalar_one_or_none()

    async def _ensure_schema(self) -> None:
        await self._db.execute(
            text(
                "CREATE TABLE IF NOT EXISTS conversation_slots ("
                "workspace_folder VARCHAR NOT NULL, "
                "slot_id VARCHAR NOT NULL, "
                "title VARCHAR NOT NULL, "
                "created_by VARCHAR, "
                "created_at DATETIME NOT NULL, "
                "PRIMARY KEY (workspace_folder, slot_id)"
                ")"
            )
        )
        await self._db.commit()


__all__ = ["ConversationSlotService"]
