"""Admin route placeholders."""

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])

__all__ = ["router"]
