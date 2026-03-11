from __future__ import annotations

from pathlib import Path
import io
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_build_docker_command_uses_release_image_defaults() -> None:
    from scripts import build_docker

    command = build_docker.build_docker_command()

    assert command == ["docker", "build", "-t", "portex:v1.0.0", "."]


def test_build_docker_command_supports_custom_file_and_context() -> None:
    from scripts import build_docker

    command = build_docker.build_docker_command(
        tag="portex/agent-runner:dev",
        dockerfile="container/agent-runner/Dockerfile",
        context="container/agent-runner",
    )

    assert command == [
        "docker",
        "build",
        "-t",
        "portex/agent-runner:dev",
        "-f",
        "container/agent-runner/Dockerfile",
        "container/agent-runner",
    ]


def test_main_returns_subprocess_exit_code(monkeypatch) -> None:
    from scripts import build_docker

    captured: dict[str, object] = {}

    class CompletedProcess:
        returncode = 7

    def fake_run(command, *, cwd, check):
        captured["command"] = command
        captured["cwd"] = cwd
        captured["check"] = check
        return CompletedProcess()

    monkeypatch.setattr(build_docker.subprocess, "run", fake_run)

    exit_code = build_docker.main(
        [
            "--tag",
            "portex/agent-runner:dev",
            "--file",
            "container/agent-runner/Dockerfile",
            "--context",
            "container/agent-runner",
        ]
    )

    assert exit_code == 7
    assert captured["command"] == [
        "docker",
        "build",
        "-t",
        "portex/agent-runner:dev",
        "-f",
        "container/agent-runner/Dockerfile",
        "container/agent-runner",
    ]
    assert captured["cwd"] == build_docker.PROJECT_ROOT
    assert captured["check"] is False


def test_main_returns_127_when_docker_command_is_missing(monkeypatch) -> None:
    from scripts import build_docker

    def fake_run(command, *, cwd, check):
        _ = (command, cwd, check)
        raise FileNotFoundError("docker command not found")

    monkeypatch.setattr(build_docker.subprocess, "run", fake_run)
    stderr = io.StringIO()

    exit_code = build_docker.main(["--tag", "portex:v1.0.0"], stderr=stderr)

    assert exit_code == 127
    assert "docker command not found" in stderr.getvalue()


def test_main_returns_127_when_docker_command_is_missing(
    monkeypatch,
    capsys,
) -> None:
    from scripts import build_docker

    def fake_run(command, *, cwd, check):
        _ = (command, cwd, check)
        raise FileNotFoundError("docker")

    monkeypatch.setattr(build_docker.subprocess, "run", fake_run)

    exit_code = build_docker.main([])

    captured = capsys.readouterr()
    assert exit_code == 127
    assert captured.err.strip() == "docker command not found"
