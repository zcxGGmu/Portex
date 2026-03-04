"""Map OpenAI Agents SDK stream events into PortexEvent models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from portex.contracts.events import EventType, PortexEvent


def map_sdk_event(
    sdk_event: Any,
    *,
    run_id: str,
    seq: int,
    timestamp: datetime | None = None,
) -> PortexEvent | None:
    ts = timestamp or datetime.now()
    event_type = getattr(sdk_event, "type", None)

    if event_type == "agent_updated_stream_event":
        return PortexEvent(
            event_type=EventType.RUN_STARTED,
            run_id=run_id,
            payload={"agent_name": getattr(getattr(sdk_event, "new_agent", None), "name", None)},
            seq=seq,
            timestamp=ts,
        )

    if event_type == "raw_response_event":
        raw_type = getattr(getattr(sdk_event, "data", None), "type", None)
        if raw_type == "response.output_text.delta":
            return PortexEvent(
                event_type=EventType.TOKEN_DELTA,
                run_id=run_id,
                payload={"delta": getattr(sdk_event.data, "delta", None)},
                seq=seq,
                timestamp=ts,
            )
        if raw_type == "response.completed":
            return PortexEvent(
                event_type=EventType.RUN_COMPLETED,
                run_id=run_id,
                payload={"status": raw_type},
                seq=seq,
                timestamp=ts,
            )
        if raw_type in {"response.failed", "response.incomplete"}:
            return PortexEvent(
                event_type=EventType.RUN_FAILED,
                run_id=run_id,
                payload={"status": raw_type},
                seq=seq,
                timestamp=ts,
            )
        return None

    if event_type == "run_item_stream_event":
        name = getattr(sdk_event, "name", None)
        raw_item = getattr(getattr(sdk_event, "item", None), "raw_item", None)
        if name == "tool_called":
            return PortexEvent(
                event_type=EventType.TOOL_STARTED,
                run_id=run_id,
                payload={
                    "tool_name": getattr(raw_item, "name", None),
                    "tool_call_id": getattr(raw_item, "call_id", None),
                },
                seq=seq,
                timestamp=ts,
            )
        if name == "tool_output":
            return PortexEvent(
                event_type=EventType.TOOL_COMPLETED,
                run_id=run_id,
                payload={
                    "tool_name": getattr(raw_item, "name", None),
                    "tool_call_id": getattr(raw_item, "call_id", None),
                    "output": getattr(raw_item, "output", None),
                },
                seq=seq,
                timestamp=ts,
            )
        return None

    return None
