from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_run_event_payload_uses_independent_default_dicts() -> None:
    from infra.runtime.adapter import RunEvent

    first = RunEvent(event_type="run.started", run_id="run-1")
    second = RunEvent(event_type="run.started", run_id="run-2")

    first.payload["k"] = "v"

    assert second.payload == {}


def test_run_request_contains_runtime_fields() -> None:
    from infra.runtime.adapter import RunRequest

    request = RunRequest(
        request_id="req-1",
        group_folder="group-a",
        message="hello",
        session_id="session-1",
        user_id="user-1",
    )

    assert request.request_id == "req-1"
    assert request.group_folder == "group-a"
    assert request.message == "hello"
    assert request.session_id == "session-1"
    assert request.user_id == "user-1"
