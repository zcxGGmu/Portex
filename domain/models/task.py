"""SQLAlchemy scheduled task model."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from domain.models.base import Base


class ScheduledTask(Base):
    """Scheduled prompt execution task."""

    __tablename__ = "scheduled_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    group_folder: Mapped[str] = mapped_column(String, nullable=False)
    chat_jid: Mapped[str] = mapped_column(String, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    schedule_type: Mapped[str | None] = mapped_column(String)
    schedule_value: Mapped[str | None] = mapped_column(String)
    next_run: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
