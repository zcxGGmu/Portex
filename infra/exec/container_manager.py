"""Container lifecycle orchestration for agent runner instances."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Protocol, runtime_checkable

from .docker import (
    DockerClient,
    GROUP_CONTAINER_PATH,
    IPC_CONTAINER_PATH,
    MEMORY_CONTAINER_PATH,
    SESSIONS_CONTAINER_PATH,
    SKILLS_CONTAINER_PATH,
    build_volumes,
)

CONTAINER_IMAGE = "portex/agent-runner:latest"
CONTAINER_COMMAND = ["python", "-m", "src.runner"]
CONTAINER_WORKDIR = GROUP_CONTAINER_PATH
CONTAINER_NAME_PREFIX = "portex-agent"
_CONTAINER_NAME_SEGMENT = re.compile(r"[^A-Za-z0-9_.-]+")


@runtime_checkable
class ContainerInputPayload(Protocol):
    """Runtime-visible subset of the agent runner input payload."""

    group_folder: str
    session_id: str | None
    agent_name: str


def _sanitize_container_name_segment(value: str, *, default: str) -> str:
    sanitized = _CONTAINER_NAME_SEGMENT.sub("-", value).strip("-.")
    return sanitized or default


class ContainerManager:
    """Compose Docker execution defaults for agent runner containers."""

    def __init__(
        self,
        docker_client: DockerClient,
        *,
        container_image: str = CONTAINER_IMAGE,
        data_root: str | Path | None = None,
        readonly_mounts: set[str] | None = None,
    ) -> None:
        self.client = docker_client
        self.container_image = container_image
        self.data_root = Path(data_root).expanduser() if data_root is not None else None
        self.readonly_mounts = set(readonly_mounts or set())

    def build_container_name(
        self,
        group_folder: str,
        payload: ContainerInputPayload,
    ) -> str:
        """Build a predictable container name for tracing and later lifecycle steps."""
        safe_group = _sanitize_container_name_segment(group_folder, default="group")
        safe_session = _sanitize_container_name_segment(
            payload.session_id or "",
            default="",
        )
        if safe_session:
            return f"{CONTAINER_NAME_PREFIX}-{safe_group}-{safe_session}"
        return f"{CONTAINER_NAME_PREFIX}-{safe_group}"

    def build_environment(
        self,
        group_folder: str,
        payload: ContainerInputPayload,
    ) -> dict[str, str]:
        """Build runner metadata passed through container environment variables."""
        return {
            "PORTEX_RUN_MODE": "container",
            "PORTEX_GROUP_FOLDER": group_folder,
            "PORTEX_SESSION_ID": payload.session_id or "",
            "PORTEX_AGENT_NAME": payload.agent_name,
            "PORTEX_GROUP_DIR": GROUP_CONTAINER_PATH,
            "PORTEX_IPC_DIR": IPC_CONTAINER_PATH,
            "PORTEX_MEMORY_DIR": MEMORY_CONTAINER_PATH,
            "PORTEX_SKILLS_DIR": SKILLS_CONTAINER_PATH,
            "PORTEX_SESSIONS_DIR": SESSIONS_CONTAINER_PATH,
        }

    def build_runner_volumes(
        self,
        group_folder: str,
        user_id: str,
    ) -> dict[str, dict[str, str]]:
        """Build the default volume mappings for one agent container."""
        return build_volumes(
            group_folder,
            user_id,
            data_root=self.data_root,
            readonly_mounts=self.readonly_mounts,
        )

    async def start_agent_container(
        self,
        group_folder: str,
        user_id: str,
        payload: ContainerInputPayload,
    ) -> str:
        """Start one runner container and return its Docker container ID."""
        if payload.group_folder != group_folder:
            raise ValueError(
                "Container payload group_folder does not match the requested group_folder"
            )

        container = await self.client.run_container(
            image=self.container_image,
            command=CONTAINER_COMMAND,
            volumes=self.build_runner_volumes(group_folder, user_id),
            environment=self.build_environment(group_folder, payload),
            name=self.build_container_name(group_folder, payload),
            working_dir=CONTAINER_WORKDIR,
            detach=True,
            remove=False,
        )
        return container.id

    async def stop_container(
        self,
        container_id: str,
        *,
        timeout: int = 30,
    ) -> None:
        """Stop one runner container and remove it afterwards."""
        self.client.stop_container(container_id, timeout=timeout)
        self.client.remove_container(container_id, force=False)

    async def is_container_healthy(self, container_id: str) -> bool:
        """Return whether one runner container is currently running."""
        container = self.client.get_container(container_id)
        return container.status == "running"

__all__ = [
    "CONTAINER_COMMAND",
    "CONTAINER_IMAGE",
    "CONTAINER_WORKDIR",
    "ContainerInputPayload",
    "ContainerManager",
]
