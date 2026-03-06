from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNNER_ROOT = PROJECT_ROOT / "container" / "agent-runner"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))


class FakeContainer:
    def __init__(
        self,
        container_id: str = "started-container",
        *,
        status: str = "created",
    ) -> None:
        self.id = container_id
        self.status = status


class FakeDockerClient:
    def __init__(self) -> None:
        self.started_container = FakeContainer()
        self.containers: dict[str, FakeContainer] = {
            self.started_container.id: self.started_container
        }
        self.get_calls: list[str] = []
        self.run_calls: list[dict[str, object]] = []
        self.stop_calls: list[dict[str, object]] = []
        self.wait_calls: list[dict[str, object]] = []
        self.remove_calls: list[dict[str, object]] = []
        self.operation_log: list[str] = []
        self.get_error: Exception | None = None
        self.run_error: Exception | None = None
        self.stop_error: Exception | None = None
        self.wait_error: Exception | None = None
        self.remove_error: Exception | None = None
        self.remove_errors_by_force: dict[bool, Exception | None] = {
            False: None,
            True: None,
        }

    async def run_container(
        self,
        image: str,
        command: list[str] | None = None,
        *,
        volumes: dict[str, dict[str, str]] | None = None,
        environment: dict[str, str] | None = None,
        name: str | None = None,
        working_dir: str | None = None,
        detach: bool = True,
        remove: bool = False,
    ) -> FakeContainer:
        self.run_calls.append(
            {
                "image": image,
                "command": command,
                "volumes": volumes,
                "environment": environment,
                "name": name,
                "working_dir": working_dir,
                "detach": detach,
                "remove": remove,
            }
        )
        if self.run_error is not None:
            raise self.run_error
        return self.started_container

    def get_container(self, name: str) -> FakeContainer:
        self.get_calls.append(name)
        if self.get_error is not None:
            raise self.get_error
        return self.containers[name]

    def stop_container(self, name: str, *, timeout: int | None = None) -> None:
        self.operation_log.append("stop")
        self.stop_calls.append({"name": name, "timeout": timeout})
        if self.stop_error is not None:
            raise self.stop_error

    def wait_container(self, name: str, **kwargs: object) -> dict[str, int]:
        self.operation_log.append("wait")
        self.wait_calls.append({"name": name, **dict(kwargs)})
        if self.wait_error is not None:
            raise self.wait_error
        return {"StatusCode": 0}

    def remove_container(self, name: str, *, force: bool = False) -> None:
        self.operation_log.append("remove")
        self.remove_calls.append({"name": name, "force": force})
        if self.remove_errors_by_force[force] is not None:
            raise self.remove_errors_by_force[force]
        if self.remove_error is not None:
            raise self.remove_error


@pytest.mark.asyncio
async def test_start_agent_container_calls_run_container_with_expected_defaults(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from infra.exec.container_manager import (
        CONTAINER_COMMAND,
        CONTAINER_IMAGE,
        CONTAINER_WORKDIR,
        ContainerManager,
    )
    from src.types import ContainerInput

    fake_client = FakeDockerClient()
    built_volumes = {
        str(tmp_path / "group"): {
            "bind": "/workspace/group",
            "mode": "rw",
        }
    }
    captured: dict[str, object] = {}

    def fake_build_volumes(
        group_folder: str,
        user_id: str,
        *,
        data_root: Path | None = None,
        readonly_mounts: set[str] | None = None,
    ) -> dict[str, dict[str, str]]:
        captured["group_folder"] = group_folder
        captured["user_id"] = user_id
        captured["data_root"] = data_root
        captured["readonly_mounts"] = readonly_mounts
        return built_volumes

    monkeypatch.setattr("infra.exec.container_manager.build_volumes", fake_build_volumes)

    manager = ContainerManager(
        fake_client,
        data_root=tmp_path / "data",
        readonly_mounts={"memory"},
    )
    payload = ContainerInput(
        prompt="hello from manager",
        group_folder="group-a",
        session_id="session-1",
        agent_name="RunnerAgent",
    )

    container_id = await manager.start_agent_container(
        group_folder="group-a",
        user_id="user-1",
        payload=payload,
    )

    assert container_id == "started-container"
    assert captured == {
        "group_folder": "group-a",
        "user_id": "user-1",
        "data_root": tmp_path / "data",
        "readonly_mounts": {"memory"},
    }
    assert fake_client.run_calls == [
        {
            "image": CONTAINER_IMAGE,
            "command": CONTAINER_COMMAND,
            "volumes": built_volumes,
            "environment": {
                "PORTEX_RUN_MODE": "container",
                "PORTEX_GROUP_FOLDER": "group-a",
                "PORTEX_SESSION_ID": "session-1",
                "PORTEX_AGENT_NAME": "RunnerAgent",
                "PORTEX_GROUP_DIR": "/workspace/group",
                "PORTEX_IPC_DIR": "/workspace/ipc",
                "PORTEX_MEMORY_DIR": "/workspace/memory",
                "PORTEX_SKILLS_DIR": "/workspace/skills",
                "PORTEX_SESSIONS_DIR": "/home/portex/.claude",
            },
            "name": "portex-agent-group-a-session-1",
            "working_dir": CONTAINER_WORKDIR,
            "detach": True,
            "remove": False,
        }
    ]


@pytest.mark.asyncio
async def test_start_agent_container_rejects_mismatched_group_folder() -> None:
    from infra.exec.container_manager import ContainerManager
    from src.types import ContainerInput

    fake_client = FakeDockerClient()
    manager = ContainerManager(fake_client)
    payload = ContainerInput(prompt="hello", group_folder="group-b")

    with pytest.raises(ValueError, match="group_folder"):
        await manager.start_agent_container(
            group_folder="group-a",
            user_id="user-1",
            payload=payload,
        )

    assert fake_client.run_calls == []


@pytest.mark.asyncio
async def test_start_agent_container_propagates_docker_execution_errors() -> None:
    from infra.exec.container_manager import ContainerManager
    from infra.exec.docker import DockerExecutionError
    from src.types import ContainerInput

    fake_client = FakeDockerClient()
    fake_client.run_error = DockerExecutionError("docker unavailable")
    manager = ContainerManager(fake_client)
    payload = ContainerInput(prompt="hello", group_folder="group-a")

    with pytest.raises(DockerExecutionError, match="docker unavailable"):
        await manager.start_agent_container(
            group_folder="group-a",
            user_id="user-1",
            payload=payload,
        )


@pytest.mark.asyncio
async def test_stop_container_stops_then_removes_with_lifecycle_defaults() -> None:
    from infra.exec.container_manager import ContainerManager

    fake_client = FakeDockerClient()
    manager = ContainerManager(fake_client)

    await manager.stop_container("container-123")

    assert fake_client.stop_calls == [{"name": "container-123", "timeout": 30}]
    assert fake_client.remove_calls == [{"name": "container-123", "force": False}]
    assert fake_client.operation_log == ["stop", "remove"]


@pytest.mark.asyncio
async def test_stop_container_does_not_remove_when_stop_fails() -> None:
    from infra.exec.container_manager import ContainerManager
    from infra.exec.docker import DockerExecutionError

    fake_client = FakeDockerClient()
    fake_client.stop_error = DockerExecutionError("stop failed")
    manager = ContainerManager(fake_client)

    with pytest.raises(DockerExecutionError, match="stop failed"):
        await manager.stop_container("container-123")

    assert fake_client.stop_calls == [{"name": "container-123", "timeout": 30}]
    assert fake_client.remove_calls == []
    assert fake_client.operation_log == ["stop"]


@pytest.mark.asyncio
async def test_stop_container_propagates_remove_failures_after_stop() -> None:
    from infra.exec.container_manager import ContainerManager
    from infra.exec.docker import DockerExecutionError

    fake_client = FakeDockerClient()
    fake_client.remove_error = DockerExecutionError("remove failed")
    manager = ContainerManager(fake_client)

    with pytest.raises(DockerExecutionError, match="remove failed"):
        await manager.stop_container("container-123")

    assert fake_client.stop_calls == [{"name": "container-123", "timeout": 30}]
    assert fake_client.remove_calls == [{"name": "container-123", "force": False}]
    assert fake_client.operation_log == ["stop", "remove"]


@pytest.mark.asyncio
async def test_is_container_healthy_returns_true_for_running_container() -> None:
    from infra.exec.container_manager import ContainerManager

    fake_client = FakeDockerClient()
    fake_client.containers["container-healthy"] = FakeContainer(
        "container-healthy",
        status="running",
    )
    manager = ContainerManager(fake_client)

    is_healthy = await manager.is_container_healthy("container-healthy")

    assert is_healthy is True
    assert fake_client.get_calls == ["container-healthy"]


@pytest.mark.asyncio
async def test_is_container_healthy_returns_false_for_non_running_container() -> None:
    from infra.exec.container_manager import ContainerManager

    fake_client = FakeDockerClient()
    fake_client.containers["container-exited"] = FakeContainer(
        "container-exited",
        status="exited",
    )
    manager = ContainerManager(fake_client)

    is_healthy = await manager.is_container_healthy("container-exited")

    assert is_healthy is False
    assert fake_client.get_calls == ["container-exited"]


@pytest.mark.asyncio
async def test_is_container_healthy_propagates_container_lookup_errors() -> None:
    from infra.exec.container_manager import ContainerManager
    from infra.exec.docker import DockerExecutionError

    fake_client = FakeDockerClient()
    fake_client.get_error = DockerExecutionError("container missing")
    manager = ContainerManager(fake_client)

    with pytest.raises(DockerExecutionError, match="container missing"):
        await manager.is_container_healthy("container-missing")

    assert fake_client.get_calls == ["container-missing"]


@pytest.mark.asyncio
async def test_graceful_shutdown_stops_waits_and_removes_container() -> None:
    from infra.exec.container_manager import ContainerManager

    fake_client = FakeDockerClient()
    manager = ContainerManager(fake_client)

    await manager.graceful_shutdown("container-123")

    assert fake_client.stop_calls == [{"name": "container-123", "timeout": 30}]
    assert fake_client.wait_calls == [{"name": "container-123"}]
    assert fake_client.remove_calls == [{"name": "container-123", "force": False}]
    assert fake_client.operation_log == ["stop", "wait", "remove"]


@pytest.mark.asyncio
async def test_graceful_shutdown_force_removes_when_stop_fails() -> None:
    from infra.exec.container_manager import ContainerManager
    from infra.exec.docker import DockerExecutionError

    fake_client = FakeDockerClient()
    fake_client.stop_error = DockerExecutionError("stop failed")
    manager = ContainerManager(fake_client)

    await manager.graceful_shutdown("container-123")

    assert fake_client.stop_calls == [{"name": "container-123", "timeout": 30}]
    assert fake_client.wait_calls == []
    assert fake_client.remove_calls == [{"name": "container-123", "force": True}]
    assert fake_client.operation_log == ["stop", "remove"]


@pytest.mark.asyncio
async def test_graceful_shutdown_force_removes_when_wait_fails() -> None:
    from infra.exec.container_manager import ContainerManager
    from infra.exec.docker import DockerExecutionError

    fake_client = FakeDockerClient()
    fake_client.wait_error = DockerExecutionError("wait failed")
    manager = ContainerManager(fake_client)

    await manager.graceful_shutdown("container-123")

    assert fake_client.stop_calls == [{"name": "container-123", "timeout": 30}]
    assert fake_client.wait_calls == [{"name": "container-123"}]
    assert fake_client.remove_calls == [{"name": "container-123", "force": True}]
    assert fake_client.operation_log == ["stop", "wait", "remove"]


@pytest.mark.asyncio
async def test_graceful_shutdown_force_removes_when_regular_remove_fails() -> None:
    from infra.exec.container_manager import ContainerManager
    from infra.exec.docker import DockerExecutionError

    fake_client = FakeDockerClient()
    fake_client.remove_errors_by_force[False] = DockerExecutionError("remove failed")
    manager = ContainerManager(fake_client)

    await manager.graceful_shutdown("container-123")

    assert fake_client.stop_calls == [{"name": "container-123", "timeout": 30}]
    assert fake_client.wait_calls == [{"name": "container-123"}]
    assert fake_client.remove_calls == [
        {"name": "container-123", "force": False},
        {"name": "container-123", "force": True},
    ]
    assert fake_client.operation_log == ["stop", "wait", "remove", "remove"]


@pytest.mark.asyncio
async def test_graceful_shutdown_propagates_force_remove_failures() -> None:
    from infra.exec.container_manager import ContainerManager
    from infra.exec.docker import DockerExecutionError

    fake_client = FakeDockerClient()
    fake_client.wait_error = DockerExecutionError("wait failed")
    fake_client.remove_error = DockerExecutionError("force remove failed")
    manager = ContainerManager(fake_client)

    with pytest.raises(DockerExecutionError, match="force remove failed"):
        await manager.graceful_shutdown("container-123")

    assert fake_client.stop_calls == [{"name": "container-123", "timeout": 30}]
    assert fake_client.wait_calls == [{"name": "container-123"}]
    assert fake_client.remove_calls == [{"name": "container-123", "force": True}]
    assert fake_client.operation_log == ["stop", "wait", "remove"]
