"""Minimal HTTP security-header middleware."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

DEFAULT_SECURITY_HEADERS: Final[tuple[tuple[str, str], ...]] = (
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "no-referrer"),
    (
        "Permissions-Policy",
        "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
        "magnetometer=(), microphone=(), payment=(), usb=()",
    ),
)


class SecurityHeadersMiddleware:
    """Apply a small default set of security headers to HTTP responses."""

    def __init__(
        self,
        app: ASGIApp,
        headers: Iterable[tuple[str, str]] = DEFAULT_SECURITY_HEADERS,
    ) -> None:
        self.app = app
        self.headers = tuple(headers)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                raw_headers = message.setdefault("headers", [])
                headers = MutableHeaders(raw=raw_headers)
                for name, value in self.headers:
                    if name not in headers:
                        headers[name] = value
            await send(message)

        await self.app(scope, receive, send_with_security_headers)


__all__ = ["DEFAULT_SECURITY_HEADERS", "SecurityHeadersMiddleware"]
