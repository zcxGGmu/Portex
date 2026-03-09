from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_user_model_declares_expected_default_columns() -> None:
    from domain.models.user import User

    role = User.__table__.c.role
    status = User.__table__.c.status
    permissions = User.__table__.c.permissions
    must_change_password = User.__table__.c.must_change_password
    created_at = User.__table__.c.created_at
    updated_at = User.__table__.c.updated_at

    assert role.nullable is False
    assert role.default is not None
    assert role.default.arg == "member"

    assert status.nullable is False
    assert status.default is not None
    assert status.default.arg == "active"

    assert permissions.nullable is False
    assert permissions.default is not None
    assert permissions.default.arg == "[]"

    assert must_change_password.nullable is False
    assert must_change_password.default is not None
    assert must_change_password.default.arg is False

    assert created_at.nullable is False
    assert created_at.default is not None
    assert callable(created_at.default.arg)
    assert created_at.default.arg.__name__ == "utcnow"

    assert updated_at.nullable is False
    assert updated_at.default is not None
    assert callable(updated_at.default.arg)
    assert updated_at.default.arg.__name__ == "utcnow"


def test_message_and_task_models_keep_expected_runtime_defaults() -> None:
    from domain.models.message import Message
    from domain.models.task import ScheduledTask

    timestamp = Message.__table__.c.timestamp
    is_from_me = Message.__table__.c.is_from_me
    attachments = Message.__table__.c.attachments
    status = ScheduledTask.__table__.c.status
    next_run = ScheduledTask.__table__.c.next_run
    created_at = ScheduledTask.__table__.c.created_at

    assert timestamp.nullable is False
    assert timestamp.default is not None
    assert callable(timestamp.default.arg)
    assert timestamp.default.arg.__name__ == "utcnow"

    assert is_from_me.nullable is False
    assert is_from_me.default is not None
    assert is_from_me.default.arg is False

    assert attachments.nullable is True

    assert status.nullable is False
    assert status.default is not None
    assert status.default.arg == "active"

    assert next_run.nullable is True

    assert created_at.nullable is False
    assert created_at.default is not None
    assert callable(created_at.default.arg)
    assert created_at.default.arg.__name__ == "utcnow"


def test_invite_and_session_models_keep_expected_optional_fields() -> None:
    from domain.models.invite_code import InviteCode
    from domain.models.session import Session

    role = InviteCode.__table__.c.role
    permission_template = InviteCode.__table__.c.permission_template
    expires_at = InviteCode.__table__.c.expires_at
    used_by = InviteCode.__table__.c.used_by
    used_at = InviteCode.__table__.c.used_at
    agent_id = Session.__table__.c.agent_id

    assert role.nullable is False
    assert role.default is not None
    assert role.default.arg == "member"

    assert permission_template.nullable is True
    assert expires_at.nullable is True
    assert used_by.nullable is True
    assert used_at.nullable is True

    assert Session.__table__.c.group_folder.primary_key is True
    assert Session.__table__.c.session_id.primary_key is True

    assert agent_id.nullable is False
    assert agent_id.default is not None
    assert agent_id.default.arg == ""
