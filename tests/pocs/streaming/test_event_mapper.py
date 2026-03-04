from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from pocs.streaming.event_mapper import map_sdk_event


def test_map_raw_delta_event() -> None:
    event = SimpleNamespace(
        type="raw_response_event",
        data=SimpleNamespace(type="response.output_text.delta", delta="你好"),
    )
    mapped = map_sdk_event(event)
    assert mapped is not None
    assert mapped["event_type"] == "run.token.delta"
    assert mapped["payload"]["delta"] == "你好"


def test_map_tool_called_event() -> None:
    event = SimpleNamespace(
        type="run_item_stream_event",
        name="tool_called",
        item=SimpleNamespace(raw_item=SimpleNamespace(name="read_file", call_id="call_1")),
    )
    mapped = map_sdk_event(event)
    assert mapped is not None
    assert mapped["event_type"] == "run.tool.started"
    assert mapped["payload"]["tool_name"] == "read_file"
    assert mapped["payload"]["tool_call_id"] == "call_1"


def test_map_response_completed_event() -> None:
    event = SimpleNamespace(
        type="raw_response_event",
        data=SimpleNamespace(type="response.completed"),
    )
    mapped = map_sdk_event(event)
    assert mapped is not None
    assert mapped["event_type"] == "run.completed"
