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


def test_init_db_backfills_missing_indexes_for_existing_tables(tmp_path: Path) -> None:
    from scripts import init_db

    database_path = tmp_path / "portex-existing.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"

    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE messages (
                id VARCHAR PRIMARY KEY,
                chat_jid VARCHAR NOT NULL,
                sender VARCHAR NOT NULL,
                content TEXT,
                timestamp DATETIME NOT NULL,
                is_from_me BOOLEAN NOT NULL,
                attachments TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE scheduled_tasks (
                id VARCHAR PRIMARY KEY,
                group_folder VARCHAR NOT NULL,
                chat_jid VARCHAR NOT NULL,
                prompt TEXT NOT NULL,
                schedule_type VARCHAR,
                schedule_value VARCHAR,
                next_run DATETIME,
                status VARCHAR NOT NULL,
                created_at DATETIME NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    exit_code = init_db.main(["--database-url", database_url])

    assert exit_code == 0

    connection = sqlite3.connect(database_path)
    try:
        message_indexes = {
            row[1] for row in connection.execute("PRAGMA index_list('messages')").fetchall()
        }
        task_indexes = {
            row[1] for row in connection.execute("PRAGMA index_list('scheduled_tasks')").fetchall()
        }
    finally:
        connection.close()

    assert "idx_messages_chat_jid" in message_indexes
    assert "idx_messages_timestamp" in message_indexes
    assert "idx_tasks_next_run" in task_indexes


def test_init_db_backfills_registered_groups_binding_columns_for_existing_tables(
    tmp_path: Path,
) -> None:
    from scripts import init_db

    database_path = tmp_path / "portex-registered-groups.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"

    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE registered_groups (
                jid VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                folder VARCHAR NOT NULL,
                added_at DATETIME NOT NULL,
                container_config TEXT,
                created_by VARCHAR
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    exit_code = init_db.main(["--database-url", database_url])

    assert exit_code == 0

    connection = sqlite3.connect(database_path)
    try:
        columns = {
            row[1]: row
            for row in connection.execute("PRAGMA table_info('registered_groups')").fetchall()
        }
    finally:
        connection.close()

    assert "is_home" in columns
    assert columns["is_home"][3] == 1
    assert columns["is_home"][4] == "0"
    assert "target_workspace_jid" in columns
    assert columns["target_workspace_jid"][3] == 0
    assert columns["target_workspace_jid"][4] is None
