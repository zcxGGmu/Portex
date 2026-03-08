from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from domain import models as domain_models  # noqa: E402
from domain.models import (  # noqa: E402
    Base,
    GroupMember,
    InviteCode,
    Message,
    RegisteredGroup,
    ScheduledTask,
    Session,
    User,
)


def _task_run_log_model():
    task_run_log = getattr(domain_models, "TaskRunLog", None)

    assert task_run_log is not None
    return task_run_log


def test_model_table_names() -> None:
    task_run_log = _task_run_log_model()

    assert User.__tablename__ == "users"
    assert GroupMember.__tablename__ == "group_members"
    assert InviteCode.__tablename__ == "invite_codes"
    assert Message.__tablename__ == "messages"
    assert Session.__tablename__ == "sessions"
    assert RegisteredGroup.__tablename__ == "registered_groups"
    assert ScheduledTask.__tablename__ == "scheduled_tasks"
    assert task_run_log.__tablename__ == "task_run_logs"


def test_model_key_fields_exist() -> None:
    task_run_log = _task_run_log_model()
    user_columns = User.__table__.columns.keys()
    group_member_columns = GroupMember.__table__.columns.keys()
    invite_columns = InviteCode.__table__.columns.keys()
    message_columns = Message.__table__.columns.keys()
    session_columns = Session.__table__.columns.keys()
    task_run_log_columns = task_run_log.__table__.columns.keys()

    assert "username" in user_columns
    assert "avatar_emoji" in user_columns
    assert "avatar_color" in user_columns
    assert "ai_name" in user_columns
    assert "ai_avatar_emoji" in user_columns
    assert "must_change_password" in user_columns
    assert "last_login_at" in user_columns
    assert "disable_reason" in user_columns
    assert "notes" in user_columns
    assert "group_jid" in group_member_columns
    assert "user_id" in group_member_columns
    assert "role" in group_member_columns
    assert "joined_at" in group_member_columns
    assert "role" in invite_columns
    assert "permission_template" in invite_columns
    assert "used_at" in invite_columns
    assert "attachments" in message_columns
    assert "group_folder" in session_columns
    assert "id" in task_run_log_columns
    assert "task_id" in task_run_log_columns
    assert "run_at" in task_run_log_columns
    assert "duration_ms" in task_run_log_columns
    assert "status" in task_run_log_columns
    assert "result" in task_run_log_columns
    assert "error" in task_run_log_columns


def test_user_model_extended_account_columns_have_expected_defaults() -> None:
    must_change_password = User.__table__.c.must_change_password
    disable_reason = User.__table__.c.disable_reason
    notes = User.__table__.c.notes
    last_login_at = User.__table__.c.last_login_at

    assert must_change_password.nullable is False
    assert must_change_password.default is not None
    assert must_change_password.default.arg is False
    assert disable_reason.nullable is True
    assert notes.nullable is True
    assert last_login_at.nullable is True


def test_invite_code_model_fields_have_expected_defaults() -> None:
    role = InviteCode.__table__.c.role
    permission_template = InviteCode.__table__.c.permission_template
    expires_at = InviteCode.__table__.c.expires_at
    used_by = InviteCode.__table__.c.used_by
    used_at = InviteCode.__table__.c.used_at

    assert role.nullable is False
    assert role.default is not None
    assert role.default.arg == "member"
    assert permission_template.nullable is True
    assert expires_at.nullable is True
    assert used_by.nullable is True
    assert used_at.nullable is True


def test_group_member_model_fields_have_expected_defaults() -> None:
    role = GroupMember.__table__.c.role
    joined_at = GroupMember.__table__.c.joined_at

    assert role.nullable is False
    assert joined_at.nullable is False
    assert joined_at.default is not None


def test_task_run_log_model_fields_have_expected_nullability() -> None:
    task_run_log = _task_run_log_model()

    task_id = task_run_log.__table__.c.task_id
    run_at = task_run_log.__table__.c.run_at
    duration_ms = task_run_log.__table__.c.duration_ms
    status = task_run_log.__table__.c.status
    result = task_run_log.__table__.c.result
    error = task_run_log.__table__.c.error

    assert task_id.nullable is False
    assert run_at.nullable is False
    assert duration_ms.nullable is False
    assert status.nullable is False
    assert result.nullable is True
    assert error.nullable is True


def test_shared_metadata_contains_all_tables() -> None:
    task_run_log = _task_run_log_model()
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "users",
        "group_members",
        "invite_codes",
        "messages",
        "sessions",
        "registered_groups",
        "scheduled_tasks",
        "task_run_logs",
    }

    assert expected.issubset(table_names)
    assert User.metadata is Base.metadata
    assert GroupMember.metadata is Base.metadata
    assert InviteCode.metadata is Base.metadata
    assert Message.metadata is Base.metadata
    assert Session.metadata is Base.metadata
    assert RegisteredGroup.metadata is Base.metadata
    assert ScheduledTask.metadata is Base.metadata
    assert task_run_log.metadata is Base.metadata
