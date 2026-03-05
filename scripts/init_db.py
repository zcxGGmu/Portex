#!/usr/bin/env python3
"""Initialize database placeholder script."""

from __future__ import annotations

import argparse


def main() -> int:
    """Run placeholder database initialization."""
    parser = argparse.ArgumentParser(description="Initialize Portex database.")
    parser.add_argument(
        "--dsn",
        default="sqlite:///./data/portex.db",
        help="Database DSN for initialization.",
    )
    args = parser.parse_args()
    print(f"[placeholder] init db with dsn: {args.dsn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
