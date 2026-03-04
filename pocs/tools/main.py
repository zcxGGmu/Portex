"""Tool-calling PoC entrypoint for OpenAI Agents SDK."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from agents import Agent, RunContextWrapper, Runner, function_tool


def invoke_read_file_locally(path: str) -> str:
    """Local implementation used by the SDK tool wrapper and tests."""
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


@function_tool
def read_file(ctx: RunContextWrapper[Any], path: str) -> str:
    """读取文件内容"""
    return invoke_read_file_locally(path)


def build_agent() -> Agent:
    return Agent(
        name="ToolsPoC",
        instructions="你是一个有帮助的助手。必要时使用 read_file 工具读取文件内容。",
        tools=[read_file],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Portex tools PoC")
    parser.add_argument("--dry-run", action="store_true", help="Run local tool invocation only")
    parser.add_argument(
        "--sample-file",
        default="README.md",
        help="File path used by local invocation or online prompt construction",
    )
    parser.add_argument(
        "--prompt",
        default="请使用 read_file 工具读取 {path} 的内容并总结第一行。",
        help="Prompt template for online run; {path} will be replaced",
    )
    return parser.parse_args()


def run_dry_run(sample_file: str) -> int:
    content = invoke_read_file_locally(sample_file)
    print(
        json.dumps(
            {
                "tool": "read_file",
                "path": sample_file,
                "chars": len(content),
                "preview": content[:120],
            },
            ensure_ascii=False,
        )
    )
    return 0


async def run_online(sample_file: str, prompt_template: str) -> int:
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Use --dry-run for local validation.")
        return 2
    prompt = prompt_template.format(path=sample_file)
    result = await Runner.run(build_agent(), input=prompt)
    print(str(result.final_output))
    return 0


def main() -> int:
    args = parse_args()
    sample_file = str(Path(args.sample_file))
    if args.dry_run:
        return run_dry_run(sample_file)
    return asyncio.run(run_online(sample_file, args.prompt))


if __name__ == "__main__":
    raise SystemExit(main())
