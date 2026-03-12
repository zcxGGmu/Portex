"""Default execution-plane wiring for app entrypoints."""

from __future__ import annotations

from functools import lru_cache

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


__all__ = ["get_execution_coordinator", "reset_execution_coordinator"]
