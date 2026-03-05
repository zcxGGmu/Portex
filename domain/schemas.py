"""Domain schema placeholders."""

from pydantic import BaseModel


class HealthSchema(BaseModel):
    """Schema for service health responses."""

    status: str = "ok"


__all__ = ["HealthSchema"]
