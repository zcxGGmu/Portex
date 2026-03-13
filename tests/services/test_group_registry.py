from __future__ import annotations

from datetime import datetime, timedelta
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
    database_path = tmp_path / "group-registry.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"
    engine = create_async_engine(database_url)

    async with engine.begin() as connection:
        await connection.run_sync(_base_metadata().create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_ensure_registered_group_inserts_new_row(db_session: AsyncSession) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)

    group = await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat 1",
        folder="chat-abc123",
        created_by="user-1",
    )

    assert group.jid == "telegram:chat-1"
    assert group.name == "Telegram Chat 1"
    assert group.folder == "chat-abc123"
    assert group.created_by == "user-1"
    assert isinstance(group.added_at, datetime)


@pytest.mark.asyncio
async def test_ensure_registered_group_is_idempotent_and_preserves_added_at(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)

    original = await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat 1",
        folder="chat-abc123",
        created_by="user-1",
    )

    updated = await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat Renamed",
        folder="chat-abc123",
        created_by=None,
    )

    assert updated.jid == original.jid
    assert updated.added_at == original.added_at
    assert updated.name == "Telegram Chat Renamed"
    assert updated.created_by == "user-1"


@pytest.mark.asyncio
async def test_ensure_registered_group_does_not_clear_home_or_created_by_on_repeat_write(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)

    original = await service.ensure_registered_group(
        jid="web:home-user-1",
        name="Alice Home",
        folder="home-user-1",
        created_by="user-1",
        is_home=True,
    )

    updated = await service.ensure_registered_group(
        jid="web:home-user-1",
        name="Alice Home Updated",
        folder="home-user-1",
        created_by="user-2",
    )

    assert updated.jid == original.jid
    assert updated.name == "Alice Home Updated"
    assert updated.created_by == "user-1"
    assert updated.is_home is True


@pytest.mark.asyncio
async def test_list_registered_groups_returns_persisted_rows_in_deterministic_order(
    db_session: AsyncSession,
) -> None:
    from domain.models.group import RegisteredGroup
    from services.group_registry import GroupRegistryService

    later = RegisteredGroup(
        jid="telegram:chat-2",
        name="Second Chat",
        folder="chat-222",
        added_at=datetime(2026, 3, 13, 10, 5),
        created_by=None,
    )
    earlier = RegisteredGroup(
        jid="telegram:chat-1",
        name="First Chat",
        folder="chat-111",
        added_at=datetime(2026, 3, 13, 10, 0) - timedelta(seconds=1),
        created_by="user-1",
    )
    db_session.add_all([later, earlier])
    await db_session.commit()

    service = GroupRegistryService(db=db_session)

    groups = await service.list_registered_groups()

    assert [(group.jid, group.folder) for group in groups] == [
        ("telegram:chat-1", "chat-111"),
        ("telegram:chat-2", "chat-222"),
    ]


@pytest.mark.asyncio
async def test_ensure_home_workspace_creates_personal_home_for_member(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)

    home = await service.ensure_home_workspace(
        user_id="user-1",
        role="member",
        username="alice",
    )

    assert home.jid == "web:home-user-1"
    assert home.folder == "home-user-1"
    assert home.name == "alice Home"
    assert home.created_by == "user-1"
    assert home.is_home is True


@pytest.mark.asyncio
async def test_ensure_home_workspace_reuses_shared_main_for_owner(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)

    first = await service.ensure_home_workspace(
        user_id="owner-1",
        role="owner",
        username="owner-one",
    )
    second = await service.ensure_home_workspace(
        user_id="owner-2",
        role="owner",
        username="owner-two",
    )

    assert first.jid == "web:main"
    assert first.folder == "main"
    assert first.is_home is True
    assert second.jid == "web:main"
    assert second.folder == "main"
    assert second.created_by == "owner-1"


@pytest.mark.asyncio
async def test_get_web_workspace_by_folder_prefers_canonical_web_row(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)
    await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat",
        folder="home-user-1",
        created_by=None,
    )
    await service.ensure_registered_group(
        jid="web:home-user-1",
        name="Alice Home",
        folder="home-user-1",
        created_by="user-1",
        is_home=True,
    )

    resolved = await service.get_web_workspace_by_folder("home-user-1")

    assert resolved is not None
    assert resolved.jid == "web:home-user-1"
    assert resolved.is_home is True
