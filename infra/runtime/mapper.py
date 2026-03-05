"""Map OpenAI Agents SDK events into runtime stream events."""

from __future__ import annotations

from typing import Any

from .adapter import RunEvent


def _payload(**kwargs: Any) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if value is not None}


def map_sdk_event(sdk_event: Any, *, run_id: str) -> RunEvent | None:
    """Map a single SDK stream event into ``RunEvent``."""
    event_type = getattr(sdk_event, "type", None)

    if event_type == "agent_updated_stream_event":
        return RunEvent(
            event_type="run.started",
            run_id=run_id,
            payload=_payload(agent_name=getattr(getattr(sdk_event, "new_agent", None), "name", None)),
        )

    if event_type == "raw_response_event":
        raw_type = getattr(getattr(sdk_event, "data", None), "type", None)
        if raw_type == "response.output_text.delta":
            return RunEvent(
                event_type="run.token.delta",
                run_id=run_id,
                payload=_payload(delta=getattr(sdk_event.data, "delta", None)),
            )
        if raw_type == "response.completed":
            return RunEvent(
                event_type="run.completed",
                run_id=run_id,
                payload=_payload(status=raw_type),
            )
        if raw_type in {"response.failed", "response.incomplete"}:
            return RunEvent(
                event_type="run.failed",
                run_id=run_id,
                payload=_payload(status=raw_type),
            )
        return None

    if event_type == "run_item_stream_event":
        raw_item = getattr(getattr(sdk_event, "item", None), "raw_item", None)

        if getattr(sdk_event, "name", None) == "tool_called":
            return RunEvent(
                event_type="run.tool.started",
                run_id=run_id,
                payload=_payload(
                    tool_name=getattr(raw_item, "name", None),
                    tool_call_id=getattr(raw_item, "call_id", None),
                ),
            )
        if getattr(sdk_event, "name", None) == "tool_output":
            return RunEvent(
                event_type="run.tool.completed",
                run_id=run_id,
                payload=_payload(
                    tool_name=getattr(raw_item, "name", None),
                    tool_call_id=getattr(raw_item, "call_id", None),
                    output=getattr(raw_item, "output", None),
                ),
            )
        return None

    return None


__all__ = ["map_sdk_event"]
