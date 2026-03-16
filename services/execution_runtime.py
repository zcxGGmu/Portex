"""Default execution-plane wiring for app entrypoints."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from domain.schemas import MonitorBackendHealthResponse
from infra.exec.container_manager import ContainerManager
from infra.exec.docker import DockerClient
from infra.exec.process import ProcessExecutor
from infra.runtime.openai import OpenAIAgentsRuntime
from services.execution_backends import (
    ContainerBackend,
    HostProcessBackend,
    OpenAIRuntimeBackend,
)
from services.execution_coordinator import ExecutionCoordinator
from services.execution_policy import ExecutionPolicy
from services.terminal_bridge import DockerExecTerminalBridge
from services.terminal_sessions import TerminalSessionService


def _default_runtime_factory(group_folder: str) -> OpenAIAgentsRuntime:
    _ = group_folder
    return OpenAIAgentsRuntime(tools=[])


@lru_cache(maxsize=1)
def get_execution_coordinator() -> ExecutionCoordinator:
    return ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={
            "openai_runtime": OpenAIRuntimeBackend(
                runtime_factory=_default_runtime_factory,
            ),
            "host_process": HostProcessBackend(
                process_executor=ProcessExecutor(),
            ),
            "docker_container": ContainerBackend(
                container_manager=ContainerManager(DockerClient()),
            ),
        },
    )


def reset_execution_coordinator() -> None:
    get_execution_coordinator.cache_clear()


@lru_cache(maxsize=1)
def get_terminal_session_service() -> TerminalSessionService:
    container_manager = ContainerManager(DockerClient())
    return TerminalSessionService(
        bridge_factory=lambda **kwargs: DockerExecTerminalBridge(
            container_manager=container_manager,
            group_folder=kwargs["group_folder"],
            owner_user_id=kwargs["owner_user_id"],
            session_id=kwargs["session_id"],
        ),
        recover_active_sessions=True,
    )


def reset_terminal_session_service() -> None:
    get_terminal_session_service.cache_clear()


def build_monitor_backend_health(
    coordinator: ExecutionCoordinator,
) -> list[MonitorBackendHealthResponse]:
    reports: list[MonitorBackendHealthResponse] = []
    for backend_name in coordinator.list_backend_names():
        backend = coordinator.get_backend(backend_name)
        if backend is None:
            reports.append(
                MonitorBackendHealthResponse(
                    backend=backend_name,
                    status="error",
                    detail="backend is not registered",
                )
            )
            continue
        reports.append(_probe_backend_health(backend_name, backend))
    return reports


def _probe_backend_health(backend_name: str, backend: Any) -> MonitorBackendHealthResponse:
    try:
        if backend_name == "openai_runtime":
            backend._runtime_factory("__monitor__")
            return MonitorBackendHealthResponse(
                backend=backend_name,
                status="ok",
                detail="runtime factory available",
            )
        if backend_name == "host_process":
            backend._process_executor.validate_runner_root()
            return MonitorBackendHealthResponse(
                backend=backend_name,
                status="ok",
                detail="host runner root validated",
            )
        if backend_name == "docker_container":
            backend._container_manager.client.list_containers(all=False)
            return MonitorBackendHealthResponse(
                backend=backend_name,
                status="ok",
                detail="docker daemon reachable",
            )
        return MonitorBackendHealthResponse(
            backend=backend_name,
            status="ok",
            detail="backend registered",
        )
    except Exception as exc:
        return MonitorBackendHealthResponse(
            backend=backend_name,
            status="error",
            detail=str(exc),
        )


__all__ = [
    "build_monitor_backend_health",
    "get_execution_coordinator",
    "get_terminal_session_service",
    "reset_execution_coordinator",
    "reset_terminal_session_service",
]
