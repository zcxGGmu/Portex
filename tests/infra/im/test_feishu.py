from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import sys

import pytest
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def json(self) -> dict[str, object]:
        return self._payload


class _FakeAsyncClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def post(self, url: str, json: dict[str, object]) -> _FakeResponse:
        self.calls.append((url, json))
        return _FakeResponse(self._payload)


def _pad(content: bytes) -> bytes:
    padding = 16 - (len(content) % 16)
    return content + bytes([padding]) * padding


def _encrypt_event(*, encrypt_key: str, payload: dict[str, object], app_id: str) -> str:
    key = base64.b64decode(encrypt_key + "=")
    iv = key[:16]
    payload_bytes = json.dumps(payload).encode("utf-8")
    message = len(payload_bytes).to_bytes(4, byteorder="big") + payload_bytes + app_id.encode(
        "utf-8"
    )
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(_pad(b"0123456789abcdef" + message)) + encryptor.finalize()
    return base64.b64encode(encrypted).decode("utf-8")


@pytest.mark.asyncio
async def test_get_access_token_returns_token_on_success() -> None:
    from infra.im.feishu import FeishuClient

    fake_client = _FakeAsyncClient(
        {
            "code": 0,
            "tenant_access_token": "tenant-token",
        }
    )
    client = FeishuClient(
        app_id="app-id",
        app_secret="app-secret",
        http_client=fake_client,
    )

    token = await client.get_access_token()

    assert token == "tenant-token"
    assert fake_client.calls == [
        (
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            {"app_id": "app-id", "app_secret": "app-secret"},
        )
    ]


@pytest.mark.asyncio
async def test_get_access_token_raises_when_feishu_returns_error_code() -> None:
    from infra.im.feishu import FeishuClient, FeishuClientError

    client = FeishuClient(
        app_id="app-id",
        app_secret="app-secret",
        http_client=_FakeAsyncClient({"code": 999, "msg": "bad credentials"}),
    )

    with pytest.raises(FeishuClientError, match="bad credentials"):
        await client.get_access_token()


def test_verify_signature_returns_true_for_matching_digest() -> None:
    from infra.im.feishu import FeishuClient

    timestamp = "1700000000"
    nonce = "nonce-1"
    body = '{"challenge":"ok"}'
    token = "verification-token"
    signature = hashlib.sha256(f"{timestamp}{nonce}{token}{body}".encode("utf-8")).hexdigest()
    client = FeishuClient(
        app_id="app-id",
        app_secret="app-secret",
        verification_token=token,
    )

    assert client.verify_signature(timestamp, nonce, body, signature) is True
    assert client.verify_signature(timestamp, nonce, body, "invalid") is False


def test_decrypt_event_returns_decoded_payload() -> None:
    from infra.im.feishu import FeishuClient

    encrypt_key = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG"
    payload = {"schema": "2.0", "header": {"event_id": "event-1"}}
    encrypted = _encrypt_event(
        encrypt_key=encrypt_key,
        payload=payload,
        app_id="app-id",
    )
    client = FeishuClient(
        app_id="app-id",
        app_secret="app-secret",
        encrypt_key=encrypt_key,
    )

    assert client.decrypt_event(encrypted) == payload


def test_decrypt_event_raises_without_encrypt_key() -> None:
    from infra.im.feishu import FeishuClient, FeishuClientError

    client = FeishuClient(app_id="app-id", app_secret="app-secret")

    with pytest.raises(FeishuClientError, match="encrypt_key"):
        client.decrypt_event("anything")
