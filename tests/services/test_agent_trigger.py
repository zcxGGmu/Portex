from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class FakeWebSocketManager:
    def __init__(self) -> None:
        self.sent_messages: list[tuple[str, str]] = []

    async def send_message(self, message: str, room: str) -> None:
        self.sent_messages.append((message, room))


class BlockingResult:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.finished = asyncio.Event()
        self.cancel_calls = 0

    def cancel(self) -> None:
        self.cancel_calls += 1
        self.finished.set()

    async def stream_events(self):
        self.started.set()
        yield SimpleNamespace(type="agent_updated_stream_event", new_agent=SimpleNamespace(name="Portex"))
        await self.finished.wait()


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


@pytest.mark.asyncio
async def test_trigger_agent_execution_completes_after_runtime_cancel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from infra.runtime.openai import OpenAIAgentsRuntime
    from services.agent_trigger import trigger_agent_execution

    result = BlockingResult()

    class FakeRunner:
        @staticmethod
        def run_streamed(agent: object, input: str) -> BlockingResult:  # noqa: A002
            _ = (agent, input)
            return result

    monkeypatch.setattr("infra.runtime.openai.Runner", FakeRunner)

    runtime = OpenAIAgentsRuntime(tools=[])
    manager = FakeWebSocketManager()

    execution = asyncio.create_task(
        trigger_agent_execution(
            group_folder="group-cancel",
            message="hello",
            user_id="user-cancel",
            websocket_manager=manager,
            runtime_factory=lambda _group: runtime,
            request_id="run-cancel",
        )
    )

    await asyncio.wait_for(result.started.wait(), timeout=1)
    await runtime.cancel("run-cancel")

    run_id = await asyncio.wait_for(execution, timeout=1)

    assert run_id == "run-cancel"
    assert result.cancel_calls == 1
    assert len(manager.sent_messages) == 1

    payload = json.loads(manager.sent_messages[0][0])
    assert payload["event_type"] == "run.started"
    assert payload["run_id"] == "run-cancel"
