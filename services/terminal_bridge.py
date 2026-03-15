"""Terminal bridge abstractions and docker-backed implementation."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import re
from typing import Protocol
from uuid import uuid4

from infra.exec.container_manager import CONTAINER_WORKDIR, ContainerManager

DEFAULT_DOCKER_EXECUTABLE = "docker"
_SAFE_CONTAINER_SEGMENT = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(frozen=True, slots=True)
class TerminalBridgeEvent:
    type: str
    data: str | None = None
    exit_code: int | None = None
    error: str | None = None


TerminalBridgeEventHandler = Callable[[TerminalBridgeEvent], Awaitable[None]]


class TerminalBridge(Protocol):
    async def start(self, on_event: TerminalBridgeEventHandler) -> None:
        ...

    async def send_input(self, data: str) -> None:
        ...

    async def resize(self, *, cols: int, rows: int) -> None:
        ...

    async def close(self) -> None:
        ...


@dataclass(frozen=True, slots=True)
class TerminalContainerPayload:
    group_folder: str
    session_id: str | None
    agent_name: str = "terminal"


def build_terminal_container_name(group_folder: str, session_id: str) -> str:
    safe_group = _SAFE_CONTAINER_SEGMENT.sub("-", group_folder).strip("-.") or "group"
    safe_session = _SAFE_CONTAINER_SEGMENT.sub("-", session_id).strip("-.") or uuid4().hex[:8]
    return f"portex-terminal-{safe_group}-{safe_session}"


class DockerExecTerminalBridge:
    """Best-effort docker-backed terminal bridge for backend-only terminal sessions."""

    def __init__(
        self,
        *,
        container_manager: ContainerManager,
        group_folder: str,
        owner_user_id: str,
        session_id: str,
        docker_executable: str = DEFAULT_DOCKER_EXECUTABLE,
        create_subprocess_exec: Callable[..., Awaitable[asyncio.subprocess.Process]] | None = None,
    ) -> None:
        self._container_manager = container_manager
        self._group_folder = group_folder
        self._owner_user_id = owner_user_id
        self._session_id = session_id
        self._docker_executable = docker_executable
        self._create_subprocess_exec = create_subprocess_exec or asyncio.create_subprocess_exec
        self._container_name = build_terminal_container_name(group_folder, session_id)
        self._exec_process: asyncio.subprocess.Process | None = None
        self._reader_tasks: list[asyncio.Task[None]] = []

    @property
    def container_name(self) -> str:
        return self._container_name

    async def start(self, on_event: TerminalBridgeEventHandler) -> None:
        payload = TerminalContainerPayload(
            group_folder=self._group_folder,
            session_id=self._session_id,
        )
        await self._container_manager.client.run_container(
            image=self._container_manager.container_image,
            command=["tail", "-f", "/dev/null"],
            volumes=self._container_manager.build_runner_volumes(
                self._group_folder,
                self._owner_user_id,
            ),
            environment=self._container_manager.build_environment(self._group_folder, payload),
            name=self._container_name,
            working_dir=CONTAINER_WORKDIR,
            detach=True,
            remove=False,
        )
        self._exec_process = await self._create_subprocess_exec(
            self._docker_executable,
            "exec",
            "-i",
            self._container_name,
            "/bin/sh",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._reader_tasks = [
            asyncio.create_task(self._forward_stream(self._exec_process.stdout, on_event)),
            asyncio.create_task(self._forward_stream(self._exec_process.stderr, on_event)),
            asyncio.create_task(self._watch_process_exit(on_event)),
        ]

    async def send_input(self, data: str) -> None:
        if self._exec_process is None or self._exec_process.stdin is None:
            return
        self._exec_process.stdin.write(data.encode("utf-8"))
        await self._exec_process.stdin.drain()

    async def resize(self, *, cols: int, rows: int) -> None:
        _ = (cols, rows)
        # v1 keeps the resize contract and test seam explicit, but does not yet
        # implement terminal-size propagation for the docker exec subprocess.
        return None

    async def close(self) -> None:
        process = self._exec_process
        self._exec_process = None

        if process is not None:
            if process.stdin is not None:
                process.stdin.close()
            if process.returncode is None:
                process.kill()
                try:
                    await asyncio.wait_for(process.wait(), timeout=1)
                except asyncio.TimeoutError:
                    pass

        for task in self._reader_tasks:
            if not task.done():
                task.cancel()
        if self._reader_tasks:
            await asyncio.gather(*self._reader_tasks, return_exceptions=True)
        self._reader_tasks.clear()

        try:
            await self._container_manager.graceful_shutdown(self._container_name)
        except Exception:
            return None

    async def _forward_stream(
        self,
        stream: asyncio.StreamReader | None,
        on_event: TerminalBridgeEventHandler,
    ) -> None:
        if stream is None:
            return
        while True:
            chunk = await stream.read(1024)
            if not chunk:
                return
            await on_event(TerminalBridgeEvent(type="output", data=chunk.decode("utf-8", errors="ignore")))

    async def _watch_process_exit(self, on_event: TerminalBridgeEventHandler) -> None:
        process = self._exec_process
        if process is None:
            return
        return_code = await process.wait()
        await on_event(TerminalBridgeEvent(type="exit", exit_code=return_code))


__all__ = [
    "DEFAULT_DOCKER_EXECUTABLE",
    "DockerExecTerminalBridge",
    "TerminalBridge",
    "TerminalBridgeEvent",
    "TerminalBridgeEventHandler",
    "build_terminal_container_name",
]
