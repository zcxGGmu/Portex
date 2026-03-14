"""Group routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import get_current_user, require_permission
from app.openapi import openapi_error_responses
from infra.db.database import get_db
from domain.models.group_member import GroupMember
from domain.schemas import (
    CreateGroupMemberRequest,
    DeleteGroupMemberResponse,
    GroupListResponse,
    GroupMemberListResponse,
    GroupMemberResponse,
    GroupSummaryResponse,
)
from services.auth import AuthUser, auth_service
from services.group_member_service import GroupMemberService
from services.group_registry import GroupRegistryService

router = APIRouter(prefix="/groups", tags=["groups"])


def _to_group_member_response(member: GroupMember) -> GroupMemberResponse:
    return GroupMemberResponse(
        group_id=member.group_folder,
        user_id=member.user_id,
        role=member.role,
        joined_at=member.joined_at,
    )


def _to_group_summary_response(group) -> GroupSummaryResponse:
    return GroupSummaryResponse(
        group_id=group.folder,
        name=group.name,
    )


def get_group_registry_service(
    db: AsyncSession = Depends(get_db),
) -> GroupRegistryService:
    return GroupRegistryService(db=db)


def get_group_member_service(
    db: AsyncSession = Depends(get_db),
) -> GroupMemberService:
    return GroupMemberService(db=db)


def _is_raw_im_endpoint(group) -> bool:
    jid = getattr(group, "jid", None)
    if not isinstance(jid, str):
        return False
    return jid.startswith("telegram:") or jid.startswith("feishu:")


async def _resolve_workspace_by_group_id(
    group_id: str,
    group_registry: GroupRegistryService,
):
    return await group_registry.get_web_workspace_by_folder(group_id)


async def _ensure_owner_role_change_supported(
    *,
    group_folder: str,
    user_id: str,
    requested_role: str,
    group_member_service: GroupMemberService,
) -> None:
    existing_member = await group_member_service.get_member(group_folder, user_id)
    if requested_role == "owner":
        if existing_member is None or existing_member.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="owner role changes are not supported",
            )
        return

    if existing_member is not None and existing_member.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="owner role changes are not supported",
        )


@router.get(
    "",
    response_model=GroupListResponse,
    summary="List groups",
    description=(
        "Return the current minimal group list visible to the authenticated user."
    ),
    responses=openapi_error_responses(status.HTTP_401_UNAUTHORIZED),
)
async def list_groups(
    current_user: AuthUser = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
) -> GroupListResponse:
    await group_registry.ensure_home_workspace(
        user_id=current_user.id,
        role=current_user.role,
        username=current_user.username,
    )
    return GroupListResponse(
        groups=[
            _to_group_summary_response(group)
            for group in await group_registry.list_registered_groups()
            if (
                isinstance(getattr(group, "jid", None), str)
                and group.jid.startswith("web:")
                and not _is_raw_im_endpoint(group)
                and (
                    (current_user.role == "owner" and getattr(group, "folder", None) == "main")
                    or await group_registry.user_can_access_group(
                        user_id=current_user.id,
                        group=group,
                    )
                )
            )
        ]
    )


@router.get(
    "/{group_id}/members",
    response_model=GroupMemberListResponse,
    summary="List group members",
    description=(
        "List members for a group. Group membership is required to read the current "
        "member list."
    ),
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def list_group_members(
    group_id: str,
    current_user: AuthUser = Depends(require_permission("groups", "read")),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    group_member_service: GroupMemberService = Depends(get_group_member_service),
) -> GroupMemberListResponse:
    workspace = await _resolve_workspace_by_group_id(group_id, group_registry)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group not found",
        )
    if not await group_registry.user_can_access_group(user_id=current_user.id, group=workspace):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group not found",
        )
    if workspace.is_home:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="home workspaces do not support member management",
        )

    members = await group_member_service.list_members(workspace.folder)
    return GroupMemberListResponse(
        members=[_to_group_member_response(member) for member in members]
    )


@router.post(
    "/{group_id}/members",
    response_model=GroupMemberResponse,
    summary="Add a group member",
    description=(
        "Add or update a group member. Only the group owner can write membership, "
        "and owner-role transfer or demotion is not supported."
    ),
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def add_group_member(
    group_id: str,
    request: CreateGroupMemberRequest,
    current_user: AuthUser = Depends(require_permission("groups", "write")),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    group_member_service: GroupMemberService = Depends(get_group_member_service),
) -> GroupMemberResponse:
    workspace = await _resolve_workspace_by_group_id(group_id, group_registry)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group not found",
        )
    if not await group_registry.user_can_access_group(user_id=current_user.id, group=workspace):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group not found",
        )
    if workspace.is_home:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="home workspaces do not support member management",
        )
    if not await group_registry.user_can_manage_members(user_id=current_user.id, group=workspace):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission denied",
        )

    if auth_service.get_user_by_id(request.user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user not found",
        )
    await _ensure_owner_role_change_supported(
        group_folder=workspace.folder,
        user_id=request.user_id,
        requested_role=request.role,
        group_member_service=group_member_service,
    )

    try:
        member = await group_member_service.add_member(
            workspace.folder,
            request.user_id,
            role=request.role,
            added_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return _to_group_member_response(member)


@router.delete(
    "/{group_id}/members/{user_id}",
    response_model=DeleteGroupMemberResponse,
    summary="Remove a group member",
    description=(
        "Remove a group member. Only the group owner can remove members, and the "
        "owner cannot remove themself."
    ),
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def remove_group_member(
    group_id: str,
    user_id: str,
    current_user: AuthUser = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    group_member_service: GroupMemberService = Depends(get_group_member_service),
) -> DeleteGroupMemberResponse:
    workspace = await _resolve_workspace_by_group_id(group_id, group_registry)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group not found",
        )
    if not await group_registry.user_can_access_group(user_id=current_user.id, group=workspace):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group not found",
        )
    if workspace.is_home:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="home workspaces do not support member management",
        )

    if user_id == current_user.id:
        current_role = await group_member_service.get_member_role(workspace.folder, current_user.id)
        if current_role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="group member not found",
            )
        if current_role == "owner":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="group owner cannot remove self",
            )
        removed = await group_member_service.remove_member(workspace.folder, user_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="group member not found",
            )
        return DeleteGroupMemberResponse(status="removed")

    if not await group_registry.user_can_manage_members(user_id=current_user.id, group=workspace):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission denied",
        )

    try:
        removed = await group_member_service.remove_member(workspace.folder, user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group member not found",
        )
    return DeleteGroupMemberResponse(status="removed")


__all__ = ["get_group_member_service", "get_group_registry_service", "router"]
