from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_unified_message_accepts_optional_group_folder_and_normalizes_timestamp() -> None:
    from domain.schemas import UnifiedMessage

    message = UnifiedMessage(
        channel="telegram",
        chat_jid="telegram:-3001",
        sender_id="4001",
        group_folder=None,
        content="hello unified",
        message_id="201",
        timestamp=datetime(2026, 3, 9, 12, 0, 0),
    )

    assert message.group_folder is None
    assert message.content == "hello unified"
    assert message.timestamp == datetime(2026, 3, 9, 12, 0, 0, tzinfo=timezone.utc)


def test_unified_message_allows_empty_content_for_non_text_messages() -> None:
    from domain.schemas import UnifiedMessage

    message = UnifiedMessage(
        channel="feishu",
        chat_jid="feishu:oc_chat",
        sender_id="ou_sender",
        group_folder="team-alpha",
        content="",
        message_id="om_message",
        timestamp=datetime(2026, 3, 9, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert message.content == ""
    assert message.group_folder == "team-alpha"


def test_unified_message_raises_explicit_error_when_timestamp_normalization_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import domain.schemas as schemas

    monkeypatch.setattr(schemas, "_normalize_utc_datetime", lambda value: None)

    with pytest.raises(ValueError, match="UnifiedMessage.timestamp normalization returned None"):
        schemas.UnifiedMessage(
            channel="web",
            chat_jid="group-demo",
            sender_id="user-1",
            group_folder="group-demo",
            content="hello",
            message_id="msg-1",
            timestamp=datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc),
        )


def test_task_run_log_response_raises_explicit_error_when_run_at_normalization_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import domain.schemas as schemas

    monkeypatch.setattr(schemas, "_normalize_utc_datetime", lambda value: None)

    with pytest.raises(ValueError, match="TaskRunLogResponse.run_at normalization returned None"):
        schemas.TaskRunLogResponse(
            id=1,
            task_id="task-1",
            run_at=datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc),
            duration_ms=25,
            status="success",
            result="ok",
        )
