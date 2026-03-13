from __future__ import annotations

import asyncio
from collections import deque
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _request(
    *,
    group_folder: str,
    prompt: str,
    requested_mode: str | None = None,
    timeout_ms: int | None = None,
    fresh_session: bool = False,
):
    from services.execution_coordinator import ExecutionRequest

    return ExecutionRequest(
        group_folder=group_folder,
        chat_jid=group_folder,
        user_id="user-a",
        prompt=prompt,
        source="web",
        requested_mode=requested_mode,
        timeout_ms=timeout_ms,
        fresh_session=fresh_session,
    )


class _RecordingBackend:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self._gate = asyncio.Event()

    async def execute(self, request, *, run_id: str, session_id: str):
        self.calls.append(
            {
                "run_id": run_id,
                "group_folder": request.group_folder,
                "prompt": request.prompt,
                "session_id": session_id,
            }
        )
        await self._gate.wait()
        return {
            "status": "completed",
            "final_output": f"reply:{request.prompt}",
        }

    async def cancel(self, run_id: str) -> None:
        _ = run_id

    def release(self) -> None:
        self._gate.set()


class _TimeoutBackend:
    def __init__(self) -> None:
        self.cancelled_run_ids: list[str] = []

    async def execute(self, request, *, run_id: str, session_id: str):
        _ = (request, run_id, session_id)
        await asyncio.sleep(0.05)
        return {"status": "completed", "final_output": "late"}

    async def cancel(self, run_id: str) -> None:
        self.cancelled_run_ids.append(run_id)


class _CancellableBackend:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self._cancelled = asyncio.Event()
        self.cancelled_run_ids: list[str] = []

    async def execute(self, request, *, run_id: str, session_id: str):
        self.calls.append(
            {
                "run_id": run_id,
                "group_folder": request.group_folder,
                "prompt": request.prompt,
                "session_id": session_id,
            }
        )
        await self._cancelled.wait()
        return {"status": "completed", "final_output": "should-be-ignored"}

    async def cancel(self, run_id: str) -> None:
        self.cancelled_run_ids.append(run_id)
        self._cancelled.set()


class _NonCooperativeBackend:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.cancelled_run_ids: list[str] = []
        self.started = asyncio.Event()

    async def execute(self, request, *, run_id: str, session_id: str):
        _ = session_id
        self.calls.append(request.prompt)
        if request.prompt == "first":
            self.started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                raise
        return {"status": "completed", "final_output": f"reply:{request.prompt}"}

    async def cancel(self, run_id: str) -> None:
        self.cancelled_run_ids.append(run_id)


class _BlockingCancelBackend:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.calls: list[str] = []
        self.cancelled_run_ids: list[str] = []

    async def execute(self, request, *, run_id: str, session_id: str):
        _ = (run_id, session_id)
        self.calls.append(request.prompt)
        self.started.set()
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            raise

    async def cancel(self, run_id: str) -> None:
        self.cancelled_run_ids.append(run_id)
        await asyncio.Future()


class _TimeoutCleanupBackend:
    def __init__(self) -> None:
        self.cancelled_run_ids: list[str] = []
        self.cancel_gate = asyncio.Event()
        self.calls: list[str] = []

    async def execute(self, request, *, run_id: str, session_id: str):
        _ = (run_id, session_id)
        self.calls.append(request.prompt)
        if request.prompt == "first":
            await asyncio.sleep(0.05)
            return {"status": "completed", "final_output": "too-late"}
        return {"status": "completed", "final_output": f"reply:{request.prompt}"}

    async def cancel(self, run_id: str) -> None:
        self.cancelled_run_ids.append(run_id)
        await self.cancel_gate.wait()


class _SequentialBackend:
    def __init__(self, outcomes: list[dict[str, object] | Exception]) -> None:
        self.calls: list[dict[str, object]] = []
        self._outcomes = deque(outcomes)

    async def execute(self, request, *, run_id: str, session_id: str):
        self.calls.append(
            {
                "run_id": run_id,
                "group_folder": request.group_folder,
                "prompt": request.prompt,
                "session_id": session_id,
            }
        )
        outcome = self._outcomes.popleft()
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def cancel(self, run_id: str) -> None:
        _ = run_id


@pytest.mark.asyncio
async def test_execution_coordinator_processes_one_group_fifo_and_reuses_session() -> None:
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy

    backend = _RecordingBackend()
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
    )

    first = await coordinator.submit_execution(_request(group_folder="group-a", prompt="first"))
    second = await coordinator.submit_execution(_request(group_folder="group-a", prompt="second"))

    assert coordinator.get_status(first.run_id) == "queued"
    assert coordinator.get_status(second.run_id) == "queued"

    await asyncio.sleep(0)
    assert coordinator.get_status(first.run_id) == "running"
    assert coordinator.get_status(second.run_id) == "queued"

    backend.release()
    first_result = await coordinator.wait_for_run(first.run_id)
    second_result = await coordinator.wait_for_run(second.run_id)

    assert first_result.status == "completed"
    assert second_result.status == "completed"
    assert [call["prompt"] for call in backend.calls] == ["first", "second"]
    assert backend.calls[0]["session_id"] == backend.calls[1]["session_id"]


@pytest.mark.asyncio
async def test_execution_coordinator_allows_different_groups_to_progress_independently() -> None:
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy

    backend = _RecordingBackend()
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
    )

    first = await coordinator.submit_execution(_request(group_folder="group-a", prompt="alpha"))
    second = await coordinator.submit_execution(_request(group_folder="group-b", prompt="beta"))

    await asyncio.sleep(0)

    assert coordinator.get_status(first.run_id) == "running"
    assert coordinator.get_status(second.run_id) == "running"

    backend.release()
    await coordinator.wait_for_run(first.run_id)
    await coordinator.wait_for_run(second.run_id)


@pytest.mark.asyncio
async def test_execution_coordinator_cancels_queued_run_without_executing_backend() -> None:
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy

    backend = _RecordingBackend()
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
    )

    first = await coordinator.submit_execution(_request(group_folder="group-a", prompt="first"))
    second = await coordinator.submit_execution(_request(group_folder="group-a", prompt="second"))

    await asyncio.sleep(0)
    cancelled = await coordinator.cancel(second.run_id)
    backend.release()

    first_result = await coordinator.wait_for_run(first.run_id)
    second_result = await coordinator.wait_for_run(second.run_id)

    assert cancelled is True
    assert first_result.status == "completed"
    assert second_result.status == "cancelled"
    assert [call["prompt"] for call in backend.calls] == ["first"]


@pytest.mark.asyncio
async def test_execution_coordinator_marks_timeout_and_calls_backend_cancel() -> None:
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy

    backend = _TimeoutBackend()
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
    )

    handle = await coordinator.submit_execution(
        _request(group_folder="group-a", prompt="slow", timeout_ms=10)
    )
    result = await coordinator.wait_for_run(handle.run_id)
    await asyncio.sleep(0)

    assert result.status == "timeout"
    assert result.timeout_ms == 10
    assert backend.cancelled_run_ids == [handle.run_id]


@pytest.mark.asyncio
async def test_execution_coordinator_marks_running_run_cancelled() -> None:
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy

    backend = _CancellableBackend()
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
    )

    handle = await coordinator.submit_execution(_request(group_folder="group-a", prompt="cancel-me"))
    await asyncio.sleep(0)

    cancelled = await coordinator.cancel(handle.run_id)
    result = await coordinator.wait_for_run(handle.run_id)
    await asyncio.sleep(0)

    assert cancelled is True
    assert result.status == "cancelled"
    assert result.group_folder == "group-a"
    assert result.backend == "openai_runtime"
    assert result.session_id == "group-a"
    assert backend.cancelled_run_ids == [handle.run_id]


@pytest.mark.asyncio
async def test_execution_coordinator_fresh_session_creates_distinct_session_id() -> None:
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy

    backend = _RecordingBackend()
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
    )

    first = await coordinator.submit_execution(_request(group_folder="group-a", prompt="first"))
    second = await coordinator.submit_execution(
        _request(group_folder="group-a", prompt="second", requested_mode=None)
    )
    third = await coordinator.submit_execution(
        _request(group_folder="group-a", prompt="third", requested_mode=None, fresh_session=True)
    )

    backend.release()
    await coordinator.wait_for_run(first.run_id)
    await coordinator.wait_for_run(second.run_id)
    await coordinator.wait_for_run(third.run_id)

    assert backend.calls[0]["session_id"] == backend.calls[1]["session_id"]
    assert backend.calls[2]["session_id"] != backend.calls[1]["session_id"]


@pytest.mark.asyncio
async def test_execution_coordinator_fails_when_policy_selects_missing_backend() -> None:
    from services.execution_coordinator import ExecutionCoordinator

    class MissingBackendPolicy:
        def select_backend(self, request):
            _ = request
            return "missing-backend"

    coordinator = ExecutionCoordinator(
        execution_policy=MissingBackendPolicy(),
        backends={},
    )

    handle = await coordinator.submit_execution(_request(group_folder="group-a", prompt="oops"))
    result = await coordinator.wait_for_run(handle.run_id)

    assert result.status == "failed"
    assert result.error == "unknown execution backend: missing-backend"


@pytest.mark.asyncio
async def test_execution_coordinator_running_cancel_unblocks_next_same_group_request() -> None:
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy

    backend = _NonCooperativeBackend()
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
    )

    first = await coordinator.submit_execution(_request(group_folder="group-a", prompt="first"))
    second = await coordinator.submit_execution(_request(group_folder="group-a", prompt="second"))

    await backend.started.wait()
    cancelled = await coordinator.cancel(first.run_id)
    first_result = await coordinator.wait_for_run(first.run_id)
    second_result = await coordinator.wait_for_run(second.run_id)

    assert cancelled is True
    assert first_result.status == "cancelled"
    assert second_result.status == "completed"
    assert backend.calls == ["first", "second"]


@pytest.mark.asyncio
async def test_execution_coordinator_invalid_requested_mode_returns_failed_result() -> None:
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy

    backend = _RecordingBackend()
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
    )

    handle = await coordinator.submit_execution(
        _request(group_folder="group-a", prompt="bad-mode", requested_mode="unknown")
    )
    result = await coordinator.wait_for_run(handle.run_id)

    assert result.status == "failed"
    assert result.error == "unsupported execution mode: unknown"
    assert backend.calls == []


@pytest.mark.asyncio
async def test_execution_coordinator_running_cancel_does_not_wait_for_blocking_backend_cancel() -> None:
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy

    backend = _BlockingCancelBackend()
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
    )

    handle = await coordinator.submit_execution(_request(group_folder="group-a", prompt="block"))
    await backend.started.wait()

    result = await asyncio.wait_for(coordinator.cancel(handle.run_id), timeout=0.05)
    terminal = await coordinator.wait_for_run(handle.run_id)
    await asyncio.sleep(0)

    assert result is True
    assert terminal.status == "cancelled"
    assert backend.cancelled_run_ids == [handle.run_id]


@pytest.mark.asyncio
async def test_execution_coordinator_timeout_releases_queue_before_backend_cleanup_finishes() -> None:
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy

    backend = _TimeoutCleanupBackend()
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
    )

    first = await coordinator.submit_execution(
        _request(group_folder="group-a", prompt="first", timeout_ms=10)
    )
    second = await coordinator.submit_execution(_request(group_folder="group-a", prompt="second"))

    first_result = await asyncio.wait_for(coordinator.wait_for_run(first.run_id), timeout=0.05)
    second_result = await asyncio.wait_for(coordinator.wait_for_run(second.run_id), timeout=0.05)

    backend.cancel_gate.set()
    await asyncio.sleep(0)

    assert first_result.status == "timeout"
    assert second_result.status == "completed"
    assert backend.calls == ["first", "second"]
    assert backend.cancelled_run_ids == [first.run_id]


@pytest.mark.asyncio
async def test_execution_coordinator_only_commits_fresh_session_after_success() -> None:
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy
    from services.workspace_lifecycle import WorkspaceSessionStore

    session_store = WorkspaceSessionStore(
        new_session_id_factory=lambda workspace_key: f"{workspace_key}:fresh"
    )
    backend = _SequentialBackend(
        [
            {"status": "completed", "final_output": "reply:first"},
            RuntimeError("fresh failed"),
            {"status": "completed", "final_output": "reply:third"},
        ]
    )
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
        workspace_session_store=session_store,
    )

    first = await coordinator.submit_execution(_request(group_folder="group-a", prompt="first"))
    await coordinator.wait_for_run(first.run_id)

    second = await coordinator.submit_execution(
        _request(group_folder="group-a", prompt="second", fresh_session=True)
    )
    second_result = await coordinator.wait_for_run(second.run_id)

    third = await coordinator.submit_execution(_request(group_folder="group-a", prompt="third"))
    await coordinator.wait_for_run(third.run_id)

    assert second_result.status == "failed"
    assert [call["session_id"] for call in backend.calls] == [
        "group-a",
        "group-a:fresh",
        "group-a",
    ]
    assert session_store.get_state("group-a").session_id == "group-a"


@pytest.mark.asyncio
async def test_execution_coordinator_invalidates_stale_session_and_retries_once_fresh() -> None:
    from services.execution_backends import SessionResumeFailedError
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy
    from services.workspace_lifecycle import WorkspaceSessionStore

    session_store = WorkspaceSessionStore(
        new_session_id_factory=lambda workspace_key: f"{workspace_key}:fresh"
    )
    backend = _SequentialBackend(
        [
            {"status": "completed", "final_output": "reply:first"},
            SessionResumeFailedError("resume failed"),
            {"status": "completed", "final_output": "reply:second"},
        ]
    )
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
        workspace_session_store=session_store,
    )

    first = await coordinator.submit_execution(_request(group_folder="group-a", prompt="first"))
    await coordinator.wait_for_run(first.run_id)

    second = await coordinator.submit_execution(_request(group_folder="group-a", prompt="second"))
    second_result = await coordinator.wait_for_run(second.run_id)

    assert second_result.status == "completed"
    assert second_result.final_output == "reply:second"
    assert [call["session_id"] for call in backend.calls] == [
        "group-a",
        "group-a",
        "group-a:fresh",
    ]
    assert session_store.get_state("group-a").session_id == "group-a:fresh"


@pytest.mark.asyncio
async def test_execution_coordinator_exposes_run_snapshot_lifecycle() -> None:
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy

    backend = _RecordingBackend()
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
    )

    handle = await coordinator.submit_execution(_request(group_folder="group-a", prompt="snapshot"))
    queued_snapshot = coordinator.get_run_snapshot(handle.run_id)

    assert queued_snapshot is not None
    assert queued_snapshot.status == "queued"
    assert queued_snapshot.created_at is not None
    assert queued_snapshot.started_at is None
    assert queued_snapshot.finished_at is None

    await asyncio.sleep(0)
    running_snapshot = coordinator.get_run_snapshot(handle.run_id)
    assert running_snapshot is not None
    assert running_snapshot.status == "running"
    assert running_snapshot.started_at is not None
    assert running_snapshot.backend == "openai_runtime"

    backend.release()
    result = await coordinator.wait_for_run(handle.run_id)
    completed_snapshot = coordinator.get_run_snapshot(handle.run_id)

    assert result.status == "completed"
    assert completed_snapshot is not None
    assert completed_snapshot.status == "completed"
    assert completed_snapshot.finished_at is not None
    assert completed_snapshot.final_output == "reply:snapshot"
    assert completed_snapshot.session_id == "group-a"


@pytest.mark.asyncio
async def test_execution_coordinator_snapshot_marks_session_recovery_retry() -> None:
    from services.execution_backends import SessionResumeFailedError
    from services.execution_coordinator import ExecutionCoordinator
    from services.execution_policy import ExecutionPolicy
    from services.workspace_lifecycle import WorkspaceSessionStore

    session_store = WorkspaceSessionStore(
        new_session_id_factory=lambda workspace_key: f"{workspace_key}:fresh"
    )
    backend = _SequentialBackend(
        [
            {"status": "completed", "final_output": "reply:first"},
            SessionResumeFailedError("resume failed"),
            {"status": "completed", "final_output": "reply:second"},
        ]
    )
    coordinator = ExecutionCoordinator(
        execution_policy=ExecutionPolicy(),
        backends={"openai_runtime": backend},
        workspace_session_store=session_store,
    )

    first = await coordinator.submit_execution(_request(group_folder="group-a", prompt="first"))
    await coordinator.wait_for_run(first.run_id)

    second = await coordinator.submit_execution(_request(group_folder="group-a", prompt="second"))
    second_result = await coordinator.wait_for_run(second.run_id)
    second_snapshot = coordinator.get_run_snapshot(second.run_id)

    assert second_result.status == "completed"
    assert second_snapshot is not None
    assert second_snapshot.recovery_attempted is True
    assert second_snapshot.recovery_reason == "resume failed"
    assert second_snapshot.recovery_succeeded is True
