"""OpenAI Agents runtime adapter implementation."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

from agents import Agent, RunResultStreaming, Runner

from .adapter import AgentRuntime, RunEvent, RunRequest
from .mapper import map_sdk_event

DEFAULT_AGENT_NAME = "PortexAgent"
DEFAULT_AGENT_INSTRUCTIONS = "你是一个专业的 AI 助手"


def _stringify_final_output(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if hasattr(value, "model_dump"):
        return json.dumps(value.model_dump(mode="json"), ensure_ascii=False)
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return str(value)


class OpenAIAgentsRuntime(AgentRuntime):
    """Runtime adapter backed by OpenAI Agents SDK."""

    def __init__(
        self,
        tools: list[Any] | None = None,
        *,
        agent_name: str = DEFAULT_AGENT_NAME,
        instructions: str = DEFAULT_AGENT_INSTRUCTIONS,
    ) -> None:
        self.agent = Agent(
            name=agent_name,
            instructions=instructions,
            tools=tools or [],
        )
        self._active_streamed_runs: dict[str, RunResultStreaming] = {}
        self._cancelled_run_ids: set[str] = set()

    async def run_streamed(self, request: RunRequest) -> AsyncIterator[RunEvent]:
        result = Runner.run_streamed(self.agent, input=request.message)
        self._active_streamed_runs[request.request_id] = result
        try:
            async for sdk_event in result.stream_events():
                mapped_event = map_sdk_event(sdk_event, run_id=request.request_id)
                if mapped_event is not None:
                    yield mapped_event
            if request.request_id not in self._cancelled_run_ids:
                final_output = _stringify_final_output(getattr(result, "final_output", None))
                yield RunEvent(
                    event_type="run.completed",
                    run_id=request.request_id,
                    payload={
                        "status": "response.completed",
                        "final_output": final_output,
                    },
                )
        finally:
            self._active_streamed_runs.pop(request.request_id, None)
            self._cancelled_run_ids.discard(request.request_id)

    async def cancel(self, run_id: str) -> None:
        result = self._active_streamed_runs.get(run_id)
        if result is not None:
            self._cancelled_run_ids.add(run_id)
            result.cancel()
        return None


# Backward-compat alias for early scaffold naming.
OpenAIRuntimeAdapter = OpenAIAgentsRuntime

__all__ = [
    "DEFAULT_AGENT_INSTRUCTIONS",
    "DEFAULT_AGENT_NAME",
    "OpenAIAgentsRuntime",
    "OpenAIRuntimeAdapter",
]
