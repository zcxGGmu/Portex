from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from pocs.streaming.main import extract_event_type


def test_extract_event_type_from_raw_delta() -> None:
    event = SimpleNamespace(
        type="raw_response_event",
        data=SimpleNamespace(type="response.output_text.delta"),
    )
    assert extract_event_type(event) == "response.output_text.delta"


def test_extract_event_type_from_run_item_event() -> None:
    event = SimpleNamespace(type="run_item_stream_event", name="tool_called")
    assert extract_event_type(event) == "run_item_stream_event:tool_called"


def test_extract_event_type_falls_back_to_event_type() -> None:
    event = SimpleNamespace(type="agent_updated_stream_event")
    assert extract_event_type(event) == "agent_updated_stream_event"
