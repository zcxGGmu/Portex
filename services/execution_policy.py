"""Execution backend selection policy for M7.2."""

from __future__ import annotations

from services.execution_coordinator import ExecutionRequest

DEFAULT_BACKEND = "openai_runtime"
MODE_TO_BACKEND = {
    "openai": "openai_runtime",
    "host": "host_process",
    "container": "docker_container",
}


class ExecutionPolicy:
    """Select one backend for an execution request."""

    def select_backend(self, request: ExecutionRequest) -> str:
        if request.requested_mode is None:
            return DEFAULT_BACKEND

        backend = MODE_TO_BACKEND.get(request.requested_mode)
        if backend is None:
            raise ValueError(f"unsupported execution mode: {request.requested_mode}")
        return backend


__all__ = ["DEFAULT_BACKEND", "ExecutionPolicy", "MODE_TO_BACKEND"]
