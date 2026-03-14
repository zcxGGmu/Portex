"""Persistent workspace membership service."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.group_member import GroupMember

VALID_GROUP_MEMBER_ROLES = ("owner", "admin", "member")


class GroupMemberService:
    """Manage workspace members through the database."""

    def __init__(self, *, db: AsyncSession) -> None:
        self._db = db

    async def list_members(self, group_folder: str) -> list[GroupMember]:
        await self._ensure_schema()
        result = await self._db.execute(
            select(GroupMember)
            .where(GroupMember.group_folder == group_folder)
            .order_by(GroupMember.user_id)
        )
        return list(result.scalars().all())

    async def add_member(
        self,
        group_folder: str,
        user_id: str,
        role: str = "member",
        *,
        added_by: str | None = None,
    ) -> GroupMember:
        await self._ensure_schema()
        normalized_role = self._validate_role(role)
        existing_member = await self.get_member(group_folder, user_id)

        if normalized_role == "owner":
            if existing_member is not None and existing_member.role != "owner":
                raise ValueError("owner role changes are not supported")
        elif existing_member is not None and existing_member.role == "owner":
            raise ValueError("owner role changes are not supported")

        joined_at = existing_member.joined_at if existing_member is not None else datetime.utcnow()
        member = GroupMember(
            group_folder=group_folder,
            user_id=user_id,
            role=normalized_role,
            joined_at=joined_at,
            added_by=existing_member.added_by if existing_member is not None else added_by,
        )
        await self._db.merge(member)
        await self._db.commit()

        persisted_member = await self.get_member(group_folder, user_id)
        if persisted_member is None:
            raise RuntimeError("failed to persist group member")
        return persisted_member

    async def remove_member(self, group_folder: str, user_id: str) -> bool:
        await self._ensure_schema()
        member = await self.get_member(group_folder, user_id)
        if member is None:
            return False
        if member.role == "owner":
            raise ValueError("group owner cannot be removed")

        await self._db.delete(member)
        await self._db.commit()
        return True

    async def get_member(self, group_folder: str, user_id: str) -> GroupMember | None:
        await self._ensure_schema()
        result = await self._db.execute(
            select(GroupMember).where(
                GroupMember.group_folder == group_folder,
                GroupMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_member_role(self, group_folder: str, user_id: str) -> str | None:
        member = await self.get_member(group_folder, user_id)
        if member is None:
            return None
        return member.role

    async def _ensure_schema(self) -> None:
        await self._db.execute(
            text(
                "CREATE TABLE IF NOT EXISTS group_members ("
                "group_folder VARCHAR NOT NULL, "
                "user_id VARCHAR NOT NULL, "
                "role VARCHAR NOT NULL, "
                "joined_at DATETIME NOT NULL, "
                "added_by VARCHAR, "
                "PRIMARY KEY (group_folder, user_id)"
                ")"
            )
        )
        await self._db.commit()

        result = await self._db.execute(text("PRAGMA table_info('group_members')"))
        columns = {row[1] for row in result.all()}
        legacy_columns = {"group_jid", "group_folder"} & columns

        if "group_jid" in columns:
            source_group_expr = "COALESCE(group_folder, group_jid)" if "group_folder" in columns else "group_jid"
            added_by_expr = "added_by" if "added_by" in columns else "NULL"
            await self._db.execute(text("DROP TABLE IF EXISTS group_members_new"))
            await self._db.execute(
                text(
                    "CREATE TABLE group_members_new ("
                    "group_folder VARCHAR NOT NULL, "
                    "user_id VARCHAR NOT NULL, "
                    "role VARCHAR NOT NULL, "
                    "joined_at DATETIME NOT NULL, "
                    "added_by VARCHAR, "
                    "PRIMARY KEY (group_folder, user_id)"
                    ")"
                )
            )
            await self._db.execute(
                text(
                    "INSERT OR IGNORE INTO group_members_new "
                    "(group_folder, user_id, role, joined_at, added_by) "
                    "SELECT "
                    f"{source_group_expr}, user_id, role, joined_at, {added_by_expr} "
                    "FROM group_members"
                )
            )
            await self._db.execute(text("DROP TABLE group_members"))
            await self._db.execute(text("ALTER TABLE group_members_new RENAME TO group_members"))
            await self._db.commit()
            return

        if "group_folder" not in legacy_columns:
            await self._db.execute(
                text(
                    "ALTER TABLE group_members "
                    "ADD COLUMN group_folder VARCHAR"
                )
            )
        if "added_by" not in columns:
            await self._db.execute(
                text(
                    "ALTER TABLE group_members "
                    "ADD COLUMN added_by VARCHAR"
                )
            )
        await self._db.commit()

    def _validate_role(self, role: str) -> str:
        if role not in VALID_GROUP_MEMBER_ROLES:
            raise ValueError(f"invalid group member role: {role}")
        return role


__all__ = ["GroupMemberService", "VALID_GROUP_MEMBER_ROLES"]
