from __future__ import annotations

import importlib
from pathlib import Path
import sys

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
