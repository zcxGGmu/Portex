from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.mark.parametrize(
    ("user_role", "group_config", "expected"),
    [
        ("admin", {"host_mode": True}, "host"),
        ("admin", {"host_mode": False}, "container"),
        ("member", {"host_mode": True}, "container"),
        ("guest", {}, "container"),
    ],
)
def test_get_execution_mode_selects_host_only_for_admin_host_groups(
    user_role: str,
    group_config: dict[str, object],
    expected: str,
) -> None:
    from services.execution_mode import get_execution_mode

    assert get_execution_mode(user_role, group_config) == expected
