"""Group routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_user, require_permission
from domain.models.group_member import GroupMember
from domain.schemas import (
    CreateGroupMemberRequest,
    GroupListResponse,
    GroupMemberListResponse,
    GroupMemberResponse,
    GroupSummaryResponse,
)
from services.auth import AuthUser, auth_service
from services.group_member_service import group_member_service

router = APIRouter(prefix="/groups", tags=["groups"])


def _to_group_member_response(member: GroupMember) -> GroupMemberResponse:
    return GroupMemberResponse(
        group_id=member.group_jid,
        user_id=member.user_id,
        role=member.role,
        joined_at=member.joined_at,
    )


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


@router.get("", response_model=GroupListResponse)
async def list_groups(
    current_user: AuthUser = Depends(get_current_user),
) -> GroupListResponse:
    _ = current_user
    return GroupListResponse(
        groups=[GroupSummaryResponse(group_id="group-demo", name="Demo Group")]
    )


@router.get("/{group_id}/members", response_model=GroupMemberListResponse)
async def list_group_members(
    group_id: str,
    current_user: AuthUser = Depends(require_permission("groups", "read")),
) -> GroupMemberListResponse:
    _require_group_membership(group_id, current_user)
    members = group_member_service.list_members(group_id)
    return GroupMemberListResponse(
        members=[_to_group_member_response(member) for member in members]
    )


@router.post("/{group_id}/members", response_model=GroupMemberResponse)
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


@router.delete("/{group_id}/members/{user_id}")
async def remove_group_member(
    group_id: str,
    user_id: str,
    current_user: AuthUser = Depends(require_permission("groups", "write")),
) -> dict[str, str]:
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
    return {"status": "removed"}


__all__ = ["router"]
