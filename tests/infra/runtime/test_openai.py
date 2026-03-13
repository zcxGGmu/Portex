from __future__ import annotations

import asyncio
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class FakeResult:
    def __init__(self, events: list[object], *, final_output: object = None) -> None:
        self._events = events
        self.final_output = final_output

    async def stream_events(self):
        for event in self._events:
            yield event


class BlockingResult:
    def __init__(self, events: list[object]) -> None:
        self._events = events
        self.started = asyncio.Event()
        self.finish = asyncio.Event()
        self.cancel_calls = 0

    def cancel(self) -> None:
        self.cancel_calls += 1
        self.finish.set()

    async def stream_events(self):
        self.started.set()
        for index, event in enumerate(self._events):
            yield event
            if index == 0:
                await self.finish.wait()


@pytest.mark.asyncio
async def test_openai_runtime_maps_stream_events(monkeypatch: pytest.MonkeyPatch) -> None:
    from infra.runtime.adapter import RunRequest
    from infra.runtime.openai import OpenAIAgentsRuntime

    captured: dict[str, object] = {}

    class FakeAgent:
        def __init__(self, *, name: str, instructions: str, tools: list[object]) -> None:
            captured["agent_name"] = name
            captured["instructions"] = instructions
            captured["tools"] = tools

    class FakeRunner:
        @staticmethod
        def run_streamed(agent: object, input: str, session=None) -> FakeResult:  # noqa: A002
            captured["input"] = input
            captured["agent"] = agent
            captured["session"] = session
            return FakeResult(
                [
                    SimpleNamespace(type="agent_updated_stream_event", new_agent=SimpleNamespace(name="Portex")),
                    SimpleNamespace(type="unknown"),
                    SimpleNamespace(
                        type="raw_response_event",
                        data=SimpleNamespace(type="response.output_text.delta", delta="hello"),
                    ),
                    SimpleNamespace(
                        type="raw_response_event",
                        data=SimpleNamespace(type="response.completed"),
                    ),
                ],
                final_output="hello world",
            )

    monkeypatch.setattr("infra.runtime.openai.Agent", FakeAgent)
    monkeypatch.setattr("infra.runtime.openai.Runner", FakeRunner)

    runtime = OpenAIAgentsRuntime(
        tools=["tool-a"],
        session_factory=lambda _request: object(),
    )
    request = RunRequest(
        request_id="run-1",
        group_folder="group-a",
        message="hi",
        session_id="session-1",
        user_id="user-1",
    )

    events = [event async for event in runtime.run_streamed(request)]

    assert captured["agent_name"] == "PortexAgent"
    assert captured["input"] == "hi"
    assert captured["session"] is not None
    assert len(events) == 3
    assert events[0].event_type == "run.started"
    assert events[1].event_type == "run.token.delta"
    assert events[2].event_type == "run.completed"
    assert events[2].payload["final_output"] == "hello world"


@pytest.mark.asyncio
async def test_openai_runtime_cancel_delegates_to_active_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    from infra.runtime.adapter import RunRequest
    from infra.runtime.openai import OpenAIAgentsRuntime

    result = BlockingResult(
        [
            SimpleNamespace(type="agent_updated_stream_event", new_agent=SimpleNamespace(name="Portex")),
            SimpleNamespace(
                type="raw_response_event",
                data=SimpleNamespace(type="response.output_text.delta", delta="hello"),
            ),
        ]
    )

    class FakeRunner:
        @staticmethod
        def run_streamed(agent: object, input: str, session=None) -> BlockingResult:  # noqa: A002
            _ = agent
            _ = input
            _ = session
            return result

    monkeypatch.setattr("infra.runtime.openai.Runner", FakeRunner)

    runtime = OpenAIAgentsRuntime(
        tools=[],
        session_factory=lambda _request: object(),
    )
    request = RunRequest(
        request_id="run-1",
        group_folder="group-a",
        message="hi",
        session_id="session-1",
        user_id="user-1",
    )

    async def consume() -> list[object]:
        return [event async for event in runtime.run_streamed(request)]

    consumer = asyncio.create_task(consume())
    await asyncio.wait_for(result.started.wait(), timeout=1)
    await asyncio.sleep(0)

    assert "run-1" in runtime._active_streamed_runs

    assert await runtime.cancel("run-1") is None
    assert result.cancel_calls == 1

    events = await asyncio.wait_for(consumer, timeout=1)

    assert len(events) == 2
    assert runtime._active_streamed_runs == {}


@pytest.mark.asyncio
async def test_openai_runtime_cleans_up_stream_registry_after_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from infra.runtime.adapter import RunRequest
    from infra.runtime.openai import OpenAIAgentsRuntime

    result = FakeResult(
        [
            SimpleNamespace(type="agent_updated_stream_event", new_agent=SimpleNamespace(name="Portex")),
            SimpleNamespace(
                type="raw_response_event",
                data=SimpleNamespace(type="response.output_text.delta", delta="done"),
            ),
            SimpleNamespace(
                type="raw_response_event",
                data=SimpleNamespace(type="response.completed"),
            ),
        ],
        final_output="done",
    )

    class FakeRunner:
        @staticmethod
        def run_streamed(agent: object, input: str, session=None) -> FakeResult:  # noqa: A002
            _ = agent
            _ = input
            _ = session
            return result

    monkeypatch.setattr("infra.runtime.openai.Runner", FakeRunner)

    runtime = OpenAIAgentsRuntime(
        tools=[],
        session_factory=lambda _request: object(),
    )
    request = RunRequest(
        request_id="run-2",
        group_folder="group-a",
        message="hi",
        session_id="session-1",
        user_id="user-1",
    )

    events = [event async for event in runtime.run_streamed(request)]

    assert len(events) == 3
    assert runtime._active_streamed_runs == {}
    assert events[-1].event_type == "run.completed"
    assert events[-1].payload["final_output"] == "done"


@pytest.mark.asyncio
async def test_openai_runtime_uses_injected_session_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    from infra.runtime.adapter import RunRequest
    from infra.runtime.openai import OpenAIAgentsRuntime

    captured: dict[str, object] = {}
    sentinel_session = object()

    class FakeRunner:
        @staticmethod
        def run_streamed(agent: object, input: str, session=None) -> FakeResult:  # noqa: A002
            _ = agent
            captured["input"] = input
            captured["session"] = session
            return FakeResult(
                [
                    SimpleNamespace(type="agent_updated_stream_event", new_agent=SimpleNamespace(name="Portex")),
                    SimpleNamespace(
                        type="raw_response_event",
                        data=SimpleNamespace(type="response.completed"),
                    ),
                ],
                final_output="done",
            )

    monkeypatch.setattr("infra.runtime.openai.Runner", FakeRunner)

    runtime = OpenAIAgentsRuntime(
        tools=[],
        session_factory=lambda request: sentinel_session if request.session_id == "session-1" else None,
    )
    request = RunRequest(
        request_id="run-3",
        group_folder="group-a",
        message="follow up",
        session_id="session-1",
        user_id="user-1",
    )

    events = [event async for event in runtime.run_streamed(request)]

    assert captured["input"] == "follow up"
    assert captured["session"] is sentinel_session
    assert events[-1].event_type == "run.completed"


def test_openai_runtime_default_session_factory_uses_group_scoped_sqlite_db(
    tmp_path: Path,
) -> None:
    from agents.memory import SQLiteSession
    from infra.runtime.adapter import RunRequest
    from infra.runtime.openai import DEFAULT_SESSION_DB_FILENAME, OpenAIAgentsRuntime

    runtime = OpenAIAgentsRuntime(tools=[], session_data_root=tmp_path)
    request = RunRequest(
        request_id="run-4",
        group_folder="group-a",
        message="hello",
        session_id="session-1",
        user_id="user-1",
    )

    session = runtime._session_factory(request)

    assert isinstance(session, SQLiteSession)
    assert session.session_id == "session-1"
    assert Path(session.db_path) == tmp_path / "group-a" / DEFAULT_SESSION_DB_FILENAME
    assert (tmp_path / "group-a").is_dir()


@pytest.mark.asyncio
async def test_openai_runtime_wraps_session_storage_errors_as_resume_failures() -> None:
    from infra.runtime.adapter import RunRequest
    from infra.runtime.openai import OpenAIAgentsRuntime, OpenAIRuntimeSessionError

    runtime = OpenAIAgentsRuntime(
        tools=[],
        session_factory=lambda _request: (_ for _ in ()).throw(sqlite3.DatabaseError("broken")),
    )
    request = RunRequest(
        request_id="run-5",
        group_folder="group-a",
        message="hello",
        session_id="session-1",
        user_id="user-1",
    )

    with pytest.raises(OpenAIRuntimeSessionError, match="broken"):
        [event async for event in runtime.run_streamed(request)]
