#!/usr/bin/env python3
"""Run the repository-local Python dependency audit."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
IGNORED_VULNERABILITIES = (
    # `ecdsa` has no newer release than 0.19.1 at the time of this audit.
    "CVE-2024-23342",
)


def build_dependency_audit_command() -> list[str]:
    """Return the pip-audit command for the current project."""
    command = [sys.executable, "-m", "pip_audit"]
    for vulnerability_id in IGNORED_VULNERABILITIES:
        command.extend(["--ignore-vuln", vulnerability_id])
    command.append(".")
    return command


def main(argv: Sequence[str] | None = None) -> int:
    """Run the repository-local dependency audit."""
    del argv
    completed = subprocess.run(  # noqa: S603 - fixed repo-owned command assembled from constants
        build_dependency_audit_command(),
        cwd=PROJECT_ROOT,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
