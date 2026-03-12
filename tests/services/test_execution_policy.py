from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _request(*, requested_mode: str | None = None, source: str = "web"):
    from services.execution_coordinator import ExecutionRequest

    return ExecutionRequest(
        group_folder="group-a",
        chat_jid="group-a",
        user_id="user-a",
        prompt="hello",
        source=source,  # type: ignore[arg-type]
        requested_mode=requested_mode,
    )


def test_policy_defaults_to_openai_runtime() -> None:
    from services.execution_policy import ExecutionPolicy

    policy = ExecutionPolicy()

    backend = policy.select_backend(_request())

    assert backend == "openai_runtime"


@pytest.mark.parametrize(
    ("requested_mode", "expected_backend"),
    [
        ("openai", "openai_runtime"),
        ("host", "host_process"),
        ("container", "docker_container"),
    ],
)
def test_policy_honors_explicit_requested_mode(
    requested_mode: str,
    expected_backend: str,
) -> None:
    from services.execution_policy import ExecutionPolicy

    policy = ExecutionPolicy()

    backend = policy.select_backend(_request(requested_mode=requested_mode))

    assert backend == expected_backend


def test_policy_rejects_unknown_mode() -> None:
    from services.execution_policy import ExecutionPolicy

    policy = ExecutionPolicy()

    with pytest.raises(ValueError, match="unsupported execution mode"):
        policy.select_backend(_request(requested_mode="unknown"))
