"""Tool registry for the agent runner."""

from __future__ import annotations

from typing import Any

from agents import RunContextWrapper, function_tool

from .message import send_message_tool
from .task import create_task_tool


@function_tool
def send_message(ctx: RunContextWrapper[Any], text: str) -> str:
    """Send a placeholder message."""
    _ = ctx
    return send_message_tool(text)


@function_tool
def create_task(ctx: RunContextWrapper[Any], title: str) -> dict[str, str]:
    """Create a placeholder task."""
    _ = ctx
    return create_task_tool(title)


def build_default_tools() -> list[Any]:
    """Return the default tool set bundled in the runner image."""
    return [send_message, create_task]


__all__ = ["build_default_tools", "create_task", "send_message"]
