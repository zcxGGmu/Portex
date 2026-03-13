from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _request(*, group_folder: str = "group-a", prompt: str = "hello"):
    from services.execution_coordinator import ExecutionRequest

    return ExecutionRequest(
        group_folder=group_folder,
        chat_jid="chat-a",
        user_id="user-a",
        prompt=prompt,
        source="web",
    )


@pytest.mark.asyncio
async def test_openai_runtime_backend_maps_run_result_and_forwards_event_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from infra.runtime.adapter import RunEvent, RunResult

    event_types: list[str] = []
    trigger_calls: list[dict[str, object]] = []

    async def fake_run_agent_execution(**kwargs):
        trigger_calls.append(kwargs)
        event_handler = kwargs["event_handler"]
        assert event_handler is not None
        await event_handler(RunEvent(event_type="run.started", run_id=kwargs["request_id"]))
        return RunResult(
            run_id=kwargs["request_id"],
            status="completed",
            final_output="runtime reply",
        )

    monkeypatch.setattr(
        "services.execution_backends.run_agent_execution",
        fake_run_agent_execution,
    )

    from services.execution_backends import OpenAIRuntimeBackend

    backend = OpenAIRuntimeBackend(runtime_factory=lambda _group: object())
    request = _request()
    request.request_metadata = {
        "event_handler": lambda event: event_types.append(event.event_type),
    }

    result = await backend.execute(
        request,
        run_id="run-openai",
        session_id="session-a",
    )

    assert result["status"] == "completed"
    assert result["final_output"] == "runtime reply"
    assert trigger_calls[0]["group_folder"] == "group-a"
    assert trigger_calls[0]["message"] == "hello"
    assert trigger_calls[0]["user_id"] == "user-a"
    assert trigger_calls[0]["request_id"] == "run-openai"
    assert trigger_calls[0]["timeout_ms"] is None
    assert event_types == ["run.started"]


@pytest.mark.asyncio
async def test_openai_runtime_backend_translates_session_resume_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from infra.runtime.openai import OpenAIRuntimeSessionError
    from services.execution_backends import OpenAIRuntimeBackend, SessionResumeFailedError

    async def fake_run_agent_execution(**kwargs):
        _ = kwargs
        raise OpenAIRuntimeSessionError("resume failed")

    monkeypatch.setattr(
        "services.execution_backends.run_agent_execution",
        fake_run_agent_execution,
    )

    backend = OpenAIRuntimeBackend(runtime_factory=lambda _group: object())

    with pytest.raises(SessionResumeFailedError, match="resume failed"):
        await backend.execute(
            _request(),
            run_id="run-openai",
            session_id="session-a",
        )


@pytest.mark.asyncio
async def test_host_process_backend_parses_runner_output() -> None:
    from infra.exec.process import ProcessRunResult
    from services.execution_backends import HostProcessBackend

    class FakeProcessExecutor:
        async def run_agent(self, group_folder, payload, *, timeout=None, run_id=None):
            assert group_folder == "group-a"
            assert payload.prompt == "hello"
            assert payload.session_id == "session-a"
            assert timeout is None
            assert run_id == "run-host"
            return ProcessRunResult(
                returncode=0,
                stdout='{"status":"success","result":"host reply"}\n',
                stderr="",
            )

        async def cancel(self, run_id: str) -> bool:
            _ = run_id
            return True

    backend = HostProcessBackend(process_executor=FakeProcessExecutor())

    result = await backend.execute(
        _request(),
        run_id="run-host",
        session_id="session-a",
    )

    assert result["status"] == "completed"
    assert result["final_output"] == "host reply"


@pytest.mark.asyncio
async def test_container_backend_runs_docker_with_framed_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeProcess:
        def __init__(self) -> None:
            self.returncode = 0

        async def communicate(self, payload: bytes) -> tuple[bytes, bytes]:
            captured["stdin"] = payload.decode("utf-8")
            return (
                (
                    "---PORTEX_OUTPUT_START---\n"
                    '{"status":"success","result":"container reply"}\n'
                    "---PORTEX_OUTPUT_END---\n"
                ).encode("utf-8"),
                b"",
            )

        def kill(self) -> None:
            return None

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> FakeProcess:
        captured["command"] = list(command)
        captured["kwargs"] = dict(kwargs)
        return FakeProcess()

    monkeypatch.setattr(
        "services.execution_backends.asyncio.create_subprocess_exec",
        fake_create_subprocess_exec,
    )

    from services.execution_backends import ContainerBackend

    class FakeContainerManager:
        container_image = "portex/agent-runner:test"

        def build_container_name(self, group_folder: str, payload) -> str:
            assert group_folder == "group-a"
            assert payload.session_id == "session-a"
            return "portex-agent-group-a-session-a"

        def build_environment(self, group_folder: str, payload) -> dict[str, str]:
            assert group_folder == "group-a"
            return {
                "PORTEX_GROUP_FOLDER": group_folder,
                "PORTEX_SESSION_ID": payload.session_id or "",
            }

        def build_runner_volumes(self, group_folder: str, user_id: str) -> dict[str, dict[str, str]]:
            assert group_folder == "group-a"
            assert user_id == "user-a"
            return {
                "/tmp/group-a": {"bind": "/workspace/group", "mode": "rw"},
                "/tmp/memory-a": {"bind": "/workspace/memory", "mode": "ro"},
            }

        async def stop_container(self, container_id: str, *, timeout: int = 30) -> None:
            _ = (container_id, timeout)

    backend = ContainerBackend(container_manager=FakeContainerManager())

    result = await backend.execute(
        _request(),
        run_id="run-container",
        session_id="session-a",
    )

    assert result["status"] == "completed"
    assert result["final_output"] == "container reply"
    assert "group-a" in str(captured["stdin"])
    command = captured["command"]
    assert command[:5] == ["docker", "run", "-i", "--rm", "--name"]
    assert "portex-agent-group-a-session-a" in command
    assert "portex/agent-runner:test" in command
