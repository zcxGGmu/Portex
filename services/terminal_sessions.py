"""Terminal session lifecycle service."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

from services.terminal_bridge import TerminalBridge, TerminalBridgeEvent

TerminalRequestedMode = Literal["openai", "host", "container"]
TerminalBackendName = Literal["docker_container"]
TerminalSessionStatus = Literal["created", "attached", "detached", "closed", "exited"]


class TerminalBackendUnsupportedError(RuntimeError):
    """Raised when the requested terminal backend cannot support terminal sessions."""


class TerminalBackendDisabledError(RuntimeError):
    """Raised when the requested terminal backend is intentionally disabled."""


class TerminalSessionConflictError(RuntimeError):
    """Raised when a workspace already has an active session owned by another user."""


class TerminalSessionNotFoundError(RuntimeError):
    """Raised when a terminal session does not exist."""


class TerminalSessionOwnershipError(RuntimeError):
    """Raised when a user attempts to control another user's terminal session."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class TerminalSessionEvent:
    event_type: str
    data: str | None = None
    exit_code: int | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class TerminalSessionRecord:
    session_id: str
    group_id: str
    group_folder: str
    owner_user_id: str
    backend: TerminalBackendName
    container_name: str | None
    status: TerminalSessionStatus
    created_at: datetime
    last_attached_at: datetime | None = None
    reconnect_deadline: datetime | None = None


@dataclass(slots=True)
class _ManagedTerminalSession:
    record: TerminalSessionRecord
    bridge: TerminalBridge
    output_queue: asyncio.Queue[TerminalSessionEvent] | None = None
    reconnect_task: asyncio.Task[None] | None = None


class TerminalSessionService:
    """Manage process-local terminal sessions and short reconnect windows."""

    def __init__(
        self,
        *,
        bridge_factory: Callable[..., TerminalBridge],
        reconnect_timeout_seconds: float = 30.0,
        now_func: Callable[[], datetime] | None = None,
    ) -> None:
        self._bridge_factory = bridge_factory
        self._reconnect_timeout_seconds = reconnect_timeout_seconds
        self._now = now_func or _utcnow
        self._sessions_by_group: dict[str, _ManagedTerminalSession] = {}
        self._sessions_by_id: dict[str, _ManagedTerminalSession] = {}
        self._lock = asyncio.Lock()

    async def create_session(
        self,
        *,
        group_id: str,
        group_folder: str,
        owner_user_id: str,
        requested_mode: TerminalRequestedMode = "container",
    ) -> TerminalSessionRecord:
        backend = self._resolve_backend(requested_mode)

        async with self._lock:
            existing = self._sessions_by_group.get(group_folder)
            if existing is not None and existing.record.status not in {"closed", "exited"}:
                if existing.record.owner_user_id != owner_user_id:
                    raise TerminalSessionConflictError("active terminal session already owned by another user")
                return existing.record
            if existing is not None:
                self._drop_session(existing)

            session_id = uuid4().hex
            bridge = self._bridge_factory(
                group_id=group_id,
                group_folder=group_folder,
                owner_user_id=owner_user_id,
                session_id=session_id,
            )
            container_name = getattr(bridge, "container_name", None)
            record = TerminalSessionRecord(
                session_id=session_id,
                group_id=group_id,
                group_folder=group_folder,
                owner_user_id=owner_user_id,
                backend=backend,
                container_name=container_name if isinstance(container_name, str) else None,
                status="created",
                created_at=self._now(),
            )
            managed = _ManagedTerminalSession(record=record, bridge=bridge)
            self._sessions_by_group[group_folder] = managed
            self._sessions_by_id[session_id] = managed

        await bridge.start(lambda event: self._handle_bridge_event(session_id, event))
        return self.get_current_session(group_folder) or record

    def get_current_session(self, group_folder: str) -> TerminalSessionRecord | None:
        session = self._sessions_by_group.get(group_folder)
        return None if session is None else session.record

    def list_sessions(self) -> list[TerminalSessionRecord]:
        """Return current in-memory session snapshots ordered by workspace folder."""

        records = [managed.record for managed in self._sessions_by_group.values()]
        records.sort(key=lambda item: (item.group_folder, item.session_id))
        return records

    async def attach_session(
        self,
        session_id: str,
        *,
        owner_user_id: str,
    ) -> tuple[TerminalSessionRecord, asyncio.Queue[TerminalSessionEvent]]:
        async with self._lock:
            managed = self._require_session(session_id)
            self._require_owner(managed, owner_user_id)
            self._cancel_reconnect_task(managed)
            queue: asyncio.Queue[TerminalSessionEvent] = asyncio.Queue()
            now = self._now()
            managed.output_queue = queue
            managed.record = replace(
                managed.record,
                status="attached",
                last_attached_at=now,
                reconnect_deadline=None,
            )
            return managed.record, queue

    async def detach_session(
        self,
        session_id: str,
        *,
        owner_user_id: str,
    ) -> TerminalSessionRecord:
        async with self._lock:
            managed = self._require_session(session_id)
            self._require_owner(managed, owner_user_id)
            deadline = self._now() + timedelta(seconds=self._reconnect_timeout_seconds)
            managed.output_queue = None
            managed.record = replace(
                managed.record,
                status="detached",
                reconnect_deadline=deadline,
            )
            self._cancel_reconnect_task(managed)
            managed.reconnect_task = asyncio.create_task(self._expire_detached_session(session_id, deadline))
            return managed.record

    async def send_input(self, session_id: str, *, owner_user_id: str, data: str) -> None:
        managed = self._require_session(session_id)
        self._require_owner(managed, owner_user_id)
        await managed.bridge.send_input(data)

    async def resize(self, session_id: str, *, owner_user_id: str, cols: int, rows: int) -> None:
        managed = self._require_session(session_id)
        self._require_owner(managed, owner_user_id)
        await managed.bridge.resize(cols=cols, rows=rows)

    async def close_session_by_group(
        self,
        group_folder: str,
        *,
        owner_user_id: str,
    ) -> TerminalSessionRecord:
        async with self._lock:
            managed = self._sessions_by_group.get(group_folder)
            if managed is None:
                raise TerminalSessionNotFoundError("terminal session not found")
            self._require_owner(managed, owner_user_id)
        return await self.close_session(managed.record.session_id, owner_user_id=owner_user_id)

    async def close_session(
        self,
        session_id: str,
        *,
        owner_user_id: str,
    ) -> TerminalSessionRecord:
        async with self._lock:
            managed = self._require_session(session_id)
            self._require_owner(managed, owner_user_id)
            self._cancel_reconnect_task(managed)
            managed.output_queue = None
            managed.record = replace(
                managed.record,
                status="closed",
                reconnect_deadline=None,
            )
        await managed.bridge.close()
        return managed.record

    def _resolve_backend(self, requested_mode: TerminalRequestedMode) -> TerminalBackendName:
        if requested_mode == "container":
            return "docker_container"
        if requested_mode == "host":
            raise TerminalBackendDisabledError("host_process backend is disabled for terminal sessions")
        raise TerminalBackendUnsupportedError("openai_runtime backend does not support terminal sessions")

    def _require_session(self, session_id: str) -> _ManagedTerminalSession:
        managed = self._sessions_by_id.get(session_id)
        if managed is None:
            raise TerminalSessionNotFoundError("terminal session not found")
        return managed

    def _require_owner(self, managed: _ManagedTerminalSession, owner_user_id: str) -> None:
        if managed.record.owner_user_id != owner_user_id:
            raise TerminalSessionOwnershipError("terminal session is owned by another user")

    def _cancel_reconnect_task(self, managed: _ManagedTerminalSession) -> None:
        task = managed.reconnect_task
        managed.reconnect_task = None
        if task is not None and not task.done():
            task.cancel()

    def _drop_session(self, managed: _ManagedTerminalSession) -> None:
        self._sessions_by_group.pop(managed.record.group_folder, None)
        self._sessions_by_id.pop(managed.record.session_id, None)
        self._cancel_reconnect_task(managed)

    async def _handle_bridge_event(self, session_id: str, event: TerminalBridgeEvent | dict[str, object]) -> None:
        if isinstance(event, dict):
            bridge_event = TerminalBridgeEvent(
                type=str(event.get("type", "")),
                data=event.get("data") if isinstance(event.get("data"), str) else None,
                exit_code=event.get("exit_code") if isinstance(event.get("exit_code"), int) else None,
                error=event.get("error") if isinstance(event.get("error"), str) else None,
            )
        else:
            bridge_event = event

        queue: asyncio.Queue[TerminalSessionEvent] | None = None
        async with self._lock:
            managed = self._sessions_by_id.get(session_id)
            if managed is None:
                return

            if bridge_event.type == "output":
                queue = managed.output_queue
            elif bridge_event.type == "exit":
                self._cancel_reconnect_task(managed)
                managed.record = replace(
                    managed.record,
                    status="exited",
                    reconnect_deadline=None,
                )
                queue = managed.output_queue
            elif bridge_event.type == "error":
                queue = managed.output_queue

        if queue is None:
            return

        if bridge_event.type == "output":
            await queue.put(TerminalSessionEvent(event_type="terminal.output", data=bridge_event.data))
        elif bridge_event.type == "exit":
            await queue.put(TerminalSessionEvent(event_type="terminal.exit", exit_code=bridge_event.exit_code))
        elif bridge_event.type == "error":
            await queue.put(TerminalSessionEvent(event_type="terminal.error", error=bridge_event.error))

    async def _expire_detached_session(self, session_id: str, deadline: datetime) -> None:
        await asyncio.sleep(self._reconnect_timeout_seconds)
        async with self._lock:
            managed = self._sessions_by_id.get(session_id)
            if managed is None:
                return
            if managed.record.status != "detached":
                return
            if managed.record.reconnect_deadline != deadline:
                return
            managed.record = replace(
                managed.record,
                status="closed",
                reconnect_deadline=None,
            )
        await managed.bridge.close()


__all__ = [
    "TerminalBackendDisabledError",
    "TerminalBackendUnsupportedError",
    "TerminalSessionConflictError",
    "TerminalSessionEvent",
    "TerminalSessionNotFoundError",
    "TerminalSessionOwnershipError",
    "TerminalSessionRecord",
    "TerminalSessionService",
]
