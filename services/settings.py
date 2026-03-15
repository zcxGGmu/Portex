"""Filesystem-backed settings service for user and global configuration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Literal

from infra.exec.security import validate_path


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SETTINGS_DIRNAME = "settings"
USERS_DIRNAME = "users"
GLOBAL_DIRNAME = "global"
MAX_SETTINGS_FILE_SIZE_BYTES = 256 * 1024
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

_PROVIDER_FILENAME = "provider.json"
_CHANNELS_FILENAME = "channels.json"
_REGISTRATION_FILENAME = "registration.json"
_APPEARANCE_FILENAME = "appearance.json"
_SYSTEM_FILENAME = "system.json"

ExecutionMode = Literal["openai", "host", "container"]


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    enabled: bool
    base_url: str
    default_model: str
    has_api_key: bool
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class ChannelsConfig:
    feishu_enabled: bool
    feishu_app_id: str
    feishu_has_app_secret: bool
    feishu_has_encrypt_key: bool
    feishu_has_verification_token: bool
    telegram_enabled: bool
    telegram_has_bot_token: bool
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class RegistrationPolicyConfig:
    allow_registration: bool
    require_invite_code: bool
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class AppearanceConfig:
    app_name: str
    ai_name: str
    ai_avatar_emoji: str
    ai_avatar_color: str
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class SystemSettingsConfig:
    default_execution_mode: ExecutionMode
    allow_host_execution: bool
    updated_at: datetime | None


class SettingsService:
    """Manage user-owned and system-owned settings stored in local JSON files."""

    def __init__(
        self,
        *,
        data_dir: str | Path | None = None,
        max_file_size_bytes: int = MAX_SETTINGS_FILE_SIZE_BYTES,
    ) -> None:
        root = Path(data_dir or DATA_DIR).expanduser().resolve()
        self._settings_root = (root / SETTINGS_DIRNAME).resolve()
        self._users_root = (self._settings_root / USERS_DIRNAME).resolve()
        self._global_root = (self._settings_root / GLOBAL_DIRNAME).resolve()
        self._users_root.mkdir(parents=True, exist_ok=True)
        self._global_root.mkdir(parents=True, exist_ok=True)
        self._max_file_size_bytes = max_file_size_bytes

    async def get_provider_config(self, user_id: str) -> ProviderConfig:
        return await asyncio.to_thread(self._get_provider_config, user_id)

    async def update_provider_config(
        self,
        user_id: str,
        *,
        enabled: bool,
        base_url: str,
        default_model: str,
        api_key: str | None = None,
    ) -> ProviderConfig:
        return await asyncio.to_thread(
            self._update_provider_config,
            user_id,
            enabled,
            base_url,
            default_model,
            api_key,
        )

    async def get_channels_config(self, user_id: str) -> ChannelsConfig:
        return await asyncio.to_thread(self._get_channels_config, user_id)

    async def update_channels_config(
        self,
        user_id: str,
        *,
        feishu_enabled: bool,
        feishu_app_id: str,
        feishu_app_secret: str,
        feishu_encrypt_key: str,
        feishu_verification_token: str,
        telegram_enabled: bool,
        telegram_bot_token: str,
    ) -> ChannelsConfig:
        return await asyncio.to_thread(
            self._update_channels_config,
            user_id,
            feishu_enabled,
            feishu_app_id,
            feishu_app_secret,
            feishu_encrypt_key,
            feishu_verification_token,
            telegram_enabled,
            telegram_bot_token,
        )

    async def get_registration_policy(self) -> RegistrationPolicyConfig:
        return await asyncio.to_thread(self._get_registration_policy)

    async def update_registration_policy(
        self,
        *,
        allow_registration: bool,
        require_invite_code: bool,
    ) -> RegistrationPolicyConfig:
        return await asyncio.to_thread(
            self._update_registration_policy,
            allow_registration,
            require_invite_code,
        )

    async def get_appearance_config(self) -> AppearanceConfig:
        return await asyncio.to_thread(self._get_appearance_config)

    async def update_appearance_config(
        self,
        *,
        app_name: str,
        ai_name: str,
        ai_avatar_emoji: str,
        ai_avatar_color: str,
    ) -> AppearanceConfig:
        return await asyncio.to_thread(
            self._update_appearance_config,
            app_name,
            ai_name,
            ai_avatar_emoji,
            ai_avatar_color,
        )

    async def get_system_settings(self) -> SystemSettingsConfig:
        return await asyncio.to_thread(self._get_system_settings)

    async def update_system_settings(
        self,
        *,
        default_execution_mode: str,
        allow_host_execution: bool,
    ) -> SystemSettingsConfig:
        return await asyncio.to_thread(
            self._update_system_settings,
            default_execution_mode,
            allow_host_execution,
        )

    def _get_provider_config(self, user_id: str) -> ProviderConfig:
        user_root = self._user_root(user_id)
        payload = self._read_json(
            self._provider_file(user_id),
            default_payload={
                "enabled": False,
                "base_url": "",
                "default_model": "",
                "api_key": "",
                "updated_at": None,
            },
            root=user_root,
        )
        return self._provider_from_payload(payload)

    def _update_provider_config(
        self,
        user_id: str,
        enabled: bool,
        base_url: str,
        default_model: str,
        api_key: str | None,
    ) -> ProviderConfig:
        user_root = self._user_root(user_id)
        current_payload = self._read_json(
            self._provider_file(user_id),
            default_payload={
                "enabled": False,
                "base_url": "",
                "default_model": "",
                "api_key": "",
                "updated_at": None,
            },
            root=user_root,
        )
        next_api_key = current_payload.get("api_key", "")
        if not isinstance(next_api_key, str):
            next_api_key = ""
        if api_key is not None:
            next_api_key = api_key.strip()

        payload = {
            "enabled": bool(enabled),
            "base_url": (base_url or "").strip(),
            "default_model": (default_model or "").strip(),
            "api_key": next_api_key,
            "updated_at": self._iso_datetime(datetime.now(timezone.utc)),
        }
        self._write_json(self._provider_file(user_id), payload=payload, root=user_root)
        return self._provider_from_payload(payload)

    def _get_channels_config(self, user_id: str) -> ChannelsConfig:
        user_root = self._user_root(user_id)
        payload = self._read_json(
            self._channels_file(user_id),
            default_payload={
                "feishu_enabled": False,
                "feishu_app_id": "",
                "feishu_app_secret": "",
                "feishu_encrypt_key": "",
                "feishu_verification_token": "",
                "telegram_enabled": False,
                "telegram_bot_token": "",
                "updated_at": None,
            },
            root=user_root,
        )
        return self._channels_from_payload(payload)

    def _update_channels_config(
        self,
        user_id: str,
        feishu_enabled: bool,
        feishu_app_id: str,
        feishu_app_secret: str,
        feishu_encrypt_key: str,
        feishu_verification_token: str,
        telegram_enabled: bool,
        telegram_bot_token: str,
    ) -> ChannelsConfig:
        user_root = self._user_root(user_id)
        payload = {
            "feishu_enabled": bool(feishu_enabled),
            "feishu_app_id": (feishu_app_id or "").strip(),
            "feishu_app_secret": (feishu_app_secret or "").strip(),
            "feishu_encrypt_key": (feishu_encrypt_key or "").strip(),
            "feishu_verification_token": (feishu_verification_token or "").strip(),
            "telegram_enabled": bool(telegram_enabled),
            "telegram_bot_token": (telegram_bot_token or "").strip(),
            "updated_at": self._iso_datetime(datetime.now(timezone.utc)),
        }
        self._write_json(self._channels_file(user_id), payload=payload, root=user_root)
        return self._channels_from_payload(payload)

    def _get_registration_policy(self) -> RegistrationPolicyConfig:
        payload = self._read_json(
            self._registration_file(),
            default_payload={
                "allow_registration": True,
                "require_invite_code": False,
                "updated_at": None,
            },
            root=self._global_root,
        )
        return RegistrationPolicyConfig(
            allow_registration=self._as_bool(payload.get("allow_registration"), default=True),
            require_invite_code=self._as_bool(payload.get("require_invite_code"), default=False),
            updated_at=self._parse_datetime(payload.get("updated_at")),
        )

    def _update_registration_policy(
        self,
        allow_registration: bool,
        require_invite_code: bool,
    ) -> RegistrationPolicyConfig:
        payload = {
            "allow_registration": bool(allow_registration),
            "require_invite_code": bool(require_invite_code),
            "updated_at": self._iso_datetime(datetime.now(timezone.utc)),
        }
        self._write_json(self._registration_file(), payload=payload, root=self._global_root)
        return RegistrationPolicyConfig(
            allow_registration=payload["allow_registration"],
            require_invite_code=payload["require_invite_code"],
            updated_at=self._parse_datetime(payload["updated_at"]),
        )

    def _get_appearance_config(self) -> AppearanceConfig:
        payload = self._read_json(
            self._appearance_file(),
            default_payload={
                "app_name": "Portex",
                "ai_name": "Portex",
                "ai_avatar_emoji": "🤖",
                "ai_avatar_color": "#0ea5e9",
                "updated_at": None,
            },
            root=self._global_root,
        )
        return AppearanceConfig(
            app_name=self._as_string(payload.get("app_name")),
            ai_name=self._as_string(payload.get("ai_name")),
            ai_avatar_emoji=self._as_string(payload.get("ai_avatar_emoji")),
            ai_avatar_color=self._as_string(payload.get("ai_avatar_color")),
            updated_at=self._parse_datetime(payload.get("updated_at")),
        )

    def _update_appearance_config(
        self,
        app_name: str,
        ai_name: str,
        ai_avatar_emoji: str,
        ai_avatar_color: str,
    ) -> AppearanceConfig:
        payload = {
            "app_name": (app_name or "").strip() or "Portex",
            "ai_name": (ai_name or "").strip() or "Portex",
            "ai_avatar_emoji": (ai_avatar_emoji or "").strip() or "🤖",
            "ai_avatar_color": (ai_avatar_color or "").strip() or "#0ea5e9",
            "updated_at": self._iso_datetime(datetime.now(timezone.utc)),
        }
        self._write_json(self._appearance_file(), payload=payload, root=self._global_root)
        return AppearanceConfig(
            app_name=payload["app_name"],
            ai_name=payload["ai_name"],
            ai_avatar_emoji=payload["ai_avatar_emoji"],
            ai_avatar_color=payload["ai_avatar_color"],
            updated_at=self._parse_datetime(payload["updated_at"]),
        )

    def _get_system_settings(self) -> SystemSettingsConfig:
        payload = self._read_json(
            self._system_file(),
            default_payload={
                "default_execution_mode": "openai",
                "allow_host_execution": False,
                "updated_at": None,
            },
            root=self._global_root,
        )
        mode = self._normalize_execution_mode(payload.get("default_execution_mode"))
        return SystemSettingsConfig(
            default_execution_mode=mode,
            allow_host_execution=self._as_bool(payload.get("allow_host_execution"), default=False),
            updated_at=self._parse_datetime(payload.get("updated_at")),
        )

    def _update_system_settings(
        self,
        default_execution_mode: str,
        allow_host_execution: bool,
    ) -> SystemSettingsConfig:
        mode = self._normalize_execution_mode(default_execution_mode)
        payload = {
            "default_execution_mode": mode,
            "allow_host_execution": bool(allow_host_execution),
            "updated_at": self._iso_datetime(datetime.now(timezone.utc)),
        }
        self._write_json(self._system_file(), payload=payload, root=self._global_root)
        return SystemSettingsConfig(
            default_execution_mode=mode,
            allow_host_execution=payload["allow_host_execution"],
            updated_at=self._parse_datetime(payload["updated_at"]),
        )

    def _provider_file(self, user_id: str) -> Path:
        return self._user_root(user_id) / _PROVIDER_FILENAME

    def _channels_file(self, user_id: str) -> Path:
        return self._user_root(user_id) / _CHANNELS_FILENAME

    def _registration_file(self) -> Path:
        return self._global_root / _REGISTRATION_FILENAME

    def _appearance_file(self) -> Path:
        return self._global_root / _APPEARANCE_FILENAME

    def _system_file(self) -> Path:
        return self._global_root / _SYSTEM_FILENAME

    def _user_root(self, user_id: str) -> Path:
        safe_user_id = self._validate_segment(user_id, label="user id")
        user_root = self._users_root / safe_user_id
        if not validate_path(user_root.resolve(strict=False), [self._users_root]):
            raise ValueError("symlink traversal detected")
        user_root.mkdir(parents=True, exist_ok=True)
        return user_root

    def _validate_segment(self, value: str, *, label: str) -> str:
        normalized = (value or "").strip()
        if not _SAFE_SEGMENT.fullmatch(normalized):
            raise ValueError(f"invalid {label}")
        return normalized

    def _read_json(self, path: Path, *, default_payload: dict[str, Any], root: Path) -> dict[str, Any]:
        self._ensure_safe_path(path, root)
        if not path.exists():
            return dict(default_payload)

        stats = path.stat()
        if stats.st_size > self._max_file_size_bytes:
            raise ValueError("settings file exceeds size limit")

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("invalid settings file") from exc

        if not isinstance(payload, dict):
            raise ValueError("invalid settings file")
        merged = dict(default_payload)
        merged.update(payload)
        return merged

    def _write_json(self, path: Path, *, payload: dict[str, Any], root: Path) -> None:
        self._ensure_safe_path(path, root)
        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        if len(encoded.encode("utf-8")) > self._max_file_size_bytes:
            raise ValueError("settings file exceeds size limit")

        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(encoded + "\n", encoding="utf-8")
        tmp_path.replace(path)

    def _ensure_safe_path(self, path: Path, root: Path) -> None:
        if not validate_path(path.resolve(strict=False), [root]):
            raise ValueError("symlink traversal detected")

    def _provider_from_payload(self, payload: dict[str, Any]) -> ProviderConfig:
        api_key = payload.get("api_key")
        if api_key is None:
            api_key = ""
        if not isinstance(api_key, str):
            raise ValueError("invalid settings file")

        return ProviderConfig(
            enabled=self._as_bool(payload.get("enabled"), default=False),
            base_url=self._as_string(payload.get("base_url")),
            default_model=self._as_string(payload.get("default_model")),
            has_api_key=bool(api_key.strip()),
            updated_at=self._parse_datetime(payload.get("updated_at")),
        )

    def _channels_from_payload(self, payload: dict[str, Any]) -> ChannelsConfig:
        feishu_secret = self._as_string(payload.get("feishu_app_secret"))
        feishu_encrypt_key = self._as_string(payload.get("feishu_encrypt_key"))
        feishu_verification = self._as_string(payload.get("feishu_verification_token"))
        telegram_token = self._as_string(payload.get("telegram_bot_token"))

        return ChannelsConfig(
            feishu_enabled=self._as_bool(payload.get("feishu_enabled"), default=False),
            feishu_app_id=self._as_string(payload.get("feishu_app_id")),
            feishu_has_app_secret=bool(feishu_secret),
            feishu_has_encrypt_key=bool(feishu_encrypt_key),
            feishu_has_verification_token=bool(feishu_verification),
            telegram_enabled=self._as_bool(payload.get("telegram_enabled"), default=False),
            telegram_has_bot_token=bool(telegram_token),
            updated_at=self._parse_datetime(payload.get("updated_at")),
        )

    def _normalize_execution_mode(self, value: object) -> ExecutionMode:
        if not isinstance(value, str):
            raise ValueError("invalid execution mode")
        normalized = value.strip().lower()
        if normalized not in {"openai", "host", "container"}:
            raise ValueError("invalid execution mode")
        return normalized  # type: ignore[return-value]

    def _as_bool(self, value: object, *, default: bool) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        raise ValueError("invalid settings file")

    def _as_string(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        raise ValueError("invalid settings file")

    def _parse_datetime(self, value: object) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("invalid settings file")
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("invalid settings file") from exc

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _iso_datetime(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat()


settings_service = SettingsService()


__all__ = [
    "AppearanceConfig",
    "ChannelsConfig",
    "MAX_SETTINGS_FILE_SIZE_BYTES",
    "ProviderConfig",
    "RegistrationPolicyConfig",
    "SettingsService",
    "SystemSettingsConfig",
    "settings_service",
]
