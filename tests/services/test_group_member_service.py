from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _base_metadata():
    from domain.models import Base

    return Base.metadata


@pytest_asyncio.fixture
async def db_session(tmp_path: Path) -> AsyncSession:
    database_path = tmp_path / "group-members.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"
    engine = create_async_engine(database_url)

    async with engine.begin() as connection:
        await connection.run_sync(_base_metadata().create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_add_member_uses_default_role_and_sets_joined_at(db_session: AsyncSession) -> None:
    from services.group_member_service import GroupMemberService

    service = GroupMemberService(db=db_session)

    member = await service.add_member("group-demo", "user-1")

    assert member.group_folder == "group-demo"
    assert member.user_id == "user-1"
    assert member.role == "member"
    assert isinstance(member.joined_at, datetime)
    assert member.added_by is None


@pytest.mark.asyncio
async def test_readding_member_updates_role_and_preserves_joined_at(
    db_session: AsyncSession,
) -> None:
    from services.group_member_service import GroupMemberService

    service = GroupMemberService(db=db_session)

    original = await service.add_member("group-demo", "user-1", role="member")
    updated = await service.add_member("group-demo", "user-1", role="admin")

    assert updated.role == "admin"
    assert updated.joined_at == original.joined_at


@pytest.mark.asyncio
async def test_list_members_returns_members_sorted_by_user_id(db_session: AsyncSession) -> None:
    from services.group_member_service import GroupMemberService

    service = GroupMemberService(db=db_session)

    await service.add_member("group-demo", "user-b", role="member")
    await service.add_member("group-demo", "user-a", role="owner")

    members = await service.list_members("group-demo")

    assert [member.user_id for member in members] == ["user-a", "user-b"]


@pytest.mark.asyncio
async def test_add_member_rejects_invalid_roles(db_session: AsyncSession) -> None:
    from services.group_member_service import GroupMemberService

    service = GroupMemberService(db=db_session)

    with pytest.raises(ValueError, match="invalid group member role"):
        await service.add_member("group-demo", "user-1", role="guest")


@pytest.mark.asyncio
async def test_remove_member_returns_true_for_existing_member_and_false_for_missing_member(
    db_session: AsyncSession,
) -> None:
    from services.group_member_service import GroupMemberService

    service = GroupMemberService(db=db_session)
    await service.add_member("group-demo", "user-1", role="member")

    assert await service.remove_member("group-demo", "user-1") is True
    assert await service.remove_member("group-demo", "user-1") is False


@pytest.mark.asyncio
async def test_get_member_role_returns_role_or_none(db_session: AsyncSession) -> None:
    from services.group_member_service import GroupMemberService

    service = GroupMemberService(db=db_session)
    await service.add_member("group-demo", "owner-1", role="owner")

    assert await service.get_member_role("group-demo", "owner-1") == "owner"
    assert await service.get_member_role("group-demo", "missing-user") is None


@pytest.mark.asyncio
async def test_owner_role_changes_are_rejected(db_session: AsyncSession) -> None:
    from services.group_member_service import GroupMemberService

    service = GroupMemberService(db=db_session)
    await service.add_member("group-demo", "owner-1", role="owner")

    with pytest.raises(ValueError, match="owner role changes are not supported"):
        await service.add_member("group-demo", "owner-1", role="member")


@pytest.mark.asyncio
async def test_transferring_owner_role_to_existing_member_is_rejected(
    db_session: AsyncSession,
) -> None:
    from services.group_member_service import GroupMemberService

    service = GroupMemberService(db=db_session)
    await service.add_member("group-demo", "owner-1", role="owner")
    await service.add_member("group-demo", "member-1", role="member")

    with pytest.raises(ValueError, match="owner role changes are not supported"):
        await service.add_member("group-demo", "member-1", role="owner")


@pytest.mark.asyncio
async def test_remove_member_rejects_removing_owner(db_session: AsyncSession) -> None:
    from services.group_member_service import GroupMemberService

    service = GroupMemberService(db=db_session)
    await service.add_member("group-demo", "owner-1", role="owner")

    with pytest.raises(ValueError, match="group owner cannot be removed"):
        await service.remove_member("group-demo", "owner-1")
