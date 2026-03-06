"""Docker SDK execution adapter."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping, Sequence
from typing import Any, NoReturn, Protocol, TypeAlias

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container


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
    "DockerClient",
    "DockerClientFactory",
    "DockerExecutionError",
    "DockerExecutor",
    "DockerSDKClient",
]
