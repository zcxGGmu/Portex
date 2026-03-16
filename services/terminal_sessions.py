"""Terminal session lifecycle service."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Literal
from uuid import uuid4

from infra.exec.security import validate_path
from services.terminal_bridge import TerminalBridge, TerminalBridgeEvent

TerminalRequestedMode = Literal["openai", "host", "container"]
TerminalBackendName = Literal["docker_container"]
TerminalSessionStatus = Literal["created", "attached", "detached", "closed", "exited"]
DEFAULT_TERMINAL_HISTORY_PERSIST_ROOT = Path(__file__).resolve().parents[1] / "data" / "terminal-history"
_TERMINAL_HISTORY_FILENAME = "latest.json"


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


@dataclass(frozen=True, slots=True)
class TerminalSessionHistorySnapshot:
    record: TerminalSessionRecord
    output: str
    output_bytes: int
    history_max_bytes: int
    truncated: bool


@dataclass(slots=True)
class _ManagedTerminalSession:
    record: TerminalSessionRecord
    bridge: TerminalBridge
    output_queue: asyncio.Queue[TerminalSessionEvent] | None = None
    reconnect_task: asyncio.Task[None] | None = None
    output_history_chunks: deque[str] = field(default_factory=deque)
    output_history_bytes: int = 0
    output_history_truncated: bool = False


class TerminalSessionService:
    """Manage process-local terminal sessions and short reconnect windows."""

    def __init__(
        self,
        *,
        bridge_factory: Callable[..., TerminalBridge],
        reconnect_timeout_seconds: float = 30.0,
        history_max_bytes: int = 32_768,
        history_persist_root: Path | str | None = None,
        now_func: Callable[[], datetime] | None = None,
    ) -> None:
        self._bridge_factory = bridge_factory
        self._reconnect_timeout_seconds = reconnect_timeout_seconds
        self._history_max_bytes = max(0, history_max_bytes)
        if history_persist_root is None:
            history_persist_root = DEFAULT_TERMINAL_HISTORY_PERSIST_ROOT
        self._history_persist_root = Path(history_persist_root).expanduser().resolve()
        self._history_persist_root.mkdir(parents=True, exist_ok=True)
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
            for chunk in managed.output_history_chunks:
                queue.put_nowait(TerminalSessionEvent(event_type="terminal.output", data=chunk))
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

    async def get_history_by_group(self, group_folder: str) -> TerminalSessionHistorySnapshot:
        async with self._lock:
            managed = self._sessions_by_group.get(group_folder)
            if managed is None:
                snapshot = None
            else:
                snapshot = self._build_history_snapshot(managed)
        if snapshot is not None:
            return snapshot
        persisted = await asyncio.to_thread(self._load_persisted_history_snapshot, group_folder)
        if persisted is None:
            raise TerminalSessionNotFoundError("terminal session not found")
        return persisted

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

    async def force_close_session_by_group(self, group_folder: str) -> TerminalSessionRecord:
        async with self._lock:
            managed = self._sessions_by_group.get(group_folder)
            if managed is None:
                raise TerminalSessionNotFoundError("terminal session not found")
            self._cancel_reconnect_task(managed)
            managed.output_queue = None
            managed.record = replace(
                managed.record,
                status="closed",
                reconnect_deadline=None,
            )
            persist_snapshot = self._build_history_snapshot(managed)
        await managed.bridge.close()
        await self._persist_history_snapshot_best_effort(persist_snapshot)
        return managed.record

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
            persist_snapshot = self._build_history_snapshot(managed)
        await managed.bridge.close()
        await self._persist_history_snapshot_best_effort(persist_snapshot)
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
        persist_snapshot: TerminalSessionHistorySnapshot | None = None
        async with self._lock:
            managed = self._sessions_by_id.get(session_id)
            if managed is None:
                return

            if bridge_event.type == "output":
                if isinstance(bridge_event.data, str):
                    self._append_output_history(managed, bridge_event.data)
                    persist_snapshot = self._build_history_snapshot(managed)
                queue = managed.output_queue
            elif bridge_event.type == "exit":
                self._cancel_reconnect_task(managed)
                managed.record = replace(
                    managed.record,
                    status="exited",
                    reconnect_deadline=None,
                )
                persist_snapshot = self._build_history_snapshot(managed)
                queue = managed.output_queue
            elif bridge_event.type == "error":
                queue = managed.output_queue

        if persist_snapshot is not None:
            await self._persist_history_snapshot_best_effort(persist_snapshot)

        if queue is None and bridge_event.type != "output":
            return

        if bridge_event.type == "output":
            if queue is not None:
                await queue.put(TerminalSessionEvent(event_type="terminal.output", data=bridge_event.data))
        elif bridge_event.type == "exit":
            if queue is not None:
                await queue.put(TerminalSessionEvent(event_type="terminal.exit", exit_code=bridge_event.exit_code))
        elif bridge_event.type == "error":
            if queue is not None:
                await queue.put(TerminalSessionEvent(event_type="terminal.error", error=bridge_event.error))

    def _append_output_history(self, managed: _ManagedTerminalSession, chunk: str) -> None:
        if self._history_max_bytes <= 0 or chunk == "":
            if self._history_max_bytes <= 0:
                managed.output_history_chunks.clear()
                managed.output_history_bytes = 0
            return

        chunk_bytes = len(chunk.encode("utf-8", errors="ignore"))
        if chunk_bytes <= 0:
            return

        managed.output_history_chunks.append(chunk)
        managed.output_history_bytes += chunk_bytes

        while managed.output_history_bytes > self._history_max_bytes and managed.output_history_chunks:
            removed = managed.output_history_chunks.popleft()
            managed.output_history_bytes -= len(removed.encode("utf-8", errors="ignore"))
            managed.output_history_truncated = True
        if managed.output_history_bytes < 0:
            managed.output_history_bytes = 0

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
            persist_snapshot = self._build_history_snapshot(managed)
        await managed.bridge.close()
        await self._persist_history_snapshot_best_effort(persist_snapshot)

    def _build_history_snapshot(self, managed: _ManagedTerminalSession) -> TerminalSessionHistorySnapshot:
        return TerminalSessionHistorySnapshot(
            record=managed.record,
            output="".join(managed.output_history_chunks),
            output_bytes=managed.output_history_bytes,
            history_max_bytes=self._history_max_bytes,
            truncated=managed.output_history_truncated,
        )

    async def _persist_history_snapshot_best_effort(
        self,
        snapshot: TerminalSessionHistorySnapshot,
    ) -> None:
        try:
            await asyncio.to_thread(self._persist_history_snapshot, snapshot)
        except Exception:
            return None

    def _persist_history_snapshot(self, snapshot: TerminalSessionHistorySnapshot) -> None:
        path = self._history_snapshot_path(snapshot.record.group_folder)
        payload = {
            "record": {
                "session_id": snapshot.record.session_id,
                "group_id": snapshot.record.group_id,
                "group_folder": snapshot.record.group_folder,
                "owner_user_id": snapshot.record.owner_user_id,
                "backend": snapshot.record.backend,
                "container_name": snapshot.record.container_name,
                "status": snapshot.record.status,
                "created_at": snapshot.record.created_at.isoformat(),
                "last_attached_at": (
                    snapshot.record.last_attached_at.isoformat()
                    if snapshot.record.last_attached_at is not None
                    else None
                ),
                "reconnect_deadline": (
                    snapshot.record.reconnect_deadline.isoformat()
                    if snapshot.record.reconnect_deadline is not None
                    else None
                ),
            },
            "output": snapshot.output,
            "output_bytes": snapshot.output_bytes,
            "history_max_bytes": snapshot.history_max_bytes,
            "truncated": snapshot.truncated,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temp.replace(path)

    def _load_persisted_history_snapshot(self, group_folder: str) -> TerminalSessionHistorySnapshot | None:
        path = self._history_snapshot_path(group_folder)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            record_payload = payload["record"]
            output = payload["output"]
        except Exception:
            return None
        if not isinstance(record_payload, dict) or not isinstance(output, str):
            return None
        if record_payload.get("backend") != "docker_container":
            return None

        created_at = self._parse_persisted_datetime(record_payload.get("created_at"))
        if created_at is None:
            return None
        status = record_payload.get("status")
        if status not in {"created", "attached", "detached", "closed", "exited"}:
            return None

        record = TerminalSessionRecord(
            session_id=str(record_payload.get("session_id", "")),
            group_id=str(record_payload.get("group_id", "")),
            group_folder=str(record_payload.get("group_folder", "")),
            owner_user_id=str(record_payload.get("owner_user_id", "")),
            backend="docker_container",
            container_name=record_payload.get("container_name")
            if isinstance(record_payload.get("container_name"), str)
            else None,
            status=status,
            created_at=created_at,
            last_attached_at=self._parse_persisted_datetime(record_payload.get("last_attached_at")),
            reconnect_deadline=self._parse_persisted_datetime(record_payload.get("reconnect_deadline")),
        )
        if record.session_id == "" or record.group_id == "" or record.group_folder == "" or record.owner_user_id == "":
            return None

        output_bytes = payload.get("output_bytes")
        if not isinstance(output_bytes, int) or output_bytes < 0:
            output_bytes = len(output.encode("utf-8", errors="ignore"))
        history_max_bytes = payload.get("history_max_bytes")
        if not isinstance(history_max_bytes, int) or history_max_bytes < 0:
            history_max_bytes = self._history_max_bytes
        truncated = payload.get("truncated")
        if not isinstance(truncated, bool):
            truncated = False
        return TerminalSessionHistorySnapshot(
            record=record,
            output=output,
            output_bytes=output_bytes,
            history_max_bytes=history_max_bytes,
            truncated=truncated,
        )

    def _history_snapshot_path(self, group_folder: str) -> Path:
        candidate = (self._history_persist_root / group_folder / _TERMINAL_HISTORY_FILENAME).resolve(strict=False)
        if not validate_path(candidate, [self._history_persist_root]):
            raise ValueError("invalid terminal history root")
        return candidate

    @staticmethod
    def _parse_persisted_datetime(value: object) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)


__all__ = [
    "TerminalBackendDisabledError",
    "TerminalBackendUnsupportedError",
    "TerminalSessionConflictError",
    "TerminalSessionEvent",
    "TerminalSessionHistorySnapshot",
    "TerminalSessionNotFoundError",
    "TerminalSessionOwnershipError",
    "TerminalSessionRecord",
    "TerminalSessionService",
]
