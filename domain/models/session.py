"""SQLAlchemy session model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from domain.models.base import Base


class Session(Base):
    """Agent session binding by group folder and session id."""

    __tablename__ = "sessions"

    group_folder: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    agent_id: Mapped[str] = mapped_column(String, default="", nullable=False)
