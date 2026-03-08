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
        self.calls: list[tuple[str, dict[str, object], dict[str, str] | None]] = []

    async def post(
        self,
        url: str,
        json: dict[str, object],
        headers: dict[str, str] | None = None,
    ) -> _FakeResponse:
        self.calls.append((url, json, headers))
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
            None,
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


def test_handle_webhook_event_normalizes_plaintext_message_event() -> None:
    from infra.im.feishu import FeishuClient, FeishuMessageEvent

    client = FeishuClient(app_id="app-id", app_secret="app-secret")

    result = client.handle_webhook_event(
        {
            "header": {"event_type": "im.message.receive_v1"},
            "event": {
                "sender": {"sender_id": {"open_id": "ou_sender"}},
                "message": {
                    "chat_id": "oc_chat",
                    "message_id": "om_message",
                    "message_type": "text",
                    "content": json.dumps({"text": "hello feishu"}),
                },
            },
        }
    )

    assert result == FeishuMessageEvent(
        event_type="im.message.receive_v1",
        chat_id="oc_chat",
        message_id="om_message",
        sender_id="ou_sender",
        message_type="text",
        text="hello feishu",
        raw_event={
            "sender": {"sender_id": {"open_id": "ou_sender"}},
            "message": {
                "chat_id": "oc_chat",
                "message_id": "om_message",
                "message_type": "text",
                "content": json.dumps({"text": "hello feishu"}),
            },
        },
    )


def test_handle_webhook_event_normalizes_encrypted_message_event() -> None:
    from infra.im.feishu import FeishuClient

    encrypt_key = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG"
    payload = {
        "header": {"event_type": "im.message.receive_v1"},
        "event": {
            "sender": {"sender_id": {"open_id": "ou_sender"}},
            "message": {
                "chat_id": "oc_chat",
                "message_id": "om_message",
                "message_type": "text",
                "content": json.dumps({"text": "encrypted hello"}),
            },
        },
    }
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

    result = client.handle_webhook_event({"encrypt": encrypted})

    assert result is not None
    assert result.text == "encrypted hello"
    assert result.chat_id == "oc_chat"


def test_handle_webhook_event_returns_none_for_unsupported_event() -> None:
    from infra.im.feishu import FeishuClient

    client = FeishuClient(app_id="app-id", app_secret="app-secret")

    assert (
        client.handle_webhook_event(
            {
                "header": {"event_type": "contact.user.created"},
                "event": {"user": {"open_id": "ou_user"}},
            }
        )
        is None
    )


def test_handle_webhook_event_keeps_ids_when_text_content_is_not_plain_text() -> None:
    from infra.im.feishu import FeishuClient

    client = FeishuClient(app_id="app-id", app_secret="app-secret")

    result = client.handle_webhook_event(
        {
            "type": "im.message.receive_v1",
            "sender": {"sender_id": {"open_id": "ou_sender"}},
            "message": {
                "chat_id": "oc_chat",
                "message_id": "om_message",
                "message_type": "image",
                "content": '{"image_key":"img_123"}',
            },
        }
    )

    assert result is not None
    assert result.chat_id == "oc_chat"
    assert result.message_id == "om_message"
    assert result.sender_id == "ou_sender"
    assert result.message_type == "image"
    assert result.text is None


@pytest.mark.asyncio
async def test_send_message_posts_expected_url_headers_and_json_body() -> None:
    from infra.im.feishu import FeishuClient

    fake_client = _FakeAsyncClient(
        {
            "code": 0,
            "tenant_access_token": "tenant-token",
            "data": {"message_id": "om_123"},
        }
    )
    client = FeishuClient(
        app_id="app-id",
        app_secret="app-secret",
        http_client=fake_client,
    )

    payload = await client.send_message(
        "oc_chat",
        {
            "msg_type": "text",
            "content": {"text": "hello feishu"},
        },
    )

    assert payload["data"]["message_id"] == "om_123"
    assert fake_client.calls == [
        (
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            {"app_id": "app-id", "app_secret": "app-secret"},
            None,
        ),
        (
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
            {
                "receive_id": "oc_chat",
                "msg_type": "text",
                "content": json.dumps({"text": "hello feishu"}),
            },
            {"Authorization": "Bearer tenant-token"},
        ),
    ]


@pytest.mark.asyncio
async def test_send_message_accepts_pre_serialized_string_content() -> None:
    from infra.im.feishu import FeishuClient

    fake_client = _FakeAsyncClient(
        {
            "code": 0,
            "tenant_access_token": "tenant-token",
            "data": {"message_id": "om_123"},
        }
    )
    client = FeishuClient(
        app_id="app-id",
        app_secret="app-secret",
        http_client=fake_client,
    )

    await client.send_message(
        "ou_user",
        {
            "msg_type": "text",
            "content": '{"text":"already string"}',
        },
        receive_id_type="open_id",
    )

    assert fake_client.calls[-1] == (
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
        {
            "receive_id": "ou_user",
            "msg_type": "text",
            "content": '{"text":"already string"}',
        },
        {"Authorization": "Bearer tenant-token"},
    )


@pytest.mark.asyncio
async def test_send_message_raises_when_feishu_returns_error_code() -> None:
    from infra.im.feishu import FeishuClient, FeishuClientError

    fake_client = _FakeAsyncClient(
        {
            "code": 0,
            "tenant_access_token": "tenant-token",
        }
    )
    message_client = _FakeAsyncClient({"code": 999, "msg": "send failed"})
    client = FeishuClient(
        app_id="app-id",
        app_secret="app-secret",
        http_client=fake_client,
    )

    async def fake_get_access_token() -> str:
        client.http_client = message_client
        return "tenant-token"

    client.get_access_token = fake_get_access_token  # type: ignore[method-assign]

    with pytest.raises(FeishuClientError, match="send failed"):
        await client.send_message(
            "oc_chat",
            {
                "msg_type": "text",
                "content": {"text": "hello feishu"},
            },
        )
