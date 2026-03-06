"""Portex event contract definitions."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    RUN_STARTED = "run.started"
    TOKEN_DELTA = "run.token.delta"
    TOOL_STARTED = "run.tool.started"
    TOOL_COMPLETED = "run.tool.completed"
    RUN_TIMEOUT = "run.timeout"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"


class PortexEvent(BaseModel):
    event_type: EventType
    run_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    seq: int
    timestamp: datetime
