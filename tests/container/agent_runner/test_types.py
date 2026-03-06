from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNNER_ROOT = PROJECT_ROOT / "container" / "agent-runner"
if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))


def test_container_input_uses_m32_defaults() -> None:
    from src.types import ContainerInput

    payload = ContainerInput(prompt="hello", group_folder="group-1")

    assert payload.prompt == "hello"
    assert payload.group_folder == "group-1"
    assert payload.session_id is None
    assert payload.agent_name == "PortexAgent"
    assert payload.instructions == "你是一个专业的 AI 助手"


def test_container_input_requires_prompt() -> None:
    from src.types import ContainerInput

    with pytest.raises(Exception):
        ContainerInput(group_folder="group-1")


def test_container_output_serializes_success_payload() -> None:
    from src.types import ContainerOutput

    output = ContainerOutput(status="success", result="done")

    assert output.model_dump() == {
        "status": "success",
        "result": "done",
        "error": None,
    }
