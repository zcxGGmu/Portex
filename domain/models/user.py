"""SQLAlchemy user model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from domain.models.base import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="member", nullable=False)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)
    permissions: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    avatar_emoji: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_color: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_name: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_avatar_emoji: Mapped[str | None] = mapped_column(String, nullable=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    disable_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
