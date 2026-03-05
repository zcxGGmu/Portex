"""Agent runner entrypoint placeholders."""

from __future__ import annotations

from typing import Any

from .event_mapper import map_event


def run_agent(payload: dict[str, Any]) -> dict[str, Any]:
    """Run the placeholder agent flow and return one mapped event."""
    return map_event({"type": "runner.started", "payload": payload})


def main() -> int:
    """CLI main entrypoint for the placeholder runner."""
    run_agent({"message": "placeholder"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
