"""Group routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import get_current_user, require_permission
from app.openapi import openapi_error_responses
from domain.models.group_member import GroupMember
from domain.schemas import (
    ConversationSlotListResponse,
    ConversationSlotResponse,
    CreateConversationSlotRequest,
    CreateGroupMemberRequest,
    CreateGroupRequest,
    DeleteGroupMemberResponse,
    GroupIMBindingListResponse,
    GroupIMBindingResponse,
    GroupListResponse,
    GroupMemberListResponse,
    GroupMemberResponse,
    GroupSummaryResponse,
    UpdateGroupRequest,
)
from infra.db.database import get_db
from services.auth import AuthUser, auth_service
from services.conversation_slot_service import ConversationSlotService
from services.group_member_service import GroupMemberService
from services.group_registry import (
    GroupIMBindingStatus,
    GroupRegistryConflictError,
    GroupRegistryService,
)

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


def _to_conversation_slot_response(slot) -> ConversationSlotResponse:
    return ConversationSlotResponse(
        group_id=slot.workspace_folder,
        slot_id=slot.slot_id,
        title=slot.title,
        created_by=slot.created_by,
        created_at=slot.created_at,
    )


def _channel_from_im_jid(im_jid: str) -> str:
    if im_jid.startswith("telegram:"):
        return "telegram"
    return "feishu"


def _to_group_im_binding_response(binding: GroupIMBindingStatus) -> GroupIMBindingResponse:
    return GroupIMBindingResponse(
        im_jid=binding.im_jid,
        name=binding.name,
        channel=binding.channel,
        fallback_group_id=binding.fallback_group_id,
        binding_state=binding.binding_state,
        target_group_id=binding.target_group_id,
        target_group_name=binding.target_group_name,
        bound_to_current_group=binding.bound_to_current_group,
    )


def get_group_registry_service(
    db: AsyncSession = Depends(get_db),
) -> GroupRegistryService:
    return GroupRegistryService(db=db)


def get_group_member_service(
    db: AsyncSession = Depends(get_db),
) -> GroupMemberService:
    return GroupMemberService(db=db)


def get_conversation_slot_service(
    db: AsyncSession = Depends(get_db),
) -> ConversationSlotService:
    return ConversationSlotService(db=db)


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


async def _require_accessible_workspace(
    *,
    group_id: str,
    current_user: AuthUser,
    group_registry: GroupRegistryService,
):
    workspace = await _resolve_workspace_by_group_id(group_id, group_registry)
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


def _require_owner_binding_role(current_user: AuthUser) -> None:
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission denied",
        )


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
    description="Return the current minimal group list visible to the authenticated user.",
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
                and await group_registry.user_can_access_group(
                    user_id=current_user.id,
                    user_role=current_user.role,
                    group=group,
                )
            )
        ]
    )


@router.post(
    "",
    response_model=GroupSummaryResponse,
    summary="Create a workspace",
    description="Create a new shared canonical workspace under the current `/groups` surface.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_409_CONFLICT,
    ),
)
async def create_group(
    request: CreateGroupRequest,
    current_user: AuthUser = Depends(require_permission("groups", "write")),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
) -> GroupSummaryResponse:
    try:
        workspace = await group_registry.create_workspace(
            folder=request.group_id,
            name=request.name,
            created_by=current_user.id,
        )
    except GroupRegistryConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return _to_group_summary_response(workspace)


@router.patch(
    "/{group_id}",
    response_model=GroupSummaryResponse,
    summary="Rename a workspace",
    description="Rename an existing shared canonical workspace without changing its folder identity.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def update_group(
    group_id: str,
    request: UpdateGroupRequest,
    current_user: AuthUser = Depends(require_permission("groups", "write")),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
) -> GroupSummaryResponse:
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    if workspace.is_home:
        try:
            await group_registry.rename_workspace(workspace, name=request.name)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
    if not await group_registry.user_can_manage_members(user_id=current_user.id, group=workspace):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission denied",
        )
    try:
        renamed = await group_registry.rename_workspace(workspace, name=request.name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return _to_group_summary_response(renamed)


@router.get(
    "/{group_id}/slots",
    response_model=ConversationSlotListResponse,
    summary="List workspace slots",
    description="List persistent conversation slots under the requested accessible workspace.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def list_group_slots(
    group_id: str,
    current_user: AuthUser = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    slot_service: ConversationSlotService = Depends(get_conversation_slot_service),
) -> ConversationSlotListResponse:
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    slots = await slot_service.list_slots(workspace.folder)
    return ConversationSlotListResponse(
        slots=[_to_conversation_slot_response(slot) for slot in slots]
    )


@router.post(
    "/{group_id}/slots",
    response_model=ConversationSlotResponse,
    summary="Create a workspace slot",
    description="Create a new persistent conversation slot under an accessible workspace.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def create_group_slot(
    group_id: str,
    request: CreateConversationSlotRequest,
    current_user: AuthUser = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    slot_service: ConversationSlotService = Depends(get_conversation_slot_service),
) -> ConversationSlotResponse:
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        slot = await slot_service.create_slot(
            workspace_folder=workspace.folder,
            slot_id=request.slot_id,
            title=request.title,
            created_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return _to_conversation_slot_response(slot)


@router.get(
    "/{group_id}/bindings/im",
    response_model=GroupIMBindingListResponse,
    summary="List workspace IM bindings",
    description="List raw IM endpoint rows and their current binding status for the requested workspace.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def list_group_im_bindings(
    group_id: str,
    current_user: AuthUser = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
) -> GroupIMBindingListResponse:
    _require_owner_binding_role(current_user)
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    bindings = await group_registry.list_im_endpoint_bindings(workspace)
    return GroupIMBindingListResponse(
        bindings=[_to_group_im_binding_response(binding) for binding in bindings]
    )


@router.put(
    "/{group_id}/bindings/im/{im_jid:path}",
    response_model=GroupIMBindingResponse,
    summary="Bind an IM endpoint",
    description="Bind a raw IM endpoint row to the requested workspace main conversation.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
    ),
)
async def bind_group_im_endpoint(
    group_id: str,
    im_jid: str,
    current_user: AuthUser = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
) -> GroupIMBindingResponse:
    _require_owner_binding_role(current_user)
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        endpoint = await group_registry.bind_im_endpoint_to_workspace(workspace, im_jid=im_jid)
    except GroupRegistryConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return _to_group_im_binding_response(
        GroupIMBindingStatus(
            im_jid=endpoint.jid,
            name=endpoint.name,
            channel=_channel_from_im_jid(endpoint.jid),
            fallback_group_id=endpoint.folder,
            binding_state="bound",
            target_group_id=workspace.folder,
            target_group_name=workspace.name,
            bound_to_current_group=True,
        )
    )


@router.delete(
    "/{group_id}/bindings/im/{im_jid:path}",
    response_model=GroupIMBindingResponse,
    summary="Unbind an IM endpoint",
    description="Clear the current workspace binding for the requested raw IM endpoint row.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def unbind_group_im_endpoint(
    group_id: str,
    im_jid: str,
    current_user: AuthUser = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
) -> GroupIMBindingResponse:
    _require_owner_binding_role(current_user)
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        endpoint = await group_registry.unbind_im_endpoint_from_workspace(workspace, im_jid=im_jid)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return _to_group_im_binding_response(
        GroupIMBindingStatus(
            im_jid=endpoint.jid,
            name=endpoint.name,
            channel=_channel_from_im_jid(endpoint.jid),
            fallback_group_id=endpoint.folder,
            binding_state="unbound",
            target_group_id=None,
            target_group_name=None,
            bound_to_current_group=False,
        )
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
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
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
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
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
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
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


__all__ = [
    "get_conversation_slot_service",
    "get_group_member_service",
    "get_group_registry_service",
    "router",
]
