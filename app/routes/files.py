"""Workspace file-management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import get_current_user, require_permission
from app.openapi import openapi_error_responses
from domain.schemas import (
    DeleteWorkspaceFileResponse,
    UpdateWorkspaceFileContentRequest,
    UserResponse,
    WorkspaceFileContentResponse,
    WorkspaceFileEntryResponse,
    WorkspaceFileListResponse,
    WorkspaceFileUploadResponse,
)
from infra.db.database import get_db
from services.group_registry import GroupRegistryService
from services.workspace_files import WorkspaceFileService

router = APIRouter(prefix="/groups", tags=["files"])


def get_group_registry_service(
    db: AsyncSession = Depends(get_db),
) -> GroupRegistryService:
    return GroupRegistryService(db=db)


def get_workspace_file_service() -> WorkspaceFileService:
    return WorkspaceFileService()


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


def _to_workspace_file_entry_response(entry) -> WorkspaceFileEntryResponse:
    return WorkspaceFileEntryResponse(
        name=entry.name,
        path=entry.path,
        type=entry.type,
        size=entry.size,
        modified_at=entry.modified_at,
    )


def _map_workspace_file_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, NotADirectoryError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, IsADirectoryError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="file operation failed")


@router.get(
    "/{group_id}/files",
    response_model=WorkspaceFileListResponse,
    summary="List workspace files",
    description="List files and directories under one accessible workspace-relative path.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def list_workspace_files(
    group_id: str,
    path: str = "",
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    workspace_files: WorkspaceFileService = Depends(get_workspace_file_service),
) -> WorkspaceFileListResponse:
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        listing = workspace_files.list_entries(workspace.folder, path)
    except Exception as exc:
        raise _map_workspace_file_error(exc) from exc
    return WorkspaceFileListResponse(
        current_path=listing.current_path,
        entries=[_to_workspace_file_entry_response(entry) for entry in listing.entries],
    )


@router.post(
    "/{group_id}/files",
    response_model=WorkspaceFileUploadResponse,
    summary="Upload workspace files",
    description="Upload one or more files into one writable workspace-relative directory.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def upload_workspace_files(
    group_id: str,
    path: str = Form(default=""),
    files: list[UploadFile] = File(...),
    current_user: UserResponse = Depends(require_permission("groups", "write")),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    workspace_files: WorkspaceFileService = Depends(get_workspace_file_service),
) -> WorkspaceFileUploadResponse:
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    uploaded_paths: list[str] = []
    try:
        for upload in files:
            content = await upload.read()
            saved = workspace_files.save_upload(
                workspace.folder,
                path,
                upload.filename or "",
                content,
            )
            uploaded_paths.append(saved.path)
    except Exception as exc:
        raise _map_workspace_file_error(exc) from exc
    return WorkspaceFileUploadResponse(files=uploaded_paths)


@router.get(
    "/{group_id}/files/download/{file_path:path}",
    summary="Download a workspace file",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def download_workspace_file(
    group_id: str,
    file_path: str,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    workspace_files: WorkspaceFileService = Depends(get_workspace_file_service),
):
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        resolved = workspace_files.resolve_download_file(workspace.folder, file_path)
    except Exception as exc:
        raise _map_workspace_file_error(exc) from exc
    return FileResponse(
        resolved.absolute_path,
        media_type=resolved.media_type,
        filename=resolved.absolute_path.name,
    )


@router.get(
    "/{group_id}/files/preview/{file_path:path}",
    summary="Preview a workspace file",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def preview_workspace_file(
    group_id: str,
    file_path: str,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    workspace_files: WorkspaceFileService = Depends(get_workspace_file_service),
):
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        resolved = workspace_files.resolve_preview_file(workspace.folder, file_path)
    except Exception as exc:
        raise _map_workspace_file_error(exc) from exc
    return FileResponse(resolved.absolute_path, media_type=resolved.media_type)


@router.get(
    "/{group_id}/files/content/{file_path:path}",
    response_model=WorkspaceFileContentResponse,
    summary="Read workspace text file content",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def get_workspace_file_content(
    group_id: str,
    file_path: str,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    workspace_files: WorkspaceFileService = Depends(get_workspace_file_service),
) -> WorkspaceFileContentResponse:
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        content = workspace_files.read_text_content(workspace.folder, file_path)
    except Exception as exc:
        raise _map_workspace_file_error(exc) from exc
    return WorkspaceFileContentResponse(
        path=content.path,
        content=content.content,
        size=content.size,
    )


@router.put(
    "/{group_id}/files/content/{file_path:path}",
    response_model=WorkspaceFileContentResponse,
    summary="Write workspace text file content",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def put_workspace_file_content(
    group_id: str,
    file_path: str,
    request: UpdateWorkspaceFileContentRequest,
    current_user: UserResponse = Depends(require_permission("groups", "write")),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    workspace_files: WorkspaceFileService = Depends(get_workspace_file_service),
) -> WorkspaceFileContentResponse:
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        content = workspace_files.write_text_content(workspace.folder, file_path, request.content)
    except Exception as exc:
        raise _map_workspace_file_error(exc) from exc
    return WorkspaceFileContentResponse(
        path=content.path,
        content=content.content,
        size=content.size,
    )


@router.delete(
    "/{group_id}/files/{file_path:path}",
    response_model=DeleteWorkspaceFileResponse,
    summary="Delete workspace file or directory",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def delete_workspace_file(
    group_id: str,
    file_path: str,
    current_user: UserResponse = Depends(require_permission("groups", "write")),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    workspace_files: WorkspaceFileService = Depends(get_workspace_file_service),
) -> DeleteWorkspaceFileResponse:
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        workspace_files.delete_path(workspace.folder, file_path)
    except Exception as exc:
        raise _map_workspace_file_error(exc) from exc
    return DeleteWorkspaceFileResponse(status="deleted")


__all__ = [
    "get_group_registry_service",
    "get_workspace_file_service",
    "router",
]
