from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from domain.models import Base, Message, RegisteredGroup, ScheduledTask, Session, User  # noqa: E402


def test_model_table_names() -> None:
    assert User.__tablename__ == "users"
    assert Message.__tablename__ == "messages"
    assert Session.__tablename__ == "sessions"
    assert RegisteredGroup.__tablename__ == "registered_groups"
    assert ScheduledTask.__tablename__ == "scheduled_tasks"


def test_model_key_fields_exist() -> None:
    user_columns = User.__table__.columns.keys()
    message_columns = Message.__table__.columns.keys()
    session_columns = Session.__table__.columns.keys()

    assert "username" in user_columns
    assert "attachments" in message_columns
    assert "group_folder" in session_columns


def test_shared_metadata_contains_all_tables() -> None:
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "users",
        "messages",
        "sessions",
        "registered_groups",
        "scheduled_tasks",
    }

    assert expected.issubset(table_names)
    assert User.metadata is Base.metadata
    assert Message.metadata is Base.metadata
    assert Session.metadata is Base.metadata
    assert RegisteredGroup.metadata is Base.metadata
    assert ScheduledTask.metadata is Base.metadata
