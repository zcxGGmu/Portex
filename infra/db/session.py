"""Database session management placeholders."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


@contextmanager
def session_scope() -> Iterator[None]:
    """Yield a placeholder session context."""
    yield None
