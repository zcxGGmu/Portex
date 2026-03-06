from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from portex.contracts.events import EventType, PortexEvent


def test_event_type_enum_values() -> None:
    assert EventType.RUN_STARTED.value == "run.started"
    assert EventType.TOOL_COMPLETED.value == "run.tool.completed"
    assert EventType.RUN_TIMEOUT.value == "run.timeout"
    assert EventType.RUN_FAILED.value == "run.failed"


def test_portex_event_model_parses_and_defaults_payload() -> None:
    event = PortexEvent(
        event_type=EventType.RUN_COMPLETED,
        run_id="run_1",
        seq=7,
        timestamp=datetime(2026, 3, 4, 23, 0, 0),
    )
    assert event.payload == {}
    assert event.event_type == EventType.RUN_COMPLETED
