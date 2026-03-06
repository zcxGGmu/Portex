"""Agent runner entrypoint backed by the OpenAI Agents SDK."""

from __future__ import annotations

import json
import sys
from typing import Any, Callable, TextIO

from agents import Agent, Runner

from .tools import build_default_tools
from .types import ContainerInput, ContainerOutput

AgentFactory = Callable[..., Any]
RunSyncCallable = Callable[..., Any]
RunAsyncCallable = Callable[..., Any]

OUTPUT_START_MARKER = "---PORTEX_OUTPUT_START---"
OUTPUT_END_MARKER = "---PORTEX_OUTPUT_END---"


def build_agent(
    payload: ContainerInput,
    *,
    agent_factory: AgentFactory = Agent,
    tools: list[Any] | None = None,
) -> Any:
    """Create the runner agent for one container invocation."""
    return agent_factory(
        name=payload.agent_name,
        instructions=payload.instructions,
        tools=tools if tools is not None else build_default_tools(),
    )


def parse_input(payload: str) -> ContainerInput:
    """Parse stdin JSON into a validated container input model."""
    return ContainerInput.model_validate_json(payload)


def _stringify_final_output(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if hasattr(value, "model_dump"):
        return json.dumps(value.model_dump(mode="json"), ensure_ascii=False)
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return str(value)


def _serialize_output(payload: ContainerOutput) -> str:
    return payload.model_dump_json(ensure_ascii=False)


def write_output(
    payload: ContainerOutput,
    *,
    stdout: TextIO | None = None,
    framed: bool = False,
) -> None:
    """Write the result envelope to stdout."""
    output_stream = stdout or sys.stdout
    if framed:
        output_stream.write(f"{OUTPUT_START_MARKER}\n")
    output_stream.write(_serialize_output(payload))
    output_stream.write("\n")
    if framed:
        output_stream.write(f"{OUTPUT_END_MARKER}\n")
    output_stream.flush()


def run_agent(
    payload: ContainerInput,
    *,
    agent_factory: AgentFactory = Agent,
    run_sync: RunSyncCallable = Runner.run_sync,
    tools: list[Any] | None = None,
) -> ContainerOutput:
    """Execute one runner request with the sync runner path."""
    try:
        agent = build_agent(
            payload,
            agent_factory=agent_factory,
            tools=tools,
        )
        result = run_sync(agent, input=payload.prompt)
    except Exception as exc:
        return ContainerOutput(status="error", error=str(exc))

    return ContainerOutput(
        status="success",
        result=_stringify_final_output(getattr(result, "final_output", None)),
    )


async def run_container_request(
    payload: ContainerInput,
    *,
    agent_factory: AgentFactory = Agent,
    run_async: RunAsyncCallable = Runner.run,
    tools: list[Any] | None = None,
) -> ContainerOutput:
    """Async compatibility wrapper for container execution."""
    try:
        agent = build_agent(
            payload,
            agent_factory=agent_factory,
            tools=tools,
        )
        result = await run_async(agent, input=payload.prompt)
    except Exception as exc:
        return ContainerOutput(status="error", error=str(exc))

    return ContainerOutput(
        status="success",
        result=_stringify_final_output(getattr(result, "final_output", None)),
    )


def main(
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    framed: bool = False,
) -> int:
    """Read one request from stdin and write one result to stdout."""
    input_stream = stdin or sys.stdin

    try:
        request = parse_input(input_stream.read())
        response = run_agent(request)
    except Exception as exc:
        response = ContainerOutput(status="error", error=str(exc))

    write_output(response, stdout=stdout, framed=framed)
    return 0 if response.status == "success" else 1


def cli(
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> int:
    """CLI entrypoint using framed stdout output."""
    return main(stdin=stdin, stdout=stdout, framed=True)


__all__ = [
    "AgentFactory",
    "OUTPUT_END_MARKER",
    "OUTPUT_START_MARKER",
    "RunAsyncCallable",
    "RunSyncCallable",
    "build_agent",
    "cli",
    "main",
    "parse_input",
    "run_agent",
    "run_container_request",
    "write_output",
]


if __name__ == "__main__":
    raise SystemExit(cli())
