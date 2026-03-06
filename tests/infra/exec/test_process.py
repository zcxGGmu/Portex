from __future__ import annotations

import asyncio
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNNER_ROOT = PROJECT_ROOT / "container" / "agent-runner"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))


class FakeProcess:
    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: bytes = b"",
        stderr: bytes = b"",
    ) -> None:
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr
        self.communicate_calls: list[bytes | None] = []
        self.kill_calls = 0

    async def communicate(self, input: bytes | None = None) -> tuple[bytes, bytes]:
        self.communicate_calls.append(input)
        return self._stdout, self._stderr

    def kill(self) -> None:
        self.kill_calls += 1


@pytest.mark.asyncio
async def test_process_executor_run_agent_returns_collected_process_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from infra.exec.process import ProcessExecutor, ProcessRunResult
    from src.types import ContainerInput

    fake_process = FakeProcess(
        returncode=0,
        stdout='{"status":"success","result":"ok"}\n'.encode("utf-8"),
        stderr="".encode("utf-8"),
    )
    captured: dict[str, object] = {}

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> FakeProcess:
        captured["command"] = list(command)
        captured["kwargs"] = dict(kwargs)
        return fake_process

    monkeypatch.setattr(
        "infra.exec.process.asyncio.create_subprocess_exec",
        fake_create_subprocess_exec,
    )

    data_root = tmp_path / "data"
    runner_root = tmp_path / "runner-root"
    runner_root.mkdir(parents=True)
    executor = ProcessExecutor(
        data_root=data_root,
        runner_root=runner_root,
        python_executable="/venv/bin/python",
    )
    payload = ContainerInput(prompt="你好", group_folder="group-a", session_id="session-1")

    result = await executor.run_agent("group-a", payload)

    assert result == ProcessRunResult(
        returncode=0,
        stdout='{"status":"success","result":"ok"}\n',
        stderr="",
    )
    assert fake_process.communicate_calls == [payload.model_dump_json().encode("utf-8")]
    assert captured["command"] == ["/venv/bin/python", "-m", "src.runner"]
    assert captured["kwargs"]["cwd"] == str(runner_root.resolve())
    assert captured["kwargs"]["stdin"] is not None
    assert captured["kwargs"]["stdout"] is not None
    assert captured["kwargs"]["stderr"] is not None

    env = captured["kwargs"]["env"]
    assert env["PORTEX_RUN_MODE"] == "host"
    assert env["PORTEX_GROUP_FOLDER"] == "group-a"
    assert env["PORTEX_GROUP_DIR"] == str((data_root / "groups" / "group-a").resolve())
    assert (data_root / "groups" / "group-a").exists()


@pytest.mark.asyncio
async def test_process_executor_run_agent_preserves_non_zero_return_codes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from infra.exec.process import ProcessExecutor
    from src.types import ContainerInput

    fake_process = FakeProcess(returncode=23, stdout=b"", stderr=b"runner failed")

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> FakeProcess:
        _ = (command, kwargs)
        return fake_process

    monkeypatch.setattr(
        "infra.exec.process.asyncio.create_subprocess_exec",
        fake_create_subprocess_exec,
    )

    executor = ProcessExecutor(data_root=tmp_path / "data", runner_root=tmp_path / "runner-root")
    payload = ContainerInput(prompt="hello", group_folder="group-a")

    result = await executor.run_agent("group-a", payload)

    assert result.returncode == 23
    assert result.stdout == ""
    assert result.stderr == "runner failed"


@pytest.mark.asyncio
async def test_process_executor_run_agent_wraps_subprocess_start_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from infra.exec.process import ProcessExecutionError, ProcessExecutor
    from src.types import ContainerInput

    async def failing_create_subprocess_exec(*command: str, **kwargs: object) -> FakeProcess:
        _ = (command, kwargs)
        raise OSError("spawn failed")

    monkeypatch.setattr(
        "infra.exec.process.asyncio.create_subprocess_exec",
        failing_create_subprocess_exec,
    )

    executor = ProcessExecutor(data_root=tmp_path / "data", runner_root=tmp_path / "runner-root")
    payload = ContainerInput(prompt="hello", group_folder="group-a")

    with pytest.raises(ProcessExecutionError, match="group-a") as exc_info:
        await executor.run_agent("group-a", payload)

    assert isinstance(exc_info.value.__cause__, OSError)


@pytest.mark.asyncio
async def test_process_executor_run_agent_rejects_group_dir_outside_allowed_directories(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from infra.exec.process import HostModeRestrictions, ProcessExecutionError, ProcessExecutor
    from src.types import ContainerInput

    create_calls = 0

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> FakeProcess:
        nonlocal create_calls
        create_calls += 1
        _ = (command, kwargs)
        return FakeProcess()

    monkeypatch.setattr(
        "infra.exec.process.asyncio.create_subprocess_exec",
        fake_create_subprocess_exec,
    )

    executor = ProcessExecutor(
        data_root=tmp_path / "data",
        runner_root=tmp_path / "runner-root",
        restrictions=HostModeRestrictions(
            allowed_directories=(tmp_path / "allowed",),
            forbidden_commands=(),
            max_execution_time=60,
        ),
    )
    payload = ContainerInput(prompt="hello", group_folder="group-a")

    with pytest.raises(ProcessExecutionError, match="outside allowed host directories"):
        await executor.run_agent("group-a", payload)

    assert create_calls == 0


def test_is_command_forbidden_matches_blacklisted_prefixes() -> None:
    from infra.exec.process import is_command_forbidden

    forbidden_commands = (
        ("rm", "-rf", "/"),
        ("dd", "if="),
    )

    assert is_command_forbidden(["rm", "-rf", "/"], forbidden_commands) is True
    assert is_command_forbidden(
        ["dd", "if=/dev/zero", "of=/tmp/out"],
        forbidden_commands,
    ) is True
    assert is_command_forbidden(["python", "-m", "src.runner"], forbidden_commands) is False


@pytest.mark.asyncio
async def test_process_executor_run_agent_enforces_max_execution_time(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from infra.exec.process import HostModeRestrictions, ProcessExecutionError, ProcessExecutor
    from src.types import ContainerInput

    fake_process = FakeProcess()
    captured_timeout: dict[str, float] = {}

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> FakeProcess:
        _ = (command, kwargs)
        return fake_process

    async def fake_wait_for(awaitable, timeout: float):
        captured_timeout["value"] = timeout
        awaitable.close()
        raise asyncio.TimeoutError

    monkeypatch.setattr(
        "infra.exec.process.asyncio.create_subprocess_exec",
        fake_create_subprocess_exec,
    )
    monkeypatch.setattr("infra.exec.process.asyncio.wait_for", fake_wait_for)

    executor = ProcessExecutor(
        data_root=tmp_path / "data",
        runner_root=tmp_path / "runner-root",
        restrictions=HostModeRestrictions(
            allowed_directories=(tmp_path / "data" / "groups",),
            forbidden_commands=(("rm", "-rf", "/"),),
            max_execution_time=5,
        ),
    )
    payload = ContainerInput(prompt="hello", group_folder="group-a")

    with pytest.raises(ProcessExecutionError, match="timed out after 5 seconds"):
        await executor.run_agent("group-a", payload, timeout=60)

    assert captured_timeout == {"value": 5}
    assert fake_process.kill_calls == 1


def test_host_mode_restrictions_define_required_security_boundaries() -> None:
    from infra.exec.process import HOST_MODE_RESTRICTIONS

    assert set(HOST_MODE_RESTRICTIONS) == {
        "allowed_directories",
        "forbidden_commands",
        "max_execution_time",
    }
    assert HOST_MODE_RESTRICTIONS["allowed_directories"]
    assert HOST_MODE_RESTRICTIONS["forbidden_commands"]
    assert HOST_MODE_RESTRICTIONS["max_execution_time"] == 3600


@pytest.mark.asyncio
async def test_process_executor_rejects_forbidden_command_fragments(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from infra.exec.process import HostModeRestrictions, ProcessExecutionError, ProcessExecutor
    from src.types import ContainerInput

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> FakeProcess:
        _ = (command, kwargs)
        return FakeProcess()

    monkeypatch.setattr(
        "infra.exec.process.asyncio.create_subprocess_exec",
        fake_create_subprocess_exec,
    )

    class UnsafeProcessExecutor(ProcessExecutor):
        def build_command(self) -> list[str]:
            return ["rm", "-rf", "/"]

    executor = UnsafeProcessExecutor(
        data_root=tmp_path / "data",
        runner_root=tmp_path / "runner-root",
        restrictions=HostModeRestrictions(
            allowed_directories=(tmp_path / "data" / "groups",),
            forbidden_commands=(("rm", "-rf", "/"),),
            max_execution_time=60,
        ),
    )
    payload = ContainerInput(prompt="hello", group_folder="group-a")

    with pytest.raises(ProcessExecutionError, match="forbidden host-mode command"):
        await executor.run_agent("group-a", payload)
