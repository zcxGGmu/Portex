from __future__ import annotations

import asyncio
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class _FakeStdin:
    def __init__(self) -> None:
        self.closed = False

    def write(self, data: bytes) -> None:
        _ = data

    async def drain(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


class _FakeProcess:
    def __init__(self) -> None:
        self.returncode: int | None = None
        self.stdin = _FakeStdin()
        self.stdout = asyncio.StreamReader()
        self.stderr = asyncio.StreamReader()
        self.stdout.feed_eof()
        self.stderr.feed_eof()
        self.wait_calls = 0
        self.kill_calls = 0

    async def wait(self) -> int:
        self.wait_calls += 1
        self.returncode = 0
        return 0

    def kill(self) -> None:
        self.kill_calls += 1
        self.returncode = 0


class _FakeContainerClient:
    def __init__(self) -> None:
        self.run_calls: list[dict[str, Any]] = []

    async def run_container(self, **kwargs: Any) -> SimpleNamespace:
        self.run_calls.append(dict(kwargs))
        return SimpleNamespace(id="container-1")


class _FakeContainerManager:
    def __init__(self) -> None:
        self.client = _FakeContainerClient()
        self.container_image = "portex/agent-runner:test"
        self.shutdown_calls: list[str] = []

    def build_runner_volumes(self, group_folder: str, owner_user_id: str) -> dict[str, dict[str, str]]:
        _ = (group_folder, owner_user_id)
        return {}

    def build_environment(self, group_folder: str, payload: object) -> dict[str, str]:
        _ = (group_folder, payload)
        return {}

    async def graceful_shutdown(self, container_id: str) -> None:
        self.shutdown_calls.append(container_id)


def _has_docker_exec_flag(command: list[str], flag: str) -> bool:
    return any(arg.startswith("-") and flag in arg[1:] for arg in command)


@pytest.mark.asyncio
async def test_docker_exec_terminal_bridge_start_requests_interactive_tty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.terminal_bridge as terminal_bridge_module
    from services.terminal_bridge import DockerExecTerminalBridge

    captured: dict[str, object] = {}

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _FakeProcess:
        captured["command"] = list(command)
        captured["kwargs"] = dict(kwargs)
        return _FakeProcess()

    fake_os = SimpleNamespace(
        openpty=lambda: (101, 102),
        read=lambda fd, size: b"",
        close=lambda fd: None,
    )
    monkeypatch.setattr(terminal_bridge_module, "os", fake_os, raising=False)

    manager = _FakeContainerManager()
    bridge = DockerExecTerminalBridge(
        container_manager=manager,
        group_folder="project-alpha",
        owner_user_id="owner-1",
        session_id="session-1",
        create_subprocess_exec=fake_create_subprocess_exec,
    )

    async def on_event(_event: object) -> None:
        return None

    await bridge.start(on_event)
    await bridge.close()

    command = captured["command"]
    kwargs = captured["kwargs"]

    assert isinstance(command, list)
    assert command[0:2] == ["docker", "exec"]
    assert _has_docker_exec_flag(command, "i") is True
    assert _has_docker_exec_flag(command, "t") is True
    assert "portex-terminal-project-alpha-session-1" in command

    assert isinstance(kwargs, dict)
    assert kwargs["stdin"] == 102
    assert kwargs["stdout"] == 102
    assert kwargs["stderr"] == 102
    assert kwargs["pass_fds"] == (102,)


@pytest.mark.asyncio
async def test_docker_exec_terminal_bridge_resize_applies_pty_winsize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.terminal_bridge as terminal_bridge_module
    from services.terminal_bridge import DockerExecTerminalBridge

    ioctl_calls: list[tuple[int, int, bytes]] = []

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _FakeProcess:
        _ = (command, kwargs)
        return _FakeProcess()

    def fake_ioctl(fd: int, op: int, data: bytes) -> int:
        ioctl_calls.append((fd, op, data))
        return 0

    fake_os = SimpleNamespace(
        openpty=lambda: (201, 202),
        read=lambda fd, size: b"",
        close=lambda fd: None,
    )
    fake_fcntl = SimpleNamespace(ioctl=fake_ioctl)
    monkeypatch.setattr(terminal_bridge_module, "os", fake_os, raising=False)
    monkeypatch.setattr(terminal_bridge_module, "fcntl", fake_fcntl, raising=False)

    manager = _FakeContainerManager()
    bridge = DockerExecTerminalBridge(
        container_manager=manager,
        group_folder="project-beta",
        owner_user_id="owner-1",
        session_id="session-2",
        create_subprocess_exec=fake_create_subprocess_exec,
    )

    async def on_event(_event: object) -> None:
        return None

    await bridge.start(on_event)
    await bridge.resize(cols=137, rows=51)
    await bridge.close()

    assert len(ioctl_calls) == 1
    fd, _op, raw = ioctl_calls[0]
    rows, cols, xpixel, ypixel = struct.unpack("HHHH", raw)
    assert fd == 201
    assert rows == 51
    assert cols == 137
    assert xpixel == 0
    assert ypixel == 0
