"""Minimal workspace/session lifecycle state for M7.2.4."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from typing import Protocol
from uuid import uuid4


@dataclass(slots=True)
class WorkspaceSessionState:
    workspace_key: str
    session_id: str | None = None
    backend: str | None = None
    ever_committed: bool = False


class WorkspaceResolver(Protocol):
    def resolve_workspace_key(self, group_folder: str, slot_id: str = "main") -> str:
        ...


class GroupFolderWorkspaceResolver:
    """Treat ``group_folder`` as the current workspace identity."""

    def resolve_workspace_key(self, group_folder: str, slot_id: str = "main") -> str:
        return build_slot_workspace_key(group_folder, slot_id)


def build_slot_workspace_key(group_folder: str, slot_id: str = "main") -> str:
    return f"{group_folder}#slot:{slot_id}"


class WorkspaceSessionStore:
    """Track the current committed session per workspace."""

    def __init__(
        self,
        *,
        new_session_id_factory: Callable[[str], str] | None = None,
    ) -> None:
        self._states: dict[str, WorkspaceSessionState] = {}
        self._new_session_id_factory = new_session_id_factory or self._default_new_session_id

    def preview_session_id(
        self,
        workspace_key: str,
        *,
        backend: str,
        fresh_session: bool = False,
    ) -> str:
        state = self._states.setdefault(workspace_key, WorkspaceSessionState(workspace_key))
        if not fresh_session and state.session_id is not None and state.backend == backend:
            return state.session_id
        if state.session_id is None and not state.ever_committed:
            return workspace_key
        return self._new_session_id_factory(workspace_key)

    def commit_success(self, workspace_key: str, *, backend: str, session_id: str) -> None:
        state = self._states.setdefault(workspace_key, WorkspaceSessionState(workspace_key))
        state.session_id = session_id
        state.backend = backend
        state.ever_committed = True

    def invalidate(self, workspace_key: str, *, reason: str) -> None:
        _ = reason
        state = self._states.setdefault(workspace_key, WorkspaceSessionState(workspace_key))
        state.session_id = None
        state.backend = None
        state.ever_committed = True

    def get_state(self, workspace_key: str) -> WorkspaceSessionState:
        state = self._states.get(workspace_key)
        if state is None:
            return WorkspaceSessionState(workspace_key=workspace_key)
        return WorkspaceSessionState(
            workspace_key=state.workspace_key,
            session_id=state.session_id,
            backend=state.backend,
            ever_committed=state.ever_committed,
        )

    def _default_new_session_id(self, workspace_key: str) -> str:
        return f"{workspace_key}:{uuid4().hex[:8]}"


__all__ = [
    "GroupFolderWorkspaceResolver",
    "build_slot_workspace_key",
    "WorkspaceResolver",
    "WorkspaceSessionState",
    "WorkspaceSessionStore",
]
