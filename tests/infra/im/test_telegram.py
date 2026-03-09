from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

import httpx
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class _FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def json(self) -> object:
        return self._payload


class _FakeAsyncClient:
    def __init__(self, payload: object) -> None:
        self._payload = payload
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def get(self, url: str, params: dict[str, object]) -> _FakeResponse:
        self.calls.append((url, params))
        return _FakeResponse(self._payload)


class _RaisingAsyncClient:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def get(self, url: str, params: dict[str, object]) -> _FakeResponse:
        _ = (url, params)
        raise self._exc


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


@pytest.mark.asyncio
async def test_get_updates_raises_for_non_dict_payload() -> None:
    from infra.im.telegram import TelegramClient, TelegramClientError

    client = TelegramClient(
        bot_token="bot-token",
        http_client=_FakeAsyncClient(["not", "a", "dict"]),
    )

    with pytest.raises(TelegramClientError, match="payload"):
        await client.get_updates()


@pytest.mark.asyncio
async def test_get_updates_wraps_transport_errors() -> None:
    from infra.im.telegram import TelegramClient, TelegramClientError

    client = TelegramClient(
        bot_token="bot-token",
        http_client=_RaisingAsyncClient(httpx.ConnectTimeout("network down")),
    )

    with pytest.raises(TelegramClientError, match="network down"):
        await client.get_updates()


def test_handle_update_normalizes_text_message() -> None:
    from infra.im.telegram import TelegramClient, TelegramMessageEvent

    client = TelegramClient(bot_token="bot-token")

    result = client.handle_update(
        {
            "update_id": 101,
            "message": {
                "message_id": 201,
                "text": "hello telegram",
                "chat": {"id": -3001, "type": "group"},
                "from": {"id": 4001, "is_bot": False},
            },
        }
    )

    assert result == TelegramMessageEvent(
        event_type="message",
        chat_id="-3001",
        message_id="201",
        sender_id="4001",
        message_type="text",
        text="hello telegram",
        raw_event={
            "message_id": 201,
            "text": "hello telegram",
            "chat": {"id": -3001, "type": "group"},
            "from": {"id": 4001, "is_bot": False},
        },
    )


def test_handle_update_returns_none_for_unsupported_update_family() -> None:
    from infra.im.telegram import TelegramClient

    client = TelegramClient(bot_token="bot-token")

    assert (
        client.handle_update(
            {
                "update_id": 101,
                "callback_query": {
                    "id": "cbq_1",
                },
            }
        )
        is None
    )


def test_handle_update_keeps_ids_for_non_text_message() -> None:
    from infra.im.telegram import TelegramClient

    client = TelegramClient(bot_token="bot-token")

    result = client.handle_update(
        {
            "update_id": 101,
            "message": {
                "message_id": 201,
                "photo": [{"file_id": "photo_1"}],
                "chat": {"id": -3001, "type": "group"},
                "from": {"id": 4001, "is_bot": False},
            },
        }
    )

    assert result is not None
    assert result.chat_id == "-3001"
    assert result.message_id == "201"
    assert result.sender_id == "4001"
    assert result.message_type == "photo"
    assert result.text is None


def test_handle_update_raises_for_invalid_message_payload() -> None:
    from infra.im.telegram import TelegramClient, TelegramClientError

    client = TelegramClient(bot_token="bot-token")

    with pytest.raises(TelegramClientError, match="chat"):
        client.handle_update(
            {
                "update_id": 101,
                "message": {
                    "message_id": 201,
                    "text": "hello telegram",
                    "chat": {},
                    "from": {"id": 4001, "is_bot": False},
                },
            }
        )


def test_handle_update_rejects_boolean_identifiers() -> None:
    from infra.im.telegram import TelegramClient, TelegramClientError

    client = TelegramClient(bot_token="bot-token")

    with pytest.raises(TelegramClientError, match="sender"):
        client.handle_update(
            {
                "update_id": 101,
                "message": {
                    "message_id": 201,
                    "text": "hello telegram",
                    "chat": {"id": -3001, "type": "group"},
                    "from": {"id": True, "is_bot": False},
                },
            }
        )


def test_send_message_raises_until_telegram_send_support_exists() -> None:
    from infra.im.telegram import TelegramClient, TelegramClientError

    client = TelegramClient(bot_token="bot-token")

    with pytest.raises(TelegramClientError, match="not implemented"):
        client.send_message("chat-id", "hello")


def test_markdown_to_html_escapes_plain_text_html_characters() -> None:
    from infra.im.telegram import TelegramClient

    client = TelegramClient(bot_token="bot-token")

    assert client.markdown_to_html("1 < 2 & 3 > 1") == "1 &lt; 2 &amp; 3 &gt; 1"


def test_markdown_to_html_converts_basic_inline_formatting() -> None:
    from infra.im.telegram import TelegramClient

    client = TelegramClient(bot_token="bot-token")

    assert (
        client.markdown_to_html("**bold** *italic* `code <tag>`")
        == "<b>bold</b> <i>italic</i> <code>code &lt;tag&gt;</code>"
    )


def test_markdown_to_html_converts_fenced_code_blocks_without_reformatting_inner_markdown() -> None:
    from infra.im.telegram import TelegramClient

    client = TelegramClient(bot_token="bot-token")

    assert (
        client.markdown_to_html("```\nif x < 1:\n  **still code**\n```")
        == "<pre><code>if x &lt; 1:\n  **still code**\n</code></pre>"
    )


def test_markdown_to_html_keeps_incomplete_markers_as_plain_text() -> None:
    from infra.im.telegram import TelegramClient

    client = TelegramClient(bot_token="bot-token")

    assert client.markdown_to_html("Use **bold and *italic") == "Use **bold and *italic"


def test_markdown_to_html_leaves_unsupported_markdown_syntax_unchanged() -> None:
    from infra.im.telegram import TelegramClient

    client = TelegramClient(bot_token="bot-token")

    assert (
        client.markdown_to_html("[link](https://example.com) & more")
        == "[link](https://example.com) &amp; more"
    )


def test_markdown_to_html_does_not_format_inside_unsupported_markdown_links() -> None:
    from infra.im.telegram import TelegramClient

    client = TelegramClient(bot_token="bot-token")

    assert (
        client.markdown_to_html("[**bold**](https://example.com?a=1&b=2)")
        == "[**bold**](https://example.com?a=1&amp;b=2)"
    )


def test_markdown_to_html_does_not_convert_nested_styles() -> None:
    from infra.im.telegram import TelegramClient

    client = TelegramClient(bot_token="bot-token")

    assert client.markdown_to_html("*italic **bold** inside*") == "*italic **bold** inside*"


def test_markdown_to_html_does_not_format_inside_inline_code() -> None:
    from infra.im.telegram import TelegramClient

    client = TelegramClient(bot_token="bot-token")

    assert client.markdown_to_html("`**x**` and `*y*`") == "<code>**x**</code> and <code>*y*</code>"


def test_telegram_message_event_converts_to_unified_message() -> None:
    from domain.schemas import UnifiedMessage
    from infra.im.telegram import TelegramClient

    client = TelegramClient(bot_token="bot-token")

    result = client.handle_update(
        {
            "update_id": 101,
            "message": {
                "message_id": 201,
                "text": "hello unified",
                "date": 1710000000,
                "chat": {"id": -3001, "type": "group"},
                "from": {"id": 4001, "is_bot": False},
            },
        }
    )

    assert result is not None
    assert result.timestamp == datetime.fromtimestamp(1710000000, tz=timezone.utc)
    assert result.to_unified_message("team-alpha") == UnifiedMessage(
        channel="telegram",
        chat_jid="telegram:-3001",
        sender_id="4001",
        group_folder="team-alpha",
        content="hello unified",
        message_id="201",
        timestamp=datetime.fromtimestamp(1710000000, tz=timezone.utc),
    )


def test_telegram_non_text_event_converts_to_unified_message_with_empty_content() -> None:
    from domain.schemas import UnifiedMessage
    from infra.im.telegram import TelegramClient

    client = TelegramClient(bot_token="bot-token")

    result = client.handle_update(
        {
            "update_id": 101,
            "message": {
                "message_id": 201,
                "photo": [{"file_id": "photo_1"}],
                "date": 1710000000,
                "chat": {"id": -3001, "type": "group"},
                "from": {"id": 4001, "is_bot": False},
            },
        }
    )

    assert result is not None
    assert result.to_unified_message() == UnifiedMessage(
        channel="telegram",
        chat_jid="telegram:-3001",
        sender_id="4001",
        group_folder=None,
        content="",
        message_id="201",
        timestamp=datetime.fromtimestamp(1710000000, tz=timezone.utc),
    )
