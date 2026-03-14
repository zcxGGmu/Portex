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
    database_path = tmp_path / "conversation-slots.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"
    engine = create_async_engine(database_url)

    async with engine.begin() as connection:
        await connection.run_sync(_base_metadata().create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_ensure_main_slot_is_idempotent(db_session: AsyncSession) -> None:
    from services.conversation_slot_service import ConversationSlotService

    service = ConversationSlotService(db=db_session)

    first = await service.ensure_main_slot("project-alpha", created_by="owner-1")
    second = await service.ensure_main_slot("project-alpha", created_by="owner-1")

    assert first.workspace_folder == "project-alpha"
    assert first.slot_id == "main"
    assert first.title == "Main"
    assert second.workspace_folder == "project-alpha"
    assert second.slot_id == "main"
    assert second.created_at == first.created_at


@pytest.mark.asyncio
async def test_create_slot_adds_non_main_slot_under_existing_workspace(
    db_session: AsyncSession,
) -> None:
    from services.conversation_slot_service import ConversationSlotService

    service = ConversationSlotService(db=db_session)
    await service.ensure_main_slot("project-alpha", created_by="owner-1")

    draft = await service.create_slot(
        workspace_folder="project-alpha",
        slot_id="draft",
        title="Draft",
        created_by="owner-1",
    )

    assert draft.workspace_folder == "project-alpha"
    assert draft.slot_id == "draft"
    assert draft.title == "Draft"
    assert draft.created_by == "owner-1"
    assert isinstance(draft.created_at, datetime)


@pytest.mark.asyncio
async def test_list_slots_returns_main_first_then_other_slots_deterministically(
    db_session: AsyncSession,
) -> None:
    from services.conversation_slot_service import ConversationSlotService

    service = ConversationSlotService(db=db_session)
    await service.ensure_main_slot("project-alpha", created_by="owner-1")
    await service.create_slot(
        workspace_folder="project-alpha",
        slot_id="zeta",
        title="Zeta",
        created_by="owner-1",
    )
    await service.create_slot(
        workspace_folder="project-alpha",
        slot_id="alpha",
        title="Alpha",
        created_by="owner-1",
    )

    slots = await service.list_slots("project-alpha")

    assert [(slot.slot_id, slot.title) for slot in slots] == [
        ("main", "Main"),
        ("alpha", "Alpha"),
        ("zeta", "Zeta"),
    ]


@pytest.mark.asyncio
async def test_get_slot_returns_none_for_missing_slot(db_session: AsyncSession) -> None:
    from services.conversation_slot_service import ConversationSlotService

    service = ConversationSlotService(db=db_session)
    await service.ensure_main_slot("project-alpha", created_by="owner-1")

    missing = await service.get_slot("project-alpha", "missing")

    assert missing is None


@pytest.mark.asyncio
async def test_create_slot_rejects_invalid_slot_id(db_session: AsyncSession) -> None:
    from services.conversation_slot_service import ConversationSlotService

    service = ConversationSlotService(db=db_session)
    await service.ensure_main_slot("project-alpha", created_by="owner-1")

    with pytest.raises(ValueError, match="invalid slot_id"):
        await service.create_slot(
            workspace_folder="project-alpha",
            slot_id="Draft Slot",
            title="Draft Slot",
            created_by="owner-1",
        )
