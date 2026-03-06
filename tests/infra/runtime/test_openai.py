from __future__ import annotations

import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class FakeResult:
    def __init__(self, events: list[object]) -> None:
        self._events = events

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
        def run_streamed(agent: object, input: str) -> FakeResult:  # noqa: A002
            captured["input"] = input
            captured["agent"] = agent
            return FakeResult(
                [
                    SimpleNamespace(type="agent_updated_stream_event", new_agent=SimpleNamespace(name="Portex")),
                    SimpleNamespace(type="unknown"),
                    SimpleNamespace(
                        type="raw_response_event",
                        data=SimpleNamespace(type="response.output_text.delta", delta="hello"),
                    ),
                ]
            )

    monkeypatch.setattr("infra.runtime.openai.Agent", FakeAgent)
    monkeypatch.setattr("infra.runtime.openai.Runner", FakeRunner)

    runtime = OpenAIAgentsRuntime(tools=["tool-a"])
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
    assert len(events) == 2
    assert events[0].event_type == "run.started"
    assert events[1].event_type == "run.token.delta"


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
        def run_streamed(agent: object, input: str) -> BlockingResult:  # noqa: A002
            _ = agent
            _ = input
            return result

    monkeypatch.setattr("infra.runtime.openai.Runner", FakeRunner)

    runtime = OpenAIAgentsRuntime(tools=[])
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
        ]
    )

    class FakeRunner:
        @staticmethod
        def run_streamed(agent: object, input: str) -> FakeResult:  # noqa: A002
            _ = agent
            _ = input
            return result

    monkeypatch.setattr("infra.runtime.openai.Runner", FakeRunner)

    runtime = OpenAIAgentsRuntime(tools=[])
    request = RunRequest(
        request_id="run-2",
        group_folder="group-a",
        message="hi",
        session_id="session-1",
        user_id="user-1",
    )

    events = [event async for event in runtime.run_streamed(request)]

    assert len(events) == 2
    assert runtime._active_streamed_runs == {}
