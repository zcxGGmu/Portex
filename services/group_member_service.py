"""In-memory group member management service."""

from __future__ import annotations

from datetime import datetime

from domain.models.group_member import GroupMember

VALID_GROUP_MEMBER_ROLES = ("owner", "admin", "member")


class GroupMemberService:
    """Manage group members using an in-memory store."""

    def __init__(self) -> None:
        self._members_by_group: dict[str, dict[str, GroupMember]] = {}

    def list_members(self, group_id: str) -> list[GroupMember]:
        members = self._members_by_group.get(group_id, {})
        return sorted(members.values(), key=lambda member: member.user_id)

    def add_member(
        self,
        group_id: str,
        user_id: str,
        role: str = "member",
    ) -> GroupMember:
        normalized_role = self._validate_role(role)
        members = self._members_by_group.setdefault(group_id, {})
        existing_member = members.get(user_id)
        joined_at = existing_member.joined_at if existing_member is not None else datetime.utcnow()
        member = GroupMember(
            group_jid=group_id,
            user_id=user_id,
            role=normalized_role,
            joined_at=joined_at,
        )
        members[user_id] = member
        return member

    def remove_member(self, group_id: str, user_id: str) -> bool:
        members = self._members_by_group.get(group_id)
        if members is None or user_id not in members:
            return False

        del members[user_id]
        if not members:
            del self._members_by_group[group_id]
        return True

    def get_member(self, group_id: str, user_id: str) -> GroupMember | None:
        members = self._members_by_group.get(group_id)
        if members is None:
            return None
        return members.get(user_id)

    def get_member_role(self, group_id: str, user_id: str) -> str | None:
        member = self.get_member(group_id, user_id)
        if member is None:
            return None
        return member.role

    def reset(self) -> None:
        self._members_by_group.clear()

    def _validate_role(self, role: str) -> str:
        if role not in VALID_GROUP_MEMBER_ROLES:
            raise ValueError(f"invalid group member role: {role}")
        return role


group_member_service = GroupMemberService()


__all__ = ["GroupMemberService", "VALID_GROUP_MEMBER_ROLES", "group_member_service"]
