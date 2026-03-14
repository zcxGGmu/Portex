"""Memory-management routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import get_current_user
from app.openapi import openapi_error_responses
from domain.schemas import (
    MemoryGlobalResponse,
    UpdateMemoryGlobalRequest,
    UpdateWorkspaceMemoryFileRequest,
    UserResponse,
    WorkspaceMemoryFileEntryResponse,
    WorkspaceMemoryFileListResponse,
    WorkspaceMemoryFileResponse,
    WorkspaceMemorySearchHitResponse,
    WorkspaceMemorySearchResponse,
)
from infra.db.database import get_db
from services.group_registry import GroupRegistryService
from services.memory import (
    GroupMemoryFileContent,
    GroupMemoryFileEntry,
    MemoryService,
    memory_service,
)

router = APIRouter(prefix="/memory", tags=["memory"])


def get_group_registry_service(
    db: AsyncSession = Depends(get_db),
) -> GroupRegistryService:
    return GroupRegistryService(db=db)


def get_memory_service() -> MemoryService:
    return memory_service


async def _require_accessible_workspace(
    *,
    group_id: str,
    current_user: UserResponse,
    group_registry: GroupRegistryService,
):
    workspace = await group_registry.get_web_workspace_by_folder(group_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group not found",
        )
    if not await group_registry.user_can_access_group(
        user_id=current_user.id,
        user_role=current_user.role,
        group=workspace,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group not found",
        )
    return workspace


def _map_memory_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (ValueError, IsADirectoryError, NotADirectoryError)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="memory operation failed",
    )


def _to_memory_global_response(
    *,
    service: MemoryService,
    user_id: str,
    content: str,
) -> MemoryGlobalResponse:
    updated_at, size = service.get_user_memory_metadata(user_id)
    return MemoryGlobalResponse(
        content=content,
        updated_at=updated_at,
        size=size,
    )


def _to_workspace_memory_file_entry_response(
    entry: GroupMemoryFileEntry,
) -> WorkspaceMemoryFileEntryResponse:
    return WorkspaceMemoryFileEntryResponse(
        path=entry.path,
        name=entry.name,
        updated_at=entry.updated_at,
        size=entry.size,
    )


def _to_workspace_memory_file_response(
    item: GroupMemoryFileContent,
) -> WorkspaceMemoryFileResponse:
    return WorkspaceMemoryFileResponse(
        path=item.path,
        content=item.content,
        updated_at=item.updated_at,
        size=item.size,
    )


def _normalize_search_hit_path(
    *,
    service: MemoryService,
    group_folder: str,
    raw_path: str,
) -> str:
    path = Path(raw_path)
    if path.is_absolute():
        memory_dir = service._get_group_memory_dir(group_folder)
        try:
            return path.resolve(strict=False).relative_to(memory_dir).as_posix()
        except ValueError:
            raise ValueError("unexpected absolute memory search hit") from None
    return path.as_posix()


@router.get(
    "/global",
    response_model=MemoryGlobalResponse,
    summary="Get global memory",
    description="Read the current user's global memory content from AGENTS.md.",
    responses=openapi_error_responses(status.HTTP_401_UNAUTHORIZED),
)
async def get_global_memory(
    current_user: UserResponse = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryGlobalResponse:
    content = await service.get_user_memory(current_user.id)
    return _to_memory_global_response(
        service=service,
        user_id=current_user.id,
        content=content,
    )


@router.put(
    "/global",
    response_model=MemoryGlobalResponse,
    summary="Update global memory",
    description="Replace the current user's global AGENTS.md memory content.",
    responses=openapi_error_responses(status.HTTP_401_UNAUTHORIZED),
)
async def update_global_memory(
    request: UpdateMemoryGlobalRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryGlobalResponse:
    await service.update_user_memory(current_user.id, request.content)
    return _to_memory_global_response(
        service=service,
        user_id=current_user.id,
        content=request.content,
    )


@router.get(
    "/workspaces/{group_id}/files",
    response_model=WorkspaceMemoryFileListResponse,
    summary="List workspace memory files",
    description="List markdown memory files under one accessible workspace memory root.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def list_workspace_memory_files(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: MemoryService = Depends(get_memory_service),
) -> WorkspaceMemoryFileListResponse:
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        files = await service.list_group_memory_files(workspace.folder)
    except Exception as exc:
        raise _map_memory_error(exc) from exc
    return WorkspaceMemoryFileListResponse(
        files=[_to_workspace_memory_file_entry_response(item) for item in files]
    )


@router.get(
    "/workspaces/{group_id}/file",
    response_model=WorkspaceMemoryFileResponse,
    summary="Read workspace memory file",
    description=(
        "Read one markdown memory file under an accessible workspace. "
        "Missing but valid paths return empty content."
    ),
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def get_workspace_memory_file(
    group_id: str,
    path: str = Query(min_length=1),
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: MemoryService = Depends(get_memory_service),
) -> WorkspaceMemoryFileResponse:
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        memory_file = await service.get_group_memory_file(workspace.folder, path)
    except Exception as exc:
        raise _map_memory_error(exc) from exc
    return _to_workspace_memory_file_response(memory_file)


@router.put(
    "/workspaces/{group_id}/file",
    response_model=WorkspaceMemoryFileResponse,
    summary="Write workspace memory file",
    description="Write one markdown memory file under an accessible workspace.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def update_workspace_memory_file(
    group_id: str,
    request: UpdateWorkspaceMemoryFileRequest,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: MemoryService = Depends(get_memory_service),
) -> WorkspaceMemoryFileResponse:
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        memory_file = await service.update_group_memory_file(
            workspace.folder,
            request.path,
            request.content,
        )
    except Exception as exc:
        raise _map_memory_error(exc) from exc
    return _to_workspace_memory_file_response(memory_file)


@router.get(
    "/workspaces/{group_id}/search",
    response_model=WorkspaceMemorySearchResponse,
    summary="Search workspace memory",
    description="Search markdown memory files under one accessible workspace memory root.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def search_workspace_memory(
    group_id: str,
    q: str,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: MemoryService = Depends(get_memory_service),
) -> WorkspaceMemorySearchResponse:
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        hits = [
            WorkspaceMemorySearchHitResponse(
                path=_normalize_search_hit_path(
                    service=service,
                    group_folder=workspace.folder,
                    raw_path=raw_path,
                )
            )
            for raw_path in await service.search_memory(workspace.folder, q)
        ]
    except Exception as exc:
        raise _map_memory_error(exc) from exc
    return WorkspaceMemorySearchResponse(hits=hits)


__all__ = [
    "get_group_registry_service",
    "get_memory_service",
    "router",
]
