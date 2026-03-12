from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Iterator

from fastapi.testclient import TestClient
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def api_client() -> Iterator[TestClient]:
    from app.main import app

    app.dependency_overrides.clear()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_telegram_ingest_route_wires_normalization_dispatch_runtime_and_outbound_handler(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from infra.im.telegram import TelegramClient
    from services.execution_coordinator import ExecutionHandle, ExecutionResult
    from services.message_dispatch import MessageDispatchService, ResolvedMessageTarget
    from services.message_router import MessageRouter

    submit_calls: list[object] = []
    store_calls: list[dict[str, object]] = []
    routed_messages: list[object] = []

    class FakeCoordinator:
        async def submit_execution(self, request):
            submit_calls.append(request)
            return ExecutionHandle(
                run_id="run-telegram",
                group_folder=request.group_folder,
                status="queued",
            )

        async def wait_for_run(self, run_id: str):
            return ExecutionResult(
                run_id=run_id,
                status="completed",
                group_folder="resolved-group",
                backend="openai_runtime",
                session_id="resolved-group",
                final_output="agent reply",
            )

    async def store_message(**kwargs):
        store_calls.append(kwargs)
        return SimpleNamespace(id=f"db-{len(store_calls)}")

    async def telegram_handler(message):
        routed_messages.append(message)

    async def unexpected_handler(message):
        raise AssertionError(f"unexpected handler invocation for {message.channel}")

    dispatch_service = MessageDispatchService(
        target_resolver=lambda message: ResolvedMessageTarget(
            group_folder="resolved-group",
            chat_jid=message.chat_jid,
        ),
        execution_coordinator=FakeCoordinator(),
        store_message=store_message,
        message_router=MessageRouter(
            feishu_handler=unexpected_handler,
            telegram_handler=telegram_handler,
            web_handler=unexpected_handler,
        ),
    )

    app.dependency_overrides[im_routes.get_telegram_client] = lambda: TelegramClient(
        bot_token="test-token"
    )
    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: dispatch_service

    response = api_client.post(
        "/im/telegram/updates",
        json={
            "update_id": 101,
            "message": {
                "message_id": 2001,
                "text": "hello telegram",
                "chat": {"id": -3001, "type": "group"},
                "from": {"id": 4001, "is_bot": False},
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "dispatched", "run_id": "run-telegram"}
    assert submit_calls[0].group_folder == "resolved-group"
    assert submit_calls[0].prompt == "hello telegram"
    assert submit_calls[0].user_id == "4001"
    assert len(store_calls) == 2
    assert store_calls[0]["is_from_me"] is False
    assert store_calls[1]["is_from_me"] is True
    assert store_calls[0]["channel"] == "telegram"
    assert store_calls[1]["run_id"] == "run-telegram"
    assert len(routed_messages) == 1
    assert routed_messages[0].channel == "telegram"
    assert routed_messages[0].content == "agent reply"
    assert routed_messages[0].group_folder == "resolved-group"
