from __future__ import annotations

from pathlib import Path
import sys

import pytest

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

    async def get(self, url: str, params: dict[str, object]) -> _FakeResponse:
        self.calls.append((url, params))
        return _FakeResponse(self._payload)


@pytest.mark.asyncio
async def test_get_updates_returns_result_and_uses_expected_request_shape() -> None:
    from infra.im.telegram import TelegramClient

    fake_client = _FakeAsyncClient(
        {
            "ok": True,
            "result": [
                {
                    "update_id": 101,
                    "message": {"message_id": 1, "text": "hello telegram"},
                }
            ],
        }
    )
    client = TelegramClient(bot_token="bot-token", http_client=fake_client)

    result = await client.get_updates(offset=99)

    assert result == [
        {
            "update_id": 101,
            "message": {"message_id": 1, "text": "hello telegram"},
        }
    ]
    assert fake_client.calls == [
        (
            "https://api.telegram.org/botbot-token/getUpdates",
            {"offset": 99, "timeout": 60},
        )
    ]


@pytest.mark.asyncio
async def test_get_updates_forwards_timeout_and_allowed_updates() -> None:
    from infra.im.telegram import TelegramClient

    fake_client = _FakeAsyncClient({"ok": True, "result": []})
    client = TelegramClient(bot_token="bot-token", http_client=fake_client)

    await client.get_updates(
        offset=105,
        timeout=10,
        allowed_updates=["message", "edited_message"],
    )

    assert fake_client.calls == [
        (
            "https://api.telegram.org/botbot-token/getUpdates",
            {
                "offset": 105,
                "timeout": 10,
                "allowed_updates": ["message", "edited_message"],
            },
        )
    ]


@pytest.mark.asyncio
async def test_get_updates_raises_for_telegram_error_payload() -> None:
    from infra.im.telegram import TelegramClient, TelegramClientError

    client = TelegramClient(
        bot_token="bot-token",
        http_client=_FakeAsyncClient(
            {
                "ok": False,
                "description": "Unauthorized",
            }
        ),
    )

    with pytest.raises(TelegramClientError, match="Unauthorized"):
        await client.get_updates()


@pytest.mark.asyncio
async def test_get_updates_raises_for_missing_result_list() -> None:
    from infra.im.telegram import TelegramClient, TelegramClientError

    client = TelegramClient(
        bot_token="bot-token",
        http_client=_FakeAsyncClient(
            {
                "ok": True,
                "result": {"update_id": 1},
            }
        ),
    )

    with pytest.raises(TelegramClientError, match="result"):
        await client.get_updates()
