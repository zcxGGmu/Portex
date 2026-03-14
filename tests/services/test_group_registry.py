from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
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
    assert group.target_workspace_jid is None
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
async def test_ensure_registered_group_preserves_existing_binding_until_explicitly_updated(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)

    original = await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat 1",
        folder="chat-abc123",
        target_workspace_jid="web:main",
    )
    assert original.target_workspace_jid == "web:main"

    unchanged = await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat 1 Renamed",
        folder="chat-abc123",
    )
    assert unchanged.target_workspace_jid == "web:main"
    updated = await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat 1 Rebound",
        folder="chat-abc123",
        target_workspace_jid="web:home-user-1",
    )

    assert updated.target_workspace_jid == "web:home-user-1"


@pytest.mark.asyncio
async def test_ensure_registered_group_can_explicitly_clear_existing_binding(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)

    original = await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat 1",
        folder="chat-abc123",
        target_workspace_jid="web:main",
    )
    assert original.target_workspace_jid == "web:main"

    cleared = await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat 1",
        folder="chat-abc123",
        target_workspace_jid=None,
    )

    assert cleared.target_workspace_jid is None


@pytest.mark.asyncio
async def test_ensure_im_endpoint_preserves_existing_endpoint_metadata(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)
    original = await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Custom Endpoint Label",
        folder="custom-folder",
        target_workspace_jid="web:main",
    )

    ensured = await service.ensure_im_endpoint(
        jid="telegram:chat-1",
        name="Fallback Endpoint Label",
        folder="chat-abc123",
    )

    assert ensured.jid == original.jid
    assert ensured.name == "Custom Endpoint Label"
    assert ensured.folder == "custom-folder"
    assert ensured.target_workspace_jid == "web:main"


@pytest.mark.asyncio
async def test_ensure_im_endpoint_creates_main_slot_for_new_endpoint(
    db_session: AsyncSession,
) -> None:
    from services.conversation_slot_service import ConversationSlotService
    from services.group_registry import GroupRegistryService

    registry = GroupRegistryService(db=db_session)
    slot_service = ConversationSlotService(db=db_session)

    endpoint = await registry.ensure_im_endpoint(
        jid="telegram:chat-1",
        name="Telegram Chat 1",
        folder="chat-abc123",
    )

    slot = await slot_service.get_slot(endpoint.folder, "main")

    assert slot is not None
    assert slot.title == "Main"


@pytest.mark.asyncio
async def test_ensure_im_endpoint_repairs_missing_main_slot_for_existing_endpoint(
    db_session: AsyncSession,
) -> None:
    from domain.models.group import RegisteredGroup
    from services.conversation_slot_service import ConversationSlotService
    from services.group_registry import GroupRegistryService

    legacy_endpoint = RegisteredGroup(
        jid="telegram:chat-legacy",
        name="Legacy Telegram Chat",
        folder="chat-legacy",
        added_at=datetime.utcnow(),
        created_by=None,
        is_home=False,
        target_workspace_jid=None,
    )
    db_session.add(legacy_endpoint)
    await db_session.commit()

    registry = GroupRegistryService(db=db_session)
    slot_service = ConversationSlotService(db=db_session)

    assert await slot_service.get_slot("chat-legacy", "main") is None

    endpoint = await registry.ensure_im_endpoint(
        jid="telegram:chat-legacy",
        name="Legacy Telegram Chat",
        folder="chat-legacy",
    )
    slot = await slot_service.get_slot(endpoint.folder, "main")

    assert slot is not None
    assert slot.title == "Main"


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
    from services.conversation_slot_service import ConversationSlotService

    service = GroupRegistryService(db=db_session)
    slot_service = ConversationSlotService(db=db_session)

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
    slot = await slot_service.get_slot("main", "main")
    assert slot is not None
    assert slot.title == "Main"


@pytest.mark.asyncio
async def test_get_web_workspace_by_folder_prefers_canonical_web_row(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService
    from services.conversation_slot_service import ConversationSlotService

    service = GroupRegistryService(db=db_session)
    slot_service = ConversationSlotService(db=db_session)
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
    slot = await slot_service.get_slot("home-user-1", "main")
    assert slot is not None
    assert slot.title == "Main"


@pytest.mark.asyncio
async def test_resolve_im_workspace_returns_fallback_endpoint_when_unbound(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)
    endpoint = await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat",
        folder="chat-abc123",
    )

    resolved = await service.resolve_im_workspace(jid="telegram:chat-1")

    assert resolved is not None
    assert resolved.jid == endpoint.jid
    assert resolved.folder == "chat-abc123"


@pytest.mark.asyncio
async def test_resolve_im_workspace_returns_bound_target_workspace_when_present(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)
    await service.ensure_registered_group(
        jid="web:main",
        name="Main",
        folder="main",
        created_by="owner-1",
        is_home=True,
    )
    await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat",
        folder="chat-abc123",
        target_workspace_jid="web:main",
    )

    resolved = await service.resolve_im_workspace(jid="telegram:chat-1")

    assert resolved is not None
    assert resolved.jid == "web:main"
    assert resolved.folder == "main"


@pytest.mark.asyncio
async def test_resolve_im_workspace_ignores_bound_im_endpoint_rows(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)
    fallback_endpoint = await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat",
        folder="chat-abc123",
        target_workspace_jid="telegram:chat-2",
    )
    await service.ensure_registered_group(
        jid="telegram:chat-2",
        name="Another Telegram Chat",
        folder="chat-def456",
    )

    resolved = await service.resolve_im_workspace(jid="telegram:chat-1")

    assert resolved is not None
    assert resolved.jid == fallback_endpoint.jid
    assert resolved.folder == fallback_endpoint.folder


@pytest.mark.asyncio
async def test_resolve_im_workspace_falls_back_when_binding_target_is_missing(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    service = GroupRegistryService(db=db_session)
    endpoint = await service.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat",
        folder="chat-abc123",
        target_workspace_jid="web:missing",
    )

    resolved = await service.resolve_im_workspace(jid="telegram:chat-1")

    assert resolved is not None
    assert resolved.jid == endpoint.jid
    assert resolved.folder == endpoint.folder


@pytest.mark.asyncio
async def test_runtime_schema_healing_backfills_binding_columns_for_older_tables(
    tmp_path: Path,
) -> None:
    from services.group_registry import GroupRegistryService

    database_path = tmp_path / "group-registry-legacy.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"

    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE registered_groups (
                jid VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                folder VARCHAR NOT NULL,
                added_at DATETIME NOT NULL,
                container_config TEXT,
                created_by VARCHAR
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        service = GroupRegistryService(db=session)
        await service.list_registered_groups()

    await engine.dispose()

    connection = sqlite3.connect(database_path)
    try:
        columns = {
            row[1]: row
            for row in connection.execute("PRAGMA table_info('registered_groups')").fetchall()
        }
    finally:
        connection.close()

    assert "is_home" in columns
    assert "target_workspace_jid" in columns


@pytest.mark.asyncio
async def test_user_can_access_non_home_workspace_as_owner_or_member(
    db_session: AsyncSession,
) -> None:
    from services.group_member_service import GroupMemberService
    from services.group_registry import GroupRegistryService

    registry = GroupRegistryService(db=db_session)
    members = GroupMemberService(db=db_session)
    workspace = await registry.ensure_registered_group(
        jid="web:project-alpha",
        name="Project Alpha",
        folder="project-alpha",
        created_by="owner-1",
    )
    await members.add_member("project-alpha", "member-1", role="member", added_by="owner-1")

    assert await registry.user_can_access_group(user_id="owner-1", group=workspace) is True
    assert await registry.user_can_access_group(user_id="member-1", group=workspace) is True
    assert await registry.user_can_access_group(user_id="outsider-1", group=workspace) is False


@pytest.mark.asyncio
async def test_user_can_access_bound_im_endpoint_through_target_workspace_membership(
    db_session: AsyncSession,
) -> None:
    from services.group_member_service import GroupMemberService
    from services.group_registry import GroupRegistryService

    registry = GroupRegistryService(db=db_session)
    members = GroupMemberService(db=db_session)
    await registry.ensure_registered_group(
        jid="web:project-alpha",
        name="Project Alpha",
        folder="project-alpha",
        created_by="owner-1",
    )
    endpoint = await registry.ensure_registered_group(
        jid="telegram:chat-1",
        name="Telegram Chat",
        folder="chat-abc123",
        created_by="owner-1",
        target_workspace_jid="web:project-alpha",
    )
    await members.add_member("project-alpha", "member-1", role="member", added_by="owner-1")

    assert await registry.user_can_access_group(user_id="member-1", group=endpoint) is True
    assert await registry.user_can_access_group(user_id="outsider-1", group=endpoint) is False


@pytest.mark.asyncio
async def test_user_can_access_shared_main_workspace_as_second_owner(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    registry = GroupRegistryService(db=db_session)
    workspace = await registry.ensure_home_workspace(
        user_id="owner-1",
        role="owner",
        username="owner-one",
    )
    await registry.ensure_home_workspace(
        user_id="owner-2",
        role="owner",
        username="owner-two",
    )

    assert (
        await registry.user_can_access_group(
            user_id="owner-2",
            user_role="owner",
            group=workspace,
        )
        is True
    )


@pytest.mark.asyncio
async def test_home_workspace_never_becomes_member_manageable(
    db_session: AsyncSession,
) -> None:
    from services.group_registry import GroupRegistryService

    registry = GroupRegistryService(db=db_session)
    home = await registry.ensure_home_workspace(
        user_id="user-1",
        role="member",
        username="alice",
    )

    assert await registry.user_can_manage_members(user_id="user-1", group=home) is False
