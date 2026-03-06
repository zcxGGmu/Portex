from __future__ import annotations

from pathlib import Path
import tomllib

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNNER_ROOT = PROJECT_ROOT / "container" / "agent-runner"


def test_agent_runner_dockerfile_contains_required_runtime_scaffold() -> None:
    dockerfile = (RUNNER_ROOT / "Dockerfile").read_text(encoding="utf-8")

    required_snippets = [
        "FROM python:3.11-slim",
        "apt-get update",
        "git",
        "curl",
        "wget",
        "ffmpeg",
        "imagemagick",
        "postgresql-client",
        "default-mysql-client",
        "WORKDIR /app",
        "COPY pyproject.toml /app/pyproject.toml",
        "COPY src /app/src",
        "pip install --no-cache-dir .",
        "useradd -m -u 1000 portex",
        "USER portex",
        'ENTRYPOINT ["python", "-m", "src.runner"]',
    ]

    for snippet in required_snippets:
        assert snippet in dockerfile


def test_agent_runner_pyproject_declares_sdk_dependencies() -> None:
    with (RUNNER_ROOT / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)

    dependencies = project["project"]["dependencies"]

    assert "openai-agents" in dependencies
    assert any(dependency.startswith("pydantic") for dependency in dependencies)
