"""Authentication middleware dependencies."""

from app.middleware.auth import (
    get_current_user,
    require_permission,
    require_role,
    security,
)

__all__ = ["get_current_user", "require_permission", "require_role", "security"]
