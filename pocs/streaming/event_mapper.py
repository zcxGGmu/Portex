"""Map OpenAI Agents SDK stream events to Portex-style event contracts."""

from __future__ import annotations

from typing import Any, TypedDict


class PortexMappedEvent(TypedDict):
    event_type: str
    payload: dict[str, Any]


def _payload(**kwargs: Any) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if value is not None}


def map_sdk_event(event: Any) -> PortexMappedEvent | None:
    """Map a single SDK stream event into a minimal Portex event."""
    event_type = getattr(event, "type", None)

    if event_type == "agent_updated_stream_event":
        return {
            "event_type": "run.started",
            "payload": _payload(agent_name=getattr(getattr(event, "new_agent", None), "name", None)),
        }

    if event_type == "raw_response_event":
        raw_type = getattr(getattr(event, "data", None), "type", None)
        if raw_type == "response.output_text.delta":
            return {
                "event_type": "run.token.delta",
                "payload": _payload(delta=getattr(event.data, "delta", None)),
            }
        if raw_type == "response.completed":
            return {"event_type": "run.completed", "payload": _payload(status=raw_type)}
        if raw_type in {"response.failed", "response.incomplete"}:
            return {"event_type": "run.failed", "payload": _payload(status=raw_type)}
        return None

    if event_type == "run_item_stream_event":
        if getattr(event, "name", None) == "tool_called":
            raw_item = getattr(getattr(event, "item", None), "raw_item", None)
            return {
                "event_type": "run.tool.started",
                "payload": _payload(
                    tool_name=getattr(raw_item, "name", None),
                    tool_call_id=getattr(raw_item, "call_id", None),
                ),
            }
        if getattr(event, "name", None) == "tool_output":
            raw_item = getattr(getattr(event, "item", None), "raw_item", None)
            return {
                "event_type": "run.tool.completed",
                "payload": _payload(
                    tool_name=getattr(raw_item, "name", None),
                    tool_call_id=getattr(raw_item, "call_id", None),
                    output=getattr(raw_item, "output", None),
                ),
            }
        return None

    return None
