"""Host process execution adapter."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import os
from pathlib import Path
import sys
from collections.abc import Mapping, Sequence
from typing import Protocol

from .security import validate_path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = PROJECT_ROOT / "data"
DEFAULT_RUNNER_ROOT = PROJECT_ROOT / "container" / "agent-runner"
RUNNER_MODULE = "src.runner"
DEFAULT_ALLOWED_DIRECTORIES = (DEFAULT_DATA_ROOT / "groups",)
DEFAULT_FORBIDDEN_COMMANDS = (
    ("rm", "-rf", "/"),
    ("dd", "if="),
)
DEFAULT_MAX_EXECUTION_TIME = 3600
HOST_MODE_RESTRICTIONS = {
    "allowed_directories": [str(path.resolve()) for path in DEFAULT_ALLOWED_DIRECTORIES],
    "forbidden_commands": ["rm -rf /", "dd if="],
    "max_execution_time": DEFAULT_MAX_EXECUTION_TIME,
}


class ContainerInputPayload(Protocol):
    """Runtime-visible subset used by the host process executor."""

    group_folder: str

    def model_dump_json(self) -> str:
        ...


@dataclass(slots=True, frozen=True)
class ProcessRunResult:
    """Structured result of one host process invocation."""

    returncode: int
    stdout: str
    stderr: str


class ProcessExecutionError(RuntimeError):
    """Raised when host process execution fails before normal completion."""


class ProcessExecutionTimeoutError(ProcessExecutionError):
    """Raised when host process execution exceeds its safety timeout."""


@dataclass(slots=True, frozen=True)
class HostModeRestrictions:
    """Security restrictions applied to host-mode process execution."""

    allowed_directories: tuple[Path, ...]
    forbidden_commands: tuple[str | tuple[str, ...], ...]
    max_execution_time: int = DEFAULT_MAX_EXECUTION_TIME


def is_command_forbidden(
    command: list[str],
    forbidden_prefixes: Sequence[str | tuple[str, ...]],
) -> bool:
    """Return whether a command argv matches any forbidden prefix."""
    command_text = " ".join(command)
    for prefix in forbidden_prefixes:
        if isinstance(prefix, str):
            if prefix in command_text:
                return True
            continue
        if not prefix or len(command) < len(prefix):
            continue
        if prefix[-1].endswith("="):
            static_prefix = prefix[:-1]
            if command[: len(static_prefix)] != list(static_prefix):
                continue
            candidate = command[len(static_prefix)]
            if candidate.startswith(prefix[-1]):
                return True
            continue
        if command[: len(prefix)] == list(prefix):
            return True
    return False


def _normalize_restrictions(
    restrictions: HostModeRestrictions | Mapping[str, object] | None,
    *,
    data_root: Path,
    runner_root: Path,
) -> HostModeRestrictions:
    if restrictions is None:
        return HostModeRestrictions(
            allowed_directories=((data_root / "groups").resolve(), runner_root.resolve()),
            forbidden_commands=tuple(HOST_MODE_RESTRICTIONS["forbidden_commands"]),
            max_execution_time=int(HOST_MODE_RESTRICTIONS["max_execution_time"]),
        )
    if isinstance(restrictions, HostModeRestrictions):
        return HostModeRestrictions(
            allowed_directories=tuple(
                Path(path).expanduser().resolve() for path in restrictions.allowed_directories
            ),
            forbidden_commands=tuple(restrictions.forbidden_commands),
            max_execution_time=restrictions.max_execution_time,
        )
    return HostModeRestrictions(
        allowed_directories=tuple(
            Path(path).expanduser().resolve()
            for path in restrictions.get("allowed_directories", [])
        ),
        forbidden_commands=tuple(
            rule if isinstance(rule, str) else tuple(rule)
            for rule in restrictions.get("forbidden_commands", [])
        ),
        max_execution_time=int(
            restrictions.get("max_execution_time", DEFAULT_MAX_EXECUTION_TIME)
        ),
    )


class ProcessExecutor:
    """Thin async wrapper around the local agent-runner process."""

    def __init__(
        self,
        *,
        data_root: str | Path | None = None,
        runner_root: str | Path | None = None,
        python_executable: str | None = None,
        restrictions: HostModeRestrictions | Mapping[str, object] | None = None,
    ) -> None:
        self.data_root = Path(data_root or DEFAULT_DATA_ROOT).expanduser().resolve()
        self.runner_root = Path(runner_root or DEFAULT_RUNNER_ROOT).expanduser().resolve()
        self.python_executable = python_executable or sys.executable
        self.restrictions = _normalize_restrictions(
            restrictions,
            data_root=self.data_root,
            runner_root=self.runner_root,
        )
        self._active_processes: dict[str, asyncio.subprocess.Process] = {}
        self._cleanup_tasks: dict[str, asyncio.Task[None]] = {}

    def build_command(self) -> list[str]:
        """Build the subprocess argv for the local runner."""
        return [self.python_executable, "-m", RUNNER_MODULE]

    def resolve_group_dir(self, group_folder: str) -> Path:
        """Resolve and create the host-mode group directory."""
        group_dir = (self.data_root / "groups" / group_folder).resolve()
        if not validate_path(group_dir, self.restrictions.allowed_directories):
            raise ProcessExecutionError(
                f"Group directory '{group_dir}' is outside allowed host directories"
            )
        group_dir.mkdir(parents=True, exist_ok=True)
        return group_dir

    def validate_runner_root(self) -> Path:
        """Validate that the runner root stays inside allowed host directories."""
        if not validate_path(self.runner_root, self.restrictions.allowed_directories):
            raise ProcessExecutionError(
                f"Runner root '{self.runner_root}' is outside allowed host directories"
            )
        return self.runner_root

    def build_env(self, group_folder: str, group_dir: Path) -> dict[str, str]:
        """Build environment variables for the host-mode runner process."""
        env = os.environ.copy()
        env.update(
            {
                "PORTEX_RUN_MODE": "host",
                "PORTEX_GROUP_FOLDER": group_folder,
                "PORTEX_GROUP_DIR": str(group_dir),
            }
        )
        return env

    def serialize_input(self, payload: ContainerInputPayload) -> bytes:
        """Serialize the runner payload to UTF-8 JSON bytes."""
        return payload.model_dump_json().encode("utf-8")

    def resolve_timeout(self, timeout: int | None = None) -> int:
        """Clamp one execution timeout to the configured host-mode limit."""
        if timeout is None:
            return self.restrictions.max_execution_time
        return min(timeout, self.restrictions.max_execution_time)

    async def run_agent(
        self,
        group_folder: str,
        payload: ContainerInputPayload,
        *,
        timeout: int | None = None,
        run_id: str | None = None,
    ) -> ProcessRunResult:
        """Execute the local runner once and collect stdout, stderr, and return code."""
        group_dir = self.resolve_group_dir(group_folder)
        runner_root = self.validate_runner_root()
        command = self.build_command()
        effective_timeout = self.resolve_timeout(timeout)
        if is_command_forbidden(command, self.restrictions.forbidden_commands):
            raise ProcessExecutionError("Refusing to run forbidden host-mode command")
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(runner_root),
                env=self.build_env(group_folder, group_dir),
            )
        except (OSError, ValueError) as exc:
            raise ProcessExecutionError(
                f"Failed to start host process runner for group '{group_folder}'"
            ) from exc

        if run_id is not None:
            self._active_processes[run_id] = process

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(self.serialize_input(payload)),
                timeout=effective_timeout,
            )
        except asyncio.CancelledError:
            if run_id is not None:
                self._ensure_cleanup_task(run_id, process)
            raise
        except asyncio.TimeoutError as exc:
            process.kill()
            await self._await_process_wait(process)
            if run_id is not None:
                self._clear_active_run(run_id)
            raise ProcessExecutionTimeoutError(
                f"Host process runner timed out after {effective_timeout} seconds for group '{group_folder}'"
            ) from exc
        else:
            if run_id is not None:
                self._clear_active_run(run_id)

        return ProcessRunResult(
            returncode=process.returncode or 0,
            stdout=stdout.decode("utf-8"),
            stderr=stderr.decode("utf-8"),
        )

    async def cancel(self, run_id: str) -> bool:
        """Best-effort cancellation for one active host-mode run."""
        process = self._active_processes.get(run_id)
        if process is None:
            return False
        cleanup_task = self._cleanup_tasks.get(run_id)
        process.kill()
        if cleanup_task is not None and not cleanup_task.done():
            await asyncio.gather(cleanup_task, return_exceptions=True)
        else:
            await self._await_process_wait(process)
            self._clear_active_run(run_id)
        return True

    def _ensure_cleanup_task(
        self,
        run_id: str,
        process: asyncio.subprocess.Process,
    ) -> None:
        existing = self._cleanup_tasks.get(run_id)
        if existing is None or existing.done():
            self._cleanup_tasks[run_id] = asyncio.create_task(
                self._cleanup_after_cancellation(run_id, process)
            )

    async def _cleanup_after_cancellation(
        self,
        run_id: str,
        process: asyncio.subprocess.Process,
    ) -> None:
        try:
            await self._await_process_wait(process)
        finally:
            self._clear_active_run(run_id)

    async def _await_process_wait(self, process: asyncio.subprocess.Process) -> None:
        wait = getattr(process, "wait", None)
        if callable(wait):
            maybe_awaitable = wait()
            if hasattr(maybe_awaitable, "__await__"):
                await maybe_awaitable

    def _clear_active_run(self, run_id: str) -> None:
        self._active_processes.pop(run_id, None)
        self._cleanup_tasks.pop(run_id, None)


ProcessRunner = ProcessExecutor


__all__ = [
    "DEFAULT_ALLOWED_DIRECTORIES",
    "DEFAULT_DATA_ROOT",
    "DEFAULT_FORBIDDEN_COMMANDS",
    "DEFAULT_MAX_EXECUTION_TIME",
    "DEFAULT_RUNNER_ROOT",
    "HostModeRestrictions",
    "HOST_MODE_RESTRICTIONS",
    "ProcessExecutionError",
    "ProcessExecutionTimeoutError",
    "ProcessExecutor",
    "ProcessRunResult",
    "ProcessRunner",
    "RUNNER_MODULE",
    "is_command_forbidden",
]
