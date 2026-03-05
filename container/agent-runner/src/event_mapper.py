"""Event mapper placeholders for the agent runner."""

from __future__ import annotations

from typing import Any


def map_event(raw_event: dict[str, Any]) -> dict[str, Any]:
    """Map a raw event into a minimal normalized structure."""
    return {
        "event_type": str(raw_event.get("type", "unknown")),
        "payload": dict(raw_event.get("payload", {})),
    }
