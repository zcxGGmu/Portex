"""Execution mode selection helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

ExecutionMode = Literal["host", "container"]


def get_execution_mode(
    user_role: str,
    group_config: Mapping[str, object],
) -> ExecutionMode:
    """Select host mode only for admin-owned groups that opt in."""
    if user_role == "admin" and bool(group_config.get("host_mode")):
        return "host"
    return "container"


__all__ = ["ExecutionMode", "get_execution_mode"]
