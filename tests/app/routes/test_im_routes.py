from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Iterator

from fastapi.testclient import TestClient
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def api_client() -> Iterator[TestClient]:
    from app.main import app

    app.dependency_overrides.clear()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_feishu_webhook_route_dispatches_normalized_message(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from infra.im.feishu import FeishuMessageEvent

    dispatched_messages: list[object] = []

    class FakeDispatchService:
        async def dispatch_inbound_message(self, message):
            dispatched_messages.append(message)
            return type("DispatchResult", (), {"run_id": "run-feishu", "status": "completed"})()

    class FakeFeishuClient:
        def handle_webhook_event(self, payload):
            assert payload["header"]["event_type"] == "im.message.receive_v1"
            return FeishuMessageEvent(
                event_type="im.message.receive_v1",
                chat_id="oc_chat",
                message_id="om_message",
                sender_id="ou_sender",
                message_type="text",
                text="hello feishu",
                raw_event=payload["event"],
                timestamp=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
            )

    app.dependency_overrides[im_routes.get_feishu_client] = lambda: FakeFeishuClient()
    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()

    response = api_client.post(
        "/im/feishu/webhook",
        json={
            "header": {"event_type": "im.message.receive_v1"},
            "event": {
                "sender": {"sender_id": {"open_id": "ou_sender"}},
                "message": {
                    "chat_id": "oc_chat",
                    "message_id": "om_message",
                    "message_type": "text",
                    "content": "{\"text\":\"hello feishu\"}",
                },
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "dispatched", "run_id": "run-feishu"}
    assert len(dispatched_messages) == 1
    assert dispatched_messages[0].channel == "feishu"
    assert dispatched_messages[0].content == "hello feishu"


def test_telegram_update_route_dispatches_normalized_message(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from infra.im.telegram import TelegramMessageEvent

    dispatched_messages: list[object] = []

    class FakeDispatchService:
        async def dispatch_inbound_message(self, message):
            dispatched_messages.append(message)
            return type("DispatchResult", (), {"run_id": "run-telegram", "status": "completed"})()

    class FakeTelegramClient:
        def handle_update(self, payload):
            assert payload["message"]["message_id"] == 2001
            return TelegramMessageEvent(
                event_type="message",
                chat_id="-3001",
                message_id="2001",
                sender_id="4001",
                message_type="text",
                text="hello telegram",
                raw_event=payload["message"],
                timestamp=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
            )

    app.dependency_overrides[im_routes.get_telegram_client] = lambda: FakeTelegramClient()
    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()

    response = api_client.post(
        "/im/telegram/updates",
        json={
            "update_id": 101,
            "message": {
                "message_id": 2001,
                "text": "hello telegram",
                "chat": {"id": -3001, "type": "group"},
                "from": {"id": 4001},
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "dispatched", "run_id": "run-telegram"}
    assert len(dispatched_messages) == 1
    assert dispatched_messages[0].channel == "telegram"
    assert dispatched_messages[0].content == "hello telegram"


def test_telegram_update_route_default_dependency_uses_bound_workspace_resolution(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from infra.im.telegram import TelegramMessageEvent

    submit_calls: list[object] = []
    resolve_calls: list[str] = []
    ensure_calls: list[dict[str, object]] = []
    routed_messages: list[object] = []
    store_calls: list[dict[str, object]] = []

    class FakeTelegramClient:
        def handle_update(self, payload):
            assert payload["message"]["message_id"] == 2001
            return TelegramMessageEvent(
                event_type="message",
                chat_id="-3001",
                message_id="2001",
                sender_id="4001",
                message_type="text",
                text="hello telegram",
                raw_event=payload["message"],
                timestamp=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
            )

    class FakeCoordinator:
        async def submit_execution(self, request):
            from services.execution_coordinator import ExecutionHandle

            submit_calls.append(request)
            return ExecutionHandle(
                run_id=request.request_id or "run-bound-im",
                group_folder=request.group_folder,
                status="queued",
            )

        async def wait_for_run(self, run_id: str):
            from services.execution_coordinator import ExecutionResult

            return ExecutionResult(
                run_id=run_id,
                status="completed",
                group_folder="main",
                backend="openai_runtime",
                session_id="main",
                final_output="reply from bound workspace",
            )

    class FakeGroupRegistry:
        async def ensure_im_endpoint(
            self,
            *,
            jid: str,
            name: str,
            folder: str,
        ):
            ensure_calls.append(
                {
                    "jid": jid,
                    "name": name,
                    "folder": folder,
                }
            )
            return type(
                "RegisteredGroup",
                (),
                {
                    "jid": jid,
                    "name": name,
                    "folder": folder,
                    "created_by": None,
                    "is_home": False,
                    "target_workspace_jid": None,
                },
            )()

        async def resolve_im_workspace(self, *, jid: str):
            resolve_calls.append(jid)
            return type(
                "RegisteredGroup",
                (),
                {
                    "jid": "web:main",
                    "folder": "main",
                    "name": "Main",
                    "created_by": "owner-1",
                    "is_home": True,
                    "target_workspace_jid": None,
                },
            )()

    async def fake_store_message(*, db, **kwargs):
        _ = db
        store_calls.append(kwargs)
        return type("StoredMessage", (), {"id": f"db-{len(store_calls)}"})()

    async def fake_send_telegram_message(message):
        routed_messages.append(message)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(im_routes, "get_execution_coordinator", lambda: FakeCoordinator(), raising=False)
    monkeypatch.setattr(im_routes, "store_message", fake_store_message, raising=False)
    monkeypatch.setattr(im_routes, "_send_telegram_message", fake_send_telegram_message, raising=False)
    app.dependency_overrides[im_routes.get_telegram_client] = lambda: FakeTelegramClient()
    app.dependency_overrides[im_routes.get_group_registry_service] = lambda: FakeGroupRegistry()

    try:
        response = api_client.post(
            "/im/telegram/updates",
            json={
                "update_id": 101,
                "message": {
                    "message_id": 2001,
                    "text": "hello telegram",
                    "chat": {"id": -3001, "type": "group"},
                    "from": {"id": 4001},
                },
            },
        )
    finally:
        app.dependency_overrides.clear()
        monkeypatch.undo()

    assert response.status_code == 200
    assert response.json()["status"] == "dispatched"
    assert resolve_calls == ["telegram:-3001"]
    assert ensure_calls[0]["jid"] == "telegram:-3001"
    assert ensure_calls[0]["folder"] == im_routes._build_group_folder("telegram:-3001")
    assert submit_calls[0].group_folder == "main"
    assert submit_calls[0].chat_jid == "telegram:-3001"
    assert routed_messages[0].chat_jid == "telegram:-3001"
    assert routed_messages[0].group_folder == "main"
    assert store_calls[0]["group_folder"] == "main"


def test_im_routes_return_ignored_for_unsupported_payloads(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import im as im_routes

    dispatch_calls: list[object] = []

    class FakeDispatchService:
        async def dispatch_inbound_message(self, message):
            dispatch_calls.append(message)
            return type("DispatchResult", (), {"run_id": "unused", "status": "completed"})()

    class FakeFeishuClient:
        def handle_webhook_event(self, payload):
            _ = payload
            return None

    class FakeTelegramClient:
        def handle_update(self, payload):
            _ = payload
            return None

    app.dependency_overrides[im_routes.get_feishu_client] = lambda: FakeFeishuClient()
    app.dependency_overrides[im_routes.get_telegram_client] = lambda: FakeTelegramClient()
    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()

    feishu_response = api_client.post("/im/feishu/webhook", json={"type": "contact.user.created"})
    telegram_response = api_client.post(
        "/im/telegram/updates",
        json={"update_id": 1, "callback_query": {"id": "cbq_1"}},
    )

    assert feishu_response.status_code == 200
    assert feishu_response.json() == {"status": "ignored"}
    assert telegram_response.status_code == 200
    assert telegram_response.json() == {"status": "ignored"}
    assert dispatch_calls == []
