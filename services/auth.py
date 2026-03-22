"""In-memory authentication service used by API routes."""

from __future__ import annotations

import base64
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt


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

_PASSWORD_HASH_SCHEME = "scrypt-v1"
_PASSWORD_HASH_N = 1 << 14
_PASSWORD_HASH_R = 8
_PASSWORD_HASH_P = 1
_PASSWORD_HASH_DKLEN = 32
_PASSWORD_HASH_SALT_BYTES = 16


def _base64_urlsafe_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _base64_urlsafe_decode(value: str) -> bytes:
    if not value:
        raise ValueError("empty base64 payload")
    padded_value = value + ("=" * ((4 - (len(value) % 4)) % 4))
    return base64.urlsafe_b64decode(padded_value.encode("ascii"))


def _derive_password_key(*, password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_PASSWORD_HASH_N,
        r=_PASSWORD_HASH_R,
        p=_PASSWORD_HASH_P,
        dklen=_PASSWORD_HASH_DKLEN,
    )

_DEFAULT_ACCESS_TOKEN_EXPIRE_DELTA = timedelta(hours=DEFAULT_ACCESS_TOKEN_EXPIRE_HOURS)


def hash_password(password: str) -> str:
    salt = os.urandom(_PASSWORD_HASH_SALT_BYTES)
    digest = _derive_password_key(password=password, salt=salt)
    return (
        f"{_PASSWORD_HASH_SCHEME}"
        f"${_PASSWORD_HASH_N}"
        f"${_PASSWORD_HASH_R}"
        f"${_PASSWORD_HASH_P}"
        f"${_PASSWORD_HASH_DKLEN}"
        f"${_base64_urlsafe_encode(salt)}"
        f"${_base64_urlsafe_encode(digest)}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, n, r, p, dklen, salt_payload, digest_payload = password_hash.split("$")
        if scheme != _PASSWORD_HASH_SCHEME:
            return False

        parsed_n = int(n)
        parsed_r = int(r)
        parsed_p = int(p)
        parsed_dklen = int(dklen)
        if (
            parsed_n != _PASSWORD_HASH_N
            or parsed_r != _PASSWORD_HASH_R
            or parsed_p != _PASSWORD_HASH_P
            or parsed_dklen != _PASSWORD_HASH_DKLEN
        ):
            return False

        salt = _base64_urlsafe_decode(salt_payload)
        expected_digest = _base64_urlsafe_decode(digest_payload)
        if len(salt) != _PASSWORD_HASH_SALT_BYTES or len(expected_digest) != _PASSWORD_HASH_DKLEN:
            return False

        actual_digest = _derive_password_key(password=password, salt=salt)
        return hmac.compare_digest(actual_digest, expected_digest)
    except (TypeError, ValueError):
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


def _to_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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


@dataclass(frozen=True, slots=True)
class AuthInviteCode:
    code: str
    created_by: str
    role: str
    permission_template: str | None = None
    expires_at: datetime | None = None
    used_by: str | None = None
    used_at: datetime | None = None


class UserAlreadyExistsError(Exception):
    """Raised when trying to register an existing username."""


class UserNotFoundError(Exception):
    """Raised when an operation targets a missing user."""


class InviteCodeAlreadyExistsError(Exception):
    """Raised when trying to create a duplicate invite code."""


class InviteCodeUnavailableError(Exception):
    """Raised when an invite code is missing, expired, or already used."""


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
        self._invite_codes_by_code: dict[str, AuthInviteCode] = {}

    def register_user(
        self,
        username: str,
        password: str,
        *,
        role: str = "member",
        invite_code: str | None = None,
    ) -> AuthUser:
        if username in self._users_by_username:
            raise UserAlreadyExistsError(username)

        effective_role = role
        if invite_code is not None:
            effective_role = self._get_available_invite(invite_code).role

        user = AuthUser(
            id=uuid4().hex,
            username=username,
            role=effective_role,
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
        if invite_code is not None:
            self.consume_invite_code(invite_code, used_by=user.id)
        return user

    def list_users(self) -> list[AuthUser]:
        return sorted(self._users_by_id.values(), key=lambda user: user.username)

    def create_invite_code(
        self,
        *,
        created_by: str,
        role: str = "member",
        permission_template: str | None = None,
        expires_at: datetime | None = None,
        code: str | None = None,
    ) -> AuthInviteCode:
        invite_code = code or uuid4().hex[:12]
        if invite_code in self._invite_codes_by_code:
            raise InviteCodeAlreadyExistsError(invite_code)

        invite = AuthInviteCode(
            code=invite_code,
            created_by=created_by,
            role=role,
            permission_template=permission_template,
            expires_at=expires_at,
            used_by=None,
            used_at=None,
        )
        self._invite_codes_by_code[invite_code] = invite
        return invite

    def list_invite_codes(self) -> list[AuthInviteCode]:
        return sorted(self._invite_codes_by_code.values(), key=lambda invite: invite.code)

    def get_invite_code(self, code: str) -> AuthInviteCode | None:
        return self._invite_codes_by_code.get(code)

    def consume_invite_code(self, code: str, *, used_by: str) -> AuthInviteCode:
        invite = self._get_available_invite(code)
        used_at = datetime.now(timezone.utc)
        updated_invite = replace(invite, used_by=used_by, used_at=used_at)
        self._invite_codes_by_code[code] = updated_invite
        return updated_invite

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

    def _get_available_invite(self, code: str) -> AuthInviteCode:
        invite = self._invite_codes_by_code.get(code)
        if invite is None:
            raise InviteCodeUnavailableError(code)
        if invite.used_by is not None or invite.used_at is not None:
            raise InviteCodeUnavailableError(code)
        if invite.expires_at is not None:
            expires_at = _to_utc_datetime(invite.expires_at)
            if expires_at < datetime.now(timezone.utc):
                raise InviteCodeUnavailableError(code)
        return invite

    def reset(self) -> None:
        self._users_by_username.clear()
        self._users_by_id.clear()
        self._invite_codes_by_code.clear()


auth_service = AuthService(secret_key=DEFAULT_AUTH_SECRET)


__all__ = [
    "AuthUser",
    "AuthInviteCode",
    "AuthService",
    "InviteCodeAlreadyExistsError",
    "InviteCodeUnavailableError",
    "UserAlreadyExistsError",
    "UserNotFoundError",
    "auth_service",
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
]
