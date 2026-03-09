from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.auth import (  # noqa: E402
    _decode_access_token,
    _encode_access_token,
    _read_positive_int_env,
    hash_password,
    verify_password,
)


def test_hash_password_roundtrip() -> None:
    password_hash = hash_password("unit-password")

    assert password_hash != "unit-password"
    assert verify_password("unit-password", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_read_positive_int_env_falls_back_for_missing_invalid_and_non_positive_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    variable = "PORTEX_UNIT_TEST_INT"

    monkeypatch.delenv(variable, raising=False)
    assert _read_positive_int_env(variable, 7) == 7

    monkeypatch.setenv(variable, "abc")
    assert _read_positive_int_env(variable, 7) == 7

    monkeypatch.setenv(variable, "0")
    assert _read_positive_int_env(variable, 7) == 7

    monkeypatch.setenv(variable, "-5")
    assert _read_positive_int_env(variable, 7) == 7

    monkeypatch.setenv(variable, "9")
    assert _read_positive_int_env(variable, 7) == 9


def test_encode_and_decode_access_token_roundtrip() -> None:
    token = _encode_access_token(
        data={"sub": "user-1"},
        secret_key="unit-secret",
        algorithm="HS256",
        default_expires_delta=timedelta(hours=1),
    )

    assert isinstance(token, str)
    assert _decode_access_token(
        token=token,
        secret_key="unit-secret",
        algorithm="HS256",
    ) == "user-1"


def test_decode_access_token_returns_none_for_missing_subject() -> None:
    token = _encode_access_token(
        data={"scope": "unit"},
        secret_key="unit-secret",
        algorithm="HS256",
        default_expires_delta=timedelta(hours=1),
    )

    assert (
        _decode_access_token(
            token=token,
            secret_key="unit-secret",
            algorithm="HS256",
        )
        is None
    )
