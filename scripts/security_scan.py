#!/usr/bin/env python3
"""Run the repository-local Ruff security scan."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SECURITY_SCAN_TARGETS = (
    "app",
    "domain",
    "infra",
    "services",
    "scripts",
    "pocs",
    "portex",
    "container/agent-runner/src",
)


def build_security_scan_command() -> list[str]:
    """Return the Ruff security scan command."""
    return [
        sys.executable,
        "-m",
        "ruff",
        "check",
        "--select",
        "S",
        *SECURITY_SCAN_TARGETS,
    ]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the repository-local security scan."""
    del argv
    completed = subprocess.run(  # noqa: S603 - fixed repo-owned command assembled from constants
        build_security_scan_command(),
        cwd=PROJECT_ROOT,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
