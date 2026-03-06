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


@pytest.mark.asyncio
async def test_trigger_agent_execution_returns_run_id_and_broadcasts_timeout() -> None:
    from infra.runtime.adapter import RunEvent, RunRequest
    from services.agent_trigger import trigger_agent_execution

    class SlowRuntime:
        def __init__(self) -> None:
            self.received_requests: list[RunRequest] = []
            self.cancelled_run_ids: list[str] = []

        async def run_streamed(self, request: RunRequest):
            self.received_requests.append(request)
            yield RunEvent(event_type="run.started", run_id=request.request_id)
            await asyncio.sleep(0.05)
            yield RunEvent(event_type="run.completed", run_id=request.request_id)

        async def cancel(self, run_id: str) -> None:
            self.cancelled_run_ids.append(run_id)

    runtime = SlowRuntime()
    manager = FakeWebSocketManager()

    run_id = await asyncio.wait_for(
        trigger_agent_execution(
            group_folder="group-timeout",
            message="hello timeout",
            user_id="user-timeout",
            websocket_manager=manager,
            runtime_factory=lambda _group: runtime,
            request_id="run-timeout",
            timeout_ms=10,
        ),
        timeout=1,
    )

    assert run_id == "run-timeout"
    assert runtime.cancelled_run_ids == ["run-timeout"]
    assert len(manager.sent_messages) == 2

    started_payload = json.loads(manager.sent_messages[0][0])
    timeout_payload = json.loads(manager.sent_messages[1][0])

    assert started_payload["event_type"] == "run.started"
    assert timeout_payload == {
        "event_type": "run.timeout",
        "run_id": "run-timeout",
        "payload": {
            "status": "timeout",
            "timeout_ms": 10,
        },
    }
    assert manager.sent_messages[1][1] == "group-timeout"


@pytest.mark.asyncio
async def test_trigger_agent_execution_timeout_cancels_active_openai_stream(
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

    run_id = await asyncio.wait_for(
        trigger_agent_execution(
            group_folder="group-openai-timeout",
            message="hello openai timeout",
            user_id="user-openai-timeout",
            websocket_manager=manager,
            runtime_factory=lambda _group: runtime,
            request_id="run-openai-timeout",
            timeout_ms=10,
        ),
        timeout=1,
    )

    assert run_id == "run-openai-timeout"
    assert result.cancel_calls == 1
    assert len(manager.sent_messages) == 2

    timeout_payload = json.loads(manager.sent_messages[1][0])
    assert timeout_payload["event_type"] == "run.timeout"
    assert timeout_payload["run_id"] == "run-openai-timeout"


@pytest.mark.asyncio
async def test_trigger_agent_execution_does_not_cancel_before_timeout() -> None:
    from infra.runtime.adapter import RunEvent, RunRequest
    from services.agent_trigger import trigger_agent_execution

    class FastRuntime:
        def __init__(self) -> None:
            self.received_requests: list[RunRequest] = []
            self.cancelled_run_ids: list[str] = []

        async def run_streamed(self, request: RunRequest):
            self.received_requests.append(request)
            yield RunEvent(event_type="run.started", run_id=request.request_id)
            await asyncio.sleep(0.001)
            yield RunEvent(
                event_type="run.completed",
                run_id=request.request_id,
                payload={"status": "ok"},
            )

        async def cancel(self, run_id: str) -> None:
            self.cancelled_run_ids.append(run_id)

    runtime = FastRuntime()
    manager = FakeWebSocketManager()

    run_id = await trigger_agent_execution(
        group_folder="group-fast",
        message="hello fast",
        user_id="user-fast",
        websocket_manager=manager,
        runtime_factory=lambda _group: runtime,
        request_id="run-fast",
        timeout_ms=200,
    )

    assert run_id == "run-fast"
    assert runtime.cancelled_run_ids == []
    assert len(manager.sent_messages) == 2

    started_payload = json.loads(manager.sent_messages[0][0])
    completed_payload = json.loads(manager.sent_messages[1][0])

    assert started_payload["event_type"] == "run.started"
    assert completed_payload["event_type"] == "run.completed"
    assert completed_payload["payload"] == {"status": "ok"}


@pytest.mark.asyncio
async def test_trigger_agent_execution_propagates_internal_timeout_error() -> None:
    from infra.runtime.adapter import RunEvent, RunRequest
    from services.agent_trigger import trigger_agent_execution

    class TimeoutRuntime:
        def __init__(self) -> None:
            self.received_requests: list[RunRequest] = []
            self.cancelled_run_ids: list[str] = []

        async def run_streamed(self, request: RunRequest):
            self.received_requests.append(request)
            yield RunEvent(event_type="run.started", run_id=request.request_id)
            raise TimeoutError("runtime internal timeout")

        async def cancel(self, run_id: str) -> None:
            self.cancelled_run_ids.append(run_id)

    runtime = TimeoutRuntime()
    manager = FakeWebSocketManager()

    with pytest.raises(TimeoutError, match="runtime internal timeout"):
        await trigger_agent_execution(
            group_folder="group-internal-timeout",
            message="hello internal timeout",
            user_id="user-internal-timeout",
            websocket_manager=manager,
            runtime_factory=lambda _group: runtime,
            request_id="run-internal-timeout",
            timeout_ms=200,
        )

    assert runtime.cancelled_run_ids == []
    assert len(manager.sent_messages) == 1

    payload = json.loads(manager.sent_messages[0][0])
    assert payload["event_type"] == "run.started"


@pytest.mark.asyncio
async def test_trigger_agent_execution_cleans_up_consumer_task_on_outer_cancellation() -> None:
    from infra.runtime.adapter import RunEvent, RunRequest
    from services.agent_trigger import trigger_agent_execution

    class HangingRuntime:
        def __init__(self) -> None:
            self.received_requests: list[RunRequest] = []
            self.active_streams = 0
            self.started = asyncio.Event()

        async def run_streamed(self, request: RunRequest):
            self.received_requests.append(request)
            self.active_streams += 1
            self.started.set()
            try:
                yield RunEvent(event_type="run.started", run_id=request.request_id)
                await asyncio.Future()
            finally:
                self.active_streams -= 1

        async def cancel(self, run_id: str) -> None:
            _ = run_id

    runtime = HangingRuntime()
    manager = FakeWebSocketManager()

    execution = asyncio.create_task(
        trigger_agent_execution(
            group_folder="group-outer-cancel",
            message="hello outer cancel",
            user_id="user-outer-cancel",
            websocket_manager=manager,
            runtime_factory=lambda _group: runtime,
            request_id="run-outer-cancel",
            timeout_ms=300_000,
        )
    )

    await asyncio.wait_for(runtime.started.wait(), timeout=1)
    execution.cancel()

    with pytest.raises(asyncio.CancelledError):
        await execution

    await asyncio.sleep(0)
    assert runtime.active_streams == 0
