from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
import threading
from typing import Iterator

from fastapi.testclient import TestClient
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def api_client() -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as client:
        yield client


def test_websocket_endpoint_starts_background_execution_for_text_message(
    api_client: TestClient,
) -> None:
    from app.routes import websocket as websocket_routes

    recorded_requests: list[object] = []

    class FakeCoordinator:
        async def submit_execution(self, request):
            from infra.runtime.adapter import RunEvent
            from services.execution_coordinator import ExecutionHandle

            recorded_requests.append(request)
            await request.request_metadata["event_handler"](
                RunEvent(event_type="run.started", run_id="run-fixed")
            )
            return ExecutionHandle(
                run_id="run-fixed",
                group_folder=request.group_folder,
                status="queued",
            )

        async def wait_for_run(self, run_id: str):
            from services.execution_coordinator import ExecutionResult

            return ExecutionResult(
                run_id=run_id,
                status="completed",
                group_folder="group-1",
                backend="openai_runtime",
                session_id="group-1",
                final_output="done",
            )

        async def cancel(self, run_id: str) -> bool:
            _ = run_id
            return True

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        websocket_routes,
        "get_execution_coordinator",
        lambda: FakeCoordinator(),
        raising=False,
    )
    monkeypatch.setattr(
        websocket_routes,
        "trigger_agent_execution",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("direct trigger should not be used")),
        raising=False,
    )

    try:
        with api_client.websocket_connect("/ws/group-1") as websocket:
            websocket.send_text("ping")

            payload = json.loads(websocket.receive_text())
            assert payload["event_type"] == "run.started"
            assert len(recorded_requests) == 1
            assert recorded_requests[0].group_folder == "group-1"
            assert recorded_requests[0].prompt == "ping"
    finally:
        monkeypatch.undo()


def test_websocket_endpoint_cancels_active_run_from_same_socket(
    api_client: TestClient,
) -> None:
    from app.routes import websocket as websocket_routes

    cancel_event = threading.Event()

    class FakeCoordinator:
        def __init__(self) -> None:
            self.cancelled_run_ids: list[str] = []

        async def submit_execution(self, request):
            from infra.runtime.adapter import RunEvent
            from services.execution_coordinator import ExecutionHandle

            await request.request_metadata["event_handler"](
                RunEvent(event_type="run.started", run_id="run-cancel")
            )
            return ExecutionHandle(
                run_id="run-cancel",
                group_folder=request.group_folder,
                status="queued",
            )

        async def wait_for_run(self, run_id: str):
            await asyncio.to_thread(cancel_event.wait)
            from services.execution_coordinator import ExecutionResult

            return ExecutionResult(
                run_id=run_id,
                status="cancelled",
                group_folder="group-1",
                backend="openai_runtime",
                session_id="group-1",
            )

        async def cancel(self, run_id: str) -> bool:
            self.cancelled_run_ids.append(run_id)
            cancel_event.set()
            return True

    coordinator = FakeCoordinator()

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        websocket_routes,
        "get_execution_coordinator",
        lambda: coordinator,
        raising=False,
    )
    monkeypatch.setattr(
        websocket_routes,
        "trigger_agent_execution",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("direct trigger should not be used")),
        raising=False,
    )

    try:
        with api_client.websocket_connect("/ws/group-1") as websocket:
            websocket.send_text("ping")
            websocket.send_text(json.dumps({"type": "cancel", "run_id": "run-cancel"}))

            assert cancel_event.wait(1)
            assert coordinator.cancelled_run_ids == ["run-cancel"]

            started_payload = json.loads(websocket.receive_text())
            failed_payload = json.loads(websocket.receive_text())
            assert started_payload["event_type"] == "run.started"
            assert failed_payload["event_type"] == "run.failed"
            assert failed_payload["payload"] == {"status": "cancelled"}
    finally:
        monkeypatch.undo()
