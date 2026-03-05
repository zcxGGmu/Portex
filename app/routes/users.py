"""User route placeholders."""

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

__all__ = ["router"]
