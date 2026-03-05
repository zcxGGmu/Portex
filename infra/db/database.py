"""Database connection placeholders for Portex."""

from __future__ import annotations


def get_database_url() -> str:
    """Return the default placeholder database URL."""
    return "sqlite:///./data/portex.db"
