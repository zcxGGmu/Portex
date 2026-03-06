from __future__ import annotations

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

    async def communicate(self, input: bytes | None = None) -> tuple[bytes, bytes]:
        self.communicate_calls.append(input)
        return self._stdout, self._stderr


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
