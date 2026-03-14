"""Shared OpenAPI metadata for the Portex HTTP API."""

from __future__ import annotations

from fastapi import status

OPENAPI_DESCRIPTION = (
    "Portex HTTP API for authentication, admin operations, groups, messages, and "
    "scheduled tasks.\n\n"
    "This OpenAPI schema documents the current HTTP surface only. The WebSocket "
    "entrypoint `/ws/{group_folder}` is implemented separately and is not represented "
    "in this schema."
)

OPENAPI_TAGS = [
    {
        "name": "health",
        "description": "Service health and readiness checks.",
    },
    {
        "name": "monitor",
        "description": "Operator-facing queue, run-status, and backend-health monitor endpoints.",
    },
    {
        "name": "auth",
        "description": "Register users and exchange username/password credentials for "
        "bearer tokens.",
    },
    {
        "name": "users",
        "description": "Current-user and user-management endpoints backed by the "
        "current in-memory auth service.",
    },
    {
        "name": "admin",
        "description": "Admin-scoped HTTP endpoints for user and invite management.",
    },
    {
        "name": "groups",
        "description": "Workspace listing, shared-workspace management, conversation "
        "slot management, IM binding management, and member management.",
    },
    {
        "name": "files",
        "description": "Workspace-scoped file browsing, upload, preview, text editing, download, and delete endpoints.",
    },
    {
        "name": "messages",
        "description": "HTTP message dispatch entrypoint backed by the current "
        "runtime-chain orchestration boundary.",
    },
    {
        "name": "executions",
        "description": "Execution run status query endpoints exposing coordinator "
        "run-state and minimal recovery signals.",
    },
    {
        "name": "tasks",
        "description": "Scheduled task CRUD and run-log inspection. Datetime fields "
        "are documented and returned in UTC while execution state remains backed by "
        "the current in-memory scheduler.",
    },
]

_ERROR_RESPONSES = {
    status.HTTP_400_BAD_REQUEST: {
        "description": "The request payload is syntactically valid but violates the "
        "current Portex API contract."
    },
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Authentication is required or the bearer token is invalid."
    },
    status.HTTP_403_FORBIDDEN: {
        "description": "The authenticated user does not have permission for this "
        "operation."
    },
    status.HTTP_404_NOT_FOUND: {
        "description": "The requested resource does not exist in the current "
        "in-memory state."
    },
    status.HTTP_409_CONFLICT: {
        "description": "The request conflicts with existing in-memory state."
    },
}


def openapi_error_responses(*status_codes: int) -> dict[int, dict[str, str]]:
    return {
        status_code: dict(_ERROR_RESPONSES[status_code])
        for status_code in status_codes
    }


__all__ = ["OPENAPI_DESCRIPTION", "OPENAPI_TAGS", "openapi_error_responses"]
