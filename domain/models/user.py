"""User domain model placeholder."""

from dataclasses import dataclass


@dataclass(slots=True)
class User:
    """Minimal user model used during initial scaffolding."""

    id: int | None = None
    username: str = ""
