from __future__ import annotations

from pathlib import Path
import tomllib
import xml.etree.ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNNER_ROOT = PROJECT_ROOT / "container" / "agent-runner"
LOGO_PATH = PROJECT_ROOT / "assets" / "portex-crab-logo.svg"


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


def test_root_release_dockerfile_contains_required_runtime_scaffold() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    required_snippets = [
        "FROM python:3.11-slim",
        "WORKDIR /app",
        "COPY pyproject.toml README.md /app/",
        "COPY app /app/app",
        "COPY services /app/services",
        "pip install --no-cache-dir .",
        "useradd -m -u 1000 portex",
        "USER portex",
        "EXPOSE 8000",
        'CMD ["python", "-m", "uvicorn", "app.main:app"',
    ]

    for snippet in required_snippets:
        assert snippet in dockerfile


def test_root_dockerignore_excludes_local_artifacts() -> None:
    dockerignore = (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8")

    required_entries = [
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "data",
        "web/node_modules",
        "web/dist",
    ]

    for entry in required_entries:
        assert entry in dockerignore


def test_readmes_reference_shared_portex_logo_asset() -> None:
    for relative_path in ("README.md", "README.zh-CN.md"):
        content = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")

        assert 'src="assets/portex-crab-logo.svg"' in content
        assert 'alt="Portex project logo"' in content


def test_portex_logo_asset_exists_and_is_valid_svg() -> None:
    assert LOGO_PATH.exists()

    root = ET.fromstring(LOGO_PATH.read_text(encoding="utf-8"))

    assert root.tag.endswith("svg")
    assert root.attrib["viewBox"] == "0 0 512 512"
