from __future__ import annotations

import asyncio
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class FakeBridge:
    def __init__(self) -> None:
        self.started = False
        self.closed = False
        self.inputs: list[str] = []
        self.resizes: list[tuple[int, int]] = []
        self._event_handler = None

    async def start(self, on_event) -> None:
        self.started = True
        self._event_handler = on_event

    async def send_input(self, data: str) -> None:
        self.inputs.append(data)

    async def resize(self, *, cols: int, rows: int) -> None:
        self.resizes.append((cols, rows))

    async def close(self) -> None:
        self.closed = True

    async def emit_output(self, data: str) -> None:
        assert self._event_handler is not None
        await self._event_handler({"type": "output", "data": data})

    async def emit_exit(self, exit_code: int = 0) -> None:
        assert self._event_handler is not None
        await self._event_handler({"type": "exit", "exit_code": exit_code})


@pytest.mark.asyncio
async def test_terminal_session_service_rejects_openai_runtime_backend() -> None:
    from services.terminal_sessions import (
        TerminalBackendUnsupportedError,
        TerminalSessionService,
    )

    service = TerminalSessionService(bridge_factory=lambda **_: FakeBridge())

    with pytest.raises(TerminalBackendUnsupportedError, match="openai_runtime"):
        await service.create_session(
            group_id="project-alpha",
            group_folder="project-alpha",
            owner_user_id="owner-1",
            requested_mode="openai",
        )


@pytest.mark.asyncio
async def test_terminal_session_service_rejects_host_backend_for_v1() -> None:
    from services.terminal_sessions import (
        TerminalBackendDisabledError,
        TerminalSessionService,
    )

    service = TerminalSessionService(bridge_factory=lambda **_: FakeBridge())

    with pytest.raises(TerminalBackendDisabledError, match="host_process"):
        await service.create_session(
            group_id="project-alpha",
            group_folder="project-alpha",
            owner_user_id="owner-1",
            requested_mode="host",
        )


@pytest.mark.asyncio
async def test_terminal_session_service_creates_container_session_and_forwards_io() -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(bridge_factory=bridge_factory)

    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    attached_session, output_queue = await service.attach_session(
        session.session_id,
        owner_user_id="owner-1",
    )

    await service.send_input(session.session_id, owner_user_id="owner-1", data="ls\n")
    await service.resize(session.session_id, owner_user_id="owner-1", cols=120, rows=40)
    await created_bridges[0].emit_output("hello")

    event = await asyncio.wait_for(output_queue.get(), timeout=0.1)

    assert session.group_id == "project-alpha"
    assert session.backend == "docker_container"
    assert attached_session.status == "attached"
    assert created_bridges[0].started is True
    assert created_bridges[0].inputs == ["ls\n"]
    assert created_bridges[0].resizes == [(120, 40)]
    assert event.event_type == "terminal.output"
    assert event.data == "hello"


@pytest.mark.asyncio
async def test_terminal_session_service_rejects_conflicting_owner() -> None:
    from services.terminal_sessions import (
        TerminalSessionConflictError,
        TerminalSessionService,
    )

    service = TerminalSessionService(bridge_factory=lambda **_: FakeBridge())

    await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )

    with pytest.raises(TerminalSessionConflictError, match="active terminal session"):
        await service.create_session(
            group_id="project-alpha",
            group_folder="project-alpha",
            owner_user_id="owner-2",
            requested_mode="container",
        )


@pytest.mark.asyncio
async def test_terminal_session_service_allows_owner_reconnect_before_timeout() -> None:
    from services.terminal_sessions import TerminalSessionService

    service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=0.2,
    )

    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await service.attach_session(session.session_id, owner_user_id="owner-1")
    await service.detach_session(session.session_id, owner_user_id="owner-1")

    reattached_session, _output_queue = await service.attach_session(
        session.session_id,
        owner_user_id="owner-1",
    )

    assert reattached_session.session_id == session.session_id
    assert reattached_session.status == "attached"
    assert reattached_session.reconnect_deadline is None


@pytest.mark.asyncio
async def test_terminal_session_service_closes_detached_session_after_timeout() -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=0.01,
    )

    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await service.attach_session(session.session_id, owner_user_id="owner-1")
    await service.detach_session(session.session_id, owner_user_id="owner-1")

    await asyncio.sleep(0.05)
    current = service.get_current_session("project-alpha")

    assert current is not None
    assert current.status == "closed"
    assert created_bridges[0].closed is True


@pytest.mark.asyncio
async def test_terminal_session_service_lists_sessions_by_workspace_folder() -> None:
    from services.terminal_sessions import TerminalSessionService

    service = TerminalSessionService(bridge_factory=lambda **_: FakeBridge())

    alpha = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    beta = await service.create_session(
        group_id="project-beta",
        group_folder="project-beta",
        owner_user_id="owner-2",
        requested_mode="container",
    )
    await service.attach_session(alpha.session_id, owner_user_id="owner-1")
    await service.attach_session(beta.session_id, owner_user_id="owner-2")
    await service.detach_session(beta.session_id, owner_user_id="owner-2")
    await service.close_session(beta.session_id, owner_user_id="owner-2")

    sessions = service.list_sessions()

    assert [item.group_folder for item in sessions] == ["project-alpha", "project-beta"]
    assert [item.status for item in sessions] == ["attached", "closed"]


@pytest.mark.asyncio
async def test_terminal_session_service_lists_sessions_with_deterministic_group_order() -> None:
    from services.terminal_sessions import TerminalSessionService

    service = TerminalSessionService(bridge_factory=lambda **_: FakeBridge())

    alpha = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await service.attach_session(alpha.session_id, owner_user_id="owner-1")

    beta = await service.create_session(
        group_id="project-beta",
        group_folder="project-beta",
        owner_user_id="owner-2",
        requested_mode="container",
    )
    await service.close_session(beta.session_id, owner_user_id="owner-2")

    sessions = service.list_sessions()

    assert [item.group_folder for item in sessions] == ["project-alpha", "project-beta"]
    assert [item.status for item in sessions] == ["attached", "closed"]


@pytest.mark.asyncio
async def test_terminal_session_service_list_sessions_reflects_lifecycle_transitions() -> None:
    from services.terminal_sessions import TerminalSessionService

    service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
    )

    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    assert service.list_sessions()[0].status == "created"

    await service.attach_session(session.session_id, owner_user_id="owner-1")
    assert service.list_sessions()[0].status == "attached"

    await service.detach_session(session.session_id, owner_user_id="owner-1")
    assert service.list_sessions()[0].status == "detached"

    await service.close_session(session.session_id, owner_user_id="owner-1")
    assert service.list_sessions()[0].status == "closed"


@pytest.mark.asyncio
async def test_terminal_session_service_force_close_ignores_session_owner() -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(bridge_factory=bridge_factory)
    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await service.attach_session(session.session_id, owner_user_id="owner-1")

    force_closed = await service.force_close_session_by_group("project-alpha")
    current = service.get_current_session("project-alpha")

    assert force_closed.status == "closed"
    assert current is not None
    assert current.status == "closed"
    assert created_bridges[0].closed is True


@pytest.mark.asyncio
async def test_terminal_session_service_replays_recent_output_after_reattach() -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
    )
    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _first_attach, queue = await service.attach_session(session.session_id, owner_user_id="owner-1")
    await created_bridges[0].emit_output("first\n")
    await created_bridges[0].emit_output("second\n")
    await asyncio.wait_for(queue.get(), timeout=0.1)
    await asyncio.wait_for(queue.get(), timeout=0.1)

    await service.detach_session(session.session_id, owner_user_id="owner-1")
    _reattach, replay_queue = await service.attach_session(session.session_id, owner_user_id="owner-1")

    replay_event_1 = await asyncio.wait_for(replay_queue.get(), timeout=0.1)
    replay_event_2 = await asyncio.wait_for(replay_queue.get(), timeout=0.1)

    assert replay_event_1.event_type == "terminal.output"
    assert replay_event_1.data == "first\n"
    assert replay_event_2.event_type == "terminal.output"
    assert replay_event_2.data == "second\n"


@pytest.mark.asyncio
async def test_terminal_session_service_replay_history_is_bounded_by_max_bytes() -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_max_bytes=10,
    )
    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _first_attach, queue = await service.attach_session(session.session_id, owner_user_id="owner-1")
    await created_bridges[0].emit_output("12345")
    await created_bridges[0].emit_output("67890")
    await created_bridges[0].emit_output("abc")
    await asyncio.wait_for(queue.get(), timeout=0.1)
    await asyncio.wait_for(queue.get(), timeout=0.1)
    await asyncio.wait_for(queue.get(), timeout=0.1)

    await service.detach_session(session.session_id, owner_user_id="owner-1")
    _reattach, replay_queue = await service.attach_session(session.session_id, owner_user_id="owner-1")

    replay_event_1 = await asyncio.wait_for(replay_queue.get(), timeout=0.1)
    replay_event_2 = await asyncio.wait_for(replay_queue.get(), timeout=0.1)

    assert replay_event_1.data == "67890"
    assert replay_event_2.data == "abc"


@pytest.mark.asyncio
async def test_terminal_session_service_returns_history_snapshot_with_metadata() -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_max_bytes=8,
    )
    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _first_attach, queue = await service.attach_session(session.session_id, owner_user_id="owner-1")
    await created_bridges[0].emit_output("12345")
    await created_bridges[0].emit_output("67890")
    await asyncio.wait_for(queue.get(), timeout=0.1)
    await asyncio.wait_for(queue.get(), timeout=0.1)

    snapshot = await service.get_history_by_group("project-alpha")

    assert snapshot.record.session_id == session.session_id
    assert snapshot.output == "67890"
    assert snapshot.output_bytes == 5
    assert snapshot.history_max_bytes == 8
    assert snapshot.truncated is True


@pytest.mark.asyncio
async def test_terminal_session_service_history_lookup_raises_for_missing_workspace() -> None:
    from services.terminal_sessions import TerminalSessionNotFoundError, TerminalSessionService

    service = TerminalSessionService(bridge_factory=lambda **_: FakeBridge())

    with pytest.raises(TerminalSessionNotFoundError, match="terminal session not found"):
        await service.get_history_by_group("missing-workspace")


@pytest.mark.asyncio
async def test_terminal_session_service_history_can_be_loaded_from_persisted_snapshot_after_restart(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    first_service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_max_bytes=16,
        history_persist_root=tmp_path / "terminal-history",
    )
    session = await first_service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _attached, queue = await first_service.attach_session(session.session_id, owner_user_id="owner-1")
    await created_bridges[0].emit_output("line-1\n")
    await created_bridges[0].emit_output("line-2\n")
    await asyncio.wait_for(queue.get(), timeout=0.1)
    await asyncio.wait_for(queue.get(), timeout=0.1)
    await first_service.close_session(session.session_id, owner_user_id="owner-1")

    restarted_service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_max_bytes=16,
        history_persist_root=tmp_path / "terminal-history",
    )
    snapshot = await restarted_service.get_history_by_group("project-alpha")

    assert snapshot.record.session_id == session.session_id
    assert snapshot.record.status == "closed"
    assert snapshot.output == "line-1\nline-2\n"
    assert snapshot.output_bytes == len("line-1\nline-2\n".encode("utf-8"))
    assert snapshot.history_max_bytes == 16
