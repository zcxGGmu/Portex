"""Message domain model placeholder."""

from dataclasses import dataclass


@dataclass(slots=True)
class Message:
    """Minimal message model used during initial scaffolding."""

    id: int | None = None
    sender_id: int | None = None
    content: str = ""
