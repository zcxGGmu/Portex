"""Group domain model placeholder."""

from dataclasses import dataclass


@dataclass(slots=True)
class Group:
    """Minimal group model used during initial scaffolding."""

    id: int | None = None
    name: str = ""
