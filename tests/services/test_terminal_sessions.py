from __future__ import annotations

import asyncio
from datetime import timedelta
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


class FlakyStartBridge(FakeBridge):
    def __init__(self, *, fail_on_start: bool) -> None:
        super().__init__()
        self._fail_on_start = fail_on_start

    async def start(self, on_event) -> None:
        if self._fail_on_start:
            raise RuntimeError("bridge start failed")
        await super().start(on_event)


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


@pytest.mark.asyncio
async def test_terminal_session_service_recovers_active_session_without_output_after_restart(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    persist_root = tmp_path / "terminal-history"
    first_service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
    )
    session = await first_service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )

    restarted_service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
        recover_active_sessions=True,
    )
    recovered = restarted_service.get_current_session("project-alpha")

    assert recovered is not None
    assert recovered.session_id == session.session_id
    assert recovered.status == "detached"
    assert recovered.reconnect_deadline is None


@pytest.mark.asyncio
async def test_terminal_session_service_owner_can_attach_recovered_session_after_restart(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    first_bridges: list[FakeBridge] = []

    def first_bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        first_bridges.append(bridge)
        return bridge

    persist_root = tmp_path / "terminal-history"
    first_service = TerminalSessionService(
        bridge_factory=first_bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
    )
    session = await first_service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _attached, queue = await first_service.attach_session(session.session_id, owner_user_id="owner-1")
    await first_bridges[0].emit_output("line-1\n")
    await asyncio.wait_for(queue.get(), timeout=0.1)

    restarted_bridges: list[FakeBridge] = []

    def restarted_bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        restarted_bridges.append(bridge)
        return bridge

    restarted_service = TerminalSessionService(
        bridge_factory=restarted_bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
        recover_active_sessions=True,
    )
    recovered = restarted_service.get_current_session("project-alpha")
    assert recovered is not None
    assert recovered.status == "detached"

    attached, replay_queue = await restarted_service.attach_session(
        session.session_id,
        owner_user_id="owner-1",
    )
    replay_event = await asyncio.wait_for(replay_queue.get(), timeout=0.1)
    await restarted_service.send_input(session.session_id, owner_user_id="owner-1", data="pwd\n")

    assert attached.status == "attached"
    assert replay_event.event_type == "terminal.output"
    assert replay_event.data == "line-1\n"
    assert len(restarted_bridges) == 1
    assert restarted_bridges[0].started is True
    assert restarted_bridges[0].inputs == ["pwd\n"]


@pytest.mark.asyncio
async def test_terminal_session_service_recovered_active_session_conflicts_for_other_owner(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import (
        TerminalSessionConflictError,
        TerminalSessionService,
    )

    persist_root = tmp_path / "terminal-history"
    first_service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
    )
    await first_service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )

    restarted_service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
        recover_active_sessions=True,
    )
    with pytest.raises(TerminalSessionConflictError, match="active terminal session"):
        await restarted_service.create_session(
            group_id="project-alpha",
            group_folder="project-alpha",
            owner_user_id="owner-2",
            requested_mode="container",
        )


@pytest.mark.asyncio
async def test_terminal_session_service_recovered_attach_failure_closes_session_and_allows_fresh_create(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    persist_root = tmp_path / "terminal-history"
    first_service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
    )
    session = await first_service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )

    start_attempt = 0

    def restarted_bridge_factory(**_: object) -> FakeBridge:
        nonlocal start_attempt
        start_attempt += 1
        return FlakyStartBridge(fail_on_start=start_attempt == 1)

    restarted_service = TerminalSessionService(
        bridge_factory=restarted_bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
        recover_active_sessions=True,
    )
    with pytest.raises(RuntimeError, match="bridge start failed"):
        await restarted_service.attach_session(
            session.session_id,
            owner_user_id="owner-1",
        )
    failed = restarted_service.get_current_session("project-alpha")
    assert failed is not None
    assert failed.status == "closed"

    fresh = await restarted_service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    assert fresh.session_id != session.session_id


@pytest.mark.asyncio
async def test_terminal_session_service_lists_history_inventory_with_persisted_fallback(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    persist_root = tmp_path / "terminal-history"
    first_service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_max_bytes=32,
        history_persist_root=persist_root,
    )
    alpha = await first_service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _alpha_attached, alpha_queue = await first_service.attach_session(alpha.session_id, owner_user_id="owner-1")
    await created_bridges[0].emit_output("alpha-output\n")
    await asyncio.wait_for(alpha_queue.get(), timeout=0.1)
    await first_service.close_session(alpha.session_id, owner_user_id="owner-1")

    second_service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_max_bytes=32,
        history_persist_root=persist_root,
    )
    beta = await second_service.create_session(
        group_id="project-beta",
        group_folder="project-beta",
        owner_user_id="owner-2",
        requested_mode="container",
    )
    _beta_attached, beta_queue = await second_service.attach_session(beta.session_id, owner_user_id="owner-2")
    await created_bridges[1].emit_output("beta-output\n")
    await asyncio.wait_for(beta_queue.get(), timeout=0.1)

    inventory = second_service.list_history_summaries()
    inventory_by_folder = {item.record.group_folder: item for item in inventory}

    assert [item.record.group_folder for item in inventory] == ["project-alpha", "project-beta"]
    assert inventory_by_folder["project-alpha"].record.status == "closed"
    assert inventory_by_folder["project-alpha"].output_bytes > 0
    assert inventory_by_folder["project-beta"].record.status == "attached"
    assert inventory_by_folder["project-beta"].output_bytes > 0


@pytest.mark.asyncio
async def test_terminal_session_service_lists_history_timeline_with_pagination(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_max_bytes=64,
        history_persist_root=tmp_path / "terminal-history",
    )
    first = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _first_attached, first_queue = await service.attach_session(first.session_id, owner_user_id="owner-1")
    await created_bridges[0].emit_output("first\n")
    await asyncio.wait_for(first_queue.get(), timeout=0.1)
    await service.close_session(first.session_id, owner_user_id="owner-1")

    second = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _second_attached, second_queue = await service.attach_session(second.session_id, owner_user_id="owner-1")
    await created_bridges[1].emit_output("second\n")
    await asyncio.wait_for(second_queue.get(), timeout=0.1)

    first_page = await service.list_history_timeline_by_group("project-alpha", limit=1, offset=0)
    second_page = await service.list_history_timeline_by_group("project-alpha", limit=1, offset=1)

    assert first_page.limit == 1
    assert first_page.offset == 0
    assert first_page.has_more is True
    assert len(first_page.items) == 1
    assert first_page.items[0].record.session_id == second.session_id

    assert second_page.limit == 1
    assert second_page.offset == 1
    assert second_page.has_more is False
    assert len(second_page.items) == 1
    assert second_page.items[0].record.session_id == first.session_id


@pytest.mark.asyncio
async def test_terminal_session_service_timeline_dedupes_latest_and_archived_snapshots(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )
    first = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await service.close_session(first.session_id, owner_user_id="owner-1")

    second = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await service.close_session(second.session_id, owner_user_id="owner-1")

    page = await service.list_history_timeline_by_group("project-alpha", limit=20, offset=0)
    session_ids = [item.record.session_id for item in page.items]

    assert session_ids == [second.session_id, first.session_id]
    assert page.has_more is False


@pytest.mark.asyncio
async def test_terminal_session_service_timeline_skips_malformed_archived_snapshots(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    persist_root = tmp_path / "terminal-history"
    service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
    )
    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await service.close_session(session.session_id, owner_user_id="owner-1")

    malformed = persist_root / "project-alpha" / "snapshots" / "broken.json"
    malformed.parent.mkdir(parents=True, exist_ok=True)
    malformed.write_text("{not-json", encoding="utf-8")

    restarted = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
    )
    page = await restarted.list_history_timeline_by_group("project-alpha", limit=20, offset=0)

    assert [item.record.session_id for item in page.items] == [session.session_id]


@pytest.mark.asyncio
async def test_terminal_session_service_timeline_raises_for_missing_workspace() -> None:
    from services.terminal_sessions import TerminalSessionNotFoundError, TerminalSessionService

    service = TerminalSessionService(bridge_factory=lambda **_: FakeBridge())

    with pytest.raises(TerminalSessionNotFoundError, match="terminal session not found"):
        await service.list_history_timeline_by_group("missing-workspace", limit=20, offset=0)


@pytest.mark.asyncio
async def test_terminal_session_service_filters_history_timeline_by_status(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )
    closed = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _closed_attached, closed_queue = await service.attach_session(closed.session_id, owner_user_id="owner-1")
    await created_bridges[0].emit_output("closed-output\n")
    await asyncio.wait_for(closed_queue.get(), timeout=0.1)
    await service.close_session(closed.session_id, owner_user_id="owner-1")

    attached = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _attached_record, attached_queue = await service.attach_session(attached.session_id, owner_user_id="owner-1")
    await created_bridges[1].emit_output("attached-output\n")
    await asyncio.wait_for(attached_queue.get(), timeout=0.1)

    page = await service.list_history_timeline_by_group(
        "project-alpha",
        limit=20,
        offset=0,
        status="closed",
    )

    assert [item.record.session_id for item in page.items] == [closed.session_id]


@pytest.mark.asyncio
async def test_terminal_session_service_filters_history_timeline_by_owner_and_prefix_with_pagination(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )
    first = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await service.close_session(first.session_id, owner_user_id="owner-1")

    second = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-2",
        requested_mode="container",
    )
    await service.close_session(second.session_id, owner_user_id="owner-2")

    third = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-2",
        requested_mode="container",
    )
    await service.close_session(third.session_id, owner_user_id="owner-2")

    first_page = await service.list_history_timeline_by_group(
        "project-alpha",
        limit=1,
        offset=0,
        owner_user_id="owner-2",
        session_id_prefix=third.session_id[:8],
    )
    second_page = await service.list_history_timeline_by_group(
        "project-alpha",
        limit=1,
        offset=1,
        owner_user_id="owner-2",
    )

    assert [item.record.session_id for item in first_page.items] == [third.session_id]
    assert first_page.has_more is False
    assert [item.record.session_id for item in second_page.items] == [second.session_id]
    assert second_page.has_more is False


@pytest.mark.asyncio
async def test_terminal_session_service_filters_history_timeline_by_snapshot_from_and_to(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    persist_root = tmp_path / "terminal-history"
    writer = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
    )
    first = await writer.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await writer.close_session(first.session_id, owner_user_id="owner-1")
    second = await writer.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await writer.close_session(second.session_id, owner_user_id="owner-1")
    third = await writer.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await writer.close_session(third.session_id, owner_user_id="owner-1")

    service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
    )

    page = await service.list_history_timeline_by_group("project-alpha", limit=20, offset=0)
    snapshots_by_id = {item.record.session_id: item.snapshot_at for item in page.items}
    second_snapshot_at = snapshots_by_id[second.session_id]
    third_snapshot_at = snapshots_by_id[third.session_id]
    lower_bound = min(second_snapshot_at, third_snapshot_at)
    upper_bound = max(second_snapshot_at, third_snapshot_at)

    from_filtered = await service.list_history_timeline_by_group(
        "project-alpha",
        limit=20,
        offset=0,
        snapshot_from=second_snapshot_at,
    )
    to_filtered = await service.list_history_timeline_by_group(
        "project-alpha",
        limit=20,
        offset=0,
        snapshot_to=second_snapshot_at,
    )
    bounded = await service.list_history_timeline_by_group(
        "project-alpha",
        limit=20,
        offset=0,
        snapshot_from=lower_bound,
        snapshot_to=upper_bound,
    )

    expected_from = [
        item.record.session_id
        for item in page.items
        if item.snapshot_at >= second_snapshot_at
    ]
    expected_to = [
        item.record.session_id
        for item in page.items
        if item.snapshot_at <= second_snapshot_at
    ]
    expected_bounded = {
        item.record.session_id
        for item in page.items
        if lower_bound <= item.snapshot_at <= upper_bound
    }

    assert [item.record.session_id for item in from_filtered.items] == expected_from
    assert [item.record.session_id for item in to_filtered.items] == expected_to
    assert {item.record.session_id for item in bounded.items} == expected_bounded


@pytest.mark.asyncio
async def test_terminal_session_service_time_range_filters_reject_invalid_bounds(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )
    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await service.close_session(session.session_id, owner_user_id="owner-1")
    page = await service.list_history_timeline_by_group("project-alpha", limit=20, offset=0)
    snapshot_at = page.items[0].snapshot_at

    with pytest.raises(ValueError, match="snapshot_from must be less than or equal to snapshot_to"):
        await service.list_history_timeline_by_group(
            "project-alpha",
            limit=20,
            offset=0,
            snapshot_from=snapshot_at,
            snapshot_to=snapshot_at - timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="snapshot_from must be less than or equal to snapshot_to"):
        await service.search_history_by_group(
            "project-alpha",
            query="error",
            limit=20,
            offset=0,
            snapshot_from=snapshot_at,
            snapshot_to=snapshot_at - timedelta(seconds=1),
        )


@pytest.mark.asyncio
async def test_terminal_session_service_get_history_snapshot_reads_archived_session(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )
    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    await service.close_session(session.session_id, owner_user_id="owner-1")

    snapshot = await service.get_history_snapshot_by_group("project-alpha", session.session_id)

    assert snapshot.record.session_id == session.session_id
    assert snapshot.record.status == "closed"


@pytest.mark.asyncio
async def test_terminal_session_service_get_history_snapshot_reads_latest_persisted_session(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    persist_root = tmp_path / "terminal-history"
    first_service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
    )
    session = await first_service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _attached, queue = await first_service.attach_session(session.session_id, owner_user_id="owner-1")
    await created_bridges[0].emit_output("persisted-latest\n")
    await asyncio.wait_for(queue.get(), timeout=0.1)

    restarted = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
    )
    snapshot = await restarted.get_history_snapshot_by_group("project-alpha", session.session_id)

    assert snapshot.record.session_id == session.session_id
    assert snapshot.record.status == "attached"
    assert snapshot.output == "persisted-latest\n"


@pytest.mark.asyncio
async def test_terminal_session_service_get_history_snapshot_reads_in_memory_session(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )
    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _attached, queue = await service.attach_session(session.session_id, owner_user_id="owner-1")
    await created_bridges[0].emit_output("in-memory-output\n")
    await asyncio.wait_for(queue.get(), timeout=0.1)

    snapshot = await service.get_history_snapshot_by_group("project-alpha", session.session_id)

    assert snapshot.record.session_id == session.session_id
    assert snapshot.record.status == "attached"
    assert snapshot.output == "in-memory-output\n"


@pytest.mark.asyncio
async def test_terminal_session_service_get_history_snapshot_raises_for_missing_session(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionNotFoundError, TerminalSessionService

    service = TerminalSessionService(
        bridge_factory=lambda **_: FakeBridge(),
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )

    with pytest.raises(TerminalSessionNotFoundError, match="terminal session not found"):
        await service.get_history_snapshot_by_group("project-alpha", "missing-session")


@pytest.mark.asyncio
async def test_terminal_session_service_searches_history_output_with_pagination(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    persist_root = tmp_path / "terminal-history"
    first_service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
    )
    archived = await first_service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _archived_record, archived_queue = await first_service.attach_session(
        archived.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error one\nERROR two\n")
    await asyncio.wait_for(archived_queue.get(), timeout=0.1)
    await first_service.close_session(archived.session_id, owner_user_id="owner-1")

    latest_without_match = await first_service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _latest_record, latest_queue = await first_service.attach_session(
        latest_without_match.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("all good here\n")
    await asyncio.wait_for(latest_queue.get(), timeout=0.1)
    await first_service.close_session(latest_without_match.session_id, owner_user_id="owner-1")

    restarted = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root,
    )
    active = await restarted.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-2",
        requested_mode="container",
    )
    _active_record, active_queue = await restarted.attach_session(active.session_id, owner_user_id="owner-2")
    await created_bridges[2].emit_output("memory eRrOr hit\n")
    await asyncio.wait_for(active_queue.get(), timeout=0.1)

    first_page = await restarted.search_history_by_group(
        "project-alpha",
        query="error",
        limit=1,
        offset=0,
    )
    second_page = await restarted.search_history_by_group(
        "project-alpha",
        query="error",
        limit=1,
        offset=1,
    )

    assert first_page.total == 2
    assert first_page.has_more is True
    assert len(first_page.items) == 1
    assert first_page.items[0].record.session_id == archived.session_id
    assert first_page.items[0].match_count == 2
    assert first_page.items[0].snippets
    assert "error" in first_page.items[0].snippets[0].lower()
    assert [item.match_index for item in first_page.items[0].snippet_matches] == [0, 1]
    assert [item.match_offset for item in first_page.items[0].snippet_matches] == [0, 10]
    assert first_page.items[0].snippet_matches[0].text == first_page.items[0].snippets[0]

    assert second_page.total == 2
    assert second_page.has_more is False
    assert len(second_page.items) == 1
    assert second_page.items[0].record.session_id == active.session_id
    assert second_page.items[0].match_count == 1
    assert [item.match_index for item in second_page.items[0].snippet_matches] == [0]
    assert [item.match_offset for item in second_page.items[0].snippet_matches] == [7]


@pytest.mark.asyncio
async def test_terminal_session_service_search_supports_explicit_sort_modes(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    oldest = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _oldest_record, oldest_queue = await service.attach_session(
        oldest.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error in oldest session\n")
    await asyncio.wait_for(oldest_queue.get(), timeout=0.1)
    await service.close_session(oldest.session_id, owner_user_id="owner-1")

    middle = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _middle_record, middle_queue = await service.attach_session(
        middle.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("error error error in middle session\n")
    await asyncio.wait_for(middle_queue.get(), timeout=0.1)
    await service.close_session(middle.session_id, owner_user_id="owner-1")

    newest = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _newest_record, newest_queue = await service.attach_session(
        newest.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[2].emit_output("error error in newest session\n")
    await asyncio.wait_for(newest_queue.get(), timeout=0.1)
    await service.close_session(newest.session_id, owner_user_id="owner-1")

    relevance_page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )
    newest_page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=2,
        offset=0,
        sort="newest",
    )
    newest_second_page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=2,
        offset=2,
        sort="newest",
    )
    oldest_page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
        sort="oldest",
    )

    assert [item.record.session_id for item in relevance_page.items] == [
        middle.session_id,
        newest.session_id,
        oldest.session_id,
    ]
    assert [item.record.session_id for item in newest_page.items] == [
        newest.session_id,
        middle.session_id,
    ]
    assert newest_page.has_more is True
    assert [item.record.session_id for item in newest_second_page.items] == [oldest.session_id]
    assert newest_second_page.has_more is False
    assert [item.record.session_id for item in oldest_page.items] == [
        oldest.session_id,
        middle.session_id,
        newest.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_prefers_concentrated_matches_over_newer_sparse_matches(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    concentrated = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _concentrated_record, concentrated_queue = await service.attach_session(
        concentrated.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error error trailing text\n")
    await asyncio.wait_for(concentrated_queue.get(), timeout=0.1)
    await service.close_session(concentrated.session_id, owner_user_id="owner-1")

    sparse = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _sparse_record, sparse_queue = await service.attach_session(
        sparse.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output(f"error {'x' * 40} error trailing text\n")
    await asyncio.wait_for(sparse_queue.get(), timeout=0.1)
    await service.close_session(sparse.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        concentrated.session_id,
        sparse.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_prefers_earlier_first_match_when_cluster_span_is_tied(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    earlier = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _earlier_record, earlier_queue = await service.attach_session(
        earlier.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error--error.....\n")
    await asyncio.wait_for(earlier_queue.get(), timeout=0.1)
    await service.close_session(earlier.session_id, owner_user_id="owner-1")

    later = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _later_record, later_queue = await service.attach_session(
        later.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output(".....error--error\n")
    await asyncio.wait_for(later_queue.get(), timeout=0.1)
    await service.close_session(later.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        earlier.session_id,
        later.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_uses_recency_only_as_a_weak_tie_breaker(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    older = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _older_record, older_queue = await service.attach_session(
        older.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error--error\n")
    await asyncio.wait_for(older_queue.get(), timeout=0.1)
    await service.close_session(older.session_id, owner_user_id="owner-1")

    newer = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _newer_record, newer_queue = await service.attach_session(
        newer.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("error--error\n")
    await asyncio.wait_for(newer_queue.get(), timeout=0.1)
    await service.close_session(newer.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        newer.session_id,
        older.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_pagination_slices_the_globally_ranked_result_set(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    concentrated = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _concentrated_record, concentrated_queue = await service.attach_session(
        concentrated.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error error bridge text\n")
    await asyncio.wait_for(concentrated_queue.get(), timeout=0.1)
    await service.close_session(concentrated.session_id, owner_user_id="owner-1")

    earlier = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _earlier_record, earlier_queue = await service.attach_session(
        earlier.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("error--error.....\n")
    await asyncio.wait_for(earlier_queue.get(), timeout=0.1)
    await service.close_session(earlier.session_id, owner_user_id="owner-1")

    sparse = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _sparse_record, sparse_queue = await service.attach_session(
        sparse.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[2].emit_output(f"error {'x' * 20} error\n")
    await asyncio.wait_for(sparse_queue.get(), timeout=0.1)
    await service.close_session(sparse.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=2,
        offset=1,
    )

    assert page.total == 3
    assert page.has_more is False
    assert [item.record.session_id for item in page.items] == [
        earlier.session_id,
        sparse.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_prefers_whole_word_matches_over_substring_only_matches(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    exact_word = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _exact_word_record, exact_word_queue = await service.attach_session(
        exact_word.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("zzzz error zzzz error\n")
    await asyncio.wait_for(exact_word_queue.get(), timeout=0.1)
    await service.close_session(exact_word.session_id, owner_user_id="owner-1")

    substring_only = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _substring_only_record, substring_only_queue = await service.attach_session(
        substring_only.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("terror terror\n")
    await asyncio.wait_for(substring_only_queue.get(), timeout=0.1)
    await service.close_session(substring_only.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        exact_word.session_id,
        substring_only.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_prefers_earlier_first_whole_word_offset_when_counts_tie(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    earlier_whole_word = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _earlier_record, earlier_queue = await service.attach_session(
        earlier_whole_word.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("aa error bbbbbbbbbbbbbbbb error\n")
    await asyncio.wait_for(earlier_queue.get(), timeout=0.1)
    await service.close_session(earlier_whole_word.session_id, owner_user_id="owner-1")

    later_whole_word = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _later_record, later_queue = await service.attach_session(
        later_whole_word.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("bbbbbbbbbbbbbbbb error error\n")
    await asyncio.wait_for(later_queue.get(), timeout=0.1)
    await service.close_session(later_whole_word.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        earlier_whole_word.session_id,
        later_whole_word.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_falls_back_to_m8_5_17_signals_when_no_whole_word_match(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    concentrated = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _concentrated_record, concentrated_queue = await service.attach_session(
        concentrated.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output(f"terror terror {'y' * 200}\n")
    await asyncio.wait_for(concentrated_queue.get(), timeout=0.1)
    await service.close_session(concentrated.session_id, owner_user_id="owner-1")

    sparse = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _sparse_record, sparse_queue = await service.attach_session(
        sparse.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output(f"terror {'x' * 20} terror\n")
    await asyncio.wait_for(sparse_queue.get(), timeout=0.1)
    await service.close_session(sparse.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        concentrated.session_id,
        sparse.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_word_boundary_pagination_uses_global_ordering(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    exact_word = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _exact_word_record, exact_word_queue = await service.attach_session(
        exact_word.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("zzzz error zzzz error\n")
    await asyncio.wait_for(exact_word_queue.get(), timeout=0.1)
    await service.close_session(exact_word.session_id, owner_user_id="owner-1")

    later_exact_word = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _later_exact_word_record, later_exact_word_queue = await service.attach_session(
        later_exact_word.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("bbbbbbbbbbbbbbbb error error\n")
    await asyncio.wait_for(later_exact_word_queue.get(), timeout=0.1)
    await service.close_session(later_exact_word.session_id, owner_user_id="owner-1")

    substring_only = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _substring_only_record, substring_only_queue = await service.attach_session(
        substring_only.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[2].emit_output("terror terror\n")
    await asyncio.wait_for(substring_only_queue.get(), timeout=0.1)
    await service.close_session(substring_only.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=2,
        offset=1,
    )

    assert page.total == 3
    assert page.has_more is False
    assert [item.record.session_id for item in page.items] == [
        later_exact_word.session_id,
        substring_only.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_prefers_line_start_whole_word_matches_over_mid_line_whole_word_matches(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 19, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _line_start_record, line_start_queue = await service.attach_session(
        line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output(f"{'p' * 40}\nerror: alpha\n{'q' * 20}\nerror: beta\n")
    await asyncio.wait_for(line_start_queue.get(), timeout=0.1)
    await service.close_session(line_start.session_id, owner_user_id="owner-1")

    mid_line_only = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _mid_line_record, mid_line_queue = await service.attach_session(
        mid_line_only.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("aa error bb error\n")
    await asyncio.wait_for(mid_line_queue.get(), timeout=0.1)
    await service.close_session(mid_line_only.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        line_start.session_id,
        mid_line_only.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_prefers_earlier_line_start_whole_word_offset_when_counts_tie(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 19, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    earlier_line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _earlier_record, earlier_queue = await service.attach_session(
        earlier_line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output(f"{'p' * 18} error alpha\nerror beta\n")
    await asyncio.wait_for(earlier_queue.get(), timeout=0.1)
    await service.close_session(earlier_line_start.session_id, owner_user_id="owner-1")

    later_line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _later_record, later_queue = await service.attach_session(
        later_line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output(f"aa error alpha {'x' * 40}\nerror beta\n")
    await asyncio.wait_for(later_queue.get(), timeout=0.1)
    await service.close_session(later_line_start.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        earlier_line_start.session_id,
        later_line_start.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_falls_back_to_m8_5_18_signals_when_no_line_start_whole_word_match(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 19, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    concentrated = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _concentrated_record, concentrated_queue = await service.attach_session(
        concentrated.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output(f"aa error error {'y' * 200}\n")
    await asyncio.wait_for(concentrated_queue.get(), timeout=0.1)
    await service.close_session(concentrated.session_id, owner_user_id="owner-1")

    sparse = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _sparse_record, sparse_queue = await service.attach_session(
        sparse.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output(f"aa error {'x' * 20} error\n")
    await asyncio.wait_for(sparse_queue.get(), timeout=0.1)
    await service.close_session(sparse.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        concentrated.session_id,
        sparse.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_line_boundary_pagination_uses_global_ordering(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 19, 10, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    line_start_dominant = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _line_start_dominant_record, line_start_dominant_queue = await service.attach_session(
        line_start_dominant.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output(f"{'p' * 50}\nerror one\n{'q' * 30}\nerror two\n")
    await asyncio.wait_for(line_start_dominant_queue.get(), timeout=0.1)
    await service.close_session(line_start_dominant.session_id, owner_user_id="owner-1")

    mixed_line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _mixed_line_start_record, mixed_line_start_queue = await service.attach_session(
        mixed_line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output(f"aa error mid {'x' * 50}\nerror line\n")
    await asyncio.wait_for(mixed_line_start_queue.get(), timeout=0.1)
    await service.close_session(mixed_line_start.session_id, owner_user_id="owner-1")

    mid_line_only = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _mid_line_only_record, mid_line_only_queue = await service.attach_session(
        mid_line_only.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[2].emit_output("aa error bb error\n")
    await asyncio.wait_for(mid_line_only_queue.get(), timeout=0.1)
    await service.close_session(mid_line_only.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=2,
        offset=1,
    )

    assert page.total == 3
    assert page.has_more is False
    assert [item.record.session_id for item in page.items] == [
        mixed_line_start.session_id,
        mid_line_only.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_prefers_cleaner_line_start_results_when_line_start_strength_is_tied(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 19, 11, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    cleaner_line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _cleaner_record, cleaner_queue = await service.attach_session(
        cleaner_line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error start\nterror noise\nterror noise\n")
    await asyncio.wait_for(cleaner_queue.get(), timeout=0.1)
    await service.close_session(cleaner_line_start.session_id, owner_user_id="owner-1")

    noisier_line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _noisier_record, noisier_queue = await service.attach_session(
        noisier_line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("error start\nmid error here\ntail error there\n")
    await asyncio.wait_for(noisier_queue.get(), timeout=0.1)
    await service.close_session(noisier_line_start.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        cleaner_line_start.session_id,
        noisier_line_start.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_preserves_first_line_start_tie_break_when_noise_is_tied(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 19, 11, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    earlier_line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _earlier_record, earlier_queue = await service.attach_session(
        earlier_line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error alpha\nprefix error beta\nterror gamma\n")
    await asyncio.wait_for(earlier_queue.get(), timeout=0.1)
    await service.close_session(earlier_line_start.session_id, owner_user_id="owner-1")

    later_line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _later_record, later_queue = await service.attach_session(
        later_line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("prefix error alpha\nerror beta\nterror gamma\n")
    await asyncio.wait_for(later_queue.get(), timeout=0.1)
    await service.close_session(later_line_start.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        earlier_line_start.session_id,
        later_line_start.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_line_start_quality_pagination_uses_global_ordering(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 19, 11, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    cleaner_line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _cleaner_record, cleaner_queue = await service.attach_session(
        cleaner_line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error start\nterror noise\nterror noise\n")
    await asyncio.wait_for(cleaner_queue.get(), timeout=0.1)
    await service.close_session(cleaner_line_start.session_id, owner_user_id="owner-1")

    noisier_line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _noisier_record, noisier_queue = await service.attach_session(
        noisier_line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("error start\nmid error here\ntail error there\n")
    await asyncio.wait_for(noisier_queue.get(), timeout=0.1)
    await service.close_session(noisier_line_start.session_id, owner_user_id="owner-1")

    no_line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _no_line_start_record, no_line_start_queue = await service.attach_session(
        no_line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[2].emit_output("aa error bb error cc\n")
    await asyncio.wait_for(no_line_start_queue.get(), timeout=0.1)
    await service.close_session(no_line_start.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=2,
        offset=1,
    )

    assert page.total == 3
    assert page.has_more is False
    assert [item.record.session_id for item in page.items] == [
        noisier_line_start.session_id,
        no_line_start.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_prefers_line_start_log_markers_over_plain_line_start_hits(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 19, 12, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    marker_style = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _marker_record, marker_queue = await service.attach_session(
        marker_style.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error: aa\nterror zz\n")
    await asyncio.wait_for(marker_queue.get(), timeout=0.1)
    await service.close_session(marker_style.session_id, owner_user_id="owner-1")

    plain_line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _plain_record, plain_queue = await service.attach_session(
        plain_line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("error aa.\nterror zz\n")
    await asyncio.wait_for(plain_queue.get(), timeout=0.1)
    await service.close_session(plain_line_start.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        marker_style.session_id,
        plain_line_start.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_prefers_earlier_line_start_log_marker_offset_when_counts_tie(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 19, 12, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    earlier_marker = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _earlier_record, earlier_queue = await service.attach_session(
        earlier_marker.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error: aa\nerror bb.\n")
    await asyncio.wait_for(earlier_queue.get(), timeout=0.1)
    await service.close_session(earlier_marker.session_id, owner_user_id="owner-1")

    later_marker = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _later_record, later_queue = await service.attach_session(
        later_marker.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("error aa.\nerror: bb\n")
    await asyncio.wait_for(later_queue.get(), timeout=0.1)
    await service.close_session(later_marker.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        earlier_marker.session_id,
        later_marker.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_falls_back_to_m8_5_20_signals_when_no_log_markers_exist(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 19, 12, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    cleaner_plain = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _cleaner_record, cleaner_queue = await service.attach_session(
        cleaner_plain.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error aa.\nterror zz\n")
    await asyncio.wait_for(cleaner_queue.get(), timeout=0.1)
    await service.close_session(cleaner_plain.session_id, owner_user_id="owner-1")

    noisier_plain = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _noisier_record, noisier_queue = await service.attach_session(
        noisier_plain.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("error aa.\nmid error here\n")
    await asyncio.wait_for(noisier_queue.get(), timeout=0.1)
    await service.close_session(noisier_plain.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
    )

    assert [item.record.session_id for item in page.items] == [
        cleaner_plain.session_id,
        noisier_plain.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_relevance_log_marker_pagination_uses_global_ordering(
    tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone

    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    current_time = datetime(2026, 3, 19, 12, 0, tzinfo=timezone.utc)

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
        now_func=now_func,
    )

    earlier_marker = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _earlier_record, earlier_queue = await service.attach_session(
        earlier_marker.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error: aa\nerror bb.\n")
    await asyncio.wait_for(earlier_queue.get(), timeout=0.1)
    await service.close_session(earlier_marker.session_id, owner_user_id="owner-1")

    later_marker = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _later_record, later_queue = await service.attach_session(
        later_marker.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("error aa.\nerror: bb\n")
    await asyncio.wait_for(later_queue.get(), timeout=0.1)
    await service.close_session(later_marker.session_id, owner_user_id="owner-1")

    plain_line_start = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _plain_record, plain_queue = await service.attach_session(
        plain_line_start.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[2].emit_output("error aa.\nerror bb.\n")
    await asyncio.wait_for(plain_queue.get(), timeout=0.1)
    await service.close_session(plain_line_start.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=2,
        offset=1,
    )

    assert page.total == 3
    assert page.has_more is False
    assert [item.record.session_id for item in page.items] == [
        later_marker.session_id,
        plain_line_start.session_id,
    ]


@pytest.mark.asyncio
async def test_terminal_session_service_search_returns_empty_page_when_no_match(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )
    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _record, queue = await service.attach_session(session.session_id, owner_user_id="owner-1")
    await created_bridges[0].emit_output("no incidents\n")
    await asyncio.wait_for(queue.get(), timeout=0.1)
    await service.close_session(session.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=20,
        offset=0,
    )

    assert page.total == 0
    assert page.has_more is False
    assert page.items == []


@pytest.mark.asyncio
async def test_terminal_session_service_search_filters_snapshots_by_status(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )

    closed_owner_1 = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _closed_owner_1_attached, queue_0 = await service.attach_session(
        closed_owner_1.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error in closed owner one\n")
    await asyncio.wait_for(queue_0.get(), timeout=0.1)
    await service.close_session(closed_owner_1.session_id, owner_user_id="owner-1")

    attached_owner_2 = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-2",
        requested_mode="container",
    )
    _attached_owner_2_record, queue_1 = await service.attach_session(
        attached_owner_2.session_id,
        owner_user_id="owner-2",
    )
    await created_bridges[1].emit_output("error in attached owner two\n")
    await asyncio.wait_for(queue_1.get(), timeout=0.1)

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
        status="closed",
    )

    assert page.total == 1
    assert len(page.items) == 1
    assert page.items[0].record.session_id == closed_owner_1.session_id
    assert page.items[0].record.status == "closed"


@pytest.mark.asyncio
async def test_terminal_session_service_search_filters_snapshots_by_snapshot_to(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )

    older = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _older_attached, older_queue = await service.attach_session(
        older.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error in older session\n")
    await asyncio.wait_for(older_queue.get(), timeout=0.1)
    await service.close_session(older.session_id, owner_user_id="owner-1")

    newer = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _newer_attached, newer_queue = await service.attach_session(
        newer.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("error in newer session\n")
    await asyncio.wait_for(newer_queue.get(), timeout=0.1)
    await service.close_session(newer.session_id, owner_user_id="owner-1")

    timeline_page = await service.list_history_timeline_by_group("project-alpha", limit=20, offset=0)
    snapshots_by_id = {item.record.session_id: item.snapshot_at for item in timeline_page.items}

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=20,
        offset=0,
        snapshot_to=snapshots_by_id[older.session_id],
    )

    assert page.total == 1
    assert [item.record.session_id for item in page.items] == [older.session_id]


@pytest.mark.asyncio
async def test_terminal_session_service_search_filters_snapshots_by_owner_user_id(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )

    owner_1_session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _owner_1_record, queue_0 = await service.attach_session(
        owner_1_session.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error in owner one session\n")
    await asyncio.wait_for(queue_0.get(), timeout=0.1)
    await service.close_session(owner_1_session.session_id, owner_user_id="owner-1")

    owner_2_session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-2",
        requested_mode="container",
    )
    _owner_2_record, queue_1 = await service.attach_session(
        owner_2_session.session_id,
        owner_user_id="owner-2",
    )
    await created_bridges[1].emit_output("error in owner two session\n")
    await asyncio.wait_for(queue_1.get(), timeout=0.1)
    await service.close_session(owner_2_session.session_id, owner_user_id="owner-2")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
        owner_user_id="owner-2",
    )

    assert page.total == 1
    assert len(page.items) == 1
    assert page.items[0].record.session_id == owner_2_session.session_id
    assert page.items[0].record.owner_user_id == "owner-2"


@pytest.mark.asyncio
async def test_terminal_session_service_search_filters_snapshots_by_session_id_prefix(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )

    first_session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _first_record, queue_0 = await service.attach_session(
        first_session.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error in first session\n")
    await asyncio.wait_for(queue_0.get(), timeout=0.1)
    await service.close_session(first_session.session_id, owner_user_id="owner-1")

    second_session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _second_record, queue_1 = await service.attach_session(
        second_session.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[1].emit_output("error in second session\n")
    await asyncio.wait_for(queue_1.get(), timeout=0.1)
    await service.close_session(second_session.session_id, owner_user_id="owner-1")

    page = await service.search_history_by_group(
        "project-alpha",
        query="error",
        limit=10,
        offset=0,
        session_id_prefix=second_session.session_id[:12],
    )

    assert page.total == 1
    assert len(page.items) == 1
    assert page.items[0].record.session_id == second_session.session_id


@pytest.mark.asyncio
async def test_terminal_session_service_search_raises_when_filters_remove_all_snapshots(
    tmp_path: Path,
) -> None:
    from services.terminal_sessions import TerminalSessionNotFoundError, TerminalSessionService

    created_bridges: list[FakeBridge] = []

    def bridge_factory(**_: object) -> FakeBridge:
        bridge = FakeBridge()
        created_bridges.append(bridge)
        return bridge

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=tmp_path / "terminal-history",
    )

    session = await service.create_session(
        group_id="project-alpha",
        group_folder="project-alpha",
        owner_user_id="owner-1",
        requested_mode="container",
    )
    _record, queue = await service.attach_session(
        session.session_id,
        owner_user_id="owner-1",
    )
    await created_bridges[0].emit_output("error in only session\n")
    await asyncio.wait_for(queue.get(), timeout=0.1)
    await service.close_session(session.session_id, owner_user_id="owner-1")

    with pytest.raises(TerminalSessionNotFoundError, match="terminal session not found"):
        await service.search_history_by_group(
            "project-alpha",
            query="error",
            limit=10,
            offset=0,
            owner_user_id="owner-2",
        )


@pytest.mark.asyncio
async def test_terminal_session_service_search_raises_for_missing_workspace() -> None:
    from services.terminal_sessions import TerminalSessionNotFoundError, TerminalSessionService

    service = TerminalSessionService(bridge_factory=lambda **_: FakeBridge())

    with pytest.raises(TerminalSessionNotFoundError, match="terminal session not found"):
        await service.search_history_by_group(
            "missing-workspace",
            query="error",
            limit=20,
            offset=0,
        )
