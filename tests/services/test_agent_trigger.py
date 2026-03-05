from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class FakeWebSocketManager:
    def __init__(self) -> None:
        self.sent_messages: list[tuple[str, str]] = []

    async def send_message(self, message: str, room: str) -> None:
        self.sent_messages.append((message, room))


@pytest.mark.asyncio
async def test_trigger_agent_execution_streams_runtime_events() -> None:
    from infra.runtime.adapter import RunEvent, RunRequest
    from services.agent_trigger import trigger_agent_execution

    class FakeRuntime:
        def __init__(self) -> None:
            self.received_requests: list[RunRequest] = []

        async def run_streamed(self, request: RunRequest):
            self.received_requests.append(request)
            yield RunEvent(event_type="run.started", run_id=request.request_id, payload={"step": 1})
            yield RunEvent(
                event_type="run.completed",
                run_id=request.request_id,
                payload={"final_output": "done"},
            )

        async def cancel(self, run_id: str) -> None:
            _ = run_id

    runtime = FakeRuntime()
    manager = FakeWebSocketManager()

    def runtime_factory(group_folder: str):
        assert group_folder == "group-a"
        return runtime

    def session_id_factory(group_folder: str) -> str:
        assert group_folder == "group-a"
        return "session-a"

    run_id = await trigger_agent_execution(
        group_folder="group-a",
        message="hello",
        user_id="user-a",
        websocket_manager=manager,
        runtime_factory=runtime_factory,
        session_id_factory=session_id_factory,
        request_id="run-fixed",
    )

    assert run_id == "run-fixed"
    assert len(runtime.received_requests) == 1

    request = runtime.received_requests[0]
    assert request.request_id == "run-fixed"
    assert request.group_folder == "group-a"
    assert request.message == "hello"
    assert request.session_id == "session-a"
    assert request.user_id == "user-a"

    assert len(manager.sent_messages) == 2
    first_message, first_room = manager.sent_messages[0]
    second_message, second_room = manager.sent_messages[1]

    assert first_room == "group-a"
    assert second_room == "group-a"

    first_payload = json.loads(first_message)
    second_payload = json.loads(second_message)

    assert first_payload["event_type"] == "run.started"
    assert second_payload["event_type"] == "run.completed"


@pytest.mark.asyncio
async def test_trigger_agent_execution_uses_group_folder_as_default_session_id() -> None:
    from infra.runtime.adapter import RunEvent, RunRequest
    from services.agent_trigger import trigger_agent_execution

    class FakeRuntime:
        def __init__(self) -> None:
            self.received_requests: list[RunRequest] = []

        async def run_streamed(self, request: RunRequest):
            self.received_requests.append(request)
            yield RunEvent(event_type="run.started", run_id=request.request_id)

        async def cancel(self, run_id: str) -> None:
            _ = run_id

    runtime = FakeRuntime()
    manager = FakeWebSocketManager()

    await trigger_agent_execution(
        group_folder="group-default",
        message="hi",
        user_id="user-default",
        websocket_manager=manager,
        runtime_factory=lambda _group: runtime,
        request_id="run-default",
    )

    assert runtime.received_requests[0].session_id == "group-default"
