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


__all__ = ["FeishuClient", "FeishuClientError"]
