"""Host process execution adapter."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Any, Protocol

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = PROJECT_ROOT / "data"
DEFAULT_RUNNER_ROOT = PROJECT_ROOT / "container" / "agent-runner"
RUNNER_MODULE = "src.runner"


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
    """Raised when the host process cannot be started."""


class ProcessExecutor:
    """Thin async wrapper around the local agent-runner process."""

    def __init__(
        self,
        *,
        data_root: str | Path | None = None,
        runner_root: str | Path | None = None,
        python_executable: str | None = None,
    ) -> None:
        self.data_root = Path(data_root or DEFAULT_DATA_ROOT).expanduser().resolve()
        self.runner_root = Path(runner_root or DEFAULT_RUNNER_ROOT).expanduser().resolve()
        self.python_executable = python_executable or sys.executable

    def build_command(self) -> list[str]:
        """Build the subprocess argv for the local runner."""
        return [self.python_executable, "-m", RUNNER_MODULE]

    def resolve_group_dir(self, group_folder: str) -> Path:
        """Resolve and create the host-mode group directory."""
        group_dir = (self.data_root / "groups" / group_folder).resolve()
        group_dir.mkdir(parents=True, exist_ok=True)
        return group_dir

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

    async def run_agent(
        self,
        group_folder: str,
        payload: ContainerInputPayload,
    ) -> ProcessRunResult:
        """Execute the local runner once and collect stdout, stderr, and return code."""
        group_dir = self.resolve_group_dir(group_folder)
        try:
            process = await asyncio.create_subprocess_exec(
                *self.build_command(),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.runner_root),
                env=self.build_env(group_folder, group_dir),
            )
        except (OSError, ValueError) as exc:
            raise ProcessExecutionError(
                f"Failed to start host process runner for group '{group_folder}'"
            ) from exc

        stdout, stderr = await process.communicate(self.serialize_input(payload))
        return ProcessRunResult(
            returncode=process.returncode or 0,
            stdout=stdout.decode("utf-8"),
            stderr=stderr.decode("utf-8"),
        )


ProcessRunner = ProcessExecutor


__all__ = [
    "DEFAULT_DATA_ROOT",
    "DEFAULT_RUNNER_ROOT",
    "ProcessExecutionError",
    "ProcessExecutor",
    "ProcessRunResult",
    "ProcessRunner",
    "RUNNER_MODULE",
]
