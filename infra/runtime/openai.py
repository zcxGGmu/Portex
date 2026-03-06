"""OpenAI Agents runtime adapter implementation."""

from __future__ import annotations

from typing import Any, AsyncIterator

from agents import Agent, RunResultStreaming, Runner

from .adapter import AgentRuntime, RunEvent, RunRequest
from .mapper import map_sdk_event

DEFAULT_AGENT_NAME = "PortexAgent"
DEFAULT_AGENT_INSTRUCTIONS = "你是一个专业的 AI 助手"


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

    async def run_streamed(self, request: RunRequest) -> AsyncIterator[RunEvent]:
        result = Runner.run_streamed(self.agent, input=request.message)
        self._active_streamed_runs[request.request_id] = result
        try:
            async for sdk_event in result.stream_events():
                mapped_event = map_sdk_event(sdk_event, run_id=request.request_id)
                if mapped_event is not None:
                    yield mapped_event
        finally:
            self._active_streamed_runs.pop(request.request_id, None)

    async def cancel(self, run_id: str) -> None:
        result = self._active_streamed_runs.get(run_id)
        if result is not None:
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
