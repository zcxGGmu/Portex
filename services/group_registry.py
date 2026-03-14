"""Persistent registered-group helpers for M7.3.1."""

from __future__ import annotations

from datetime import datetime
from typing import Final

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.group import RegisteredGroup
from services.conversation_slot_service import ConversationSlotService
from services.group_member_service import GroupMemberService

_UNSET: Final = object()


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

    async def get_registered_group(self, jid: str) -> RegisteredGroup | None:
        await self._ensure_schema()
        return await self._db.get(RegisteredGroup, jid)

    async def ensure_im_endpoint(
        self,
        *,
        jid: str,
        name: str,
        folder: str,
    ) -> RegisteredGroup:
        await self._ensure_schema()
        existing = await self._db.get(RegisteredGroup, jid)
        if existing is not None:
            await self._ensure_main_slot_for_workspace(existing)
            return existing

        return await self.ensure_registered_group(
            jid=jid,
            name=name,
            folder=folder,
        )

    async def ensure_registered_group(
        self,
        *,
        jid: str,
        name: str,
        folder: str,
        created_by: str | None = None,
        is_home: bool | None = None,
        target_workspace_jid: str | None | object = _UNSET,
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
            if target_workspace_jid is not _UNSET:
                existing.target_workspace_jid = target_workspace_jid
            await self._db.commit()
            await self._db.refresh(existing)
            await self._ensure_main_slot_for_workspace(existing)
            return existing

        group = RegisteredGroup(
            jid=jid,
            name=name,
            folder=folder,
            added_at=datetime.utcnow(),
            created_by=created_by,
            is_home=bool(is_home),
            target_workspace_jid=None
            if target_workspace_jid is _UNSET
            else target_workspace_jid,
        )
        self._db.add(group)
        await self._db.commit()
        await self._db.refresh(group)
        await self._ensure_main_slot_for_workspace(group)
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
        workspace = groups[0]
        await self._ensure_main_slot_for_workspace(workspace)
        return workspace

    async def resolve_im_workspace(self, *, jid: str) -> RegisteredGroup | None:
        endpoint = await self.get_registered_group(jid)
        if endpoint is None:
            return None
        if endpoint.target_workspace_jid:
            bound_workspace = await self.get_registered_group(endpoint.target_workspace_jid)
            if bound_workspace is not None and bound_workspace.jid.startswith("web:"):
                return bound_workspace
        return endpoint

    async def user_can_access_group(
        self,
        *,
        user_id: str,
        user_role: str | None = None,
        group: RegisteredGroup,
    ) -> bool:
        await self._ensure_schema()
        if group.is_home:
            if group.jid == "web:main" and group.folder == "main" and user_role == "owner":
                return True
            return group.created_by == user_id

        if group.jid.startswith("web:"):
            if group.created_by == user_id:
                return True
            return await self._is_member(group.folder, user_id)

        if group.target_workspace_jid:
            bound_workspace = await self.resolve_im_workspace(jid=group.jid)
            if bound_workspace is not None and bound_workspace.jid != group.jid:
                return await self.user_can_access_group(
                    user_id=user_id,
                    user_role=user_role,
                    group=bound_workspace,
                )

        return group.created_by == user_id

    async def user_can_manage_members(
        self,
        *,
        user_id: str,
        group: RegisteredGroup,
    ) -> bool:
        await self._ensure_schema()
        if group.is_home:
            return False
        if not group.jid.startswith("web:"):
            return False
        return group.created_by == user_id

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
                "is_home BOOLEAN NOT NULL DEFAULT 0, "
                "target_workspace_jid VARCHAR"
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
        if columns and "target_workspace_jid" not in columns:
            await self._db.execute(
                text(
                    "ALTER TABLE registered_groups "
                    "ADD COLUMN target_workspace_jid VARCHAR"
                )
            )
            await self._db.commit()

    async def _is_member(self, group_folder: str, user_id: str) -> bool:
        member_service = GroupMemberService(db=self._db)
        return await member_service.get_member(group_folder, user_id) is not None

    async def _ensure_main_slot_for_workspace(self, group: RegisteredGroup) -> None:
        slot_service = ConversationSlotService(db=self._db)
        await slot_service.ensure_main_slot(group.folder, created_by=group.created_by)


__all__ = ["GroupRegistryService"]
