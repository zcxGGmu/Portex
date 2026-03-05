from __future__ import annotations

from pathlib import Path
import sqlite3
import sys

from sqlalchemy import Column, Integer, MetaData, Table

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_main_returns_success_code(monkeypatch) -> None:
    from scripts import init_db

    async def fake_init_db(database_url=None) -> None:
        return None

    monkeypatch.setattr(init_db, "init_db", fake_init_db)

    assert init_db.main([]) == 0


def test_main_creates_database_and_table(
    monkeypatch, tmp_path: Path
) -> None:
    from scripts import init_db

    database_path = tmp_path / "portex-test.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"

    metadata = MetaData()
    Table(
        "test_records",
        metadata,
        Column("id", Integer, primary_key=True),
    )

    monkeypatch.setattr(init_db, "get_model_metadata", lambda: metadata)

    exit_code = init_db.main(["--database-url", database_url])

    assert exit_code == 0
    assert database_path.exists()

    connection = sqlite3.connect(database_path)
    try:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_records'"
        ).fetchone()
    finally:
        connection.close()

    assert row is not None
