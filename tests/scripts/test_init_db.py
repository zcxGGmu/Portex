from __future__ import annotations

from pathlib import Path
import sqlite3
import subprocess
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


def test_script_runs_successfully_when_executed_directly(tmp_path: Path) -> None:
    database_path = tmp_path / "portex-direct-script.db"
    project_root = Path(__file__).resolve().parents[2]

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/init_db.py",
            "--database-url",
            f"sqlite+aiosqlite:///{database_path}",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert database_path.exists()


def test_init_db_creates_todo_defined_indexes(tmp_path: Path) -> None:
    from scripts import init_db

    database_path = tmp_path / "portex-indexes.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"

    exit_code = init_db.main(["--database-url", database_url])

    assert exit_code == 0
    assert database_path.exists()

    connection = sqlite3.connect(database_path)
    try:
        message_indexes = {
            row[1] for row in connection.execute("PRAGMA index_list('messages')").fetchall()
        }
        task_indexes = {
            row[1] for row in connection.execute("PRAGMA index_list('scheduled_tasks')").fetchall()
        }
        message_chat_jid_columns = [
            row[2]
            for row in connection.execute("PRAGMA index_info('idx_messages_chat_jid')").fetchall()
        ]
        message_timestamp_columns = [
            row[2]
            for row in connection.execute("PRAGMA index_info('idx_messages_timestamp')").fetchall()
        ]
        task_next_run_columns = [
            row[2]
            for row in connection.execute("PRAGMA index_info('idx_tasks_next_run')").fetchall()
        ]
    finally:
        connection.close()

    assert "idx_messages_chat_jid" in message_indexes
    assert "idx_messages_timestamp" in message_indexes
    assert "idx_tasks_next_run" in task_indexes
    assert message_chat_jid_columns == ["chat_jid"]
    assert message_timestamp_columns == ["timestamp"]
    assert task_next_run_columns == ["next_run"]
