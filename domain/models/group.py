"""SQLAlchemy registered group model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from domain.models.base import Base


class RegisteredGroup(Base):
    """Registered chat group metadata."""

    __tablename__ = "registered_groups"

    jid: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    folder: Mapped[str] = mapped_column(String, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    container_config: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String)
    is_home: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    target_workspace_jid: Mapped[str | None] = mapped_column(String, nullable=True)
