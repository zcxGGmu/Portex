"""Database engine and session factory for Portex."""

from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/portex.db")
POOL_SIZE = 20
MAX_OVERFLOW = 10


def _uses_static_pool(database_url: str) -> bool:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        return False

    database_name = url.database or ""
    if database_name in {"", ":memory:"}:
        return True

    if database_name.startswith("file::memory:"):
        return True

    return database_name.startswith("file:") and url.query.get("mode") == "memory"


def create_database_engine(database_url: str = DATABASE_URL) -> AsyncEngine:
    if _uses_static_pool(database_url):
        return create_async_engine(database_url, poolclass=StaticPool)

    return create_async_engine(
        database_url,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
    )


engine = create_database_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session."""
    async with AsyncSessionLocal() as session:
        yield session
