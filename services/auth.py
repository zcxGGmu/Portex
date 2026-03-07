"""In-memory authentication service used by API routes."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
import os
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import MissingBackendError, UnknownHashError


def _read_positive_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


DEFAULT_AUTH_SECRET = os.getenv("PORTEX_AUTH_SECRET", "portex-dev-secret")
DEFAULT_AUTH_ALGORITHM = os.getenv("PORTEX_AUTH_ALGORITHM", "HS256")
DEFAULT_ACCESS_TOKEN_EXPIRE_HOURS = _read_positive_int_env(
    "PORTEX_AUTH_ACCESS_TOKEN_EXPIRE_HOURS",
    24,
)


def _build_password_context() -> CryptContext:
    """Prefer bcrypt; safely fallback to pbkdf2_sha256 when bcrypt backend is missing."""
    preferred = CryptContext(schemes=["bcrypt"], deprecated="auto")
    try:
        probe_hash = preferred.hash("portex-password-probe")
        preferred.verify("portex-password-probe", probe_hash)
        return preferred
    except Exception:
        # Explicit fallback for environments where bcrypt backend is unavailable.
        return CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


_PWD_CONTEXT = _build_password_context()
_DEFAULT_ACCESS_TOKEN_EXPIRE_DELTA = timedelta(hours=DEFAULT_ACCESS_TOKEN_EXPIRE_HOURS)


def hash_password(password: str) -> str:
    return _PWD_CONTEXT.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _PWD_CONTEXT.verify(password, password_hash)
    except (MissingBackendError, UnknownHashError, ValueError):
        return False


def _encode_access_token(
    *,
    data: dict[str, Any],
    secret_key: str,
    algorithm: str,
    default_expires_delta: timedelta,
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    expire_at = datetime.now(timezone.utc) + (expires_delta or default_expires_delta)
    to_encode["exp"] = expire_at
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def _decode_access_token(*, token: str, secret_key: str, algorithm: str) -> str | None:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    except JWTError:
        return None

    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    return _encode_access_token(
        data=data,
        secret_key=DEFAULT_AUTH_SECRET,
        algorithm=DEFAULT_AUTH_ALGORITHM,
        default_expires_delta=_DEFAULT_ACCESS_TOKEN_EXPIRE_DELTA,
        expires_delta=expires_delta,
    )


def decode_access_token(token: str) -> str | None:
    return _decode_access_token(
        token=token,
        secret_key=DEFAULT_AUTH_SECRET,
        algorithm=DEFAULT_AUTH_ALGORITHM,
    )


@dataclass(frozen=True, slots=True)
class AuthUser:
    """Public user shape returned by the auth service."""

    id: str
    username: str
    role: str
    status: str
    avatar_emoji: str | None = None
    avatar_color: str | None = None
    ai_name: str | None = None
    ai_avatar_emoji: str | None = None
    must_change_password: bool = False
    last_login_at: datetime | None = None
    disable_reason: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class _UserRecord:
    user: AuthUser
    password_hash: str


class UserAlreadyExistsError(Exception):
    """Raised when trying to register an existing username."""


class UserNotFoundError(Exception):
    """Raised when an operation targets a missing user."""


class AuthService:
    """Minimal auth service for registration, login and token handling."""

    def __init__(
        self,
        *,
        secret_key: str,
        algorithm: str = DEFAULT_AUTH_ALGORITHM,
        access_token_expire_hours: int = DEFAULT_ACCESS_TOKEN_EXPIRE_HOURS,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expires_delta = timedelta(hours=access_token_expire_hours)
        self._users_by_username: dict[str, _UserRecord] = {}
        self._users_by_id: dict[str, AuthUser] = {}

    def register_user(
        self,
        username: str,
        password: str,
        *,
        role: str = "member",
    ) -> AuthUser:
        if username in self._users_by_username:
            raise UserAlreadyExistsError(username)

        user = AuthUser(
            id=uuid4().hex,
            username=username,
            role=role,
            status="active",
            avatar_emoji=None,
            avatar_color=None,
            ai_name=None,
            ai_avatar_emoji=None,
            must_change_password=False,
            last_login_at=None,
            disable_reason=None,
            notes=None,
        )
        record = _UserRecord(user=user, password_hash=hash_password(password))
        self._users_by_username[username] = record
        self._users_by_id[user.id] = user
        return user

    def list_users(self) -> list[AuthUser]:
        return sorted(self._users_by_id.values(), key=lambda user: user.username)

    def update_user(
        self,
        user_id: str,
        **changes: str | bool | None,
    ) -> AuthUser:
        current_user = self._users_by_id.get(user_id)
        if current_user is None:
            raise UserNotFoundError(user_id)

        allowed_fields = {
            "role",
            "status",
            "avatar_emoji",
            "avatar_color",
            "ai_name",
            "ai_avatar_emoji",
            "must_change_password",
            "disable_reason",
            "notes",
        }
        updated_fields = {
            field_name: field_value
            for field_name, field_value in changes.items()
            if field_name in allowed_fields
        }
        updated_user = replace(current_user, **updated_fields)
        record = self._users_by_username[updated_user.username]
        record.user = updated_user
        self._users_by_id[user_id] = updated_user
        return updated_user

    def authenticate_user(self, username: str, password: str) -> AuthUser | None:
        record = self._users_by_username.get(username)
        if record is None:
            return None
        if not verify_password(password, record.password_hash):
            return None
        return record.user

    def create_access_token(self, user_id: str) -> str:
        # Backward-compatible service API expected by existing routes/tests.
        return _encode_access_token(
            data={"sub": user_id},
            secret_key=self._secret_key,
            algorithm=self._algorithm,
            default_expires_delta=self._access_token_expires_delta,
        )

    def decode_access_token(self, token: str) -> str | None:
        return _decode_access_token(
            token=token,
            secret_key=self._secret_key,
            algorithm=self._algorithm,
        )

    def get_user_by_id(self, user_id: str) -> AuthUser | None:
        return self._users_by_id.get(user_id)

    def reset(self) -> None:
        self._users_by_username.clear()
        self._users_by_id.clear()


auth_service = AuthService(secret_key=DEFAULT_AUTH_SECRET)


__all__ = [
    "AuthUser",
    "AuthService",
    "UserAlreadyExistsError",
    "UserNotFoundError",
    "auth_service",
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
]
