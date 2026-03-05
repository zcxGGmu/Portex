"""Application configuration helpers."""

import logging


def setup_logging() -> None:
    """Configure process-wide logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
