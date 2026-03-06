from __future__ import annotations

from io import StringIO
from pathlib import Path
import sys
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNNER_ROOT = PROJECT_ROOT / "container" / "agent-runner"
if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))


def test_container_protocol_defaults() -> None:
    from src.types import ContainerInput, ContainerOutput

    payload = ContainerInput(prompt="hello", group_folder="group-a")

    assert payload.agent_name == "PortexAgent"
    assert payload.instructions == "你是一个专业的 AI 助手"
    assert payload.session_id is None

    output = ContainerOutput(status="success", result="done")
    assert output.result == "done"
    assert output.error is None


def test_run_agent_builds_agent_and_returns_success_output() -> None:
    from src.runner import run_agent
    from src.types import ContainerInput

    captured: dict[str, object] = {}

    class FakeAgent:
        def __init__(self, *, name: str, instructions: str, tools: list[object]) -> None:
            captured["agent"] = {
                "name": name,
                "instructions": instructions,
                "tools": tools,
            }

    def fake_run_sync(agent: object, input: str) -> object:
        captured["run"] = {"agent": agent, "input": input}
        return SimpleNamespace(final_output="runner-complete")

    payload = ContainerInput(
        prompt="hello from container",
        group_folder="group-a",
        agent_name="RunnerAgent",
        instructions="Be concise",
    )

    output = run_agent(
        payload,
        agent_factory=FakeAgent,
        run_sync=fake_run_sync,
        tools=["tool-a"],
    )

    assert output.status == "success"
    assert output.result == "runner-complete"
    assert output.error is None
    assert captured["agent"] == {
        "name": "RunnerAgent",
        "instructions": "Be concise",
        "tools": ["tool-a"],
    }
    assert captured["run"] == {
        "agent": captured["run"]["agent"],
        "input": "hello from container",
    }


def test_run_agent_wraps_runtime_failures_into_error_output() -> None:
    from src.runner import run_agent
    from src.types import ContainerInput

    class FakeAgent:
        def __init__(self, *, name: str, instructions: str, tools: list[object]) -> None:
            _ = (name, instructions, tools)

    def failing_run_sync(agent: object, input: str) -> object:
        _ = (agent, input)
        raise RuntimeError("provider unavailable")

    payload = ContainerInput(prompt="hello", group_folder="group-a")

    output = run_agent(
        payload,
        agent_factory=FakeAgent,
        run_sync=failing_run_sync,
        tools=[],
    )

    assert output.status == "error"
    assert output.result is None
    assert output.error == "provider unavailable"


def test_main_reads_stdin_and_writes_output_json(monkeypatch) -> None:
    from src import runner
    from src.types import ContainerOutput

    stdin = StringIO('{"prompt":"hello","group_folder":"group-a"}')
    stdout = StringIO()
    captured: dict[str, object] = {}

    def fake_run_agent(payload):
        captured["payload"] = payload
        return ContainerOutput(status="success", result="ok")

    monkeypatch.setattr(runner, "run_agent", fake_run_agent)

    exit_code = runner.main(stdin=stdin, stdout=stdout)

    assert exit_code == 0
    assert captured["payload"].prompt == "hello"
    assert captured["payload"].group_folder == "group-a"

    output = ContainerOutput.model_validate_json(stdout.getvalue())
    assert output.status == "success"
    assert output.result == "ok"
