from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sys
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def _base_metadata():
    from domain.models import Base

    return Base.metadata


def _message_model():
    from domain.models.message import Message

    return Message


@pytest_asyncio.fixture
async def db_session(tmp_path: Path) -> AsyncSession:
    database_path = tmp_path / "message-service.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"
    engine = create_async_engine(database_url)

    async with engine.begin() as connection:
        await connection.run_sync(_base_metadata().create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_store_message_persists_with_default_direction(db_session: AsyncSession) -> None:
    from services.message_service import store_message

    message = await store_message(
        db=db_session,
        chat_jid="group-demo",
        sender="alice",
        content="hello world",
    )

    UUID(message.id)
    assert message.chat_jid == "group-demo"
    assert message.sender == "alice"
    assert message.content == "hello world"
    assert message.is_from_me is False
    assert isinstance(message.timestamp, datetime)

    persisted = await db_session.get(_message_model(), message.id)
    assert persisted is not None
    assert persisted.chat_jid == "group-demo"
    assert persisted.sender == "alice"


@pytest.mark.asyncio
async def test_store_message_supports_outbound_flag(db_session: AsyncSession) -> None:
    from services.message_service import store_message

    message = await store_message(
        db=db_session,
        chat_jid="group-demo",
        sender="assistant",
        content="response",
        is_from_me=True,
    )

    assert message.is_from_me is True

    persisted = await db_session.get(_message_model(), message.id)
    assert persisted is not None
    assert persisted.is_from_me is True


@pytest.mark.asyncio
async def test_store_message_serializes_dispatch_metadata_into_attachments(
    db_session: AsyncSession,
) -> None:
    from services.message_service import store_message

    message = await store_message(
        db=db_session,
        chat_jid="telegram:chat-1",
        sender="assistant",
        content="response",
        is_from_me=True,
        channel="telegram",
        group_folder="group-1",
        run_id="run-123",
        external_message_id="external-123",
    )

    assert message.attachments == json.dumps(
        {
            "channel": "telegram",
            "external_message_id": "external-123",
            "group_folder": "group-1",
            "run_id": "run-123",
        },
        sort_keys=True,
    )

    persisted = await db_session.get(_message_model(), message.id)
    assert persisted is not None
    assert persisted.attachments == message.attachments


@pytest.mark.asyncio
async def test_store_message_keeps_attachments_empty_when_no_metadata_is_provided(
    db_session: AsyncSession,
) -> None:
    from services.message_service import store_message

    message = await store_message(
        db=db_session,
        chat_jid="group-demo",
        sender="alice",
        content="hello world",
    )

    assert message.attachments is None
