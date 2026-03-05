#!/usr/bin/env python3
"""Initialize database tables."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domain.models import Base
from infra.db.database import engine as default_engine


def get_model_metadata() -> MetaData:
    """Return the unified model metadata."""
    return Base.metadata


async def init_db(database_url: str | None = None) -> None:
    """Create all tables defined in the unified metadata."""
    metadata = get_model_metadata()
    if database_url:
        db_engine: AsyncEngine = create_async_engine(database_url)
        should_dispose = True
    else:
        db_engine = default_engine
        should_dispose = False

    try:
        async with db_engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
    finally:
        if should_dispose:
            await db_engine.dispose()


def main(argv: Sequence[str] | None = None) -> int:
    """Run database initialization as a script."""
    parser = argparse.ArgumentParser(description="Initialize Portex database.")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Optional database URL override.",
    )
    args = parser.parse_args(argv)
    asyncio.run(init_db(database_url=args.database_url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
