"""Message route placeholders."""

from fastapi import APIRouter

router = APIRouter(prefix="/messages", tags=["messages"])

__all__ = ["router"]
