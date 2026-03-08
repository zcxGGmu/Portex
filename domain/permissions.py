"""Role-based permission templates for Portex."""

from __future__ import annotations

from typing import Final

PermissionMapping = dict[str, tuple[str, ...]]


PERMISSION_TEMPLATES: Final[dict[str, PermissionMapping]] = {
    "owner": {
        "users": ("read", "write", "delete", "admin"),
        "groups": ("read", "write", "delete"),
        "messages": ("read", "write"),
        "tasks": ("read", "write", "execute"),
        "settings": ("read", "write"),
    },
    "admin": {
        "users": ("read", "write"),
        "groups": ("read", "write"),
        "messages": ("read", "write"),
        "tasks": ("read", "write", "execute"),
        "settings": ("read",),
    },
    "member": {
        "groups": ("read",),
        "messages": ("read", "write"),
        "tasks": ("read",),
    },
}


def get_permissions_for_role(role: str) -> PermissionMapping:
    permissions = PERMISSION_TEMPLATES.get(role)
    if permissions is None:
        return {}
    return dict(permissions)


def has_permission(role: str, resource: str, action: str) -> bool:
    permissions = get_permissions_for_role(role)
    return action in permissions.get(resource, ())


__all__ = [
    "PERMISSION_TEMPLATES",
    "PermissionMapping",
    "get_permissions_for_role",
    "has_permission",
]
