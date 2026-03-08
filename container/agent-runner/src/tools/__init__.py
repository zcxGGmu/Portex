"""Tool registry for the agent runner."""

from __future__ import annotations

from typing import Any

from agents import RunContextWrapper, function_tool

from .memory import memory_append_tool, memory_search_tool
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


@function_tool
def memory_append(ctx: RunContextWrapper[Any], content: str) -> str:
    """Append content to mounted group memory."""
    _ = ctx
    return memory_append_tool(content)


@function_tool
def memory_search(ctx: RunContextWrapper[Any], query: str) -> list[str]:
    """Search mounted group memory markdown files."""
    _ = ctx
    return memory_search_tool(query)


def build_default_tools() -> list[Any]:
    """Return the default tool set bundled in the runner image."""
    return [send_message, create_task, memory_append, memory_search]


__all__ = [
    "build_default_tools",
    "create_task",
    "memory_append",
    "memory_search",
    "send_message",
]
