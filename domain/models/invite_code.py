"""SQLAlchemy invite code model."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from domain.models.base import Base


class InviteCode(Base):
    """Invite code contract for future persistence-backed registration flows."""

    __tablename__ = "invite_codes"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="member", nullable=False)
    permission_template: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    used_by: Mapped[str | None] = mapped_column(String, nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
