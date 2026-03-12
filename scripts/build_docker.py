#!/usr/bin/env python3
"""Build Docker images for the repository."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import argparse
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE_TAG = "portex:v1.0.0"
DEFAULT_DOCKERFILE = "Dockerfile"
DEFAULT_CONTEXT = "."
DOCKER_COMMAND_MISSING_MESSAGE = "docker command not found"


def build_docker_command(
    *,
    tag: str = DEFAULT_IMAGE_TAG,
    dockerfile: str = DEFAULT_DOCKERFILE,
    context: str = DEFAULT_CONTEXT,
) -> list[str]:
    """Return the docker build command for the requested image."""
    command = ["docker", "build", "-t", tag]
    if dockerfile != DEFAULT_DOCKERFILE:
        command.extend(["-f", dockerfile])
    command.append(context)
    return command


def main(
    argv: Sequence[str] | None = None,
    *,
    stderr=sys.stderr,
) -> int:
    """Run docker build for the requested image definition."""
    parser = argparse.ArgumentParser(description="Build a Portex Docker image.")
    parser.add_argument("--tag", default=DEFAULT_IMAGE_TAG, help="Docker image tag.")
    parser.add_argument(
        "--file",
        dest="dockerfile",
        default=DEFAULT_DOCKERFILE,
        help="Dockerfile path relative to the repository root.",
    )
    parser.add_argument(
        "--context",
        default=DEFAULT_CONTEXT,
        help="Build context path relative to the repository root.",
    )
    args = parser.parse_args(argv)

    try:
        completed = subprocess.run(  # noqa: S603 - repo-owned docker command with explicit args
            build_docker_command(
                tag=args.tag,
                dockerfile=args.dockerfile,
                context=args.context,
            ),
            cwd=PROJECT_ROOT,
            check=False,
        )
    except FileNotFoundError:
        print(DOCKER_COMMAND_MISSING_MESSAGE, file=stderr)
        return 127

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
