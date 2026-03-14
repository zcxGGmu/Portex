"""Message persistence service helpers."""

from __future__ import annotations

from datetime import datetime
import json
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.message import Message


def _build_attachments_payload(
    *,
    channel: str | None,
    group_folder: str | None,
    run_id: str | None,
    external_message_id: str | None,
) -> str | None:
    payload = {
        key: value
        for key, value in {
            "channel": channel,
            "group_folder": group_folder,
            "run_id": run_id,
            "external_message_id": external_message_id,
        }.items()
        if value is not None
    }
    if not payload:
        return None
    return json.dumps(payload, sort_keys=True)


async def store_message(
    db: AsyncSession,
    chat_jid: str,
    sender: str,
    content: str,
    is_from_me: bool = False,
    slot_id: str = "main",
    channel: str | None = None,
    group_folder: str | None = None,
    run_id: str | None = None,
    external_message_id: str | None = None,
) -> Message:
    """Store a chat message and return the persisted record."""
    message = Message(
        id=str(uuid4()),
        chat_jid=chat_jid,
        sender=sender,
        content=content,
        is_from_me=is_from_me,
        timestamp=datetime.utcnow(),
        slot_id=slot_id,
        attachments=_build_attachments_payload(
            channel=channel,
            group_folder=group_folder,
            run_id=run_id,
            external_message_id=external_message_id,
        ),
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


__all__ = ["store_message"]
