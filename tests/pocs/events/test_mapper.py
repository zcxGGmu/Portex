from datetime import datetime
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from pocs.events.mapper import map_sdk_event
from portex.contracts.events import EventType


def test_map_tool_output_to_tool_completed() -> None:
    event = SimpleNamespace(
        type="run_item_stream_event",
        name="tool_output",
        item=SimpleNamespace(
            raw_item=SimpleNamespace(name="read_file", call_id="call_1", output="ok")
        ),
    )
    mapped = map_sdk_event(event, run_id="run_1", seq=2, timestamp=datetime(2026, 3, 4))
    assert mapped is not None
    assert mapped.event_type == EventType.TOOL_COMPLETED
    assert mapped.payload["output"] == "ok"


def test_map_response_failed_to_run_failed() -> None:
    event = SimpleNamespace(
        type="raw_response_event",
        data=SimpleNamespace(type="response.failed"),
    )
    mapped = map_sdk_event(event, run_id="run_1", seq=3, timestamp=datetime(2026, 3, 4))
    assert mapped is not None
    assert mapped.event_type == EventType.RUN_FAILED


def test_map_unknown_event_returns_none() -> None:
    event = SimpleNamespace(type="unknown_event")
    assert map_sdk_event(event, run_id="run_1", seq=4, timestamp=datetime(2026, 3, 4)) is None
