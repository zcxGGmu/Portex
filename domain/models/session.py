"""Session domain model placeholder."""

from dataclasses import dataclass


@dataclass(slots=True)
class Session:
    """Minimal session model used during initial scaffolding."""

    id: int | None = None
    user_id: int | None = None
    token: str = ""
