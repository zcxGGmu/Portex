"""Shared SQLAlchemy declarative base for domain models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models in domain.models."""

    pass
