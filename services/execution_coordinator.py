"""Per-group execution coordinator for M7.2."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol
from uuid import uuid4

ExecutionSource = Literal["web", "im", "scheduled"]
ExecutionStatus = Literal["queued", "running", "completed", "failed", "cancelled", "timeout"]


@dataclass(slots=True)
class ExecutionRequest:
    group_folder: str
    chat_jid: str
    user_id: str
    prompt: str
    source: ExecutionSource
    requested_mode: str | None = None
    timeout_ms: int | None = None
    fresh_session: bool = False


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
    final_output: str | None = None
    error: str | None = None
    timeout_ms: int | None = None


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
        max_completed_runs: int = 256,
    ) -> None:
        self._execution_policy = execution_policy
        self._backends = dict(backends)
        self._max_completed_runs = max_completed_runs
        self._group_queues: dict[str, deque[tuple[str, ExecutionRequest]]] = {}
        self._group_workers: dict[str, asyncio.Task[None]] = {}
        self._run_futures: dict[str, asyncio.Future[ExecutionResult]] = {}
        self._run_requests: dict[str, ExecutionRequest] = {}
        self._statuses: dict[str, ExecutionStatus] = {}
        self._running_backends: dict[str, ExecutionBackend] = {}
        self._running_tasks: dict[str, asyncio.Task[ExecutionResult]] = {}
        self._session_ids: dict[str, str] = {}
        self._run_session_ids: dict[str, str] = {}
        self._cancelled_run_ids: set[str] = set()
        self._completed_results: dict[str, ExecutionResult] = {}
        self._completed_order: deque[str] = deque()

    async def submit_execution(self, request: ExecutionRequest) -> ExecutionHandle:
        run_id = uuid4().hex
        future: asyncio.Future[ExecutionResult] = asyncio.get_running_loop().create_future()
        self._run_futures[run_id] = future
        self._run_requests[run_id] = request
        self._statuses[run_id] = "queued"
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
            session_id = self._peek_session_id(request)
            self._store_terminal_result(
                self._build_result(
                    run_id=run_id,
                    group_folder=request.group_folder,
                    backend=backend,
                    session_id=session_id,
                    status="cancelled",
                )
            )
            return True
        if status == "running":
            request = self._run_requests[run_id]
            backend_name = self._safe_select_backend_name(request)
            session_id = self._run_session_ids.get(run_id, self._peek_session_id(request))
            backend = self._running_backends.get(run_id)
            if backend is not None:
                self._cancelled_run_ids.add(run_id)
                self._statuses[run_id] = "cancelled"
                await backend.cancel(run_id)
                execution_task = self._running_tasks.get(run_id)
                if execution_task is not None and not execution_task.done():
                    execution_task.cancel()
                self._store_terminal_result(
                    self._build_result(
                        run_id=run_id,
                        group_folder=request.group_folder,
                        backend=backend_name,
                        session_id=session_id,
                        status="cancelled",
                    )
                )
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
                        session_id=self._peek_session_id(request),
                        status="failed",
                        error=str(exc),
                    )
                )
        self._group_workers.pop(group_folder, None)

    async def _execute_request(self, run_id: str, request: ExecutionRequest) -> None:
        try:
            backend_name = self._select_backend_name(request)
        except Exception as exc:
            session_id = self._peek_session_id(request)
            self._store_terminal_result(
                self._build_result(
                    run_id=run_id,
                    group_folder=request.group_folder,
                    backend="unknown",
                    session_id=session_id,
                    status="failed",
                    error=str(exc),
                )
            )
            return

        backend = self._backends.get(backend_name)
        session_id = self._resolve_session_id(request)
        self._run_session_ids[run_id] = session_id
        if backend is None:
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

        self._statuses[run_id] = "running"
        self._running_backends[run_id] = backend
        execution_task = asyncio.create_task(
            self._run_backend_with_timeout(
                backend,
                request,
                run_id=run_id,
                backend_name=backend_name,
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
            await backend.cancel(run_id)
            return self._build_result(
                run_id=run_id,
                group_folder=request.group_folder,
                backend=backend_name,
                session_id=session_id,
                status="timeout",
                timeout_ms=request.timeout_ms,
            )
        except Exception as exc:
            return self._build_result(
                run_id=run_id,
                group_folder=request.group_folder,
                backend=backend_name,
                session_id=session_id,
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
            status=raw_result.get("status", "completed"),
            final_output=raw_result.get("final_output"),
            error=raw_result.get("error"),
            timeout_ms=raw_result.get("timeout_ms"),
        )

    def _resolve_session_id(self, request: ExecutionRequest) -> str:
        if request.fresh_session or request.group_folder not in self._session_ids:
            self._session_ids[request.group_folder] = self._new_session_id(request.group_folder)
        return self._session_ids[request.group_folder]

    def _peek_session_id(self, request: ExecutionRequest) -> str:
        if request.fresh_session:
            return self._new_session_id(request.group_folder)
        return self._session_ids.get(request.group_folder, self._new_session_id(request.group_folder))

    def _new_session_id(self, group_folder: str) -> str:
        if group_folder not in self._session_ids:
            return group_folder
        return f"{group_folder}:{uuid4().hex[:8]}"

    def _select_backend_name(self, request: ExecutionRequest) -> str:
        return self._execution_policy.select_backend(request)

    def _safe_select_backend_name(self, request: ExecutionRequest) -> str:
        try:
            return self._select_backend_name(request)
        except Exception:
            return "unknown"

    def _store_terminal_result(self, result: ExecutionResult) -> None:
        self._statuses[result.run_id] = result.status
        self._completed_results[result.run_id] = result
        self._completed_order.append(result.run_id)
        while len(self._completed_order) > self._max_completed_runs:
            stale_run_id = self._completed_order.popleft()
            self._completed_results.pop(stale_run_id, None)
            self._statuses.pop(stale_run_id, None)

        future = self._run_futures.pop(result.run_id, None)
        if future is not None and not future.done():
            future.set_result(result)
        self._run_requests.pop(result.run_id, None)

    def _build_result(
        self,
        *,
        run_id: str,
        group_folder: str,
        backend: str,
        session_id: str,
        status: ExecutionStatus,
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
    "ExecutionSource",
    "ExecutionStatus",
]
