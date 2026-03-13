"""OpenAI Agents runtime adapter implementation."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, AsyncIterator
from collections.abc import Callable

from agents import Agent, RunResultStreaming, Runner
from agents.memory import SQLiteSession

from .adapter import AgentRuntime, RunEvent, RunRequest
from .mapper import map_sdk_event
from infra.exec.security import validate_path

DEFAULT_AGENT_NAME = "PortexAgent"
DEFAULT_AGENT_INSTRUCTIONS = "你是一个专业的 AI 助手"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SESSION_DATA_ROOT = PROJECT_ROOT / "data" / "sessions"
DEFAULT_SESSION_DB_FILENAME = "agents-sdk.sqlite3"

SessionFactory = Callable[[RunRequest], object | None]


class OpenAIRuntimeSessionError(RuntimeError):
    """Raised when runtime session persistence cannot be resumed safely."""


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
        session_factory: SessionFactory | None = None,
        session_data_root: str | Path | None = None,
    ) -> None:
        self.agent = Agent(
            name=agent_name,
            instructions=instructions,
            tools=tools or [],
        )
        self._session_data_root = Path(
            session_data_root or DEFAULT_SESSION_DATA_ROOT
        ).expanduser().resolve()
        self._session_factory = session_factory or self._default_session_factory
        self._active_streamed_runs: dict[str, RunResultStreaming] = {}
        self._cancelled_run_ids: set[str] = set()

    async def run_streamed(self, request: RunRequest) -> AsyncIterator[RunEvent]:
        try:
            session = self._session_factory(request)
            result = Runner.run_streamed(self.agent, input=request.message, session=session)
        except Exception as exc:
            if self._is_session_error(exc):
                raise OpenAIRuntimeSessionError(str(exc)) from exc
            raise
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

    def _default_session_factory(self, request: RunRequest) -> SQLiteSession:
        return SQLiteSession(
            session_id=request.session_id,
            db_path=self._session_db_path(request.group_folder),
        )

    def _session_db_path(self, group_folder: str) -> Path:
        group_dir = (self._session_data_root / group_folder).resolve()
        if not validate_path(group_dir, [self._session_data_root]):
            raise OpenAIRuntimeSessionError(
                f"session path for group '{group_folder}' escapes the configured root"
            )
        group_dir.mkdir(parents=True, exist_ok=True)
        return group_dir / DEFAULT_SESSION_DB_FILENAME

    def _is_session_error(self, exc: Exception) -> bool:
        return isinstance(exc, (sqlite3.Error, OSError))


# Backward-compat alias for early scaffold naming.
OpenAIRuntimeAdapter = OpenAIAgentsRuntime

__all__ = [
    "DEFAULT_AGENT_INSTRUCTIONS",
    "DEFAULT_AGENT_NAME",
    "DEFAULT_SESSION_DATA_ROOT",
    "DEFAULT_SESSION_DB_FILENAME",
    "OpenAIRuntimeSessionError",
    "OpenAIAgentsRuntime",
    "OpenAIRuntimeAdapter",
    "SessionFactory",
]
