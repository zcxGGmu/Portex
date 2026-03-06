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
    def __init__(self, container_id: str = "started-container") -> None:
        self.id = container_id


class FakeDockerClient:
    def __init__(self) -> None:
        self.started_container = FakeContainer()
        self.run_calls: list[dict[str, object]] = []
        self.run_error: Exception | None = None

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
