#!/usr/bin/env python3
# ruff: noqa: E402
"""Initialize database tables."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import MetaData, inspect
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from domain.models import Base
from infra.db.database import create_database_engine, engine as default_engine


def get_model_metadata() -> MetaData:
    """Return the unified model metadata."""
    return Base.metadata


def _create_missing_indexes(connection: Connection, metadata: MetaData) -> None:
    for table in metadata.sorted_tables:
        for index in table.indexes:
            index.create(bind=connection, checkfirst=True)


def _backfill_registered_group_columns(connection: Connection) -> None:
    inspector = inspect(connection)
    if "registered_groups" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("registered_groups")}
    if "is_home" not in columns:
        connection.exec_driver_sql(
            "ALTER TABLE registered_groups "
            "ADD COLUMN is_home BOOLEAN NOT NULL DEFAULT 0"
        )
    if "target_workspace_jid" not in columns:
        connection.exec_driver_sql(
            "ALTER TABLE registered_groups "
            "ADD COLUMN target_workspace_jid VARCHAR"
        )


def _backfill_group_member_columns(connection: Connection) -> None:
    inspector = inspect(connection)
    if "group_members" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("group_members")}
    if (
        "group_folder" in columns
        and "added_by" in columns
        and "group_jid" not in columns
    ):
        return

    if "group_folder" in columns and "group_jid" in columns:
        group_folder_expr = "COALESCE(group_folder, group_jid)"
    elif "group_folder" in columns:
        group_folder_expr = "group_folder"
    else:
        group_folder_expr = "group_jid"

    added_by_expr = "added_by" if "added_by" in columns else "NULL"
    temp_table_name = "group_members__portex_backfill"

    connection.exec_driver_sql(f"DROP TABLE IF EXISTS {temp_table_name}")
    connection.exec_driver_sql(
        f"""
        CREATE TABLE {temp_table_name} (
            group_folder VARCHAR NOT NULL,
            user_id VARCHAR NOT NULL,
            role VARCHAR NOT NULL,
            joined_at DATETIME NOT NULL,
            added_by VARCHAR,
            PRIMARY KEY (group_folder, user_id)
        )
        """
    )
    connection.exec_driver_sql(
        f"""
        INSERT INTO {temp_table_name} (group_folder, user_id, role, joined_at, added_by)
        SELECT {group_folder_expr}, user_id, role, joined_at, {added_by_expr}
        FROM group_members
        """
    )
    connection.exec_driver_sql("DROP TABLE group_members")
    connection.exec_driver_sql(
        f"ALTER TABLE {temp_table_name} RENAME TO group_members"
    )


async def init_db(database_url: str | None = None) -> None:
    """Create all tables defined in the unified metadata."""
    metadata = get_model_metadata()
    if database_url:
        db_engine: AsyncEngine = create_database_engine(database_url)
        should_dispose = True
    else:
        db_engine = default_engine
        should_dispose = False

    try:
        async with db_engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
            await connection.run_sync(_backfill_registered_group_columns)
            await connection.run_sync(_backfill_group_member_columns)
            await connection.run_sync(lambda sync_connection: _create_missing_indexes(sync_connection, metadata))
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
