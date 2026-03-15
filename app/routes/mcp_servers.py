"""MCP server management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_user
from app.openapi import openapi_error_responses
from domain.schemas import (
    DeleteMcpServerResponse,
    McpServerDetailResponse,
    McpServerListResponse,
    McpServerSummaryResponse,
    UpdateMcpServerRequest,
    UpdateMcpServerStateRequest,
    UserResponse,
)
from services.mcp_servers import (
    McpServerDetail,
    McpServerEntry,
    McpServersService,
    mcp_servers_service,
)

router = APIRouter(prefix="/mcp-servers", tags=["mcp_servers"])


def get_mcp_servers_service() -> McpServersService:
    return mcp_servers_service


def _map_mcp_servers_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, (ValueError, IsADirectoryError, NotADirectoryError)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="mcp server operation failed",
    )


def _to_mcp_server_summary_response(item: McpServerEntry) -> McpServerSummaryResponse:
    return McpServerSummaryResponse(
        server_id=item.server_id,
        transport=item.transport,
        enabled=item.enabled,
        updated_at=item.updated_at,
    )


def _to_mcp_server_detail_response(item: McpServerDetail) -> McpServerDetailResponse:
    return McpServerDetailResponse(
        server_id=item.server_id,
        transport=item.transport,
        enabled=item.enabled,
        description=item.description,
        created_at=item.created_at,
        updated_at=item.updated_at,
        command=item.command,
        args=item.args,
        env=item.env,
        url=item.url,
        headers=item.headers,
    )


@router.get(
    "",
    response_model=McpServerListResponse,
    summary="List MCP servers",
    description="List MCP server configs for the current user.",
    responses=openapi_error_responses(status.HTTP_401_UNAUTHORIZED),
)
async def list_mcp_servers(
    current_user: UserResponse = Depends(get_current_user),
    service: McpServersService = Depends(get_mcp_servers_service),
) -> McpServerListResponse:
    try:
        items = await service.list_user_servers(current_user.id)
    except Exception as exc:
        raise _map_mcp_servers_error(exc) from exc
    return McpServerListResponse(
        servers=[_to_mcp_server_summary_response(item) for item in items]
    )


@router.get(
    "/{server_id}",
    response_model=McpServerDetailResponse,
    summary="Get MCP server detail",
    description="Read one MCP server config for the current user.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def get_mcp_server(
    server_id: str,
    current_user: UserResponse = Depends(get_current_user),
    service: McpServersService = Depends(get_mcp_servers_service),
) -> McpServerDetailResponse:
    try:
        detail = await service.get_user_server(current_user.id, server_id)
    except Exception as exc:
        raise _map_mcp_servers_error(exc) from exc
    return _to_mcp_server_detail_response(detail)


@router.put(
    "/{server_id}",
    response_model=McpServerDetailResponse,
    summary="Update MCP server",
    description="Create or update one MCP server config for the current user.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
    ),
)
async def put_mcp_server(
    server_id: str,
    request: UpdateMcpServerRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: McpServersService = Depends(get_mcp_servers_service),
) -> McpServerDetailResponse:
    try:
        detail = await service.upsert_user_server(
            current_user.id,
            server_id,
            transport=request.transport,
            command=request.command,
            args=request.args,
            env=request.env,
            url=request.url,
            headers=request.headers,
            description=request.description,
        )
    except Exception as exc:
        raise _map_mcp_servers_error(exc) from exc
    return _to_mcp_server_detail_response(detail)


@router.patch(
    "/{server_id}/state",
    response_model=McpServerDetailResponse,
    summary="Update MCP server state",
    description="Enable or disable one MCP server config without editing transport fields.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def patch_mcp_server_state(
    server_id: str,
    request: UpdateMcpServerStateRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: McpServersService = Depends(get_mcp_servers_service),
) -> McpServerDetailResponse:
    try:
        detail = await service.set_user_server_enabled(
            current_user.id,
            server_id,
            enabled=request.enabled,
        )
    except Exception as exc:
        raise _map_mcp_servers_error(exc) from exc
    return _to_mcp_server_detail_response(detail)


@router.delete(
    "/{server_id}",
    response_model=DeleteMcpServerResponse,
    summary="Delete MCP server",
    description="Delete one MCP server config for the current user.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def delete_mcp_server(
    server_id: str,
    current_user: UserResponse = Depends(get_current_user),
    service: McpServersService = Depends(get_mcp_servers_service),
) -> DeleteMcpServerResponse:
    try:
        await service.delete_user_server(current_user.id, server_id)
    except Exception as exc:
        raise _map_mcp_servers_error(exc) from exc
    return DeleteMcpServerResponse(status="deleted")


__all__ = ["get_mcp_servers_service", "router"]
