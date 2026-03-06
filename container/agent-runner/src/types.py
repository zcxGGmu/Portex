"""Shared container protocol types for the agent runner."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

DEFAULT_AGENT_NAME = "PortexAgent"
DEFAULT_AGENT_INSTRUCTIONS = "你是一个专业的 AI 助手"


class ContainerInput(BaseModel):
    """Validated JSON payload accepted by the runner stdin."""

    model_config = ConfigDict(extra="forbid")

    prompt: str
    group_folder: str
    session_id: str | None = None
    agent_name: str = DEFAULT_AGENT_NAME
    instructions: str = DEFAULT_AGENT_INSTRUCTIONS


class ContainerOutput(BaseModel):
    """JSON envelope written by the runner stdout."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "error", "timeout"]
    result: str | None = None
    error: str | None = None


__all__ = [
    "ContainerInput",
    "ContainerOutput",
    "DEFAULT_AGENT_INSTRUCTIONS",
    "DEFAULT_AGENT_NAME",
]
