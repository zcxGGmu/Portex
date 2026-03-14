"""Skills-management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_user
from app.openapi import openapi_error_responses
from domain.schemas import (
    DeleteSkillResponse,
    SkillDetailResponse,
    SkillListResponse,
    SkillSummaryResponse,
    UpdateSkillRequest,
    UpdateSkillStateRequest,
    UserResponse,
)
from services.skills import SkillDetail, SkillEntry, SkillsService, skills_service

router = APIRouter(prefix="/skills", tags=["skills"])


def get_skills_service() -> SkillsService:
    return skills_service


def _map_skills_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, (ValueError, IsADirectoryError, NotADirectoryError)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="skill operation failed",
    )


def _to_skill_summary_response(item: SkillEntry) -> SkillSummaryResponse:
    return SkillSummaryResponse(
        skill_id=item.skill_id,
        enabled=item.enabled,
        updated_at=item.updated_at,
        size=item.size,
    )


def _to_skill_detail_response(item: SkillDetail) -> SkillDetailResponse:
    return SkillDetailResponse(
        skill_id=item.skill_id,
        enabled=item.enabled,
        updated_at=item.updated_at,
        size=item.size,
        content=item.content,
    )


@router.get(
    "",
    response_model=SkillListResponse,
    summary="List skills",
    description="List the current user's skills from the user-local skills root.",
    responses=openapi_error_responses(status.HTTP_401_UNAUTHORIZED),
)
async def list_skills(
    current_user: UserResponse = Depends(get_current_user),
    service: SkillsService = Depends(get_skills_service),
) -> SkillListResponse:
    try:
        items = await service.list_user_skills(current_user.id)
    except Exception as exc:
        raise _map_skills_error(exc) from exc
    return SkillListResponse(skills=[_to_skill_summary_response(item) for item in items])


@router.get(
    "/{skill_id}",
    response_model=SkillDetailResponse,
    summary="Get skill detail",
    description="Read one skill file and return its current state and content.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def get_skill(
    skill_id: str,
    current_user: UserResponse = Depends(get_current_user),
    service: SkillsService = Depends(get_skills_service),
) -> SkillDetailResponse:
    try:
        detail = await service.get_user_skill(current_user.id, skill_id)
    except Exception as exc:
        raise _map_skills_error(exc) from exc
    return _to_skill_detail_response(detail)


@router.put(
    "/{skill_id}",
    response_model=SkillDetailResponse,
    summary="Update skill content",
    description="Create or update one user-owned skill content file.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
    ),
)
async def put_skill(
    skill_id: str,
    request: UpdateSkillRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: SkillsService = Depends(get_skills_service),
) -> SkillDetailResponse:
    try:
        detail = await service.upsert_user_skill(current_user.id, skill_id, request.content)
    except Exception as exc:
        raise _map_skills_error(exc) from exc
    return _to_skill_detail_response(detail)


@router.patch(
    "/{skill_id}/state",
    response_model=SkillDetailResponse,
    summary="Update skill state",
    description="Enable or disable one user-owned skill without changing its content.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def patch_skill_state(
    skill_id: str,
    request: UpdateSkillStateRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: SkillsService = Depends(get_skills_service),
) -> SkillDetailResponse:
    try:
        detail = await service.set_user_skill_enabled(
            current_user.id,
            skill_id,
            enabled=request.enabled,
        )
    except Exception as exc:
        raise _map_skills_error(exc) from exc
    return _to_skill_detail_response(detail)


@router.delete(
    "/{skill_id}",
    response_model=DeleteSkillResponse,
    summary="Delete skill",
    description="Delete one user-owned skill directory and its skill file.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def delete_skill(
    skill_id: str,
    current_user: UserResponse = Depends(get_current_user),
    service: SkillsService = Depends(get_skills_service),
) -> DeleteSkillResponse:
    try:
        await service.delete_user_skill(current_user.id, skill_id)
    except Exception as exc:
        raise _map_skills_error(exc) from exc
    return DeleteSkillResponse(status="deleted")


__all__ = ["get_skills_service", "router"]
