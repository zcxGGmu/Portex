from __future__ import annotations

from datetime import datetime, timezone
import json
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


def _message_model():
    from domain.models.message import Message

    return Message


def _metadata_payload(**kwargs: str) -> str:
    return json.dumps(kwargs, sort_keys=True)


@pytest_asyncio.fixture
async def db_session(tmp_path: Path) -> AsyncSession:
    database_path = tmp_path / "usage-audit.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"
    engine = create_async_engine(database_url)

    async with engine.begin() as connection:
        await connection.run_sync(_base_metadata().create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_usage_stats_aggregates_summary_daily_and_channel_breakdown(
    db_session: AsyncSession,
) -> None:
    from services.usage_audit import UsageAuditService

    Message = _message_model()
    db_session.add_all(
        [
            Message(
                id="msg-1",
                chat_jid="web:project-alpha",
                sender="alice",
                content="hello",
                timestamp=datetime(2026, 3, 14, 8, 0),
                is_from_me=False,
                slot_id="main",
                attachments=_metadata_payload(
                    channel="web",
                    group_folder="project-alpha",
                    run_id="run-1",
                    external_message_id="in-1",
                ),
            ),
            Message(
                id="msg-2",
                chat_jid="web:project-alpha",
                sender="portex",
                content="reply",
                timestamp=datetime(2026, 3, 14, 8, 0, 3),
                is_from_me=True,
                slot_id="main",
                attachments=_metadata_payload(
                    channel="web",
                    group_folder="project-alpha",
                    run_id="run-1",
                    external_message_id="out-1",
                ),
            ),
            Message(
                id="msg-3",
                chat_jid="telegram:chat-1",
                sender="bob",
                content="ping",
                timestamp=datetime(2026, 3, 15, 9, 30),
                is_from_me=False,
                slot_id="main",
                attachments=_metadata_payload(
                    channel="telegram",
                    group_folder="team-beta",
                    run_id="run-2",
                    external_message_id="tg-3",
                ),
            ),
            Message(
                id="msg-out-window",
                chat_jid="web:old",
                sender="legacy",
                content="old",
                timestamp=datetime(2026, 2, 20, 9, 0),
                is_from_me=False,
                slot_id="main",
                attachments=_metadata_payload(
                    channel="web",
                    group_folder="old",
                    run_id="run-old",
                ),
            ),
        ]
    )
    await db_session.commit()

    service = UsageAuditService(
        db=db_session,
        now_func=lambda: datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc),
    )

    stats = await service.get_usage_stats(days=7)

    assert stats.days == 7
    assert stats.summary.total_messages == 3
    assert stats.summary.total_runs == 2
    assert stats.summary.total_user_messages == 2
    assert stats.summary.total_assistant_messages == 1
    assert stats.summary.total_active_days == 2

    assert [item.date for item in stats.daily] == ["2026-03-14", "2026-03-15"]
    assert stats.daily[0].message_count == 2
    assert stats.daily[0].run_count == 1
    assert stats.daily[1].message_count == 1
    assert stats.daily[1].run_count == 1

    channels = {item.channel: item for item in stats.channels}
    assert channels["web"].message_count == 2
    assert channels["web"].run_count == 1
    assert channels["telegram"].message_count == 1
    assert channels["telegram"].run_count == 1


@pytest.mark.asyncio
async def test_get_usage_stats_tolerates_invalid_attachments_and_clamps_days(
    db_session: AsyncSession,
) -> None:
    from services.usage_audit import UsageAuditService

    Message = _message_model()
    db_session.add(
        Message(
            id="msg-invalid",
            chat_jid="feishu:oc_123",
            sender="alice",
            content="text",
            timestamp=datetime(2026, 3, 15, 10, 0),
            is_from_me=False,
            slot_id="main",
            attachments="{not-json",
        )
    )
    await db_session.commit()

    service = UsageAuditService(
        db=db_session,
        now_func=lambda: datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc),
    )

    stats = await service.get_usage_stats(days=999)

    assert stats.days == 365
    assert stats.summary.total_messages == 1
    assert stats.summary.total_runs == 0
    assert stats.channels[0].channel == "feishu"
    assert stats.channels[0].message_count == 1


@pytest.mark.asyncio
async def test_list_audit_messages_supports_limit_group_filter_and_has_more(
    db_session: AsyncSession,
) -> None:
    from services.usage_audit import UsageAuditService

    Message = _message_model()
    db_session.add_all(
        [
            Message(
                id="msg-1",
                chat_jid="web:project-alpha",
                sender="alice",
                content="one",
                timestamp=datetime(2026, 3, 15, 10, 0),
                is_from_me=False,
                slot_id="main",
                attachments=_metadata_payload(
                    channel="web",
                    group_folder="project-alpha",
                    run_id="run-1",
                    external_message_id="in-1",
                ),
            ),
            Message(
                id="msg-2",
                chat_jid="web:project-alpha",
                sender="portex",
                content="two",
                timestamp=datetime(2026, 3, 15, 10, 1),
                is_from_me=True,
                slot_id="main",
                attachments=_metadata_payload(
                    channel="web",
                    group_folder="project-alpha",
                    run_id="run-1",
                    external_message_id="out-1",
                ),
            ),
            Message(
                id="msg-3",
                chat_jid="telegram:chat-2",
                sender="bob",
                content="three",
                timestamp=datetime(2026, 3, 15, 10, 2),
                is_from_me=False,
                slot_id="main",
                attachments=_metadata_payload(
                    channel="telegram",
                    group_folder="team-beta",
                    run_id="run-2",
                    external_message_id="tg-3",
                ),
            ),
        ]
    )
    await db_session.commit()

    service = UsageAuditService(db=db_session)

    limited = await service.list_audit_messages(limit=1)
    assert limited.limit == 1
    assert limited.has_more is True
    assert len(limited.items) == 1
    assert limited.items[0].message_id == "msg-3"

    filtered = await service.list_audit_messages(limit=20, group_id="project-alpha")
    assert filtered.group_id == "project-alpha"
    assert filtered.has_more is False
    assert [item.message_id for item in filtered.items] == ["msg-2", "msg-1"]
    assert all(item.group_id == "project-alpha" for item in filtered.items)
