from __future__ import annotations

from pathlib import Path
import sys

from docker.errors import APIError, NotFound
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class FakeContainer:
    def __init__(
        self,
        container_id: str,
        *,
        wait_result: dict[str, int] | None = None,
        logs_result: bytes = b"container logs",
    ) -> None:
        self.id = container_id
        self.stop_calls: list[dict[str, object]] = []
        self.wait_calls: list[dict[str, object]] = []
        self.logs_calls: list[dict[str, object]] = []
        self.remove_calls: list[dict[str, object]] = []
        self.stop_error: Exception | None = None
        self.wait_error: Exception | None = None
        self.logs_error: Exception | None = None
        self.remove_error: Exception | None = None
        self._wait_result = wait_result or {"StatusCode": 0}
        self._logs_result = logs_result

    def stop(self, **kwargs: object) -> None:
        self.stop_calls.append(dict(kwargs))
        if self.stop_error is not None:
            raise self.stop_error

    def wait(self, **kwargs: object) -> dict[str, int]:
        self.wait_calls.append(dict(kwargs))
        if self.wait_error is not None:
            raise self.wait_error
        return self._wait_result

    def logs(self, **kwargs: object) -> bytes:
        self.logs_calls.append(dict(kwargs))
        if self.logs_error is not None:
            raise self.logs_error
        return self._logs_result

    def remove(self, **kwargs: object) -> None:
        self.remove_calls.append(dict(kwargs))
        if self.remove_error is not None:
            raise self.remove_error


class FakeContainerCollection:
    def __init__(self, containers: dict[str, FakeContainer] | None = None) -> None:
        self._containers = containers or {
            "container-1": FakeContainer("container-1"),
            "container-2": FakeContainer("container-2"),
        }
        self.list_calls: list[dict[str, object]] = []
        self.get_calls: list[str] = []
        self.run_calls: list[dict[str, object]] = []
        self.list_error: Exception | None = None
        self.run_error: Exception | None = None
        self.get_errors: dict[str, Exception] = {}

    def list(self, **kwargs: object) -> list[FakeContainer]:
        self.list_calls.append(dict(kwargs))
        if self.list_error is not None:
            raise self.list_error
        return list(self._containers.values())

    def get(self, name: str) -> FakeContainer:
        self.get_calls.append(name)
        if name in self.get_errors:
            raise self.get_errors[name]
        return self._containers[name]

    def run(self, image: str, command: list[str] | None = None, **kwargs: object) -> FakeContainer:
        self.run_calls.append(
            {
                "image": image,
                "command": command,
                **dict(kwargs),
            }
        )
        if self.run_error is not None:
            raise self.run_error
        return FakeContainer("started-container")


class FakeDockerSDKClient:
    def __init__(self, containers: FakeContainerCollection | None = None) -> None:
        self.containers = containers or FakeContainerCollection()


def test_docker_client_uses_from_env_lazily_and_caches_sdk_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from infra.exec.docker import DockerClient

    fake_client = FakeDockerSDKClient()
    from_env_calls = 0

    def fake_from_env() -> FakeDockerSDKClient:
        nonlocal from_env_calls
        from_env_calls += 1
        return fake_client

    monkeypatch.setattr("infra.exec.docker.docker.from_env", fake_from_env)

    client = DockerClient()

    assert from_env_calls == 0

    client.list_containers()
    client.get_container("container-1")

    assert from_env_calls == 1


def test_docker_client_allows_injected_client_factory() -> None:
    from infra.exec.docker import DockerClient

    fake_client = FakeDockerSDKClient()
    factory_calls = 0

    def client_factory() -> FakeDockerSDKClient:
        nonlocal factory_calls
        factory_calls += 1
        return fake_client

    client = DockerClient(client_factory=client_factory)
    container = client.get_container("container-1")

    assert container.id == "container-1"
    assert factory_calls == 1


def test_docker_client_list_containers_forwards_all_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from infra.exec.docker import DockerClient

    fake_client = FakeDockerSDKClient()
    monkeypatch.setattr("infra.exec.docker.docker.from_env", lambda: fake_client)

    client = DockerClient()
    containers = client.list_containers(all=True)

    assert [container.id for container in containers] == ["container-1", "container-2"]
    assert fake_client.containers.list_calls == [{"all": True}]


def test_docker_client_get_container_wraps_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from infra.exec.docker import DockerClient, DockerExecutionError

    fake_client = FakeDockerSDKClient()
    fake_client.containers.get_errors["missing-container"] = NotFound("missing")
    monkeypatch.setattr("infra.exec.docker.docker.from_env", lambda: fake_client)

    client = DockerClient()

    with pytest.raises(
        DockerExecutionError,
        match="missing-container",
    ) as exc_info:
        client.get_container("missing-container")

    assert isinstance(exc_info.value.__cause__, NotFound)


@pytest.mark.asyncio
async def test_docker_client_run_container_forwards_supported_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from infra.exec.docker import DockerClient

    fake_client = FakeDockerSDKClient()
    monkeypatch.setattr("infra.exec.docker.docker.from_env", lambda: fake_client)

    client = DockerClient()
    container = await client.run_container(
        image="portex/agent-runner:latest",
        command=["python", "-m", "runner"],
        volumes={"/tmp/data": {"bind": "/workspace", "mode": "rw"}},
        environment={"PORTEX_GROUP": "group-a"},
        name="portex-agent-group-a",
        working_dir="/workspace",
        detach=False,
        remove=True,
    )

    assert container.id == "started-container"
    assert fake_client.containers.run_calls == [
        {
            "image": "portex/agent-runner:latest",
            "command": ["python", "-m", "runner"],
            "volumes": {"/tmp/data": {"bind": "/workspace", "mode": "rw"}},
            "environment": {"PORTEX_GROUP": "group-a"},
            "name": "portex-agent-group-a",
            "working_dir": "/workspace",
            "detach": False,
            "remove": True,
        }
    ]


@pytest.mark.asyncio
async def test_docker_client_run_container_wraps_sdk_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from infra.exec.docker import DockerClient, DockerExecutionError

    fake_client = FakeDockerSDKClient()
    fake_client.containers.run_error = APIError("docker run failed")
    monkeypatch.setattr("infra.exec.docker.docker.from_env", lambda: fake_client)

    client = DockerClient()

    with pytest.raises(
        DockerExecutionError,
        match="portex/agent-runner:latest",
    ) as exc_info:
        await client.run_container(
            image="portex/agent-runner:latest",
            command=["python", "-m", "runner"],
            volumes={},
            environment={},
        )

    assert isinstance(exc_info.value.__cause__, APIError)


def test_docker_client_lifecycle_helpers_delegate_to_container(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from infra.exec.docker import DockerClient

    target_container = FakeContainer(
        "agent-container",
        wait_result={"StatusCode": 23},
        logs_result=b"line-1\nline-2",
    )
    fake_client = FakeDockerSDKClient(
        FakeContainerCollection({"agent-container": target_container})
    )
    monkeypatch.setattr("infra.exec.docker.docker.from_env", lambda: fake_client)

    client = DockerClient()
    client.stop_container("agent-container", timeout=30)
    wait_result = client.wait_container("agent-container")
    logs = client.get_logs("agent-container", stdout=True, stderr=False, tail=10)
    client.remove_container("agent-container", force=True)

    assert target_container.stop_calls == [{"timeout": 30}]
    assert wait_result == {"StatusCode": 23}
    assert target_container.wait_calls == [{}]
    assert logs == b"line-1\nline-2"
    assert target_container.logs_calls == [{"stdout": True, "stderr": False, "tail": 10}]
    assert target_container.remove_calls == [{"force": True}]


def test_docker_client_stop_container_wraps_container_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from infra.exec.docker import DockerClient, DockerExecutionError

    target_container = FakeContainer("agent-container")
    target_container.stop_error = APIError("stop failed")
    fake_client = FakeDockerSDKClient(
        FakeContainerCollection({"agent-container": target_container})
    )
    monkeypatch.setattr("infra.exec.docker.docker.from_env", lambda: fake_client)

    client = DockerClient()

    with pytest.raises(
        DockerExecutionError,
        match="agent-container",
    ) as exc_info:
        client.stop_container("agent-container")

    assert isinstance(exc_info.value.__cause__, APIError)


def test_build_readonly_volume_returns_ro_binding() -> None:
    from infra.exec.docker import build_readonly_volume

    volume = build_readonly_volume("/host/skills", "/workspace/skills")

    assert volume == {
        "/host/skills": {
            "bind": "/workspace/skills",
            "mode": "ro",
        }
    }


def test_build_volumes_creates_expected_rw_and_ro_mounts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import infra.exec.docker as docker_module

    data_dir = tmp_path / "data"
    monkeypatch.setattr(docker_module, "DATA_DIR", data_dir)

    volumes = docker_module.build_volumes(group_folder="group-alpha", user_id="user-123")

    assert volumes == {
        str(data_dir / "sessions" / "group-alpha" / ".claude"): {
            "bind": "/home/portex/.claude",
            "mode": "rw",
        },
        str(data_dir / "memory" / "group-alpha"): {
            "bind": "/workspace/memory",
            "mode": "rw",
        },
        str(data_dir / "ipc" / "group-alpha"): {
            "bind": "/workspace/ipc",
            "mode": "rw",
        },
        str(data_dir / "groups" / "group-alpha"): {
            "bind": "/workspace/group",
            "mode": "rw",
        },
        str(data_dir / "skills" / "user-123"): {
            "bind": "/workspace/skills",
            "mode": "ro",
        },
    }

    for host_path in volumes:
        assert Path(host_path).exists()


def test_build_volumes_rejects_invalid_group_folder(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import infra.exec.docker as docker_module
    from infra.exec.docker import DockerExecutionError

    monkeypatch.setattr(docker_module, "DATA_DIR", tmp_path / "data")

    with pytest.raises(DockerExecutionError, match="group_folder"):
        docker_module.build_volumes(group_folder="../escape", user_id="user-123")


def test_build_readonly_volume_uses_ro_mode(tmp_path: Path) -> None:
    from infra.exec.docker import build_readonly_volume

    host_path = tmp_path / "skills"
    host_path.mkdir()

    volume = build_readonly_volume(host_path, "/workspace/skills")

    assert volume == {
        str(host_path.resolve()): {
            "bind": "/workspace/skills",
            "mode": "ro",
        }
    }


def test_build_volumes_creates_expected_mounts(tmp_path: Path) -> None:
    from infra.exec.docker import build_volumes

    data_root = tmp_path / "data"

    volumes = build_volumes("group-a", "user-1", data_root=data_root)

    assert volumes[str((data_root / "sessions" / "group-a" / ".claude").resolve())] == {
        "bind": "/home/portex/.claude",
        "mode": "rw",
    }
    assert volumes[str((data_root / "memory" / "group-a").resolve())] == {
        "bind": "/workspace/memory",
        "mode": "rw",
    }
    assert volumes[str((data_root / "ipc" / "group-a").resolve())] == {
        "bind": "/workspace/ipc",
        "mode": "rw",
    }
    assert volumes[str((data_root / "groups" / "group-a").resolve())] == {
        "bind": "/workspace/group",
        "mode": "rw",
    }
    assert volumes[str((data_root / "skills" / "user-1").resolve())] == {
        "bind": "/workspace/skills",
        "mode": "ro",
    }


def test_build_volumes_supports_readonly_mount_overrides(tmp_path: Path) -> None:
    from infra.exec.docker import build_volumes

    data_root = tmp_path / "data"

    volumes = build_volumes(
        "group-a",
        "user-1",
        data_root=data_root,
        readonly_mounts={"memory", "skills"},
    )

    assert volumes[str((data_root / "memory" / "group-a").resolve())]["mode"] == "ro"
    assert volumes[str((data_root / "skills" / "user-1").resolve())]["mode"] == "ro"


def test_build_volumes_rejects_path_traversal(tmp_path: Path) -> None:
    from infra.exec.docker import DockerExecutionError, build_volumes

    with pytest.raises(DockerExecutionError, match="outside allowed roots"):
        build_volumes("../../escape", "user-1", data_root=tmp_path / "data")
