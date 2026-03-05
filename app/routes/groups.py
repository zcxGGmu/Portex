"""Group route placeholders."""

from fastapi import APIRouter

router = APIRouter(prefix="/groups", tags=["groups"])

__all__ = ["router"]
