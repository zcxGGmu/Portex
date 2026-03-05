#!/usr/bin/env python3
"""Build Docker image placeholder script."""

from __future__ import annotations

import argparse


def main() -> int:
    """Run placeholder Docker build command."""
    parser = argparse.ArgumentParser(description="Build agent-runner Docker image.")
    parser.add_argument("--tag", default="portex/agent-runner:dev", help="Image tag.")
    args = parser.parse_args()
    print(f"[placeholder] build docker image: {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
