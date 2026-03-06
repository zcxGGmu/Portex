"""Docker SDK execution adapter."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
import re
from typing import Any, NoReturn, Protocol, TypeAlias

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container

from .security import validate_path

DEFAULT_DATA_ROOT = Path("data")
DATA_DIR = DEFAULT_DATA_ROOT
READ_ONLY_MODE = "ro"
READ_WRITE_MODE = "rw"
SESSIONS_CONTAINER_PATH = "/home/portex/.claude"
MEMORY_CONTAINER_PATH = "/workspace/memory"
IPC_CONTAINER_PATH = "/workspace/ipc"
GROUP_CONTAINER_PATH = "/workspace/group"
SKILLS_CONTAINER_PATH = "/workspace/skills"
SAFE_PATH_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ContainerCollection(Protocol):
    def list(self, *, all: bool = False) -> list[Container]:
        ...

    def get(self, name: str) -> Container:
        ...

    def run(
        self,
        image: str,
        command: Sequence[str] | None = None,
        **kwargs: Any,
    ) -> Container:
        ...


class DockerSDKClient(Protocol):
    containers: ContainerCollection


DockerClientFactory: TypeAlias = Callable[[], DockerSDKClient]


class DockerExecutionError(RuntimeError):
    """Raised when Docker SDK operations fail inside the execution layer."""


def _validate_path_segment(value: str, *, label: str) -> str:
    if not SAFE_PATH_SEGMENT.fullmatch(value):
        raise DockerExecutionError(
            f"Invalid {label} '{value}': resolved path is outside allowed roots"
        )
    return value


def build_volume(
    host_path: str | Path,
    container_path: str,
    *,
    read_only: bool = False,
) -> dict[str, dict[str, str]]:
    """Build one Docker SDK volume mapping."""
    resolved_host_path = Path(host_path).expanduser()
    return {
        str(resolved_host_path): {
            "bind": container_path,
            "mode": READ_ONLY_MODE if read_only else READ_WRITE_MODE,
        }
    }


def build_readonly_volume(
    host_path: str | Path,
    container_path: str,
) -> dict[str, dict[str, str]]:
    """Build one read-only Docker SDK volume mapping."""
    return build_volume(host_path, container_path, read_only=True)


def _scoped_directory(root: str | Path, *parts: str, label: str) -> Path:
    base_root = Path(root).expanduser().resolve()
    base_root.mkdir(parents=True, exist_ok=True)
    candidate = base_root.joinpath(*parts).resolve()
    if not validate_path(candidate, [base_root]):
        raise DockerExecutionError(
            f"Invalid {label} '{parts[0]}': resolved path '{candidate}' is outside allowed roots"
        )
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def build_volumes(
    group_folder: str,
    user_id: str,
    *,
    data_root: str | Path | None = None,
    readonly_mounts: set[str] | None = None,
) -> dict[str, dict[str, str]]:
    """Build the default host-to-container volume mappings."""
    readonly_names = set(readonly_mounts or set())
    root = Path(data_root or DATA_DIR).expanduser().resolve()
    safe_group_folder = _validate_path_segment(group_folder, label="group_folder")
    safe_user_id = _validate_path_segment(user_id, label="user_id")

    sessions_dir = _scoped_directory(root / "sessions", safe_group_folder, ".claude", label="group_folder")
    memory_dir = _scoped_directory(root / "memory", safe_group_folder, label="group_folder")
    ipc_dir = _scoped_directory(root / "ipc", safe_group_folder, label="group_folder")
    group_dir = _scoped_directory(root / "groups", safe_group_folder, label="group_folder")
    skills_dir = _scoped_directory(root / "skills", safe_user_id, label="user_id")

    mounts: dict[str, dict[str, str]] = {}
    mounts.update(
        build_volume(
            sessions_dir,
            SESSIONS_CONTAINER_PATH,
            read_only="sessions" in readonly_names,
        )
    )
    mounts.update(
        build_volume(
            memory_dir,
            MEMORY_CONTAINER_PATH,
            read_only="memory" in readonly_names,
        )
    )
    mounts.update(
        build_volume(
            ipc_dir,
            IPC_CONTAINER_PATH,
            read_only="ipc" in readonly_names,
        )
    )
    mounts.update(
        build_volume(
            group_dir,
            GROUP_CONTAINER_PATH,
            read_only="group" in readonly_names,
        )
    )
    mounts.update(
        build_readonly_volume(skills_dir, SKILLS_CONTAINER_PATH)
        if "skills" not in readonly_names
        else build_volume(skills_dir, SKILLS_CONTAINER_PATH, read_only=True)
    )
    return mounts


class DockerClient:
    """Thin wrapper around the Docker SDK client."""

    def __init__(self, client_factory: DockerClientFactory | None = None) -> None:
        self._client_factory = client_factory or docker.from_env
        self._client: DockerSDKClient | None = None

    def _get_client(self) -> DockerSDKClient:
        if self._client is None:
            try:
                self._client = self._client_factory()
            except DockerException as exc:
                self._raise_execution_error(
                    "Failed to create Docker client from environment",
                    exc,
                )
        return self._client

    def _get_bound_container(self, name: str) -> Container:
        try:
            return self._get_client().containers.get(name)
        except NotFound as exc:
            self._raise_execution_error(
                f"Docker container '{name}' was not found",
                exc,
            )
        except DockerException as exc:
            self._raise_execution_error(
                f"Failed to load Docker container '{name}'",
                exc,
            )

    def _raise_execution_error(self, message: str, exc: DockerException) -> NoReturn:
        raise DockerExecutionError(message) from exc

    def list_containers(self, *, all: bool = False) -> list[Container]:
        """List containers from the Docker daemon."""
        try:
            return list(self._get_client().containers.list(all=all))
        except DockerException as exc:
            self._raise_execution_error("Failed to list Docker containers", exc)

    def get_container(self, name: str) -> Container:
        """Fetch a container by name or ID."""
        return self._get_bound_container(name)

    async def run_container(
        self,
        image: str,
        command: Sequence[str] | None = None,
        *,
        volumes: Mapping[str, Any] | None = None,
        environment: Mapping[str, str] | None = None,
        name: str | None = None,
        working_dir: str | None = None,
        detach: bool = True,
        remove: bool = False,
    ) -> Container:
        """Run a container with explicit lifecycle defaults."""
        run_kwargs: dict[str, Any] = {
            "volumes": dict(volumes or {}),
            "environment": dict(environment or {}),
            "detach": detach,
            "remove": remove,
        }
        if name is not None:
            run_kwargs["name"] = name
        if working_dir is not None:
            run_kwargs["working_dir"] = working_dir

        try:
            return await asyncio.to_thread(
                self._get_client().containers.run,
                image,
                list(command) if command is not None else None,
                **run_kwargs,
            )
        except DockerException as exc:
            self._raise_execution_error(
                f"Failed to run Docker container from image '{image}'",
                exc,
            )

    def stop_container(self, name: str, *, timeout: int | None = None) -> None:
        """Stop a running container."""
        stop_kwargs = {"timeout": timeout} if timeout is not None else {}

        try:
            self._get_bound_container(name).stop(**stop_kwargs)
        except DockerException as exc:
            self._raise_execution_error(
                f"Failed to stop Docker container '{name}'",
                exc,
            )

    def get_logs(self, name: str, **kwargs: Any) -> bytes:
        """Return container logs."""
        try:
            return self._get_bound_container(name).logs(**kwargs)
        except DockerException as exc:
            self._raise_execution_error(
                f"Failed to read logs for Docker container '{name}'",
                exc,
            )

    def wait_container(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Wait until a container exits."""
        try:
            result = self._get_bound_container(name).wait(**kwargs)
        except DockerException as exc:
            self._raise_execution_error(
                f"Failed to wait for Docker container '{name}'",
                exc,
            )
        return dict(result)

    def remove_container(self, name: str, *, force: bool = False) -> None:
        """Remove a container."""
        try:
            self._get_bound_container(name).remove(force=force)
        except DockerException as exc:
            self._raise_execution_error(
                f"Failed to remove Docker container '{name}'",
                exc,
            )


DockerExecutor = DockerClient

__all__ = [
    "Container",
    "DATA_DIR",
    "DEFAULT_DATA_ROOT",
    "DockerClient",
    "DockerClientFactory",
    "DockerExecutionError",
    "DockerExecutor",
    "DockerSDKClient",
    "build_readonly_volume",
    "build_volume",
    "build_volumes",
]
