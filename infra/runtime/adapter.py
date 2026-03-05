"""Runtime adapter abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Protocol, runtime_checkable


@dataclass(slots=True)
class RunRequest:
    request_id: str
    group_folder: str
    message: str
    session_id: str
    user_id: str


@dataclass(slots=True)
class RunEvent:
    event_type: str
    run_id: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RunResult:
    status: str
    final_output: str


@runtime_checkable
class AgentRuntime(Protocol):
    async def run_streamed(self, request: RunRequest) -> AsyncIterator[RunEvent]:
        ...

    async def cancel(self, run_id: str) -> None:
        ...


__all__ = ["AgentRuntime", "RunEvent", "RunRequest", "RunResult"]
