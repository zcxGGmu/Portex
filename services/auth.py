"""In-memory authentication service used by API routes."""

from __future__ import annotations

from dataclasses import dataclass
import os
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext


@dataclass(frozen=True, slots=True)
class AuthUser:
    """Public user shape returned by the auth service."""

    id: str
    username: str
    role: str
    status: str


@dataclass(slots=True)
class _UserRecord:
    user: AuthUser
    password_hash: str


class UserAlreadyExistsError(Exception):
    """Raised when trying to register an existing username."""


class AuthService:
    """Minimal auth service for registration, login and token handling."""

    def __init__(self, *, secret_key: str, algorithm: str = "HS256") -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        self._users_by_username: dict[str, _UserRecord] = {}
        self._users_by_id: dict[str, AuthUser] = {}

    def register_user(self, username: str, password: str) -> AuthUser:
        if username in self._users_by_username:
            raise UserAlreadyExistsError(username)

        user = AuthUser(
            id=uuid4().hex,
            username=username,
            role="member",
            status="active",
        )
        record = _UserRecord(user=user, password_hash=self._pwd_context.hash(password))
        self._users_by_username[username] = record
        self._users_by_id[user.id] = user
        return user

    def authenticate_user(self, username: str, password: str) -> AuthUser | None:
        record = self._users_by_username.get(username)
        if record is None:
            return None
        if not self._pwd_context.verify(password, record.password_hash):
            return None
        return record.user

    def create_access_token(self, user_id: str) -> str:
        return jwt.encode({"sub": user_id}, self._secret_key, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> str | None:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
        except JWTError:
            return None

        subject = payload.get("sub")
        return subject if isinstance(subject, str) else None

    def get_user_by_id(self, user_id: str) -> AuthUser | None:
        return self._users_by_id.get(user_id)

    def reset(self) -> None:
        self._users_by_username.clear()
        self._users_by_id.clear()


auth_service = AuthService(secret_key=os.getenv("PORTEX_AUTH_SECRET", "portex-dev-secret"))


__all__ = ["AuthUser", "AuthService", "UserAlreadyExistsError", "auth_service"]
