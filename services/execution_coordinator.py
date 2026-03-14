"""Per-group execution coordinator for M7.2."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Literal, Protocol
from uuid import uuid4

from services.workspace_lifecycle import (
    GroupFolderWorkspaceResolver,
    WorkspaceResolver,
    WorkspaceSessionStore,
)

ExecutionSource = Literal["web", "im", "scheduled"]
ExecutionStatus = Literal["queued", "running", "completed", "failed", "cancelled", "timeout"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class ExecutionRequest:
    group_folder: str
    chat_jid: str
    user_id: str
    prompt: str
    source: ExecutionSource
    slot_id: str = "main"
    requested_mode: str | None = None
    timeout_ms: int | None = None
    fresh_session: bool = False
    request_id: str | None = None
    request_metadata: Mapping[str, Any] | None = None


@dataclass(slots=True)
class ExecutionHandle:
    run_id: str
    group_folder: str
    status: ExecutionStatus


@dataclass(slots=True)
class ExecutionResult:
    run_id: str
    status: ExecutionStatus
    group_folder: str
    backend: str
    session_id: str
    slot_id: str = "main"
    final_output: str | None = None
    error: str | None = None
    timeout_ms: int | None = None


@dataclass(slots=True)
class ExecutionRunSnapshot:
    run_id: str
    group_folder: str
    chat_jid: str
    user_id: str
    source: ExecutionSource
    requested_mode: str | None
    status: ExecutionStatus
    slot_id: str = "main"
    backend: str | None = None
    session_id: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    final_output: str | None = None
    error: str | None = None
    timeout_ms: int | None = None
    recovery_attempted: bool = False
    recovery_reason: str | None = None
    recovery_succeeded: bool | None = None


@dataclass(frozen=True, slots=True)
class MonitorQueueGroupSnapshot:
    group_id: str
    queued_runs: int
    running_runs: int
    active_run_id: str | None = None
    active_backend: str | None = None


class ExecutionBackend(Protocol):
    async def execute(
        self,
        request: ExecutionRequest,
        *,
        run_id: str,
        session_id: str,
    ) -> dict[str, Any] | ExecutionResult:
        ...

    async def cancel(self, run_id: str) -> None:
        ...


class ExecutionPolicyProtocol(Protocol):
    def select_backend(self, request: ExecutionRequest) -> str:
        ...


class ExecutionCoordinator:
    """Coordinate one active execution at a time per group."""

    def __init__(
        self,
        *,
        execution_policy: ExecutionPolicyProtocol,
        backends: Mapping[str, ExecutionBackend],
        workspace_resolver: WorkspaceResolver | None = None,
        workspace_session_store: WorkspaceSessionStore | None = None,
        max_completed_runs: int = 256,
    ) -> None:
        self._execution_policy = execution_policy
        self._backends = dict(backends)
        self._workspace_resolver = workspace_resolver or GroupFolderWorkspaceResolver()
        self._workspace_session_store = workspace_session_store or WorkspaceSessionStore()
        self._max_completed_runs = max_completed_runs
        self._group_queues: dict[str, deque[tuple[str, ExecutionRequest]]] = {}
        self._group_workers: dict[str, asyncio.Task[None]] = {}
        self._run_futures: dict[str, asyncio.Future[ExecutionResult]] = {}
        self._run_requests: dict[str, ExecutionRequest] = {}
        self._statuses: dict[str, ExecutionStatus] = {}
        self._running_backends: dict[str, ExecutionBackend] = {}
        self._running_tasks: dict[str, asyncio.Task[ExecutionResult]] = {}
        self._run_session_ids: dict[str, str] = {}
        self._cancelled_run_ids: set[str] = set()
        self._completed_results: dict[str, ExecutionResult] = {}
        self._completed_order: deque[str] = deque()
        self._run_snapshots: dict[str, ExecutionRunSnapshot] = {}

    async def submit_execution(self, request: ExecutionRequest) -> ExecutionHandle:
        run_id = request.request_id or uuid4().hex
        future: asyncio.Future[ExecutionResult] = asyncio.get_running_loop().create_future()
        self._run_futures[run_id] = future
        self._run_requests[run_id] = request
        self._statuses[run_id] = "queued"
        self._run_snapshots[run_id] = ExecutionRunSnapshot(
            run_id=run_id,
            group_folder=request.group_folder,
            chat_jid=request.chat_jid,
            user_id=request.user_id,
            source=request.source,
            slot_id=request.slot_id,
            requested_mode=request.requested_mode,
            status="queued",
        )
        queue = self._group_queues.setdefault(request.group_folder, deque())
        queue.append((run_id, request))
        self._ensure_worker(request.group_folder)
        return ExecutionHandle(
            run_id=run_id,
            group_folder=request.group_folder,
            status="queued",
        )

    def get_status(self, run_id: str) -> ExecutionStatus | None:
        return self._statuses.get(run_id)

    def get_run_snapshot(self, run_id: str) -> ExecutionRunSnapshot | None:
        snapshot = self._run_snapshots.get(run_id)
        if snapshot is None:
            return None
        return replace(snapshot)

    def get_monitor_queue_snapshot(self) -> list[MonitorQueueGroupSnapshot]:
        groups: dict[str, dict[str, int | str | None]] = {}
        for run_id, request in self._run_requests.items():
            status = self._statuses.get(run_id)
            if status not in {"queued", "running"}:
                continue
            current = groups.setdefault(
                request.group_folder,
                {
                    "queued_runs": 0,
                    "running_runs": 0,
                    "active_run_id": None,
                    "active_backend": None,
                },
            )
            if status == "queued":
                current["queued_runs"] = int(current["queued_runs"]) + 1
                continue
            current["running_runs"] = int(current["running_runs"]) + 1
            current["active_run_id"] = run_id
            snapshot = self._run_snapshots.get(run_id)
            current["active_backend"] = None if snapshot is None else snapshot.backend

        return [
            MonitorQueueGroupSnapshot(
                group_id=group_id,
                queued_runs=int(values["queued_runs"]),
                running_runs=int(values["running_runs"]),
                active_run_id=values["active_run_id"],
                active_backend=values["active_backend"],
            )
            for group_id, values in sorted(groups.items())
        ]

    def list_run_snapshots(self, limit: int = 50) -> list[ExecutionRunSnapshot]:
        snapshots = [replace(snapshot) for snapshot in self._run_snapshots.values()]
        snapshots.sort(key=lambda snapshot: snapshot.created_at, reverse=True)
        return snapshots[:limit]

    def list_backend_names(self) -> list[str]:
        return sorted(self._backends.keys())

    def get_backend(self, backend_name: str) -> ExecutionBackend | None:
        return self._backends.get(backend_name)

    async def wait_for_run(self, run_id: str) -> ExecutionResult:
        completed = self._completed_results.get(run_id)
        if completed is not None:
            return completed
        future = self._run_futures[run_id]
        return await future

    async def cancel(self, run_id: str) -> bool:
        status = self._statuses.get(run_id)
        if status is None:
            return False
        if status == "queued":
            request = self._run_requests[run_id]
            backend = self._safe_select_backend_name(request)
            session_id = self._peek_session_id(request, backend)
            self._store_terminal_result(
                self._build_result(
                    run_id=run_id,
                        group_folder=request.group_folder,
                        backend=backend,
                        session_id=session_id,
                        slot_id=request.slot_id,
                        status="cancelled",
                    )
                )
            return True
        if status == "running":
            request = self._run_requests[run_id]
            backend_name = self._safe_select_backend_name(request)
            session_id = self._run_session_ids.get(run_id, self._peek_session_id(request, backend_name))
            backend = self._running_backends.get(run_id)
            if backend is not None:
                self._cancelled_run_ids.add(run_id)
                self._statuses[run_id] = "cancelled"
                execution_task = self._running_tasks.get(run_id)
                if execution_task is not None and not execution_task.done():
                    execution_task.cancel()
                self._store_terminal_result(
                    self._build_result(
                        run_id=run_id,
                        group_folder=request.group_folder,
                        backend=backend_name,
                        session_id=session_id,
                        slot_id=request.slot_id,
                        status="cancelled",
                    )
                )
                asyncio.create_task(self._best_effort_backend_cancel(backend, run_id))
                return True
        return False

    def _ensure_worker(self, group_folder: str) -> None:
        task = self._group_workers.get(group_folder)
        if task is None or task.done():
            self._group_workers[group_folder] = asyncio.create_task(self._run_group_queue(group_folder))

    async def _run_group_queue(self, group_folder: str) -> None:
        queue = self._group_queues[group_folder]
        while queue:
            run_id, request = queue.popleft()
            future = self._run_futures.get(run_id)
            if future is None or future.done():
                continue
            try:
                await self._execute_request(run_id, request)
            except Exception as exc:  # pragma: no cover - defensive coordinator guard
                self._store_terminal_result(
                    self._build_result(
                        run_id=run_id,
                        group_folder=request.group_folder,
                        backend=self._safe_select_backend_name(request),
                        session_id=self._peek_session_id(
                            request,
                            self._safe_select_backend_name(request),
                        ),
                        slot_id=request.slot_id,
                        status="failed",
                        error=str(exc),
                    )
                )
        self._group_workers.pop(group_folder, None)

    async def _execute_request(self, run_id: str, request: ExecutionRequest) -> None:
        try:
            backend_name = self._select_backend_name(request)
        except Exception as exc:
            session_id = self._peek_session_id(request, "unknown")
            self._store_terminal_result(
                self._build_result(
                    run_id=run_id,
                    group_folder=request.group_folder,
                    backend="unknown",
                    session_id=session_id,
                    slot_id=request.slot_id,
                    status="failed",
                    error=str(exc),
                )
            )
            return

        backend = self._backends.get(backend_name)
        if backend is None:
            session_id = self._peek_session_id(request, backend_name)
            self._store_terminal_result(
                self._build_result(
                    run_id=run_id,
                    group_folder=request.group_folder,
                    backend=backend_name,
                    session_id=session_id,
                    status="failed",
                    error=f"unknown execution backend: {backend_name}",
                )
            )
            return

        workspace_key = self._workspace_key(request)
        session_id = self._resolve_session_id(request, backend_name)
        self._run_session_ids[run_id] = session_id
        self._statuses[run_id] = "running"
        self._mark_running(
            run_id,
            backend=backend_name,
            session_id=session_id,
        )
        self._running_backends[run_id] = backend
        execution_task = asyncio.create_task(
            self._execute_backend_with_lifecycle(
                backend,
                request,
                run_id=run_id,
                backend_name=backend_name,
                workspace_key=workspace_key,
                session_id=session_id,
            )
        )
        self._running_tasks[run_id] = execution_task

        try:
            result = await execution_task
        except asyncio.CancelledError:
            if run_id in self._cancelled_run_ids:
                self._cancelled_run_ids.discard(run_id)
                return
            raise
        finally:
            self._running_backends.pop(run_id, None)
            self._running_tasks.pop(run_id, None)
            self._run_session_ids.pop(run_id, None)

        if run_id in self._cancelled_run_ids:
            self._cancelled_run_ids.discard(run_id)
            return
        self._store_terminal_result(result)

    async def _execute_backend_with_lifecycle(
        self,
        backend: ExecutionBackend,
        request: ExecutionRequest,
        *,
        run_id: str,
        backend_name: str,
        workspace_key: str,
        session_id: str,
    ) -> ExecutionResult:
        try:
            result = await self._run_backend_with_timeout(
                backend,
                request,
                run_id=run_id,
                backend_name=backend_name,
                session_id=session_id,
            )
        except RuntimeError as exc:
            if self._should_retry_session_resume(
                backend_name=backend_name,
                request=request,
                error=exc,
            ):
                self._mark_recovery_attempt(run_id, reason=str(exc))
                self._workspace_session_store.invalidate(workspace_key, reason=str(exc))
                retry_session_id = self._resolve_session_id(
                    request,
                    backend_name,
                    fresh_session=True,
                )
                self._run_session_ids[run_id] = retry_session_id
                try:
                    result = await self._run_backend_with_timeout(
                        backend,
                        request,
                        run_id=run_id,
                        backend_name=backend_name,
                        session_id=retry_session_id,
                    )
                except RuntimeError as retry_exc:
                    self._mark_recovery_result(run_id, succeeded=False)
                    return self._build_result(
                        run_id=run_id,
                        group_folder=request.group_folder,
                        backend=backend_name,
                        session_id=retry_session_id,
                        slot_id=request.slot_id,
                        status="failed",
                        error=str(retry_exc),
                    )
                self._mark_recovery_result(run_id, succeeded=True)
            else:
                return self._build_result(
                    run_id=run_id,
                    group_folder=request.group_folder,
                    backend=backend_name,
                    session_id=session_id,
                    slot_id=request.slot_id,
                    status="failed",
                    error=str(exc),
                )

        if self._uses_workspace_session(backend_name) and result.status == "completed":
            self._workspace_session_store.commit_success(
                workspace_key,
                backend=backend_name,
                session_id=result.session_id,
            )
        return result

    async def _run_backend_with_timeout(
        self,
        backend: ExecutionBackend,
        request: ExecutionRequest,
        *,
        run_id: str,
        backend_name: str,
        session_id: str,
    ) -> ExecutionResult:
        timeout_seconds = None if request.timeout_ms is None else request.timeout_ms / 1000
        try:
            if timeout_seconds is None:
                raw_result = await backend.execute(request, run_id=run_id, session_id=session_id)
            else:
                raw_result = await asyncio.wait_for(
                    backend.execute(request, run_id=run_id, session_id=session_id),
                    timeout=timeout_seconds,
                )
        except asyncio.TimeoutError:
            asyncio.create_task(self._best_effort_backend_cancel(backend, run_id))
            return self._build_result(
                run_id=run_id,
                group_folder=request.group_folder,
                backend=backend_name,
                session_id=session_id,
                slot_id=request.slot_id,
                status="timeout",
                timeout_ms=request.timeout_ms,
            )
        except RuntimeError:
            raise
        except Exception as exc:
            return self._build_result(
                run_id=run_id,
                group_folder=request.group_folder,
                backend=backend_name,
                session_id=session_id,
                slot_id=request.slot_id,
                status="failed",
                error=str(exc),
            )

        if isinstance(raw_result, ExecutionResult):
            return raw_result

        return self._build_result(
            run_id=run_id,
            group_folder=request.group_folder,
            backend=backend_name,
            session_id=session_id,
            slot_id=request.slot_id,
            status=raw_result.get("status", "completed"),
            final_output=raw_result.get("final_output"),
            error=raw_result.get("error"),
            timeout_ms=raw_result.get("timeout_ms"),
        )

    def _workspace_key(self, request: ExecutionRequest) -> str:
        return self._workspace_resolver.resolve_workspace_key(request.group_folder, request.slot_id)

    def _resolve_session_id(
        self,
        request: ExecutionRequest,
        backend_name: str,
        *,
        fresh_session: bool | None = None,
    ) -> str:
        workspace_key = self._workspace_key(request)
        effective_fresh = request.fresh_session if fresh_session is None else fresh_session
        if self._uses_workspace_session(backend_name):
            return self._workspace_session_store.preview_session_id(
                workspace_key,
                backend=backend_name,
                fresh_session=effective_fresh,
            )
        if effective_fresh:
            return f"{workspace_key}:{uuid4().hex[:8]}"
        return workspace_key

    def _peek_session_id(self, request: ExecutionRequest, backend_name: str) -> str:
        return self._resolve_session_id(request, backend_name)

    def _select_backend_name(self, request: ExecutionRequest) -> str:
        return self._execution_policy.select_backend(request)

    def _safe_select_backend_name(self, request: ExecutionRequest) -> str:
        try:
            return self._select_backend_name(request)
        except Exception:
            return "unknown"

    async def _best_effort_backend_cancel(self, backend: ExecutionBackend, run_id: str) -> None:
        try:
            await backend.cancel(run_id)
        except Exception:
            return None

    def _uses_workspace_session(self, backend_name: str) -> bool:
        return backend_name == "openai_runtime"

    def _should_retry_session_resume(
        self,
        *,
        backend_name: str,
        request: ExecutionRequest,
        error: RuntimeError,
    ) -> bool:
        if request.fresh_session or not self._uses_workspace_session(backend_name):
            return False
        try:
            from services.execution_backends import SessionResumeFailedError
        except Exception:
            return False
        return isinstance(error, SessionResumeFailedError)

    def _mark_running(self, run_id: str, *, backend: str, session_id: str) -> None:
        snapshot = self._run_snapshots.get(run_id)
        if snapshot is None:
            return
        snapshot.status = "running"
        snapshot.backend = backend
        snapshot.session_id = session_id
        snapshot.started_at = _utcnow()

    def _mark_recovery_attempt(self, run_id: str, *, reason: str) -> None:
        snapshot = self._run_snapshots.get(run_id)
        if snapshot is None:
            return
        snapshot.recovery_attempted = True
        snapshot.recovery_reason = reason
        snapshot.recovery_succeeded = None

    def _mark_recovery_result(self, run_id: str, *, succeeded: bool) -> None:
        snapshot = self._run_snapshots.get(run_id)
        if snapshot is None:
            return
        snapshot.recovery_succeeded = succeeded

    def _store_terminal_result(self, result: ExecutionResult) -> None:
        self._statuses[result.run_id] = result.status
        self._completed_results[result.run_id] = result
        self._completed_order.append(result.run_id)
        self._mark_terminal(result)
        while len(self._completed_order) > self._max_completed_runs:
            stale_run_id = self._completed_order.popleft()
            self._completed_results.pop(stale_run_id, None)
            self._statuses.pop(stale_run_id, None)
            self._run_snapshots.pop(stale_run_id, None)

        future = self._run_futures.pop(result.run_id, None)
        if future is not None and not future.done():
            future.set_result(result)
        self._run_requests.pop(result.run_id, None)

    def _mark_terminal(self, result: ExecutionResult) -> None:
        snapshot = self._run_snapshots.get(result.run_id)
        if snapshot is None:
            return
        snapshot.status = result.status
        snapshot.backend = result.backend
        snapshot.session_id = result.session_id
        snapshot.slot_id = result.slot_id
        snapshot.final_output = result.final_output
        snapshot.error = result.error
        snapshot.timeout_ms = result.timeout_ms
        snapshot.finished_at = _utcnow()

    def _build_result(
        self,
        *,
        run_id: str,
        group_folder: str,
        backend: str,
        session_id: str,
        status: ExecutionStatus,
        slot_id: str = "main",
        final_output: str | None = None,
        error: str | None = None,
        timeout_ms: int | None = None,
    ) -> ExecutionResult:
        return ExecutionResult(
            run_id=run_id,
            status=status,
            group_folder=group_folder,
            backend=backend,
            session_id=session_id,
            slot_id=slot_id,
            final_output=final_output,
            error=error,
            timeout_ms=timeout_ms,
        )


__all__ = [
    "ExecutionBackend",
    "ExecutionCoordinator",
    "ExecutionHandle",
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutionRunSnapshot",
    "ExecutionSource",
    "ExecutionStatus",
    "MonitorQueueGroupSnapshot",
]
