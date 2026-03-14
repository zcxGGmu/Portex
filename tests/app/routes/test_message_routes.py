from __future__ import annotations

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
    from services.auth import auth_service

    auth_service.reset()
    with TestClient(app) as client:
        yield client
    auth_service.reset()


def _login_headers(api_client: TestClient, username: str, password: str) -> dict[str, str]:
    api_client.post("/auth/register", json={"username": username, "password": password})
    login_response = api_client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def _login_headers_with_user_id(
    api_client: TestClient,
    username: str,
    password: str,
) -> tuple[dict[str, str], str]:
    register_response = api_client.post(
        "/auth/register",
        json={"username": username, "password": password},
    )
    assert register_response.status_code == 200
    user_id = register_response.json()["user_id"]
    login_response = api_client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}, user_id


def test_send_message_request_defaults_slot_id_to_main() -> None:
    from domain.schemas import SendMessageRequest

    request = SendMessageRequest(group_id="group-demo", content="hello from http")

    assert request.slot_id == "main"


def test_post_messages_dispatches_through_real_service_boundary(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from app.routes import messages as message_routes
    from domain.schemas import UnifiedMessage

    dispatched_messages: list[UnifiedMessage] = []
    received_modes: list[str | None] = []

    class FakeDispatchService:
        async def dispatch_inbound_message(
            self,
            message: UnifiedMessage,
            *,
            execution_mode: str | None = None,
        ):
            dispatched_messages.append(message)
            received_modes.append(execution_mode)
            return type(
                "DispatchResult",
                (),
                {
                    "run_id": "run-http-1",
                    "status": "completed",
                    "final_output": "http reply",
                },
            )()

    class FakeGroupRegistry:
        async def ensure_home_workspace(self, *, user_id: str, role: str, username: str):
            _ = user_id
            _ = role
            _ = username
            return None

        async def get_web_workspace_by_folder(self, folder: str):
            _ = folder
            return None

    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()
    app.dependency_overrides[message_routes.get_group_registry_service] = lambda: FakeGroupRegistry()

    try:
        response = api_client.post(
            "/messages",
            json={"group_id": "group-demo", "content": "hello from http"},
            headers=_login_headers(api_client, "alice", "secret"),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["run_id"] == "run-http-1"
    assert payload["final_output"] == "http reply"
    assert payload["message_id"]
    assert len(dispatched_messages) == 1
    assert dispatched_messages[0].channel == "web"
    assert dispatched_messages[0].group_folder == "group-demo"
    assert dispatched_messages[0].chat_jid == "group-demo"
    assert dispatched_messages[0].content == "hello from http"
    assert dispatched_messages[0].slot_id == "main"
    assert received_modes == [None]


def test_post_messages_maps_dispatch_errors_to_http_400(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from app.routes import messages as message_routes
    from services.message_dispatch import MessageDispatchError

    class FailingDispatchService:
        async def dispatch_inbound_message(self, message, *, execution_mode: str | None = None):
            _ = message
            _ = execution_mode
            raise MessageDispatchError("dispatch failed")

    class FakeGroupRegistry:
        async def ensure_home_workspace(self, *, user_id: str, role: str, username: str):
            _ = user_id
            _ = role
            _ = username
            return None

        async def get_web_workspace_by_folder(self, folder: str):
            _ = folder
            return None

    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FailingDispatchService()
    app.dependency_overrides[message_routes.get_group_registry_service] = lambda: FakeGroupRegistry()

    try:
        response = api_client.post(
            "/messages",
            json={"group_id": "group-demo", "content": "hello from http"},
            headers=_login_headers(api_client, "alice", "secret"),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {"detail": "dispatch failed"}


def test_post_messages_default_dependency_uses_execution_coordinator(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from app.routes import messages as message_routes

    submit_calls: list[object] = []
    store_calls: list[dict[str, object]] = []
    registered_targets: list[dict[str, object]] = []
    ensured_workspaces: list[dict[str, str]] = []

    class FakeCoordinator:
        async def submit_execution(self, request):
            from services.execution_coordinator import ExecutionHandle

            submit_calls.append(request)
            return ExecutionHandle(
                run_id=request.request_id or "run-http-coordinator",
                group_folder=request.group_folder,
                status="queued",
            )

        async def wait_for_run(self, run_id: str):
            from services.execution_coordinator import ExecutionResult

            return ExecutionResult(
                run_id=run_id,
                status="completed",
                group_folder="group-demo",
                backend="openai_runtime",
                session_id="group-demo",
                final_output="http reply",
            )

        async def cancel(self, run_id: str) -> bool:
            _ = run_id
            return True

    async def fake_store_message(*, db, **kwargs):
        _ = db
        store_calls.append(kwargs)
        return type("StoredMessage", (), {"id": f"db-{len(store_calls)}"})()

    class FakeGroupRegistry:
        async def ensure_home_workspace(self, *, user_id: str, role: str, username: str):
            ensured_workspaces.append(
                {
                    "user_id": user_id,
                    "role": role,
                    "username": username,
                }
            )
            return type(
                "RegisteredGroup",
                (),
                {
                    "jid": f"web:home-{user_id}",
                    "name": f"{username} Home",
                    "folder": f"home-{user_id}",
                    "created_by": user_id,
                    "is_home": True,
                },
            )()

        async def get_web_workspace_by_folder(self, folder: str):
            _ = folder
            return None

        async def ensure_registered_group(
            self,
            *,
            jid: str,
            name: str,
            folder: str,
            created_by: str | None = None,
        ):
            registered_targets.append(
                {
                    "jid": jid,
                    "name": name,
                    "folder": folder,
                    "created_by": created_by,
                }
            )
            return type(
                "RegisteredGroup",
                (),
                {
                    "jid": jid,
                    "name": name,
                    "folder": folder,
                    "created_by": created_by,
                },
            )()

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(im_routes, "get_execution_coordinator", lambda: FakeCoordinator(), raising=False)
    monkeypatch.setattr(im_routes, "store_message", fake_store_message, raising=False)
    monkeypatch.setattr(
        "services.message_dispatch.run_agent_execution",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("direct runtime helper should not be used")),
    )
    fake_group_registry = FakeGroupRegistry()
    app.dependency_overrides[im_routes.get_group_registry_service] = lambda: fake_group_registry
    app.dependency_overrides[message_routes.get_group_registry_service] = lambda: fake_group_registry

    try:
        response = api_client.post(
            "/messages",
            json={
                "group_id": "group-demo",
                "content": "hello from http",
                "execution_mode": "host",
            },
            headers=_login_headers(api_client, "alice", "secret"),
        )
    finally:
        app.dependency_overrides.clear()
        monkeypatch.undo()

    assert response.status_code == 200
    assert len(submit_calls) == 1
    assert ensured_workspaces[0]["role"] == "member"
    assert registered_targets == [
        {
            "jid": "group-demo",
            "name": "group-demo",
            "folder": "group-demo",
            "created_by": submit_calls[0].user_id,
        }
    ]
    assert submit_calls[0].group_folder == "group-demo"
    assert submit_calls[0].source == "web"
    assert submit_calls[0].slot_id == "main"
    assert submit_calls[0].requested_mode == "host"
    assert response.json()["run_id"] == submit_calls[0].request_id
    assert len(store_calls) == 2
    assert store_calls[0]["slot_id"] == "main"
    assert store_calls[0]["run_id"] == submit_calls[0].request_id


def test_post_messages_resolves_main_folder_to_canonical_web_jid(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from app.routes import messages as message_routes
    from domain.schemas import UnifiedMessage
    from services.auth import auth_service

    dispatched_messages: list[UnifiedMessage] = []
    ensured_workspaces: list[dict[str, str]] = []
    owner = auth_service.register_user("owner", "secret", role="owner")

    class FakeDispatchService:
        async def dispatch_inbound_message(
            self,
            message: UnifiedMessage,
            *,
            execution_mode: str | None = None,
        ):
            _ = execution_mode
            dispatched_messages.append(message)
            return type(
                "DispatchResult",
                (),
                {
                    "run_id": "run-main-workspace",
                    "status": "completed",
                    "final_output": "main reply",
                },
            )()

    class FakeGroupRegistry:
        async def ensure_home_workspace(self, *, user_id: str, role: str, username: str):
            ensured_workspaces.append(
                {
                    "user_id": user_id,
                    "role": role,
                    "username": username,
                }
            )
            return type(
                "RegisteredGroup",
                (),
                {
                    "jid": "web:main",
                    "folder": "main",
                    "name": "Main",
                    "created_by": owner.id,
                    "is_home": True,
                },
            )()

        async def get_web_workspace_by_folder(self, folder: str):
            if folder != "main":
                return None
            return type(
                "RegisteredGroup",
                (),
                {
                    "jid": "web:main",
                    "folder": "main",
                    "name": "Main",
                    "created_by": owner.id,
                    "is_home": True,
                },
            )()

        async def user_can_access_group(
            self,
            *,
            user_id: str,
            user_role: str | None = None,
            group,
        ) -> bool:
            _ = user_role
            return group.created_by == user_id

    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()
    app.dependency_overrides[message_routes.get_group_registry_service] = lambda: FakeGroupRegistry()

    try:
        response = api_client.post(
            "/messages",
            json={"group_id": "main", "content": "hello main"},
            headers={"Authorization": f"Bearer {auth_service.create_access_token(owner.id)}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(dispatched_messages) == 1
    assert dispatched_messages[0].chat_jid == "web:main"
    assert dispatched_messages[0].group_folder == "main"
    assert ensured_workspaces == [
        {
            "user_id": owner.id,
            "role": "owner",
            "username": "owner",
        }
    ]


def test_post_messages_allows_secondary_owner_on_main_workspace(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from app.routes import messages as message_routes
    from domain.schemas import UnifiedMessage
    from services.auth import auth_service

    dispatched_messages: list[UnifiedMessage] = []
    access_calls: list[dict[str, str | None]] = []
    secondary_owner = auth_service.register_user("owner-two", "secret", role="owner")
    workspace = type(
        "RegisteredGroup",
        (),
        {
            "jid": "web:main",
            "folder": "main",
            "name": "Main",
            "created_by": "owner-1",
            "is_home": True,
        },
    )()

    class FakeDispatchService:
        async def dispatch_inbound_message(
            self,
            message: UnifiedMessage,
            *,
            execution_mode: str | None = None,
        ):
            _ = execution_mode
            dispatched_messages.append(message)
            return type(
                "DispatchResult",
                (),
                {
                    "run_id": "run-main-secondary-owner",
                    "status": "completed",
                    "final_output": "main reply",
                },
            )()

    class FakeGroupRegistry:
        async def ensure_home_workspace(self, *, user_id: str, role: str, username: str):
            _ = user_id
            _ = role
            _ = username
            return workspace

        async def get_web_workspace_by_folder(self, folder: str):
            if folder == "main":
                return workspace
            return None

        async def user_can_access_group(
            self,
            *,
            user_id: str,
            user_role: str | None = None,
            group,
        ) -> bool:
            access_calls.append(
                {
                    "user_id": user_id,
                    "user_role": user_role,
                    "group_id": group.folder,
                }
            )
            return user_role == "owner" and group.folder == "main"

    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()
    app.dependency_overrides[message_routes.get_group_registry_service] = lambda: FakeGroupRegistry()

    try:
        response = api_client.post(
            "/messages",
            json={"group_id": "main", "content": "hello main"},
            headers={"Authorization": f"Bearer {auth_service.create_access_token(secondary_owner.id)}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(dispatched_messages) == 1
    assert dispatched_messages[0].chat_jid == "web:main"
    assert access_calls == [
        {
            "user_id": secondary_owner.id,
            "user_role": "owner",
            "group_id": "main",
        }
    ]


def test_post_messages_resolves_personal_home_folder_to_canonical_web_jid(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from app.routes import messages as message_routes
    from domain.schemas import UnifiedMessage

    dispatched_messages: list[UnifiedMessage] = []
    register_response = api_client.post(
        "/auth/register",
        json={"username": "alice", "password": "secret"},
    )
    user_id = register_response.json()["user_id"]
    home_folder = f"home-{user_id}"

    class FakeDispatchService:
        async def dispatch_inbound_message(
            self,
            message: UnifiedMessage,
            *,
            execution_mode: str | None = None,
        ):
            _ = execution_mode
            dispatched_messages.append(message)
            return type(
                "DispatchResult",
                (),
                {
                    "run_id": "run-home-workspace",
                    "status": "completed",
                    "final_output": "home reply",
                },
            )()

    class FakeGroupRegistry:
        async def ensure_home_workspace(self, *, user_id: str, role: str, username: str):
            _ = role
            return type(
                "RegisteredGroup",
                (),
                {
                    "jid": f"web:home-{user_id}",
                    "folder": f"home-{user_id}",
                    "name": f"{username} Home",
                    "created_by": user_id,
                    "is_home": True,
                },
            )()

        async def get_web_workspace_by_folder(self, folder: str):
            if folder != home_folder:
                return None
            return type(
                "RegisteredGroup",
                (),
                {
                    "jid": f"web:home-{user_id}",
                    "folder": home_folder,
                    "name": "Alice Home",
                    "created_by": user_id,
                    "is_home": True,
                },
            )()

        async def user_can_access_group(
            self,
            *,
            user_id: str,
            user_role: str | None = None,
            group,
        ) -> bool:
            _ = user_role
            return group.created_by == user_id

    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()
    app.dependency_overrides[message_routes.get_group_registry_service] = lambda: FakeGroupRegistry()

    try:
        response = api_client.post(
            "/messages",
            json={"group_id": home_folder, "content": "hello home"},
            headers=_login_headers(api_client, "alice", "secret"),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(dispatched_messages) == 1
    assert dispatched_messages[0].chat_jid == f"web:home-{user_id}"
    assert dispatched_messages[0].group_folder == home_folder


def test_post_messages_allows_shared_workspace_member(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from app.routes import messages as message_routes
    from domain.schemas import UnifiedMessage

    dispatched_messages: list[UnifiedMessage] = []
    _, owner_id = _login_headers_with_user_id(api_client, "owner", "secret")
    member_headers, member_id = _login_headers_with_user_id(api_client, "member", "secret")
    shared_workspace = type(
        "RegisteredGroup",
        (),
        {
            "jid": "web:shared",
            "folder": "shared",
            "name": "Shared",
            "created_by": owner_id,
            "is_home": False,
        },
    )()

    class FakeDispatchService:
        async def dispatch_inbound_message(
            self,
            message: UnifiedMessage,
            *,
            execution_mode: str | None = None,
        ):
            _ = execution_mode
            dispatched_messages.append(message)
            return type(
                "DispatchResult",
                (),
                {
                    "run_id": "run-shared-member",
                    "status": "completed",
                    "final_output": "shared reply",
                },
            )()

    class FakeGroupRegistry:
        async def ensure_home_workspace(self, *, user_id: str, role: str, username: str):
            _ = user_id
            _ = role
            _ = username
            return None

        async def get_web_workspace_by_folder(self, folder: str):
            if folder == "shared":
                return shared_workspace
            return None

        async def user_can_access_group(
            self,
            *,
            user_id: str,
            user_role: str | None = None,
            group,
        ) -> bool:
            _ = user_role
            _ = group
            return user_id in {owner_id, member_id}

    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()
    app.dependency_overrides[message_routes.get_group_registry_service] = lambda: FakeGroupRegistry()

    try:
        response = api_client.post(
            "/messages",
            json={"group_id": "shared", "content": "hello shared"},
            headers=member_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["run_id"] == "run-shared-member"
    assert len(dispatched_messages) == 1
    assert dispatched_messages[0].chat_jid == "web:shared"
    assert dispatched_messages[0].group_folder == "shared"


def test_post_messages_accepts_explicit_slot_for_existing_workspace(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from app.routes import messages as message_routes
    from domain.schemas import UnifiedMessage

    dispatched_messages: list[UnifiedMessage] = []
    _, owner_id = _login_headers_with_user_id(api_client, "owner", "secret")
    member_headers, member_id = _login_headers_with_user_id(api_client, "member", "secret")
    shared_workspace = type(
        "RegisteredGroup",
        (),
        {
            "jid": "web:shared",
            "folder": "shared",
            "name": "Shared",
            "created_by": owner_id,
            "is_home": False,
        },
    )()

    class FakeDispatchService:
        async def dispatch_inbound_message(
            self,
            message: UnifiedMessage,
            *,
            execution_mode: str | None = None,
        ):
            _ = execution_mode
            dispatched_messages.append(message)
            return type(
                "DispatchResult",
                (),
                {
                    "run_id": "run-shared-draft",
                    "status": "completed",
                    "final_output": "shared draft reply",
                },
            )()

    class FakeGroupRegistry:
        async def ensure_home_workspace(self, *, user_id: str, role: str, username: str):
            _ = user_id
            _ = role
            _ = username
            return None

        async def get_web_workspace_by_folder(self, folder: str):
            if folder == "shared":
                return shared_workspace
            return None

        async def user_can_access_group(
            self,
            *,
            user_id: str,
            user_role: str | None = None,
            group,
        ) -> bool:
            _ = user_role
            _ = group
            return user_id in {owner_id, member_id}

    class FakeSlotService:
        async def get_slot(self, workspace_folder: str, slot_id: str):
            if workspace_folder == "shared" and slot_id == "draft":
                return type(
                    "ConversationSlot",
                    (),
                    {
                        "workspace_folder": workspace_folder,
                        "slot_id": slot_id,
                    },
                )()
            return None

    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()
    app.dependency_overrides[message_routes.get_group_registry_service] = lambda: FakeGroupRegistry()
    app.dependency_overrides[message_routes.get_conversation_slot_service] = lambda: FakeSlotService()

    try:
        response = api_client.post(
            "/messages",
            json={"group_id": "shared", "content": "hello shared", "slot_id": "draft"},
            headers=member_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["run_id"] == "run-shared-draft"
    assert len(dispatched_messages) == 1
    assert dispatched_messages[0].chat_jid == "web:shared"
    assert dispatched_messages[0].group_folder == "shared"
    assert dispatched_messages[0].slot_id == "draft"


def test_post_messages_hides_inaccessible_shared_workspace(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from app.routes import messages as message_routes
    from domain.schemas import UnifiedMessage

    dispatched_messages: list[UnifiedMessage] = []
    _, owner_id = _login_headers_with_user_id(api_client, "owner", "secret")
    _, member_id = _login_headers_with_user_id(api_client, "member", "secret")
    outsider_headers, outsider_id = _login_headers_with_user_id(api_client, "outsider", "secret")
    shared_workspace = type(
        "RegisteredGroup",
        (),
        {
            "jid": "web:shared",
            "folder": "shared",
            "name": "Shared",
            "created_by": owner_id,
            "is_home": False,
        },
    )()

    class FakeDispatchService:
        async def dispatch_inbound_message(
            self,
            message: UnifiedMessage,
            *,
            execution_mode: str | None = None,
        ):
            _ = execution_mode
            dispatched_messages.append(message)
            return type(
                "DispatchResult",
                (),
                {
                    "run_id": "run-outsider",
                    "status": "completed",
                    "final_output": "should not dispatch",
                },
            )()

    class FakeGroupRegistry:
        async def ensure_home_workspace(self, *, user_id: str, role: str, username: str):
            _ = user_id
            _ = role
            _ = username
            return None

        async def get_web_workspace_by_folder(self, folder: str):
            if folder == "shared":
                return shared_workspace
            return None

        async def user_can_access_group(
            self,
            *,
            user_id: str,
            user_role: str | None = None,
            group,
        ) -> bool:
            _ = user_role
            _ = group
            return user_id in {owner_id, member_id}

    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()
    app.dependency_overrides[message_routes.get_group_registry_service] = lambda: FakeGroupRegistry()

    try:
        response = api_client.post(
            "/messages",
            json={"group_id": "shared", "content": "hello shared", "slot_id": "draft"},
            headers=outsider_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert outsider_id not in {owner_id, member_id}
    assert response.status_code == 404
    assert response.json() == {"detail": "group not found"}
    assert dispatched_messages == []


def test_post_messages_returns_404_for_missing_non_main_slot(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import im as im_routes
    from app.routes import messages as message_routes
    from domain.schemas import UnifiedMessage

    dispatched_messages: list[UnifiedMessage] = []
    _, owner_id = _login_headers_with_user_id(api_client, "owner", "secret")
    member_headers, member_id = _login_headers_with_user_id(api_client, "member", "secret")
    shared_workspace = type(
        "RegisteredGroup",
        (),
        {
            "jid": "web:shared",
            "folder": "shared",
            "name": "Shared",
            "created_by": owner_id,
            "is_home": False,
        },
    )()

    class FakeDispatchService:
        async def dispatch_inbound_message(
            self,
            message: UnifiedMessage,
            *,
            execution_mode: str | None = None,
        ):
            _ = message
            _ = execution_mode
            dispatched_messages.append(message)
            return type(
                "DispatchResult",
                (),
                {
                    "run_id": "run-should-not-dispatch",
                    "status": "completed",
                    "final_output": "should not dispatch",
                },
            )()

    class FakeGroupRegistry:
        async def ensure_home_workspace(self, *, user_id: str, role: str, username: str):
            _ = user_id
            _ = role
            _ = username
            return None

        async def get_web_workspace_by_folder(self, folder: str):
            if folder == "shared":
                return shared_workspace
            return None

        async def user_can_access_group(
            self,
            *,
            user_id: str,
            user_role: str | None = None,
            group,
        ) -> bool:
            _ = user_role
            _ = group
            return user_id in {owner_id, member_id}

    class FakeSlotService:
        async def get_slot(self, workspace_folder: str, slot_id: str):
            _ = workspace_folder
            _ = slot_id
            return None

    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()
    app.dependency_overrides[message_routes.get_group_registry_service] = lambda: FakeGroupRegistry()
    app.dependency_overrides[message_routes.get_conversation_slot_service] = lambda: FakeSlotService()

    try:
        response = api_client.post(
            "/messages",
            json={"group_id": "shared", "content": "hello shared", "slot_id": "draft"},
            headers=member_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "slot not found"}
    assert dispatched_messages == []
