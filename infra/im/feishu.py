"""Feishu client foundation for auth, signature verification, and decryption."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass

import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .base import IMClient


class FeishuClientError(RuntimeError):
    """Raised when the Feishu client cannot complete an operation."""


@dataclass(slots=True)
class FeishuMessageEvent:
    """Normalized Feishu message event payload."""

    event_type: str
    chat_id: str
    message_id: str
    sender_id: str
    message_type: str
    text: str | None
    raw_event: dict[str, object]


@dataclass(slots=True)
class FeishuClient(IMClient):
    """Minimal Feishu client skeleton for M5.1.1."""

    app_id: str
    app_secret: str
    encrypt_key: str | None = None
    verification_token: str | None = None
    base_url: str = "https://open.feishu.cn"
    http_client: httpx.AsyncClient | object | None = None

    async def get_access_token(self) -> str:
        """Fetch a tenant access token from Feishu."""
        client = self.http_client or httpx.AsyncClient()
        close_client = self.http_client is None
        try:
            response = await client.post(
                f"{self.base_url.rstrip('/')}/open-apis/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret,
                },
            )
            payload = response.json()
        finally:
            if close_client:
                await client.aclose()

        if payload.get("code") != 0:
            raise FeishuClientError(str(payload.get("msg", "failed to fetch tenant access token")))

        access_token = payload.get("tenant_access_token")
        if not isinstance(access_token, str) or access_token == "":
            raise FeishuClientError("tenant_access_token missing from Feishu response")
        return access_token

    def verify_signature(
        self,
        timestamp: str,
        nonce: str,
        body: str,
        signature: str,
    ) -> bool:
        """Verify a Feishu event request signature."""
        if self.verification_token is None:
            return False
        expected = hashlib.sha256(
            f"{timestamp}{nonce}{self.verification_token}{body}".encode("utf-8")
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def decrypt_event(self, encrypt: str) -> dict[str, object]:
        """Decrypt an encrypted Feishu event payload."""
        if self.encrypt_key is None:
            raise FeishuClientError("encrypt_key is required to decrypt Feishu events")

        key = base64.b64decode(self.encrypt_key + "=")
        iv = key[:16]
        encrypted = base64.b64decode(encrypt)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted) + decryptor.finalize()
        unpadded = self._pkcs7_unpad(decrypted)

        content = unpadded[16:]
        if len(content) < 4:
            raise FeishuClientError("invalid Feishu encrypted payload")

        json_length = int.from_bytes(content[:4], byteorder="big")
        json_bytes = content[4 : 4 + json_length]
        app_id = content[4 + json_length :].decode("utf-8")
        if app_id != self.app_id:
            raise FeishuClientError("Feishu event app_id does not match client")

        payload = json_bytes.decode("utf-8")
        return json.loads(payload)

    def handle_webhook_event(self, payload: dict[str, object]) -> FeishuMessageEvent | None:
        """Normalize a Feishu callback payload into a message event when applicable."""
        normalized_payload = payload
        if "encrypt" in payload:
            encrypt = payload.get("encrypt")
            if not isinstance(encrypt, str):
                raise FeishuClientError("invalid Feishu encrypted payload")
            normalized_payload = self.decrypt_event(encrypt)

        event_type, raw_event = self._extract_event(normalized_payload)
        if event_type != "im.message.receive_v1" or raw_event is None:
            return None

        sender_id = self._extract_sender_id(raw_event)
        message = raw_event.get("message")
        if not isinstance(message, dict):
            raise FeishuClientError("missing Feishu message payload")

        chat_id = message.get("chat_id")
        message_id = message.get("message_id")
        message_type = message.get("message_type")
        if not all(isinstance(value, str) and value for value in [chat_id, message_id, message_type]):
            raise FeishuClientError("invalid Feishu message payload")

        return FeishuMessageEvent(
            event_type=event_type,
            chat_id=chat_id,
            message_id=message_id,
            sender_id=sender_id,
            message_type=message_type,
            text=self._extract_text(message.get("content")),
            raw_event=raw_event,
        )

    def send_message(self, channel: str, text: str) -> bool:
        """Placeholder send hook reserved for later Feishu messaging work."""
        _ = (channel, text)
        return True

    def _pkcs7_unpad(self, value: bytes) -> bytes:
        if not value:
            raise FeishuClientError("invalid padded payload")
        padding = value[-1]
        if padding <= 0 or padding > 16:
            raise FeishuClientError("invalid padded payload")
        if value[-padding:] != bytes([padding]) * padding:
            raise FeishuClientError("invalid padded payload")
        return value[:-padding]

    def _extract_event(
        self,
        payload: dict[str, object],
    ) -> tuple[str | None, dict[str, object] | None]:
        header = payload.get("header")
        if isinstance(header, dict):
            event_type = header.get("event_type")
            event = payload.get("event")
            if isinstance(event_type, str) and isinstance(event, dict):
                return event_type, event

        event_type = payload.get("type")
        if isinstance(event_type, str):
            return event_type, payload
        return None, None

    def _extract_sender_id(self, event: dict[str, object]) -> str:
        sender = event.get("sender")
        if not isinstance(sender, dict):
            raise FeishuClientError("missing Feishu sender payload")
        sender_id = sender.get("sender_id")
        if isinstance(sender_id, dict):
            for key in ("open_id", "user_id", "union_id"):
                value = sender_id.get(key)
                if isinstance(value, str) and value:
                    return value
        raise FeishuClientError("invalid Feishu sender payload")

    def _extract_text(self, content: object) -> str | None:
        if not isinstance(content, str):
            return None
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        text = parsed.get("text")
        if isinstance(text, str) and text:
            return text
        return None


__all__ = ["FeishuClient", "FeishuClientError", "FeishuMessageEvent"]
