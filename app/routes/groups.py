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
from services.group_member_service import group_member_service
from services.group_registry import GroupRegistryService

router = APIRouter(prefix="/groups", tags=["groups"])


def _to_group_member_response(member: GroupMember) -> GroupMemberResponse:
    return GroupMemberResponse(
        group_id=member.group_jid,
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


def _is_group_visible_to_user(group, current_user: AuthUser) -> bool:
    if not bool(getattr(group, "is_home", False)):
        return True
    if current_user.role == "owner":
        return group.folder == "main"
    return getattr(group, "created_by", None) == current_user.id


def _require_group_membership(group_id: str, current_user: AuthUser) -> None:
    if group_member_service.get_member(group_id, current_user.id) is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission denied",
        )


def _require_group_owner(group_id: str, current_user: AuthUser) -> None:
    if group_member_service.get_member_role(group_id, current_user.id) != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission denied",
        )


def _ensure_owner_role_change_supported(
    group_id: str,
    user_id: str,
    requested_role: str,
) -> None:
    existing_member = group_member_service.get_member(group_id, user_id)
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
            if _is_group_visible_to_user(group, current_user)
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
) -> GroupMemberListResponse:
    _require_group_membership(group_id, current_user)
    members = group_member_service.list_members(group_id)
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
) -> GroupMemberResponse:
    _require_group_owner(group_id, current_user)

    if auth_service.get_user_by_id(request.user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user not found",
        )
    _ensure_owner_role_change_supported(group_id, request.user_id, request.role)

    try:
        member = group_member_service.add_member(
            group_id,
            request.user_id,
            role=request.role,
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
    current_user: AuthUser = Depends(require_permission("groups", "write")),
) -> DeleteGroupMemberResponse:
    _require_group_owner(group_id, current_user)

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="group owner cannot remove self",
        )

    removed = group_member_service.remove_member(group_id, user_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group member not found",
        )
    return DeleteGroupMemberResponse(status="removed")


__all__ = ["get_group_registry_service", "router"]
