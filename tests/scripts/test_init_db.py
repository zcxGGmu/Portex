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
        connection.execute(
            """
            INSERT INTO registered_groups (jid, name, folder, added_at, container_config, created_by)
            VALUES ('web:project-alpha', 'Project Alpha', 'project-alpha', '2026-03-14T10:00:00', NULL, 'owner-1')
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
        message_columns = {
            row[1]: row
            for row in connection.execute("PRAGMA table_info('messages')").fetchall()
        }
        conversation_slots = connection.execute(
            """
            SELECT workspace_folder, slot_id, title, created_by
            FROM conversation_slots
            ORDER BY workspace_folder, slot_id
            """
        ).fetchall()
    finally:
        connection.close()

    assert "idx_messages_chat_jid" in message_indexes
    assert "idx_messages_timestamp" in message_indexes
    assert "idx_tasks_next_run" in task_indexes
    assert "slot_id" in message_columns
    assert message_columns["slot_id"][3] == 1
    assert message_columns["slot_id"][4] == "'main'"
    assert conversation_slots == [("project-alpha", "main", "Main", "owner-1")]


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


def test_init_db_repairs_missing_main_slot_for_existing_workspace(tmp_path: Path) -> None:
    from scripts import init_db

    database_path = tmp_path / "portex-conversation-slots.db"
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
                created_by VARCHAR,
                is_home BOOLEAN NOT NULL DEFAULT 0,
                target_workspace_jid VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO registered_groups (
                jid, name, folder, added_at, container_config, created_by, is_home, target_workspace_jid
            )
            VALUES (
                'web:project-alpha',
                'Project Alpha',
                'project-alpha',
                '2026-03-14T10:00:00',
                NULL,
                'owner-1',
                0,
                NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE conversation_slots (
                workspace_folder VARCHAR NOT NULL,
                slot_id VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                created_by VARCHAR,
                created_at DATETIME NOT NULL,
                PRIMARY KEY (workspace_folder, slot_id)
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
        slots = connection.execute(
            """
            SELECT workspace_folder, slot_id, title, created_by
            FROM conversation_slots
            ORDER BY workspace_folder, slot_id
            """
        ).fetchall()
    finally:
        connection.close()

    assert slots == [("project-alpha", "main", "Main", "owner-1")]


def test_init_db_backfills_group_members_workspace_columns_for_existing_tables(
    tmp_path: Path,
) -> None:
    from scripts import init_db

    database_path = tmp_path / "portex-group-members.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"

    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE group_members (
                group_jid VARCHAR NOT NULL,
                user_id VARCHAR NOT NULL,
                role VARCHAR NOT NULL,
                joined_at DATETIME NOT NULL,
                PRIMARY KEY (group_jid, user_id)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO group_members (group_jid, user_id, role, joined_at)
            VALUES ('group-demo', 'user-1', 'owner', '2026-03-14T10:00:00')
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
            for row in connection.execute("PRAGMA table_info('group_members')").fetchall()
        }
        assert "group_jid" not in columns
        row = connection.execute(
            "SELECT group_folder, added_by FROM group_members WHERE group_folder = ? AND user_id = ?",
            ("group-demo", "user-1"),
        ).fetchone()
    finally:
        connection.close()

    assert "group_folder" in columns
    assert columns["group_folder"][3] == 1
    assert "added_by" in columns
    assert columns["added_by"][3] == 0
    assert row == ("group-demo", None)

    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            INSERT INTO group_members (group_folder, user_id, role, joined_at, added_by)
            VALUES ('project-alpha', 'user-2', 'member', '2026-03-14T10:05:00', 'user-1')
            """
        )
        inserted = connection.execute(
            """
            SELECT group_folder, user_id, role, added_by
            FROM group_members
            WHERE group_folder = 'project-alpha' AND user_id = 'user-2'
            """
        ).fetchone()
        connection.commit()
    finally:
        connection.close()

    assert inserted == ("project-alpha", "user-2", "member", "user-1")
