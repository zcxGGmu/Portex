from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from types import SimpleNamespace
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

    try:
        from services.task_service import task_service
    except ModuleNotFoundError:
        task_service = None
    try:
        from services.task_log_service import task_log_service
    except ModuleNotFoundError:
        task_log_service = None

    auth_service.reset()
    if task_service is not None:
        task_service.reset()
    if task_log_service is not None:
        task_log_service.reset()
    with TestClient(app) as client:
        yield client
    auth_service.reset()
    if task_service is not None:
        task_service.reset()
    if task_log_service is not None:
        task_log_service.reset()


def _login_headers(api_client: TestClient, username: str, password: str) -> dict[str, str]:
    login_response = api_client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _workspace(
    *,
    jid: str,
    folder: str,
    name: str,
    created_by: str | None,
    is_home: bool = False,
    target_workspace_jid: str | None = None,
):
    return SimpleNamespace(
        jid=jid,
        folder=folder,
        name=name,
        created_by=created_by,
        is_home=is_home,
        target_workspace_jid=target_workspace_jid,
    )


class FakeGroupMemberService:
    def __init__(self) -> None:
        from domain.models.group_member import GroupMember

        self._member_type = GroupMember
        self._members_by_folder: dict[str, dict[str, GroupMember]] = {}

    async def list_members(self, group_folder: str):
        members = self._members_by_folder.get(group_folder, {})
        return sorted(members.values(), key=lambda member: member.user_id)

    async def add_member(
        self,
        group_folder: str,
        user_id: str,
        role: str = "member",
        *,
        added_by: str | None = None,
    ):
        if role not in {"owner", "admin", "member"}:
            raise ValueError(f"invalid group member role: {role}")

        members = self._members_by_folder.setdefault(group_folder, {})
        existing_member = members.get(user_id)
        if role == "owner":
            if existing_member is not None and existing_member.role != "owner":
                raise ValueError("owner role changes are not supported")
        elif existing_member is not None and existing_member.role == "owner":
            raise ValueError("owner role changes are not supported")

        joined_at = existing_member.joined_at if existing_member is not None else datetime.utcnow()
        member = self._member_type(
            group_folder=group_folder,
            user_id=user_id,
            role=role,
            joined_at=joined_at,
            added_by=existing_member.added_by if existing_member is not None else added_by,
        )
        members[user_id] = member
        return member

    async def remove_member(self, group_folder: str, user_id: str) -> bool:
        members = self._members_by_folder.get(group_folder)
        if members is None:
            return False
        member = members.get(user_id)
        if member is None:
            return False
        if member.role == "owner":
            raise ValueError("group owner cannot be removed")

        del members[user_id]
        if not members:
            del self._members_by_folder[group_folder]
        return True

    async def get_member(self, group_folder: str, user_id: str):
        members = self._members_by_folder.get(group_folder)
        if members is None:
            return None
        return members.get(user_id)

    async def get_member_role(self, group_folder: str, user_id: str) -> str | None:
        member = await self.get_member(group_folder, user_id)
        if member is None:
            return None
        return member.role


class FakeGroupRegistry:
    def __init__(self, groups) -> None:
        self.groups = list(groups)

    async def ensure_home_workspace(
        self,
        *,
        user_id: str,
        role: str,
        username: str,
    ):
        _ = role
        _ = username
        return next(
            group
            for group in self.groups
            if getattr(group, "is_home", False) and getattr(group, "created_by", None) == user_id
        )

    async def list_registered_groups(self):
        return list(self.groups)

    async def get_web_workspace_by_folder(self, folder: str):
        for group in self.groups:
            if (
                getattr(group, "folder", None) == folder
                and isinstance(getattr(group, "jid", None), str)
                and group.jid.startswith("web:")
            ):
                return group
        return None

    async def user_can_access_group(
        self,
        *,
        user_id: str,
        user_role: str | None = None,
        group,
    ) -> bool:
        if getattr(group, "is_home", False):
            if (
                getattr(group, "jid", None) == "web:main"
                and getattr(group, "folder", None) == "main"
                and user_role == "owner"
            ):
                return True
            return getattr(group, "created_by", None) == user_id
        if str(getattr(group, "jid", "")).startswith("web:"):
            return getattr(group, "created_by", None) == user_id or user_id in getattr(
                group,
                "member_ids",
                set(),
            )
        if getattr(group, "target_workspace_jid", None):
            target = next((item for item in self.groups if item.jid == group.target_workspace_jid), None)
            if target is not None:
                return await self.user_can_access_group(
                    user_id=user_id,
                    user_role=user_role,
                    group=target,
                )
        return getattr(group, "created_by", None) == user_id

    async def user_can_manage_members(self, *, user_id: str, group) -> bool:
        if getattr(group, "is_home", False):
            return False
        return str(getattr(group, "jid", "")).startswith("web:") and getattr(group, "created_by", None) == user_id


def test_health_check_endpoint(api_client: TestClient) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert (
        response.headers["permissions-policy"]
        == "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
        "magnetometer=(), microphone=(), payment=(), usb=()"
    )


def test_cors_preflight_allows_localhost_5173(api_client: TestClient) -> None:
    response = api_client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in response.headers.get("access-control-allow-methods", "")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_register_login_and_get_current_user_flow(api_client: TestClient) -> None:
    register_response = api_client.post(
        "/auth/register",
        json={"username": "alice", "password": "secret"},
    )
    assert register_response.status_code == 200
    user_id = register_response.json()["user_id"]

    login_response = api_client.post(
        "/auth/login",
        json={"username": "alice", "password": "secret"},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["token_type"] == "bearer"
    assert login_payload["access_token"]

    me_response = api_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {login_payload['access_token']}"},
    )
    assert me_response.status_code == 200
    me_payload = me_response.json()
    assert me_payload["id"] == user_id
    assert me_payload["username"] == "alice"
    assert me_payload["role"] == "member"
    assert me_payload["status"] == "active"
    assert me_payload["avatar_emoji"] is None
    assert me_payload["avatar_color"] is None
    assert me_payload["ai_name"] is None
    assert me_payload["ai_avatar_emoji"] is None
    assert me_payload["must_change_password"] is False
    assert me_payload["last_login_at"] is None
    assert me_payload["disable_reason"] is None
    assert me_payload["notes"] is None


def test_register_ensures_home_workspace_for_new_user(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import auth as auth_routes

    ensure_calls: list[dict[str, str]] = []

    class HomeEnsureRegistry(FakeGroupRegistry):
        async def ensure_home_workspace(
            self,
            *,
            user_id: str,
            role: str,
            username: str,
        ):
            ensure_calls.append(
                {
                    "user_id": user_id,
                    "role": role,
                    "username": username,
                }
            )
            return None

    app.dependency_overrides[auth_routes.get_group_registry_service] = lambda: HomeEnsureRegistry([])

    try:
        response = api_client.post(
            "/auth/register",
            json={"username": "alice", "password": "secret"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert ensure_calls == [
        {
            "user_id": payload["user_id"],
            "role": "member",
            "username": "alice",
        }
    ]


def test_groups_and_messages_require_authentication(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import auth as auth_routes
    from app.routes import groups as group_routes
    from app.routes import im as im_routes
    from app.routes import messages as message_routes

    groups_unauthorized = api_client.get("/groups")
    assert groups_unauthorized.status_code == 401

    messages_unauthorized = api_client.post(
        "/messages",
        json={"group_id": "group-demo", "content": "hello"},
    )
    assert messages_unauthorized.status_code == 401

    register_response = api_client.post("/auth/register", json={"username": "bob", "password": "secret"})
    bob_user_id = register_response.json()["user_id"]
    login_response = api_client.post(
        "/auth/login",
        json={"username": "bob", "password": "secret"},
    )
    token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    fake_group_registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:home-bob",
                folder="home-bob",
                name="Bob Home",
                created_by="user-placeholder",
                is_home=True,
            ),
            _workspace(
                jid="web:home-other",
                folder="home-other",
                name="Other Home",
                created_by="user-other",
                is_home=True,
            ),
            _workspace(
                jid="web:group-alpha",
                folder="group-alpha",
                name="Alpha Workspace",
                created_by="user-placeholder",
            ),
            _workspace(
                jid="web:group-beta",
                folder="group-beta",
                name="Beta Workspace",
                created_by="user-placeholder",
            ),
        ]
    )
    for group in fake_group_registry.groups:
        if group.folder in {"home-bob", "group-alpha", "group-beta"}:
            group.created_by = bob_user_id

    app.dependency_overrides[auth_routes.get_group_registry_service] = lambda: fake_group_registry
    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: fake_group_registry
    app.dependency_overrides[message_routes.get_group_registry_service] = lambda: fake_group_registry

    groups_response = api_client.get("/groups", headers=auth_headers)
    assert groups_response.status_code == 200
    groups_payload = groups_response.json()
    assert groups_payload == {
        "groups": [
            {"group_id": "home-bob", "name": "Bob Home"},
            {"group_id": "group-alpha", "name": "Alpha Workspace"},
            {"group_id": "group-beta", "name": "Beta Workspace"},
        ]
    }

    class FakeDispatchService:
        async def dispatch_inbound_message(self, message, *, execution_mode: str | None = None):
            _ = message
            _ = execution_mode
            return type(
                "DispatchResult",
                (),
                {
                    "run_id": "run-auth-check",
                    "status": "completed",
                    "final_output": "hello back",
                },
            )()

    app.dependency_overrides[im_routes.get_message_dispatch_service] = lambda: FakeDispatchService()
    try:
        messages_response = api_client.post(
            "/messages",
            json={"group_id": "group-demo", "content": "hello"},
            headers=auth_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert messages_response.status_code == 200
    message_payload = messages_response.json()
    assert message_payload["message_id"]
    assert message_payload["status"] == "completed"
    assert message_payload["run_id"] == "run-auth-check"


def test_groups_route_ensures_home_workspace_and_hides_other_users_home_rows(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    current_user = auth_service.register_user("alice", "secret")
    auth_service.register_user("other", "secret")
    auth_headers = _login_headers(api_client, "alice", "secret")
    ensure_calls: list[dict[str, str]] = []

    class HomeAwareRegistry(FakeGroupRegistry):
        async def ensure_home_workspace(
            self,
            *,
            user_id: str,
            role: str,
            username: str,
        ):
            ensure_calls.append(
                {
                    "user_id": user_id,
                    "role": role,
                    "username": username,
                }
            )
            return await super().ensure_home_workspace(
                user_id=user_id,
                role=role,
                username=username,
            )

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: HomeAwareRegistry(
        [
            _workspace(
                jid=f"web:home-{current_user.id}",
                folder=f"home-{current_user.id}",
                name="alice Home",
                created_by=current_user.id,
                is_home=True,
            ),
            _workspace(
                jid="web:home-other-user",
                folder="home-other-user",
                name="other Home",
                created_by="other-user-id",
                is_home=True,
            ),
            _workspace(
                jid="telegram:chat-1",
                folder="chat-1",
                name="Shared Chat",
                created_by=None,
            ),
        ]
    )

    try:
        response = api_client.get("/groups", headers=auth_headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert ensure_calls == [
        {
            "user_id": current_user.id,
            "role": "member",
            "username": "alice",
        }
    ]
    assert response.json() == {
        "groups": [
            {"group_id": f"home-{current_user.id}", "name": "alice Home"},
        ]
    }


def test_groups_route_hides_raw_im_endpoint_rows_but_keeps_workspace_rows(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    current_user = auth_service.register_user("alice", "secret")
    auth_headers = _login_headers(api_client, "alice", "secret")

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: FakeGroupRegistry(
        [
            _workspace(
                jid=f"web:home-{current_user.id}",
                folder=f"home-{current_user.id}",
                name="alice Home",
                created_by=current_user.id,
                is_home=True,
            ),
            _workspace(
                jid="telegram:chat-1",
                folder="chat-1",
                name="Telegram Chat",
                created_by=None,
            ),
            _workspace(
                jid="feishu:oc_chat",
                folder="chat-2",
                name="Feishu Chat",
                created_by=None,
            ),
            _workspace(
                jid="web:group-alpha",
                folder="group-alpha",
                name="Alpha Workspace",
                created_by=current_user.id,
            ),
        ]
    )

    try:
        response = api_client.get("/groups", headers=auth_headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "groups": [
            {"group_id": f"home-{current_user.id}", "name": "alice Home"},
            {"group_id": "group-alpha", "name": "Alpha Workspace"},
        ]
    }


def test_owner_can_list_shared_main_workspace_created_by_another_owner(
    api_client: TestClient,
) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    first_owner = auth_service.register_user("owner-one", "secret", role="owner")
    second_owner = auth_service.register_user("owner-two", "secret", role="owner")
    owner_headers = _login_headers(api_client, "owner-two", "secret")

    class OwnerMainRegistry(FakeGroupRegistry):
        async def ensure_home_workspace(
            self,
            *,
            user_id: str,
            role: str,
            username: str,
        ):
            assert user_id == second_owner.id
            assert role == "owner"
            assert username == "owner-two"
            return SimpleNamespace(
                jid="web:main",
                folder="main",
                name="Main",
                created_by=first_owner.id,
                is_home=True,
            )

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: OwnerMainRegistry(
        [
            _workspace(
                jid="web:main",
                folder="main",
                name="Main",
                created_by=first_owner.id,
                is_home=True,
            ),
            _workspace(
                jid=f"web:home-{first_owner.id}",
                folder=f"home-{first_owner.id}",
                name="owner-one Home",
                created_by=first_owner.id,
                is_home=True,
            ),
        ]
    )

    try:
        response = api_client.get("/groups", headers=owner_headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "groups": [
            {"group_id": "main", "name": "Main"},
        ]
    }


def test_group_member_routes_require_authentication(api_client: TestClient) -> None:
    list_response = api_client.get("/groups/project-alpha/members")
    create_response = api_client.post(
        "/groups/project-alpha/members",
        json={"user_id": "user-1", "role": "member"},
    )
    remove_response = api_client.delete("/groups/project-alpha/members/user-1")

    assert list_response.status_code == 401
    assert create_response.status_code == 401
    assert remove_response.status_code == 401


def test_group_member_can_list_group_members(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    member_user = auth_service.register_user("member", "secret")
    member_service = FakeGroupMemberService()
    asyncio.run(member_service.add_member("project-alpha", owner_user.id, role="owner"))
    asyncio.run(
        member_service.add_member(
            "project-alpha",
            member_user.id,
            role="member",
            added_by=owner_user.id,
        )
    )
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_user.id,
            )
        ]
    )
    registry.groups[0].member_ids = {member_user.id}
    member_headers = _login_headers(api_client, "member", "secret")

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[group_routes.get_group_member_service] = lambda: member_service

    try:
        response = api_client.get("/groups/project-alpha/members", headers=member_headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["members"]) == 2
    roles_by_user_id = {member["user_id"]: member["role"] for member in payload["members"]}
    assert roles_by_user_id == {
        owner_user.id: "owner",
        member_user.id: "member",
    }


def test_non_member_cannot_list_group_members(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    auth_service.register_user("outsider", "secret")
    member_service = FakeGroupMemberService()
    asyncio.run(member_service.add_member("project-alpha", owner_user.id, role="owner"))
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_user.id,
            )
        ]
    )
    outsider_headers = _login_headers(api_client, "outsider", "secret")

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[group_routes.get_group_member_service] = lambda: member_service

    try:
        response = api_client.get("/groups/project-alpha/members", headers=outsider_headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_group_owner_can_add_member(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    target_user = auth_service.register_user("target", "secret")
    member_service = FakeGroupMemberService()
    asyncio.run(member_service.add_member("project-alpha", owner_user.id, role="owner"))
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_user.id,
            )
        ]
    )
    owner_headers = _login_headers(api_client, "owner", "secret")

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[group_routes.get_group_member_service] = lambda: member_service

    try:
        response = api_client.post(
            "/groups/project-alpha/members",
            json={"user_id": target_user.id, "role": "member"},
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["group_id"] == "project-alpha"
    assert payload["user_id"] == target_user.id
    assert payload["role"] == "member"


def test_group_admin_cannot_add_member(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    admin_user = auth_service.register_user("admin", "secret", role="admin")
    target_user = auth_service.register_user("target", "secret")
    member_service = FakeGroupMemberService()
    asyncio.run(member_service.add_member("project-alpha", owner_user.id, role="owner"))
    asyncio.run(
        member_service.add_member(
            "project-alpha",
            admin_user.id,
            role="admin",
            added_by=owner_user.id,
        )
    )
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_user.id,
            )
        ]
    )
    registry.groups[0].member_ids = {admin_user.id}
    admin_headers = _login_headers(api_client, "admin", "secret")

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[group_routes.get_group_member_service] = lambda: member_service

    try:
        response = api_client.post(
            "/groups/project-alpha/members",
            json={"user_id": target_user.id, "role": "member"},
            headers=admin_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_group_owner_can_remove_member(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    target_user = auth_service.register_user("target", "secret")
    member_service = FakeGroupMemberService()
    asyncio.run(member_service.add_member("project-alpha", owner_user.id, role="owner"))
    asyncio.run(
        member_service.add_member(
            "project-alpha",
            target_user.id,
            role="member",
            added_by=owner_user.id,
        )
    )
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_user.id,
            )
        ]
    )
    registry.groups[0].member_ids = {target_user.id}
    owner_headers = _login_headers(api_client, "owner", "secret")

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[group_routes.get_group_member_service] = lambda: member_service

    try:
        response = api_client.delete(
            f"/groups/project-alpha/members/{target_user.id}",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "removed"}


def test_group_owner_cannot_add_invalid_member_role(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    target_user = auth_service.register_user("target", "secret")
    member_service = FakeGroupMemberService()
    asyncio.run(member_service.add_member("project-alpha", owner_user.id, role="owner"))
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_user.id,
            )
        ]
    )
    owner_headers = _login_headers(api_client, "owner", "secret")

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[group_routes.get_group_member_service] = lambda: member_service

    try:
        response = api_client.post(
            "/groups/project-alpha/members",
            json={"user_id": target_user.id, "role": "guest"},
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400


def test_group_owner_cannot_promote_another_member_to_owner(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    target_user = auth_service.register_user("target", "secret", role="admin")
    member_service = FakeGroupMemberService()
    asyncio.run(member_service.add_member("project-alpha", owner_user.id, role="owner"))
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_user.id,
            )
        ]
    )
    owner_headers = _login_headers(api_client, "owner", "secret")

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[group_routes.get_group_member_service] = lambda: member_service

    try:
        response = api_client.post(
            "/groups/project-alpha/members",
            json={"user_id": target_user.id, "role": "owner"},
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert asyncio.run(member_service.get_member_role("project-alpha", target_user.id)) is None


def test_group_owner_cannot_demote_self_via_member_update(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    member_service = FakeGroupMemberService()
    asyncio.run(member_service.add_member("project-alpha", owner_user.id, role="owner"))
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_user.id,
            )
        ]
    )
    owner_headers = _login_headers(api_client, "owner", "secret")

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[group_routes.get_group_member_service] = lambda: member_service

    try:
        response = api_client.post(
            "/groups/project-alpha/members",
            json={"user_id": owner_user.id, "role": "member"},
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert asyncio.run(member_service.get_member_role("project-alpha", owner_user.id)) == "owner"


def test_group_owner_remove_missing_member_returns_404(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    member_service = FakeGroupMemberService()
    asyncio.run(member_service.add_member("project-alpha", owner_user.id, role="owner"))
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_user.id,
            )
        ]
    )
    owner_headers = _login_headers(api_client, "owner", "secret")

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[group_routes.get_group_member_service] = lambda: member_service

    try:
        response = api_client.delete(
            "/groups/project-alpha/members/missing-user-id",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_group_owner_cannot_remove_self(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    member_service = FakeGroupMemberService()
    asyncio.run(member_service.add_member("project-alpha", owner_user.id, role="owner"))
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_user.id,
            )
        ]
    )
    owner_headers = _login_headers(api_client, "owner", "secret")

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[group_routes.get_group_member_service] = lambda: member_service

    try:
        response = api_client.delete(
            f"/groups/project-alpha/members/{owner_user.id}",
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400


def test_groups_route_lists_shared_workspace_for_member(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    member_user = auth_service.register_user("member", "secret")
    member_headers = _login_headers(api_client, "member", "secret")
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid=f"web:home-{member_user.id}",
                folder=f"home-{member_user.id}",
                name="member Home",
                created_by=member_user.id,
                is_home=True,
            ),
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_user.id,
            ),
        ]
    )
    registry.groups[1].member_ids = {member_user.id}

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry

    try:
        response = api_client.get("/groups", headers=member_headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "groups": [
            {"group_id": f"home-{member_user.id}", "name": "member Home"},
            {"group_id": "project-alpha", "name": "Project Alpha"},
        ]
    }


def test_home_workspace_member_management_returns_400(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    target_user = auth_service.register_user("target", "secret")
    owner_headers = _login_headers(api_client, "owner", "secret")
    member_service = FakeGroupMemberService()
    asyncio.run(member_service.add_member("home-owner", owner_user.id, role="owner"))
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:home-owner",
                folder="home-owner",
                name="owner Home",
                created_by=owner_user.id,
                is_home=True,
            )
        ]
    )

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[group_routes.get_group_member_service] = lambda: member_service

    try:
        response = api_client.post(
            "/groups/home-owner/members",
            json={"user_id": target_user.id, "role": "member"},
            headers=owner_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400


def test_non_owner_member_can_leave_workspace(api_client: TestClient) -> None:
    from app.main import app
    from app.routes import groups as group_routes
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    member_user = auth_service.register_user("member", "secret")
    member_headers = _login_headers(api_client, "member", "secret")
    member_service = FakeGroupMemberService()
    asyncio.run(member_service.add_member("project-alpha", owner_user.id, role="owner"))
    asyncio.run(
        member_service.add_member(
            "project-alpha",
            member_user.id,
            role="member",
            added_by=owner_user.id,
        )
    )
    registry = FakeGroupRegistry(
        [
            _workspace(
                jid="web:project-alpha",
                folder="project-alpha",
                name="Project Alpha",
                created_by=owner_user.id,
            )
        ]
    )
    registry.groups[0].member_ids = {member_user.id}

    app.dependency_overrides[group_routes.get_group_registry_service] = lambda: registry
    app.dependency_overrides[group_routes.get_group_member_service] = lambda: member_service

    try:
        response = api_client.delete(
            f"/groups/project-alpha/members/{member_user.id}",
            headers=member_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "removed"}


def test_task_routes_require_authentication(api_client: TestClient) -> None:
    list_response = api_client.get("/tasks")
    logs_response = api_client.get("/tasks/task-missing/logs")
    create_response = api_client.post(
        "/tasks",
        json={
            "group_folder": "group-demo",
            "chat_jid": "group-demo",
            "prompt": "run once",
            "schedule_type": "once",
            "next_run": datetime.now(timezone.utc).isoformat(),
        },
    )
    delete_response = api_client.delete("/tasks/task-missing")

    assert list_response.status_code == 401
    assert logs_response.status_code == 401
    assert create_response.status_code == 401
    assert delete_response.status_code == 401


def test_admin_can_create_list_and_delete_tasks(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")
    next_run = datetime.now(timezone.utc) + timedelta(minutes=5)

    create_response = api_client.post(
        "/tasks",
        json={
            "group_folder": "group-demo",
            "chat_jid": "group-demo",
            "prompt": "send scheduled prompt",
            "execution_mode": "host",
            "schedule_type": "once",
            "next_run": next_run.isoformat(),
        },
        headers=admin_headers,
    )

    assert create_response.status_code == 200
    created_payload = create_response.json()
    assert created_payload["id"].startswith("task-")
    assert created_payload["group_folder"] == "group-demo"
    assert created_payload["chat_jid"] == "group-demo"
    assert created_payload["prompt"] == "send scheduled prompt"
    assert created_payload["schedule_type"] == "once"
    assert created_payload["schedule_value"] is None
    assert created_payload["execution_mode"] == "host"
    assert created_payload["status"] == "active"
    assert created_payload["next_run"]
    assert created_payload["created_at"]

    list_response = api_client.get("/tasks", headers=admin_headers)

    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert [task["id"] for task in list_payload["tasks"]] == [created_payload["id"]]
    assert list_payload["tasks"][0]["execution_mode"] == "host"

    delete_response = api_client.delete(
        f"/tasks/{created_payload['id']}",
        headers=admin_headers,
    )

    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "removed"}

    final_list_response = api_client.get("/tasks", headers=admin_headers)
    assert final_list_response.status_code == 200
    assert final_list_response.json() == {"tasks": []}


def test_task_api_normalizes_time_fields_to_utc(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")
    source_next_run = datetime(2026, 3, 8, 12, 5, 0, tzinfo=timezone(timedelta(hours=8)))

    create_response = api_client.post(
        "/tasks",
        json={
            "group_folder": "group-demo",
            "chat_jid": "group-demo",
            "prompt": "normalize timezone",
            "schedule_type": "once",
            "next_run": source_next_run.isoformat(),
        },
        headers=admin_headers,
    )

    assert create_response.status_code == 200
    created_payload = create_response.json()
    created_next_run = datetime.fromisoformat(created_payload["next_run"])
    created_at = datetime.fromisoformat(created_payload["created_at"])

    assert created_next_run == datetime(2026, 3, 8, 4, 5, 0, tzinfo=timezone.utc)
    assert created_at.tzinfo == timezone.utc

    list_response = api_client.get("/tasks", headers=admin_headers)

    assert list_response.status_code == 200
    listed_task = list_response.json()["tasks"][0]
    listed_next_run = datetime.fromisoformat(listed_task["next_run"])
    listed_created_at = datetime.fromisoformat(listed_task["created_at"])
    assert listed_next_run == datetime(2026, 3, 8, 4, 5, 0, tzinfo=timezone.utc)
    assert listed_created_at.tzinfo == timezone.utc


def test_member_can_list_tasks_but_cannot_create_or_delete_tasks(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    auth_service.register_user("member", "secret")

    admin_headers = _login_headers(api_client, "admin", "secret")
    member_headers = _login_headers(api_client, "member", "secret")
    create_seed_response = api_client.post(
        "/tasks",
        json={
            "group_folder": "group-demo",
            "chat_jid": "group-demo",
            "prompt": "scheduled task",
            "schedule_type": "once",
            "next_run": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        },
        headers=admin_headers,
    )

    assert create_seed_response.status_code == 200
    list_response = api_client.get("/tasks", headers=member_headers)
    create_response = api_client.post(
        "/tasks",
        json={
            "group_folder": "group-demo",
            "chat_jid": "group-demo",
            "prompt": "member task",
            "schedule_type": "once",
            "next_run": datetime.now(timezone.utc).isoformat(),
        },
        headers=member_headers,
    )
    delete_response = api_client.delete("/tasks/task-missing", headers=member_headers)

    assert list_response.status_code == 200
    assert len(list_response.json()["tasks"]) == 1
    assert create_response.status_code == 403
    assert delete_response.status_code == 403


def test_admin_can_list_task_logs(api_client: TestClient) -> None:
    from services.auth import auth_service
    from services.execution_coordinator import ExecutionHandle, ExecutionResult
    from services.task_service import task_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")
    monkeypatch = pytest.MonkeyPatch()

    class FakeCoordinator:
        async def submit_execution(self, request):
            return ExecutionHandle(
                run_id=request.request_id or "run-task-log",
                group_folder=request.group_folder,
                status="queued",
            )

        async def wait_for_run(self, run_id: str):
            return ExecutionResult(
                run_id=run_id,
                status="completed",
                group_folder="group-demo",
                backend="openai_runtime",
                session_id="group-demo",
                final_output="scheduled reply",
            )

    monkeypatch.setattr(task_service, "_execution_coordinator", FakeCoordinator(), raising=False)
    task = task_service.create_task(
        group_folder="group-demo",
        chat_jid="group-demo",
        prompt="run once",
        schedule_type="once",
        next_run=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    try:
        asyncio.run(task_service.run_pending())
    finally:
        monkeypatch.undo()

    response = api_client.get(f"/tasks/{task.id}/logs", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["logs"]) == 1
    assert payload["logs"][0]["task_id"] == task.id
    assert payload["logs"][0]["status"] == "success"


def test_member_can_list_task_logs(api_client: TestClient) -> None:
    from services.auth import auth_service
    from services.execution_coordinator import ExecutionHandle, ExecutionResult
    from services.task_service import task_service

    auth_service.register_user("admin", "secret", role="admin")
    auth_service.register_user("member", "secret")
    member_headers = _login_headers(api_client, "member", "secret")
    monkeypatch = pytest.MonkeyPatch()

    class FakeCoordinator:
        async def submit_execution(self, request):
            return ExecutionHandle(
                run_id=request.request_id or "run-task-log",
                group_folder=request.group_folder,
                status="queued",
            )

        async def wait_for_run(self, run_id: str):
            return ExecutionResult(
                run_id=run_id,
                status="completed",
                group_folder="group-demo",
                backend="openai_runtime",
                session_id="group-demo",
                final_output="scheduled reply",
            )

    monkeypatch.setattr(task_service, "_execution_coordinator", FakeCoordinator(), raising=False)
    task = task_service.create_task(
        group_folder="group-demo",
        chat_jid="group-demo",
        prompt="run once",
        schedule_type="once",
        next_run=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    try:
        asyncio.run(task_service.run_pending())
    finally:
        monkeypatch.undo()

    response = api_client.get(f"/tasks/{task.id}/logs", headers=member_headers)

    assert response.status_code == 200
    assert len(response.json()["logs"]) == 1


def test_task_logs_route_honors_limit(api_client: TestClient) -> None:
    from services.auth import auth_service
    from services.task_log_service import task_log_service
    from services.task_service import task_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")
    task = task_service.create_task(
        group_folder="group-demo",
        chat_jid="group-demo",
        prompt="run later",
        schedule_type="once",
        next_run=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    base_time = datetime(2026, 3, 8, 12, 0, 0)
    task_log_service.record_log(
        task_id=task.id,
        run_at=base_time,
        duration_ms=10,
        status="success",
        result="first",
    )
    latest = task_log_service.record_log(
        task_id=task.id,
        run_at=base_time + timedelta(minutes=1),
        duration_ms=20,
        status="error",
        result="second",
    )

    response = api_client.get(f"/tasks/{task.id}/logs?limit=1", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["logs"]) == 1
    assert payload["logs"][0]["id"] == latest.id


def test_task_logs_route_returns_404_for_missing_task(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")

    response = api_client.get("/tasks/task-missing/logs", headers=admin_headers)

    assert response.status_code == 404


def test_task_route_rejects_invalid_schedule_payload(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")

    response = api_client.post(
        "/tasks",
        json={
            "group_folder": "group-demo",
            "chat_jid": "group-demo",
            "prompt": "invalid once task",
            "schedule_type": "once",
        },
        headers=admin_headers,
    )

    assert response.status_code == 400


def test_delete_missing_task_returns_404(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")

    response = api_client.delete("/tasks/task-missing", headers=admin_headers)

    assert response.status_code == 404


def test_register_duplicate_username_returns_409(api_client: TestClient) -> None:
    first_response = api_client.post(
        "/auth/register",
        json={"username": "charlie", "password": "secret"},
    )
    assert first_response.status_code == 200

    second_response = api_client.post(
        "/auth/register",
        json={"username": "charlie", "password": "secret"},
    )
    assert second_response.status_code == 409


def test_login_failure_returns_401(api_client: TestClient) -> None:
    api_client.post("/auth/register", json={"username": "dora", "password": "secret"})

    failed_login = api_client.post(
        "/auth/login",
        json={"username": "dora", "password": "wrong-password"},
    )
    assert failed_login.status_code == 401


def test_admin_user_routes_require_authentication(api_client: TestClient) -> None:
    list_response = api_client.get("/admin/users")
    patch_response = api_client.patch("/admin/users/missing-user", json={"role": "admin"})

    assert list_response.status_code == 401
    assert patch_response.status_code == 401


def test_non_admin_cannot_manage_users(api_client: TestClient) -> None:
    api_client.post("/auth/register", json={"username": "member", "password": "secret"})
    member_headers = _login_headers(api_client, "member", "secret")

    list_response = api_client.get("/admin/users", headers=member_headers)
    patch_response = api_client.patch(
        "/admin/users/member-id",
        json={"role": "admin"},
        headers=member_headers,
    )

    assert list_response.status_code == 403
    assert patch_response.status_code == 403


def test_admin_can_list_users(api_client: TestClient) -> None:
    from services.auth import auth_service

    admin_user = auth_service.register_user("admin", "secret", role="admin")
    member_user = auth_service.register_user("member", "secret")
    admin_headers = _login_headers(api_client, "admin", "secret")

    response = api_client.get("/admin/users", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert [user["username"] for user in payload["users"]] == ["admin", "member"]
    assert payload["users"][0]["id"] == admin_user.id
    assert payload["users"][1]["id"] == member_user.id


def test_owner_can_list_users_via_permission_template(api_client: TestClient) -> None:
    from services.auth import auth_service

    owner_user = auth_service.register_user("owner", "secret", role="owner")
    member_user = auth_service.register_user("member", "secret")
    owner_headers = _login_headers(api_client, "owner", "secret")

    response = api_client.get("/admin/users", headers=owner_headers)

    assert response.status_code == 200
    payload = response.json()
    assert [user["username"] for user in payload["users"]] == ["member", "owner"]
    assert payload["users"][0]["id"] == member_user.id
    assert payload["users"][1]["id"] == owner_user.id


def test_admin_can_update_user(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    target_user = auth_service.register_user("member", "secret")
    admin_headers = _login_headers(api_client, "admin", "secret")

    response = api_client.patch(
        f"/admin/users/{target_user.id}",
        json={
            "role": "admin",
            "status": "disabled",
            "avatar_emoji": "🤖",
            "avatar_color": "#00AAFF",
            "ai_name": "Portex",
            "ai_avatar_emoji": "🧠",
            "must_change_password": True,
            "disable_reason": "manual-review",
            "notes": "promoted by admin",
        },
        headers=admin_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == target_user.id
    assert payload["role"] == "admin"
    assert payload["status"] == "disabled"
    assert payload["avatar_emoji"] == "🤖"
    assert payload["avatar_color"] == "#00AAFF"
    assert payload["ai_name"] == "Portex"
    assert payload["ai_avatar_emoji"] == "🧠"
    assert payload["must_change_password"] is True
    assert payload["disable_reason"] == "manual-review"
    assert payload["notes"] == "promoted by admin"


def test_admin_update_missing_user_returns_404(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")

    response = api_client.patch(
        "/admin/users/missing-user-id",
        json={"status": "disabled"},
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_admin_invite_routes_require_authentication(api_client: TestClient) -> None:
    list_response = api_client.get("/admin/invites")
    create_response = api_client.post("/admin/invites", json={})

    assert list_response.status_code == 401
    assert create_response.status_code == 401


def test_non_admin_cannot_manage_invites(api_client: TestClient) -> None:
    api_client.post("/auth/register", json={"username": "member", "password": "secret"})
    member_headers = _login_headers(api_client, "member", "secret")

    list_response = api_client.get("/admin/invites", headers=member_headers)
    create_response = api_client.post(
        "/admin/invites",
        json={"role": "admin"},
        headers=member_headers,
    )

    assert list_response.status_code == 403
    assert create_response.status_code == 403


def test_unknown_role_cannot_list_invites(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("guest", "secret", role="guest")
    guest_headers = _login_headers(api_client, "guest", "secret")

    response = api_client.get("/admin/invites", headers=guest_headers)

    assert response.status_code == 403


def test_admin_can_create_and_list_invites(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")

    create_response = api_client.post(
        "/admin/invites",
        json={"role": "admin", "permission_template": "owner-lite"},
        headers=admin_headers,
    )

    assert create_response.status_code == 200
    created_payload = create_response.json()
    assert created_payload["code"]
    assert created_payload["role"] == "admin"
    assert created_payload["permission_template"] == "owner-lite"
    assert created_payload["used_by"] is None
    assert created_payload["used_at"] is None

    list_response = api_client.get("/admin/invites", headers=admin_headers)

    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert len(list_payload["invites"]) == 1
    assert list_payload["invites"][0]["code"] == created_payload["code"]


def test_register_accepts_valid_invite_and_applies_invite_role(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")
    invite_response = api_client.post(
        "/admin/invites",
        json={"role": "admin"},
        headers=admin_headers,
    )
    invite_code = invite_response.json()["code"]

    register_response = api_client.post(
        "/auth/register",
        json={
            "username": "invited-user",
            "password": "secret",
            "invite_code": invite_code,
        },
    )

    assert register_response.status_code == 200

    login_headers = _login_headers(api_client, "invited-user", "secret")
    me_response = api_client.get("/users/me", headers=login_headers)

    assert me_response.status_code == 200
    assert me_response.json()["role"] == "admin"

    list_response = api_client.get("/admin/invites", headers=admin_headers)
    invite_payload = list_response.json()["invites"][0]
    assert invite_payload["used_by"] == register_response.json()["user_id"]
    assert invite_payload["used_at"] is not None


def test_register_rejects_invalid_invite_code(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")
    api_client.post(
        "/admin/invites",
        json={"role": "member"},
        headers=admin_headers,
    )

    register_response = api_client.post(
        "/auth/register",
        json={
            "username": "bad-invite-user",
            "password": "secret",
            "invite_code": "missing-code",
        },
    )

    assert register_response.status_code == 400


def test_register_rejects_expired_and_used_invite_codes(api_client: TestClient) -> None:
    from datetime import datetime, timedelta, timezone

    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")
    expired_response = api_client.post(
        "/admin/invites",
        json={
            "code": "expired-code",
            "role": "member",
            "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        },
        headers=admin_headers,
    )
    used_response = api_client.post(
        "/admin/invites",
        json={"code": "used-code", "role": "member"},
        headers=admin_headers,
    )
    assert expired_response.status_code == 200
    assert used_response.status_code == 200

    first_register = api_client.post(
        "/auth/register",
        json={
            "username": "first-used-user",
            "password": "secret",
            "invite_code": "used-code",
        },
    )
    assert first_register.status_code == 200

    expired_register = api_client.post(
        "/auth/register",
        json={
            "username": "expired-user",
            "password": "secret",
            "invite_code": "expired-code",
        },
    )
    used_register = api_client.post(
        "/auth/register",
        json={
            "username": "second-used-user",
            "password": "secret",
            "invite_code": "used-code",
        },
    )

    assert expired_register.status_code == 400
    assert used_register.status_code == 400


def test_duplicate_username_does_not_consume_invite_code(api_client: TestClient) -> None:
    from services.auth import auth_service

    auth_service.register_user("admin", "secret", role="admin")
    admin_headers = _login_headers(api_client, "admin", "secret")
    create_response = api_client.post(
        "/admin/invites",
        json={"code": "reusable-check", "role": "member"},
        headers=admin_headers,
    )
    assert create_response.status_code == 200

    register_response = api_client.post(
        "/auth/register",
        json={"username": "plain-user", "password": "secret"},
    )
    assert register_response.status_code == 200

    duplicate_response = api_client.post(
        "/auth/register",
        json={
            "username": "plain-user",
            "password": "new-secret",
            "invite_code": "reusable-check",
        },
    )
    assert duplicate_response.status_code == 409

    list_response = api_client.get("/admin/invites", headers=admin_headers)
    invite_payload = list_response.json()["invites"][0]
    assert invite_payload["used_by"] is None
    assert invite_payload["used_at"] is None


def test_openapi_schema_includes_global_api_metadata(api_client: TestClient) -> None:
    response = api_client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert "HTTP API" in schema["info"]["description"]
    assert "/ws/{group_folder}" in schema["info"]["description"]

    tags = {entry["name"]: entry["description"] for entry in schema["tags"]}
    assert "auth" in tags
    assert "tasks" in tags
    assert "messages" in tags
    assert "executions" in tags
    assert "scheduled" in tags["tasks"].lower()


def test_openapi_schema_documents_route_and_schema_details(api_client: TestClient) -> None:
    response = api_client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()

    register_operation = schema["paths"]["/auth/register"]["post"]
    assert "400" in register_operation["responses"]
    assert "409" in register_operation["responses"]

    create_task_operation = schema["paths"]["/tasks"]["post"]
    assert "UTC" in create_task_operation["description"]
    assert "400" in create_task_operation["responses"]
    assert "403" in create_task_operation["responses"]

    send_message_operation = schema["paths"]["/messages"]["post"]
    assert "dispatch" in send_message_operation["description"].lower()

    execution_status_operation = schema["paths"]["/executions/{run_id}"]["get"]
    assert "status" in execution_status_operation["summary"].lower()
    assert "404" in execution_status_operation["responses"]

    delete_member_operation = schema["paths"]["/groups/{group_id}/members/{user_id}"]["delete"]
    delete_member_schema = delete_member_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert delete_member_schema["$ref"].endswith("/DeleteGroupMemberResponse")

    register_schema = schema["components"]["schemas"]["RegisterRequest"]
    assert (
        register_schema["properties"]["invite_code"]["description"]
        == "Optional invite code that applies the invited role on registration."
    )

    create_task_schema = schema["components"]["schemas"]["CreateTaskRequest"]
    assert create_task_schema["properties"]["next_run"]["description"].startswith(
        "Required for one-off tasks"
    )
    assert "execution_mode" in create_task_schema["properties"]

    send_message_schema = schema["components"]["schemas"]["SendMessageRequest"]
    assert "execution_mode" in send_message_schema["properties"]
    assert "ExecutionRunStatusResponse" in schema["components"]["schemas"]


def test_openapi_schema_describes_invite_expiration_without_promising_utc(
    api_client: TestClient,
) -> None:
    response = api_client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()

    create_invite_schema = schema["components"]["schemas"]["CreateInviteCodeRequest"]
    assert (
        create_invite_schema["properties"]["expires_at"]["description"]
        == "Optional timezone-aware expiration timestamp. Portex preserves the provided offset."
    )

    invite_response_schema = schema["components"]["schemas"]["InviteCodeResponse"]
    assert (
        invite_response_schema["properties"]["expires_at"]["description"]
        == "Optional expiration timestamp returned with its stored timezone information."
    )
