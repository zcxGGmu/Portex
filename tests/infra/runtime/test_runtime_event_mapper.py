from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _map_sdk_event():
    from infra.runtime.mapper import map_sdk_event

    return map_sdk_event


def test_map_agent_updated_to_run_started() -> None:
    sdk_event = SimpleNamespace(
        type="agent_updated_stream_event",
        new_agent=SimpleNamespace(name="PortexAgent"),
    )

    event = _map_sdk_event()(sdk_event, run_id="run-1")

    assert event is not None
    assert event.event_type == "run.started"
    assert event.run_id == "run-1"
    assert event.payload["agent_name"] == "PortexAgent"


def test_map_raw_response_delta_to_token_delta() -> None:
    sdk_event = SimpleNamespace(
        type="raw_response_event",
        data=SimpleNamespace(type="response.output_text.delta", delta="hello"),
    )

    event = _map_sdk_event()(sdk_event, run_id="run-2")

    assert event is not None
    assert event.event_type == "run.token.delta"
    assert event.payload["delta"] == "hello"


def test_map_raw_response_completed_to_run_completed() -> None:
    sdk_event = SimpleNamespace(
        type="raw_response_event",
        data=SimpleNamespace(type="response.completed"),
    )

    event = _map_sdk_event()(sdk_event, run_id="run-3")

    assert event is not None
    assert event.event_type == "run.completed"


def test_map_raw_response_failed_to_run_failed() -> None:
    sdk_event = SimpleNamespace(
        type="raw_response_event",
        data=SimpleNamespace(type="response.failed"),
    )

    event = _map_sdk_event()(sdk_event, run_id="run-4")

    assert event is not None
    assert event.event_type == "run.failed"


def test_map_raw_response_incomplete_to_run_failed() -> None:
    sdk_event = SimpleNamespace(
        type="raw_response_event",
        data=SimpleNamespace(type="response.incomplete"),
    )

    event = _map_sdk_event()(sdk_event, run_id="run-4b")

    assert event is not None
    assert event.event_type == "run.failed"


def test_map_tool_called_and_tool_output_events() -> None:
    called = SimpleNamespace(
        type="run_item_stream_event",
        name="tool_called",
        item=SimpleNamespace(raw_item=SimpleNamespace(name="read_file", call_id="call-1")),
    )
    output = SimpleNamespace(
        type="run_item_stream_event",
        name="tool_output",
        item=SimpleNamespace(
            raw_item=SimpleNamespace(name="read_file", call_id="call-1", output="ok")
        ),
    )

    called_event = _map_sdk_event()(called, run_id="run-5")
    output_event = _map_sdk_event()(output, run_id="run-5")

    assert called_event is not None
    assert called_event.event_type == "run.tool.started"
    assert called_event.payload["tool_name"] == "read_file"
    assert called_event.payload["tool_call_id"] == "call-1"

    assert output_event is not None
    assert output_event.event_type == "run.tool.completed"
    assert output_event.payload["tool_name"] == "read_file"
    assert output_event.payload["tool_call_id"] == "call-1"
    assert output_event.payload["output"] == "ok"


def test_map_unknown_event_returns_none() -> None:
    sdk_event = SimpleNamespace(type="unknown_event")

    assert _map_sdk_event()(sdk_event, run_id="run-6") is None
