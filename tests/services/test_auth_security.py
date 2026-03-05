from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import sys

from jose import jwt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.auth import (  # noqa: E402
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_and_verify_password_success_and_failure() -> None:
    password_hash = hash_password("password123")

    assert password_hash != "password123"
    assert verify_password("password123", password_hash) is True
    assert verify_password("bad-password", password_hash) is False


def test_create_access_token_contains_exp_and_decodes_subject() -> None:
    token = create_access_token({"sub": "user-123"})
    claims = jwt.get_unverified_claims(token)

    assert isinstance(claims.get("exp"), (int, float))
    assert decode_access_token(token) == "user-123"


def test_decode_access_token_returns_none_for_expired_token() -> None:
    expired_token = create_access_token(
        {"sub": "user-123"},
        expires_delta=timedelta(seconds=-1),
    )

    assert decode_access_token(expired_token) is None
