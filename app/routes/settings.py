"""Settings and configuration management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_user, require_permission
from app.openapi import openapi_error_responses
from domain.schemas import (
    SettingsAppearanceResponse,
    SettingsChannelsResponse,
    SettingsProviderResponse,
    SettingsRegistrationResponse,
    SettingsSystemResponse,
    UpdateSettingsAppearanceRequest,
    UpdateSettingsChannelsRequest,
    UpdateSettingsProviderRequest,
    UpdateSettingsRegistrationRequest,
    UpdateSettingsSystemRequest,
    UserResponse,
)
from services.settings import (
    AppearanceConfig,
    ChannelsConfig,
    ProviderConfig,
    RegistrationPolicyConfig,
    SettingsService,
    SystemSettingsConfig,
    settings_service,
)

router = APIRouter(prefix="/settings", tags=["settings"])


def get_settings_service() -> SettingsService:
    return settings_service


def _map_settings_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, (ValueError, IsADirectoryError, NotADirectoryError)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="settings operation failed",
    )


def _to_provider_response(item: ProviderConfig) -> SettingsProviderResponse:
    return SettingsProviderResponse(
        enabled=item.enabled,
        base_url=item.base_url,
        default_model=item.default_model,
        has_api_key=item.has_api_key,
        updated_at=item.updated_at,
    )


def _to_channels_response(item: ChannelsConfig) -> SettingsChannelsResponse:
    return SettingsChannelsResponse(
        feishu_enabled=item.feishu_enabled,
        feishu_app_id=item.feishu_app_id,
        feishu_has_app_secret=item.feishu_has_app_secret,
        feishu_has_encrypt_key=item.feishu_has_encrypt_key,
        feishu_has_verification_token=item.feishu_has_verification_token,
        telegram_enabled=item.telegram_enabled,
        telegram_has_bot_token=item.telegram_has_bot_token,
        updated_at=item.updated_at,
    )


def _to_registration_response(item: RegistrationPolicyConfig) -> SettingsRegistrationResponse:
    return SettingsRegistrationResponse(
        allow_registration=item.allow_registration,
        require_invite_code=item.require_invite_code,
        updated_at=item.updated_at,
    )


def _to_appearance_response(item: AppearanceConfig) -> SettingsAppearanceResponse:
    return SettingsAppearanceResponse(
        app_name=item.app_name,
        ai_name=item.ai_name,
        ai_avatar_emoji=item.ai_avatar_emoji,
        ai_avatar_color=item.ai_avatar_color,
        updated_at=item.updated_at,
    )


def _to_system_response(item: SystemSettingsConfig) -> SettingsSystemResponse:
    return SettingsSystemResponse(
        default_execution_mode=item.default_execution_mode,
        allow_host_execution=item.allow_host_execution,
        updated_at=item.updated_at,
    )


@router.get(
    "/provider",
    response_model=SettingsProviderResponse,
    summary="Get provider config",
    description="Read user-owned provider configuration for the current authenticated user.",
    responses=openapi_error_responses(status.HTTP_401_UNAUTHORIZED),
)
async def get_provider_config(
    current_user: UserResponse = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsProviderResponse:
    try:
        config = await service.get_provider_config(current_user.id)
    except Exception as exc:
        raise _map_settings_error(exc) from exc
    return _to_provider_response(config)


@router.put(
    "/provider",
    response_model=SettingsProviderResponse,
    summary="Update provider config",
    description="Create or update user-owned provider configuration for the current user.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
    ),
)
async def put_provider_config(
    request: UpdateSettingsProviderRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsProviderResponse:
    try:
        config = await service.update_provider_config(
            current_user.id,
            enabled=request.enabled,
            base_url=request.base_url,
            default_model=request.default_model,
            api_key=request.api_key,
        )
    except Exception as exc:
        raise _map_settings_error(exc) from exc
    return _to_provider_response(config)


@router.get(
    "/channels",
    response_model=SettingsChannelsResponse,
    summary="Get channels config",
    description="Read user-owned channel configuration for the current authenticated user.",
    responses=openapi_error_responses(status.HTTP_401_UNAUTHORIZED),
)
async def get_channels_config(
    current_user: UserResponse = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsChannelsResponse:
    try:
        config = await service.get_channels_config(current_user.id)
    except Exception as exc:
        raise _map_settings_error(exc) from exc
    return _to_channels_response(config)


@router.put(
    "/channels",
    response_model=SettingsChannelsResponse,
    summary="Update channels config",
    description="Create or update user-owned channel configuration for the current user.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
    ),
)
async def put_channels_config(
    request: UpdateSettingsChannelsRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsChannelsResponse:
    try:
        config = await service.update_channels_config(
            current_user.id,
            feishu_enabled=request.feishu_enabled,
            feishu_app_id=request.feishu_app_id,
            feishu_app_secret=request.feishu_app_secret,
            feishu_encrypt_key=request.feishu_encrypt_key,
            feishu_verification_token=request.feishu_verification_token,
            telegram_enabled=request.telegram_enabled,
            telegram_bot_token=request.telegram_bot_token,
        )
    except Exception as exc:
        raise _map_settings_error(exc) from exc
    return _to_channels_response(config)


@router.get(
    "/registration",
    response_model=SettingsRegistrationResponse,
    summary="Get registration policy",
    description="Read system registration policy. Requires settings read permission.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def get_registration_policy(
    current_user: UserResponse = Depends(require_permission("settings", "read")),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsRegistrationResponse:
    _ = current_user
    try:
        config = await service.get_registration_policy()
    except Exception as exc:
        raise _map_settings_error(exc) from exc
    return _to_registration_response(config)


@router.put(
    "/registration",
    response_model=SettingsRegistrationResponse,
    summary="Update registration policy",
    description="Update system registration policy. Requires settings write permission.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def put_registration_policy(
    request: UpdateSettingsRegistrationRequest,
    current_user: UserResponse = Depends(require_permission("settings", "write")),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsRegistrationResponse:
    _ = current_user
    try:
        config = await service.update_registration_policy(
            allow_registration=request.allow_registration,
            require_invite_code=request.require_invite_code,
        )
    except Exception as exc:
        raise _map_settings_error(exc) from exc
    return _to_registration_response(config)


@router.get(
    "/appearance",
    response_model=SettingsAppearanceResponse,
    summary="Get appearance settings",
    description="Read system appearance settings. Requires settings read permission.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def get_appearance_config(
    current_user: UserResponse = Depends(require_permission("settings", "read")),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsAppearanceResponse:
    _ = current_user
    try:
        config = await service.get_appearance_config()
    except Exception as exc:
        raise _map_settings_error(exc) from exc
    return _to_appearance_response(config)


@router.put(
    "/appearance",
    response_model=SettingsAppearanceResponse,
    summary="Update appearance settings",
    description="Update system appearance settings. Requires settings write permission.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def put_appearance_config(
    request: UpdateSettingsAppearanceRequest,
    current_user: UserResponse = Depends(require_permission("settings", "write")),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsAppearanceResponse:
    _ = current_user
    try:
        config = await service.update_appearance_config(
            app_name=request.app_name,
            ai_name=request.ai_name,
            ai_avatar_emoji=request.ai_avatar_emoji,
            ai_avatar_color=request.ai_avatar_color,
        )
    except Exception as exc:
        raise _map_settings_error(exc) from exc
    return _to_appearance_response(config)


@router.get(
    "/system",
    response_model=SettingsSystemResponse,
    summary="Get system settings",
    description="Read system execution settings. Requires settings read permission.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def get_system_settings(
    current_user: UserResponse = Depends(require_permission("settings", "read")),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsSystemResponse:
    _ = current_user
    try:
        config = await service.get_system_settings()
    except Exception as exc:
        raise _map_settings_error(exc) from exc
    return _to_system_response(config)


@router.put(
    "/system",
    response_model=SettingsSystemResponse,
    summary="Update system settings",
    description="Update system execution settings. Requires settings write permission.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def put_system_settings(
    request: UpdateSettingsSystemRequest,
    current_user: UserResponse = Depends(require_permission("settings", "write")),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsSystemResponse:
    _ = current_user
    try:
        config = await service.update_system_settings(
            default_execution_mode=request.default_execution_mode,
            allow_host_execution=request.allow_host_execution,
        )
    except Exception as exc:
        raise _map_settings_error(exc) from exc
    return _to_system_response(config)


__all__ = ["get_settings_service", "router"]
