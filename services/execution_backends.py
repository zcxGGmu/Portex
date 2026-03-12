"""Execution backend adapters for M7.2.2."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
import json
import math
from pathlib import Path
import sys
from typing import Any

from infra.exec.container_manager import CONTAINER_COMMAND, CONTAINER_WORKDIR, ContainerManager
from infra.exec.process import ProcessExecutor
from infra.runtime.adapter import AgentRuntime, RunEvent
from services.agent_trigger import RuntimeFactory, RunEventHandler, run_agent_execution
from services.execution_coordinator import ExecutionRequest

OUTPUT_START_MARKER = "---PORTEX_OUTPUT_START---"
OUTPUT_END_MARKER = "---PORTEX_OUTPUT_END---"
DEFAULT_DOCKER_EXECUTABLE = "docker"

_REQUEST_METADATA_STORE: dict[int, Mapping[str, Any] | None] = {}


def _install_request_metadata_property() -> None:
    if hasattr(ExecutionRequest, "request_metadata"):
        return

    def getter(request: ExecutionRequest) -> Mapping[str, Any] | None:
        return _REQUEST_METADATA_STORE.get(id(request))

    def setter(request: ExecutionRequest, value: Mapping[str, Any] | None) -> None:
        _REQUEST_METADATA_STORE[id(request)] = value

    setattr(ExecutionRequest, "request_metadata", property(getter, setter))


_install_request_metadata_property()


def _timeout_seconds(timeout_ms: int | None) -> int | None:
    if timeout_ms is None:
        return None
    return max(1, math.ceil(timeout_ms / 1000))


def _load_container_protocol_types():
    project_root = Path(__file__).resolve().parents[1]
    runner_root = project_root / "container" / "agent-runner"
    if str(runner_root) not in sys.path:
        sys.path.insert(0, str(runner_root))
    from src.types import ContainerInput, ContainerOutput

    return ContainerInput, ContainerOutput


def _extract_runner_output(stdout: str) -> str | None:
    if OUTPUT_START_MARKER in stdout and OUTPUT_END_MARKER in stdout:
        start = stdout.rfind(OUTPUT_START_MARKER)
        end = stdout.find(OUTPUT_END_MARKER, start)
        if end == -1:
            return None
        return stdout[start + len(OUTPUT_START_MARKER) : end].strip()

    stripped = stdout.strip()
    if stripped == "":
        return None
    return stripped


def parse_runner_output(
    *,
    stdout: str,
    stderr: str,
    returncode: int,
    source: str,
) -> dict[str, Any]:
    raw_payload = _extract_runner_output(stdout)
    if raw_payload is None:
        error = stderr.strip() or f"{source} runner did not produce parseable output"
        return {"status": "failed", "error": error, "returncode": returncode}

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        return {
            "status": "failed",
            "error": f"{source} runner produced invalid JSON output",
            "returncode": returncode,
        }

    if not isinstance(payload, dict):
        return {
            "status": "failed",
            "error": f"{source} runner returned non-object output",
            "returncode": returncode,
        }

    runner_status = payload.get("status")
    if runner_status == "success":
        return {
            "status": "completed",
            "final_output": payload.get("result"),
            "returncode": returncode,
        }
    if runner_status == "timeout":
        return {
            "status": "timeout",
            "error": payload.get("error"),
            "returncode": returncode,
        }

    error = payload.get("error") or payload.get("result") or stderr.strip()
    if not isinstance(error, str) or error == "":
        error = f"{source} runner failed"
    return {
        "status": "failed",
        "error": error,
        "returncode": returncode,
    }


def _resolve_event_handler(request: ExecutionRequest) -> RunEventHandler | None:
    metadata = getattr(request, "request_metadata", None)
    if not isinstance(metadata, Mapping):
        return None
    candidate = metadata.get("event_handler")
    if not callable(candidate):
        return None

    async def wrapper(event: RunEvent) -> None:
        result = candidate(event)
        if hasattr(result, "__await__"):
            await result

    return wrapper


class OpenAIRuntimeBackend:
    """Thin adapter around the current structured runtime trigger."""

    def __init__(self, *, runtime_factory: RuntimeFactory) -> None:
        self._runtime_factory = runtime_factory
        self._active_runtimes: dict[str, AgentRuntime] = {}

    async def execute(
        self,
        request: ExecutionRequest,
        *,
        run_id: str,
        session_id: str,
    ) -> dict[str, Any]:
        runtime = self._runtime_factory(request.group_folder)
        self._active_runtimes[run_id] = runtime
        try:
            result = await run_agent_execution(
                group_folder=request.group_folder,
                message=request.prompt,
                user_id=request.user_id,
                runtime_factory=lambda _group: runtime,
                event_handler=_resolve_event_handler(request),
                session_id_factory=lambda _group: session_id,
                request_id=run_id,
                timeout_ms=None,
            )
        finally:
            self._active_runtimes.pop(run_id, None)

        return {
            "status": result.status,
            "final_output": result.final_output,
            "error": result.error,
            "timeout_ms": result.timeout_ms,
        }

    async def cancel(self, run_id: str) -> None:
        runtime = self._active_runtimes.get(run_id)
        if runtime is not None:
            await runtime.cancel(run_id)


class HostProcessBackend:
    """Thin adapter around ``ProcessExecutor``."""

    def __init__(self, *, process_executor: ProcessExecutor | None = None) -> None:
        self._process_executor = process_executor or ProcessExecutor()

    async def execute(
        self,
        request: ExecutionRequest,
        *,
        run_id: str,
        session_id: str,
    ) -> dict[str, Any]:
        ContainerInput, _ContainerOutput = _load_container_protocol_types()
        payload = ContainerInput(
            prompt=request.prompt,
            group_folder=request.group_folder,
            session_id=session_id,
        )
        result = await self._process_executor.run_agent(
            request.group_folder,
            payload,
            timeout=_timeout_seconds(request.timeout_ms),
            run_id=run_id,
        )
        return parse_runner_output(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
            source="host",
        )

    async def cancel(self, run_id: str) -> None:
        await self._process_executor.cancel(run_id)


class ContainerBackend:
    """Thin request-scoped adapter around the container runner."""

    def __init__(
        self,
        *,
        container_manager: ContainerManager,
        docker_executable: str = DEFAULT_DOCKER_EXECUTABLE,
        create_subprocess_exec: Callable[..., Awaitable[Any]] | None = None,
    ) -> None:
        self._container_manager = container_manager
        self._docker_executable = docker_executable
        self._create_subprocess_exec = create_subprocess_exec or asyncio.create_subprocess_exec
        self._active_processes: dict[str, Any] = {}
        self._container_names: dict[str, str] = {}

    async def execute(
        self,
        request: ExecutionRequest,
        *,
        run_id: str,
        session_id: str,
    ) -> dict[str, Any]:
        ContainerInput, _ContainerOutput = _load_container_protocol_types()
        payload = ContainerInput(
            prompt=request.prompt,
            group_folder=request.group_folder,
            session_id=session_id,
        )
        container_name = self._container_manager.build_container_name(request.group_folder, payload)
        command = self._build_command(
            request=request,
            payload=payload,
            container_name=container_name,
        )
        process = await self._create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._active_processes[run_id] = process
        self._container_names[run_id] = container_name
        try:
            stdout, stderr = await process.communicate(payload.model_dump_json().encode("utf-8"))
        finally:
            self._active_processes.pop(run_id, None)
            self._container_names.pop(run_id, None)

        return parse_runner_output(
            stdout=stdout.decode("utf-8"),
            stderr=stderr.decode("utf-8"),
            returncode=getattr(process, "returncode", 0) or 0,
            source="container",
        )

    async def cancel(self, run_id: str) -> None:
        container_name = self._container_names.get(run_id)
        if container_name is not None:
            try:
                await self._container_manager.stop_container(container_name)
            except Exception:
                pass

        process = self._active_processes.get(run_id)
        if process is not None and hasattr(process, "kill"):
            process.kill()

    def _build_command(
        self,
        *,
        request: ExecutionRequest,
        payload: Any,
        container_name: str,
    ) -> list[str]:
        command = [
            self._docker_executable,
            "run",
            "-i",
            "--rm",
            "--name",
            container_name,
        ]

        volumes = self._container_manager.build_runner_volumes(request.group_folder, request.user_id)
        for host_path, config in volumes.items():
            bind = config["bind"]
            mode = config.get("mode", "rw")
            volume = f"{host_path}:{bind}"
            if mode == "ro":
                volume = f"{volume}:ro"
            command.extend(["-v", volume])

        environment = self._container_manager.build_environment(request.group_folder, payload)
        for key, value in environment.items():
            command.extend(["-e", f"{key}={value}"])

        command.extend(["-w", CONTAINER_WORKDIR, self._container_manager.container_image])
        command.extend(CONTAINER_COMMAND)
        return command


__all__ = [
    "ContainerBackend",
    "DEFAULT_DOCKER_EXECUTABLE",
    "HostProcessBackend",
    "OUTPUT_END_MARKER",
    "OUTPUT_START_MARKER",
    "OpenAIRuntimeBackend",
    "parse_runner_output",
]
