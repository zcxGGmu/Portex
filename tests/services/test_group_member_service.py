from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def reset_group_member_service() -> None:
    from services.group_member_service import group_member_service

    group_member_service.reset()
    yield
    group_member_service.reset()


def test_add_member_uses_default_role_and_sets_joined_at() -> None:
    from services.group_member_service import group_member_service

    member = group_member_service.add_member("group-demo", "user-1")

    assert member.group_jid == "group-demo"
    assert member.user_id == "user-1"
    assert member.role == "member"
    assert isinstance(member.joined_at, datetime)


def test_readding_member_updates_role_and_preserves_joined_at() -> None:
    from services.group_member_service import group_member_service

    original = group_member_service.add_member("group-demo", "user-1", role="member")
    updated = group_member_service.add_member("group-demo", "user-1", role="admin")

    assert updated.role == "admin"
    assert updated.joined_at == original.joined_at


def test_list_members_returns_members_sorted_by_user_id() -> None:
    from services.group_member_service import group_member_service

    group_member_service.add_member("group-demo", "user-b", role="member")
    group_member_service.add_member("group-demo", "user-a", role="owner")

    members = group_member_service.list_members("group-demo")

    assert [member.user_id for member in members] == ["user-a", "user-b"]


def test_add_member_rejects_invalid_roles() -> None:
    from services.group_member_service import group_member_service

    with pytest.raises(ValueError, match="invalid group member role"):
        group_member_service.add_member("group-demo", "user-1", role="guest")


def test_remove_member_returns_true_for_existing_member_and_false_for_missing_member() -> None:
    from services.group_member_service import group_member_service

    group_member_service.add_member("group-demo", "user-1", role="member")

    assert group_member_service.remove_member("group-demo", "user-1") is True
    assert group_member_service.remove_member("group-demo", "user-1") is False


def test_get_member_role_returns_role_or_none() -> None:
    from services.group_member_service import group_member_service

    group_member_service.add_member("group-demo", "owner-1", role="owner")

    assert group_member_service.get_member_role("group-demo", "owner-1") == "owner"
    assert group_member_service.get_member_role("group-demo", "missing-user") is None
