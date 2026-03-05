"""SQLAlchemy message model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from domain.models.base import Base


class Message(Base):
    """Inbound and outbound message record."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    chat_jid: Mapped[str] = mapped_column(String, nullable=False)
    sender: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_from_me: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attachments: Mapped[str | None] = mapped_column(Text)
