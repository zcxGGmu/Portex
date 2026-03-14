"""SQLAlchemy group member model."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from domain.models.base import Base


class GroupMember(Base):
    """Formal group membership contract for future persistence-backed flows."""

    __tablename__ = "group_members"

    group_folder: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    added_by: Mapped[str | None] = mapped_column(String, nullable=True)
