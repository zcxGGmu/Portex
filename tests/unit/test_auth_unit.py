from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.auth import hash_password, verify_password  # noqa: E402


def test_hash_password_roundtrip() -> None:
    password_hash = hash_password("unit-password")

    assert password_hash != "unit-password"
    assert verify_password("unit-password", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False
