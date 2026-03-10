from __future__ import annotations

import importlib
from pathlib import Path
import sys

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import AsyncAdaptedQueuePool, StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.mark.asyncio
async def test_get_db_yields_async_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from infra.db import database

    importlib.reload(database)

    generator = database.get_db()
    session = await anext(generator)
    try:
        assert isinstance(session, AsyncSession)
    finally:
        await generator.aclose()
        await database.engine.dispose()


def test_database_url_default_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from infra.db import database

    importlib.reload(database)

    assert database.DATABASE_URL == "sqlite+aiosqlite:///./data/portex.db"


def test_default_engine_uses_explicit_queue_pool_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from infra.db import database

    importlib.reload(database)

    pool = database.engine.sync_engine.pool

    assert isinstance(pool, AsyncAdaptedQueuePool)
    assert pool.size() == database.POOL_SIZE
    assert pool._max_overflow == database.MAX_OVERFLOW


@pytest.mark.parametrize(
    "database_url",
    [
        "sqlite+aiosqlite://",
        "sqlite+aiosqlite:///:memory:",
    ],
)
@pytest.mark.asyncio
async def test_create_database_engine_uses_static_pool_for_in_memory_sqlite(
    database_url: str,
) -> None:
    from infra.db import database

    engine = database.create_database_engine(database_url)
    try:
        assert isinstance(engine.sync_engine.pool, StaticPool)
    finally:
        await engine.dispose()


def test_uses_static_pool_detects_file_memory_urls() -> None:
    from infra.db import database

    assert database._uses_static_pool("sqlite+aiosqlite:///file::memory:?cache=shared") is True
    assert (
        database._uses_static_pool(
            "sqlite+aiosqlite:///file:memdb1?mode=memory&cache=shared&uri=true"
        )
        is True
    )
