"""Streaming PoC entrypoint for OpenAI Agents SDK."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Any

from agents import Agent, Runner


def extract_event_type(event: Any) -> str:
    """Extract a stable event type string from SDK stream events."""
    event_type = getattr(event, "type", "unknown")
    if event_type == "raw_response_event":
        data_type = getattr(getattr(event, "data", None), "type", None)
        if data_type:
            return str(data_type)
    if event_type == "run_item_stream_event":
        run_item_name = getattr(event, "name", None)
        if run_item_name:
            return f"run_item_stream_event:{run_item_name}"
    return str(event_type)


async def run_streaming_poc(prompt: str) -> list[str]:
    """Run the streaming PoC once and print normalized events as JSON lines."""
    agent = Agent(
        name="Test",
        instructions="你是一个有帮助的助手",
    )
    result = Runner.run_streamed(agent, input=prompt)
    observed_types: list[str] = []
    async for event in result.stream_events():
        event_type = extract_event_type(event)
        observed_types.append(event_type)
        payload = {
            "seq": len(observed_types),
            "event_type": event_type,
        }
        delta = getattr(getattr(event, "data", None), "delta", None)
        if isinstance(delta, str) and delta:
            payload["delta"] = delta
        print(json.dumps(payload, ensure_ascii=False))
    return observed_types


def emit_dry_run_events() -> list[str]:
    """Emit deterministic sample output when no API key is configured."""
    sample_types = [
        "agent_updated_stream_event",
        "response.created",
        "response.output_text.delta",
        "run_item_stream_event:message_output_created",
        "response.completed",
    ]
    for idx, event_type in enumerate(sample_types, start=1):
        print(json.dumps({"seq": idx, "event_type": event_type}, ensure_ascii=False))
    return sample_types


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Portex streaming PoC")
    parser.add_argument("--input", default="你好", help="Agent input prompt")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Emit deterministic sample events without network calls",
    )
    return parser.parse_args()


async def async_main() -> int:
    args = parse_args()
    if args.dry_run:
        emit_dry_run_events()
        return 0
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Use --dry-run for local validation.")
        return 2
    await run_streaming_poc(args.input)
    return 0


def main() -> int:
    return asyncio.run(async_main())


if __name__ == "__main__":
    raise SystemExit(main())
