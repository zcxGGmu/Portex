"""Message persistence service helpers."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.message import Message


async def store_message(
    db: AsyncSession,
    chat_jid: str,
    sender: str,
    content: str,
    is_from_me: bool = False,
) -> Message:
    """Store a chat message and return the persisted record."""
    message = Message(
        id=str(uuid4()),
        chat_jid=chat_jid,
        sender=sender,
        content=content,
        is_from_me=is_from_me,
        timestamp=datetime.utcnow(),
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


__all__ = ["store_message"]
