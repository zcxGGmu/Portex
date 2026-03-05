"""Task domain model placeholder."""

from dataclasses import dataclass


@dataclass(slots=True)
class Task:
    """Minimal task model used during initial scaffolding."""

    id: int | None = None
    title: str = ""
    status: str = "pending"
