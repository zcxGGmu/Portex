"""Terminal session lifecycle service."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Literal
from uuid import uuid4

from infra.exec.security import validate_path
from services.terminal_bridge import TerminalBridge, TerminalBridgeEvent

TerminalRequestedMode = Literal["openai", "host", "container"]
TerminalBackendName = Literal["docker_container"]
TerminalSessionStatus = Literal["created", "attached", "detached", "closed", "exited"]
TerminalHistorySearchSort = Literal["relevance", "newest", "oldest"]
DEFAULT_TERMINAL_HISTORY_PERSIST_ROOT = Path(__file__).resolve().parents[1] / "data" / "terminal-history"
_TERMINAL_HISTORY_FILENAME = "latest.json"
_TERMINAL_HISTORY_SNAPSHOTS_DIRNAME = "snapshots"
_ACTIVE_RECOVERABLE_STATUSES: set[TerminalSessionStatus] = {"created", "attached", "detached"}
_TERMINAL_ARCHIVE_STATUSES: set[TerminalSessionStatus] = {"closed", "exited"}
_DEFAULT_SEARCH_SNIPPET_LIMIT = 3
_DEFAULT_SEARCH_SNIPPET_CONTEXT_CHARS = 40
_NO_WHOLE_WORD_MATCH_OFFSET = 1 << 60
_NO_LINE_START_WHOLE_WORD_MATCH_OFFSET = 1 << 60
_NO_LINE_START_LOG_MARKER_MATCH_OFFSET = 1 << 60
_NO_LINE_START_DELIMITED_LOG_MARKER_MATCH_OFFSET = 1 << 60
_NO_LINE_START_EXACT_TAG_MARKER_MATCH_OFFSET = 1 << 60
_NO_LINE_START_EXACT_TAG_COLON_MARKER_MATCH_OFFSET = 1 << 60
_NO_LINE_START_SQUARE_BRACKET_EXACT_TAG_DASH_MARKER_MATCH_OFFSET = 1 << 60
_NO_LINE_START_PAREN_WRAPPER_MARKER_MATCH_OFFSET = 1 << 60
_NO_LINE_START_BRACE_WRAPPER_MARKER_MATCH_OFFSET = 1 << 60
_NO_LINE_START_NON_SQUARE_BRACKET_EXACT_TAG_COLON_MARKER_MATCH_OFFSET = 1 << 60
_NO_LINE_START_NON_SQUARE_BRACKET_EXACT_TAG_DASH_MARKER_MATCH_OFFSET = 1 << 60
_NO_LINE_START_EXACT_TAG_MATCH_OFFSET = 1 << 60
_NO_LINE_START_SQUARE_BRACKET_EXACT_TAG_MATCH_OFFSET = 1 << 60
_NO_LINE_START_SQUARE_BRACKET_PLAIN_EXACT_TAG_MATCH_OFFSET = 1 << 60
_NO_LINE_START_PAREN_WRAPPER_PLAIN_EXACT_TAG_MATCH_OFFSET = 1 << 60
_NO_LINE_START_BRACE_WRAPPER_PLAIN_EXACT_TAG_MATCH_OFFSET = 1 << 60
_NO_LINE_START_ANGLE_WRAPPER_PLAIN_EXACT_TAG_MATCH_OFFSET = 1 << 60
_NO_LINE_START_PLAIN_EXACT_TAG_SINGLE_SPACE_SEPARATOR_MATCH_OFFSET = 1 << 60
_NO_LINE_START_NON_SINGLE_SPACE_PLAIN_EXACT_TAG_SEPARATOR_MATCH_OFFSET = 1 << 60
_NO_LINE_START_PLAIN_EXACT_TAG_PAYLOADLESS_SEPARATOR_MATCH_OFFSET = 1 << 60
_NO_LINE_START_PLAIN_EXACT_TAG_TAB_PREFIXED_PAYLOAD_MATCH_OFFSET = 1 << 60
_NO_LINE_START_PLAIN_EXACT_TAG_MULTI_SPACE_PAYLOAD_MATCH_OFFSET = 1 << 60
_NO_LINE_START_PLAIN_EXACT_TAG_SPACE_PREFIXED_MIXED_WHITESPACE_PAYLOAD_MATCH_OFFSET = 1 << 60
_NO_LINE_START_PLAIN_EXACT_TAG_OTHER_LEADING_MIXED_WHITESPACE_PAYLOAD_MATCH_OFFSET = 1 << 60
_NO_LINE_START_PLAIN_EXACT_TAG_OTHER_LEADING_WHITESPACE_PAYLOAD_MATCH_OFFSET = 1 << 60
_NO_LINE_START_PUNCTUATION_WRAP_MATCH_OFFSET = 1 << 60
_LINE_START_PUNCTUATION_WRAP_PAIRS = {
    "[": "]",
    "(": ")",
    "{": "}",
    "<": ">",
}


class TerminalBackendUnsupportedError(RuntimeError):
    """Raised when the requested terminal backend cannot support terminal sessions."""


class TerminalBackendDisabledError(RuntimeError):
    """Raised when the requested terminal backend is intentionally disabled."""


class TerminalSessionConflictError(RuntimeError):
    """Raised when a workspace already has an active session owned by another user."""


class TerminalSessionNotFoundError(RuntimeError):
    """Raised when a terminal session does not exist."""


class TerminalSessionOwnershipError(RuntimeError):
    """Raised when a user attempts to control another user's terminal session."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class TerminalSessionEvent:
    event_type: str
    data: str | None = None
    exit_code: int | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class TerminalSessionRecord:
    session_id: str
    group_id: str
    group_folder: str
    owner_user_id: str
    backend: TerminalBackendName
    container_name: str | None
    status: TerminalSessionStatus
    created_at: datetime
    last_attached_at: datetime | None = None
    reconnect_deadline: datetime | None = None


@dataclass(frozen=True, slots=True)
class TerminalSessionHistorySnapshot:
    record: TerminalSessionRecord
    snapshot_at: datetime
    output: str
    output_bytes: int
    history_max_bytes: int
    truncated: bool


@dataclass(frozen=True, slots=True)
class TerminalSessionHistorySummary:
    record: TerminalSessionRecord
    snapshot_at: datetime
    output_bytes: int
    history_max_bytes: int
    truncated: bool


@dataclass(frozen=True, slots=True)
class TerminalSessionHistoryTimelinePage:
    limit: int
    offset: int
    has_more: bool
    items: list[TerminalSessionHistorySummary]


@dataclass(frozen=True, slots=True)
class TerminalSessionHistorySearchMatch:
    record: TerminalSessionRecord
    snapshot_at: datetime
    match_count: int
    snippets: list[str]
    snippet_matches: list["TerminalSessionHistorySearchSnippet"]


@dataclass(frozen=True, slots=True)
class TerminalSessionHistorySearchSnippet:
    text: str
    match_index: int
    match_offset: int


@dataclass(frozen=True, slots=True)
class TerminalSessionHistorySearchPage:
    query: str
    limit: int
    offset: int
    total: int
    has_more: bool
    items: list[TerminalSessionHistorySearchMatch]


@dataclass(frozen=True, slots=True)
class _TerminalSessionHistorySearchCandidate:
    match: TerminalSessionHistorySearchMatch
    line_start_log_marker_match_count: int
    first_line_start_log_marker_offset: int
    line_start_delimited_log_marker_match_count: int
    first_line_start_delimited_log_marker_offset: int
    line_start_exact_tag_marker_match_count: int
    first_line_start_exact_tag_marker_offset: int
    line_start_exact_tag_colon_marker_match_count: int
    first_line_start_exact_tag_colon_marker_offset: int
    line_start_square_bracket_exact_tag_dash_marker_match_count: int
    first_line_start_square_bracket_exact_tag_dash_marker_offset: int
    line_start_paren_wrapper_marker_match_count: int
    first_line_start_paren_wrapper_marker_offset: int
    line_start_brace_wrapper_marker_match_count: int
    first_line_start_brace_wrapper_marker_offset: int
    line_start_non_square_bracket_exact_tag_colon_marker_match_count: int
    first_line_start_non_square_bracket_exact_tag_colon_marker_offset: int
    line_start_non_square_bracket_exact_tag_dash_marker_match_count: int
    first_line_start_non_square_bracket_exact_tag_dash_marker_offset: int
    line_start_exact_tag_match_count: int
    first_line_start_exact_tag_offset: int
    line_start_square_bracket_exact_tag_match_count: int
    first_line_start_square_bracket_exact_tag_offset: int
    first_line_start_square_bracket_plain_exact_tag_offset: int
    line_start_paren_wrapper_plain_exact_tag_match_count: int
    first_line_start_paren_wrapper_plain_exact_tag_offset: int
    line_start_brace_wrapper_plain_exact_tag_match_count: int
    first_line_start_brace_wrapper_plain_exact_tag_offset: int
    line_start_angle_wrapper_plain_exact_tag_match_count: int
    first_line_start_angle_wrapper_plain_exact_tag_offset: int
    line_start_plain_exact_tag_single_space_separator_match_count: int
    first_line_start_plain_exact_tag_single_space_separator_offset: int
    conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset: int
    conditional_line_start_plain_exact_tag_payloadless_separator_match_count: int
    conditional_first_line_start_plain_exact_tag_payloadless_separator_offset: int
    conditional_line_start_plain_exact_tag_tab_prefixed_payload_match_count: int
    conditional_first_line_start_plain_exact_tag_tab_prefixed_payload_offset: int
    conditional_line_start_plain_exact_tag_multi_space_payload_match_count: int
    conditional_first_line_start_plain_exact_tag_multi_space_payload_offset: int
    conditional_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match_count: int
    conditional_first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset: int
    conditional_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count: int
    conditional_first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset: int
    conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset: int
    conditional_non_exact_tag_punctuation_wrap_match_count: int
    line_start_punctuation_wrap_match_count: int
    first_line_start_punctuation_wrap_offset: int
    whole_word_match_count: int
    line_start_whole_word_match_count: int
    conditional_non_line_start_whole_word_match_count: int
    first_line_start_whole_word_offset: int
    first_whole_word_offset: int
    cluster_span: int
    first_match_offset: int
    match_density: float


@dataclass(slots=True)
class _ManagedTerminalSession:
    record: TerminalSessionRecord
    bridge: TerminalBridge | None
    output_queue: asyncio.Queue[TerminalSessionEvent] | None = None
    reconnect_task: asyncio.Task[None] | None = None
    output_history_chunks: deque[str] = field(default_factory=deque)
    output_history_bytes: int = 0
    output_history_truncated: bool = False


class TerminalSessionService:
    """Manage process-local terminal sessions and short reconnect windows."""

    def __init__(
        self,
        *,
        bridge_factory: Callable[..., TerminalBridge],
        reconnect_timeout_seconds: float = 30.0,
        history_max_bytes: int = 32_768,
        history_persist_root: Path | str | None = None,
        recover_active_sessions: bool = False,
        now_func: Callable[[], datetime] | None = None,
    ) -> None:
        self._bridge_factory = bridge_factory
        self._reconnect_timeout_seconds = reconnect_timeout_seconds
        self._history_max_bytes = max(0, history_max_bytes)
        if history_persist_root is None:
            history_persist_root = DEFAULT_TERMINAL_HISTORY_PERSIST_ROOT
        self._history_persist_root = Path(history_persist_root).expanduser().resolve()
        self._history_persist_root.mkdir(parents=True, exist_ok=True)
        self._now = now_func or _utcnow
        self._sessions_by_group: dict[str, _ManagedTerminalSession] = {}
        self._sessions_by_id: dict[str, _ManagedTerminalSession] = {}
        self._lock = asyncio.Lock()
        if recover_active_sessions:
            self._recover_active_sessions_from_persisted_snapshots()

    async def create_session(
        self,
        *,
        group_id: str,
        group_folder: str,
        owner_user_id: str,
        requested_mode: TerminalRequestedMode = "container",
    ) -> TerminalSessionRecord:
        backend = self._resolve_backend(requested_mode)

        async with self._lock:
            existing = self._sessions_by_group.get(group_folder)
            if existing is not None and existing.record.status not in {"closed", "exited"}:
                if existing.record.owner_user_id != owner_user_id:
                    raise TerminalSessionConflictError("active terminal session already owned by another user")
                return existing.record
            if existing is not None:
                self._drop_session(existing)

            session_id = uuid4().hex
            bridge = self._bridge_factory(
                group_id=group_id,
                group_folder=group_folder,
                owner_user_id=owner_user_id,
                session_id=session_id,
            )
            container_name = getattr(bridge, "container_name", None)
            record = TerminalSessionRecord(
                session_id=session_id,
                group_id=group_id,
                group_folder=group_folder,
                owner_user_id=owner_user_id,
                backend=backend,
                container_name=container_name if isinstance(container_name, str) else None,
                status="created",
                created_at=self._now(),
            )
            managed = _ManagedTerminalSession(record=record, bridge=bridge)
            self._sessions_by_group[group_folder] = managed
            self._sessions_by_id[session_id] = managed

        await bridge.start(lambda event: self._handle_bridge_event(session_id, event))
        async with self._lock:
            managed = self._sessions_by_id.get(session_id)
            persist_snapshot = None if managed is None else self._build_history_snapshot(managed)
        if persist_snapshot is not None:
            await self._persist_history_snapshot_best_effort(persist_snapshot)
        return self.get_current_session(group_folder) or record

    def get_current_session(self, group_folder: str) -> TerminalSessionRecord | None:
        session = self._sessions_by_group.get(group_folder)
        return None if session is None else session.record

    def list_sessions(self) -> list[TerminalSessionRecord]:
        """Return current in-memory session snapshots ordered by workspace folder."""

        records = [managed.record for managed in self._sessions_by_group.values()]
        records.sort(key=lambda item: (item.group_folder, item.session_id))
        return records

    def list_history_summaries(self) -> list[TerminalSessionHistorySummary]:
        """Return merged in-memory and persisted history summaries by workspace folder."""

        summaries_by_folder: dict[str, TerminalSessionHistorySummary] = {}

        for managed in self._sessions_by_group.values():
            snapshot = self._build_history_snapshot(managed)
            summaries_by_folder[snapshot.record.group_folder] = self._to_history_summary(snapshot)

        for snapshot in self._list_persisted_history_snapshots():
            group_folder = snapshot.record.group_folder
            if group_folder in summaries_by_folder:
                continue
            summaries_by_folder[group_folder] = self._to_history_summary(snapshot)

        items = list(summaries_by_folder.values())
        items.sort(key=lambda item: (item.record.group_folder, item.record.session_id))
        return items

    async def list_history_timeline_by_group(
        self,
        group_folder: str,
        *,
        limit: int = 20,
        offset: int = 0,
        status: TerminalSessionStatus | None = None,
        owner_user_id: str | None = None,
        session_id_prefix: str | None = None,
        snapshot_from: datetime | None = None,
        snapshot_to: datetime | None = None,
    ) -> TerminalSessionHistoryTimelinePage:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if offset < 0:
            raise ValueError("offset must be non-negative")
        snapshots = await self._list_merged_history_snapshots_by_group(group_folder)
        filtered = self._filter_history_snapshots(
            snapshots,
            status=status,
            owner_user_id=owner_user_id,
            session_id_prefix=session_id_prefix,
            snapshot_from=snapshot_from,
            snapshot_to=snapshot_to,
        )
        if not filtered:
            raise TerminalSessionNotFoundError("terminal session not found")

        summaries = [self._to_history_summary(item) for item in filtered]
        page_items = summaries[offset : offset + limit]
        has_more = (offset + limit) < len(summaries)
        return TerminalSessionHistoryTimelinePage(
            limit=limit,
            offset=offset,
            has_more=has_more,
            items=page_items,
        )

    async def get_history_snapshot_by_group(
        self,
        group_folder: str,
        session_id: str,
    ) -> TerminalSessionHistorySnapshot:
        normalized_session_id = session_id.strip()
        if normalized_session_id == "":
            raise TerminalSessionNotFoundError("terminal session not found")

        snapshots = await self._list_merged_history_snapshots_by_group(group_folder)
        for snapshot in snapshots:
            if snapshot.record.session_id == normalized_session_id:
                return snapshot
        raise TerminalSessionNotFoundError("terminal session not found")

    async def search_history_by_group(
        self,
        group_folder: str,
        *,
        query: str,
        limit: int = 20,
        offset: int = 0,
        sort: TerminalHistorySearchSort = "relevance",
        status: TerminalSessionStatus | None = None,
        owner_user_id: str | None = None,
        session_id_prefix: str | None = None,
        snapshot_from: datetime | None = None,
        snapshot_to: datetime | None = None,
        snippet_limit: int = _DEFAULT_SEARCH_SNIPPET_LIMIT,
        snippet_context_chars: int = _DEFAULT_SEARCH_SNIPPET_CONTEXT_CHARS,
    ) -> TerminalSessionHistorySearchPage:
        normalized_query = query.strip()
        normalized_sort = self._normalize_search_sort(sort)
        if normalized_query == "":
            raise ValueError("query must not be empty")
        if limit <= 0:
            raise ValueError("limit must be positive")
        if offset < 0:
            raise ValueError("offset must be non-negative")
        if snippet_limit <= 0:
            raise ValueError("snippet_limit must be positive")
        if snippet_context_chars < 0:
            raise ValueError("snippet_context_chars must be non-negative")

        snapshots = await self._list_merged_history_snapshots_by_group(group_folder)
        filtered = self._filter_history_snapshots(
            snapshots,
            status=status,
            owner_user_id=owner_user_id,
            session_id_prefix=session_id_prefix,
            snapshot_from=snapshot_from,
            snapshot_to=snapshot_to,
        )
        if not filtered:
            raise TerminalSessionNotFoundError("terminal session not found")
        items = self._search_history_snapshots(
            filtered,
            query=normalized_query,
            sort=normalized_sort,
            snippet_limit=snippet_limit,
            snippet_context_chars=snippet_context_chars,
        )
        total = len(items)
        page_items = items[offset : offset + limit]
        has_more = (offset + limit) < total
        return TerminalSessionHistorySearchPage(
            query=normalized_query,
            limit=limit,
            offset=offset,
            total=total,
            has_more=has_more,
            items=page_items,
        )

    async def attach_session(
        self,
        session_id: str,
        *,
        owner_user_id: str,
    ) -> tuple[TerminalSessionRecord, asyncio.Queue[TerminalSessionEvent]]:
        bridge_to_start: TerminalBridge | None = None
        persist_snapshot: TerminalSessionHistorySnapshot | None = None
        async with self._lock:
            managed = self._require_session(session_id)
            self._require_owner(managed, owner_user_id)
            self._cancel_reconnect_task(managed)
            queue: asyncio.Queue[TerminalSessionEvent] = asyncio.Queue()
            now = self._now()
            managed.output_queue = queue
            for chunk in managed.output_history_chunks:
                queue.put_nowait(TerminalSessionEvent(event_type="terminal.output", data=chunk))
            managed.record = replace(
                managed.record,
                status="attached",
                last_attached_at=now,
                reconnect_deadline=None,
            )
            if managed.bridge is None:
                managed.bridge = self._bridge_factory(
                    group_id=managed.record.group_id,
                    group_folder=managed.record.group_folder,
                    owner_user_id=managed.record.owner_user_id,
                    session_id=managed.record.session_id,
                )
                container_name = getattr(managed.bridge, "container_name", None)
                managed.record = replace(
                    managed.record,
                    container_name=container_name if isinstance(container_name, str) else managed.record.container_name,
                )
                bridge_to_start = managed.bridge
            persist_snapshot = self._build_history_snapshot(managed)
            record = managed.record

        if bridge_to_start is not None:
            try:
                await bridge_to_start.start(lambda event: self._handle_bridge_event(session_id, event))
            except Exception:
                failed_snapshot: TerminalSessionHistorySnapshot | None = None
                async with self._lock:
                    managed = self._sessions_by_id.get(session_id)
                    if managed is not None:
                        managed.bridge = None
                        managed.output_queue = None
                        managed.record = replace(
                            managed.record,
                            status="closed",
                            reconnect_deadline=None,
                        )
                        failed_snapshot = self._build_history_snapshot(managed)
                if failed_snapshot is not None:
                    await self._persist_history_snapshot_best_effort(failed_snapshot)
                raise

        if persist_snapshot is not None:
            await self._persist_history_snapshot_best_effort(persist_snapshot)
        return record, queue

    async def detach_session(
        self,
        session_id: str,
        *,
        owner_user_id: str,
    ) -> TerminalSessionRecord:
        persist_snapshot: TerminalSessionHistorySnapshot | None = None
        async with self._lock:
            managed = self._require_session(session_id)
            self._require_owner(managed, owner_user_id)
            deadline = self._now() + timedelta(seconds=self._reconnect_timeout_seconds)
            managed.output_queue = None
            managed.record = replace(
                managed.record,
                status="detached",
                reconnect_deadline=deadline,
            )
            self._cancel_reconnect_task(managed)
            managed.reconnect_task = asyncio.create_task(self._expire_detached_session(session_id, deadline))
            persist_snapshot = self._build_history_snapshot(managed)
            record = managed.record
        if persist_snapshot is not None:
            await self._persist_history_snapshot_best_effort(persist_snapshot)
        return record

    async def send_input(self, session_id: str, *, owner_user_id: str, data: str) -> None:
        managed = self._require_session(session_id)
        self._require_owner(managed, owner_user_id)
        bridge = self._require_live_bridge(managed)
        await bridge.send_input(data)

    async def resize(self, session_id: str, *, owner_user_id: str, cols: int, rows: int) -> None:
        managed = self._require_session(session_id)
        self._require_owner(managed, owner_user_id)
        bridge = self._require_live_bridge(managed)
        await bridge.resize(cols=cols, rows=rows)

    async def get_history_by_group(self, group_folder: str) -> TerminalSessionHistorySnapshot:
        async with self._lock:
            managed = self._sessions_by_group.get(group_folder)
            if managed is None:
                snapshot = None
            else:
                snapshot = self._build_history_snapshot(managed)
        if snapshot is not None:
            return snapshot
        persisted = await asyncio.to_thread(self._load_persisted_history_snapshot, group_folder)
        if persisted is None:
            raise TerminalSessionNotFoundError("terminal session not found")
        return persisted

    async def close_session_by_group(
        self,
        group_folder: str,
        *,
        owner_user_id: str,
    ) -> TerminalSessionRecord:
        async with self._lock:
            managed = self._sessions_by_group.get(group_folder)
            if managed is None:
                raise TerminalSessionNotFoundError("terminal session not found")
            self._require_owner(managed, owner_user_id)
        return await self.close_session(managed.record.session_id, owner_user_id=owner_user_id)

    async def force_close_session_by_group(self, group_folder: str) -> TerminalSessionRecord:
        async with self._lock:
            managed = self._sessions_by_group.get(group_folder)
            if managed is None:
                raise TerminalSessionNotFoundError("terminal session not found")
            self._cancel_reconnect_task(managed)
            managed.output_queue = None
            managed.record = replace(
                managed.record,
                status="closed",
                reconnect_deadline=None,
            )
            persist_snapshot = self._build_history_snapshot(managed)
            bridge = managed.bridge
        if bridge is not None:
            await bridge.close()
        await self._persist_history_snapshot_best_effort(persist_snapshot)
        return managed.record

    async def close_session(
        self,
        session_id: str,
        *,
        owner_user_id: str,
    ) -> TerminalSessionRecord:
        async with self._lock:
            managed = self._require_session(session_id)
            self._require_owner(managed, owner_user_id)
            self._cancel_reconnect_task(managed)
            managed.output_queue = None
            managed.record = replace(
                managed.record,
                status="closed",
                reconnect_deadline=None,
            )
            persist_snapshot = self._build_history_snapshot(managed)
            bridge = managed.bridge
        if bridge is not None:
            await bridge.close()
        await self._persist_history_snapshot_best_effort(persist_snapshot)
        return managed.record

    def _resolve_backend(self, requested_mode: TerminalRequestedMode) -> TerminalBackendName:
        if requested_mode == "container":
            return "docker_container"
        if requested_mode == "host":
            raise TerminalBackendDisabledError("host_process backend is disabled for terminal sessions")
        raise TerminalBackendUnsupportedError("openai_runtime backend does not support terminal sessions")

    def _require_session(self, session_id: str) -> _ManagedTerminalSession:
        managed = self._sessions_by_id.get(session_id)
        if managed is None:
            raise TerminalSessionNotFoundError("terminal session not found")
        return managed

    def _require_owner(self, managed: _ManagedTerminalSession, owner_user_id: str) -> None:
        if managed.record.owner_user_id != owner_user_id:
            raise TerminalSessionOwnershipError("terminal session is owned by another user")

    @staticmethod
    def _require_live_bridge(managed: _ManagedTerminalSession) -> TerminalBridge:
        if managed.bridge is None:
            raise TerminalSessionNotFoundError("terminal session bridge unavailable")
        return managed.bridge

    def _cancel_reconnect_task(self, managed: _ManagedTerminalSession) -> None:
        task = managed.reconnect_task
        managed.reconnect_task = None
        if task is not None and not task.done():
            task.cancel()

    def _drop_session(self, managed: _ManagedTerminalSession) -> None:
        self._sessions_by_group.pop(managed.record.group_folder, None)
        self._sessions_by_id.pop(managed.record.session_id, None)
        self._cancel_reconnect_task(managed)

    async def _handle_bridge_event(self, session_id: str, event: TerminalBridgeEvent | dict[str, object]) -> None:
        if isinstance(event, dict):
            bridge_event = TerminalBridgeEvent(
                type=str(event.get("type", "")),
                data=event.get("data") if isinstance(event.get("data"), str) else None,
                exit_code=event.get("exit_code") if isinstance(event.get("exit_code"), int) else None,
                error=event.get("error") if isinstance(event.get("error"), str) else None,
            )
        else:
            bridge_event = event

        queue: asyncio.Queue[TerminalSessionEvent] | None = None
        persist_snapshot: TerminalSessionHistorySnapshot | None = None
        async with self._lock:
            managed = self._sessions_by_id.get(session_id)
            if managed is None:
                return

            if bridge_event.type == "output":
                if isinstance(bridge_event.data, str):
                    self._append_output_history(managed, bridge_event.data)
                    persist_snapshot = self._build_history_snapshot(managed)
                queue = managed.output_queue
            elif bridge_event.type == "exit":
                self._cancel_reconnect_task(managed)
                managed.record = replace(
                    managed.record,
                    status="exited",
                    reconnect_deadline=None,
                )
                persist_snapshot = self._build_history_snapshot(managed)
                queue = managed.output_queue
            elif bridge_event.type == "error":
                queue = managed.output_queue

        if persist_snapshot is not None:
            await self._persist_history_snapshot_best_effort(persist_snapshot)

        if queue is None and bridge_event.type != "output":
            return

        if bridge_event.type == "output":
            if queue is not None:
                await queue.put(TerminalSessionEvent(event_type="terminal.output", data=bridge_event.data))
        elif bridge_event.type == "exit":
            if queue is not None:
                await queue.put(TerminalSessionEvent(event_type="terminal.exit", exit_code=bridge_event.exit_code))
        elif bridge_event.type == "error":
            if queue is not None:
                await queue.put(TerminalSessionEvent(event_type="terminal.error", error=bridge_event.error))

    def _append_output_history(self, managed: _ManagedTerminalSession, chunk: str) -> None:
        if self._history_max_bytes <= 0 or chunk == "":
            if self._history_max_bytes <= 0:
                managed.output_history_chunks.clear()
                managed.output_history_bytes = 0
            return

        chunk_bytes = len(chunk.encode("utf-8", errors="ignore"))
        if chunk_bytes <= 0:
            return

        managed.output_history_chunks.append(chunk)
        managed.output_history_bytes += chunk_bytes

        while managed.output_history_bytes > self._history_max_bytes and managed.output_history_chunks:
            removed = managed.output_history_chunks.popleft()
            managed.output_history_bytes -= len(removed.encode("utf-8", errors="ignore"))
            managed.output_history_truncated = True
        if managed.output_history_bytes < 0:
            managed.output_history_bytes = 0

    async def _expire_detached_session(self, session_id: str, deadline: datetime) -> None:
        await asyncio.sleep(self._reconnect_timeout_seconds)
        async with self._lock:
            managed = self._sessions_by_id.get(session_id)
            if managed is None:
                return
            if managed.record.status != "detached":
                return
            if managed.record.reconnect_deadline != deadline:
                return
            managed.record = replace(
                managed.record,
                status="closed",
                reconnect_deadline=None,
            )
            persist_snapshot = self._build_history_snapshot(managed)
            bridge = managed.bridge
        if bridge is not None:
            await bridge.close()
        await self._persist_history_snapshot_best_effort(persist_snapshot)

    def _build_history_snapshot(self, managed: _ManagedTerminalSession) -> TerminalSessionHistorySnapshot:
        return TerminalSessionHistorySnapshot(
            record=managed.record,
            snapshot_at=self._now(),
            output="".join(managed.output_history_chunks),
            output_bytes=managed.output_history_bytes,
            history_max_bytes=self._history_max_bytes,
            truncated=managed.output_history_truncated,
        )

    async def _persist_history_snapshot_best_effort(
        self,
        snapshot: TerminalSessionHistorySnapshot,
    ) -> None:
        try:
            await asyncio.to_thread(self._persist_history_snapshot, snapshot)
        except Exception:
            return None

    def _persist_history_snapshot(self, snapshot: TerminalSessionHistorySnapshot) -> None:
        payload = self._history_snapshot_payload(snapshot)
        latest_path = self._history_snapshot_path(snapshot.record.group_folder)
        self._write_snapshot_payload(latest_path, payload)
        if snapshot.record.status in _TERMINAL_ARCHIVE_STATUSES:
            archive_path = self._history_archive_snapshot_path(
                snapshot.record.group_folder,
                snapshot.record.session_id,
            )
            self._write_snapshot_payload(archive_path, payload)

    def _history_snapshot_payload(self, snapshot: TerminalSessionHistorySnapshot) -> dict[str, object]:
        return {
            "record": {
                "session_id": snapshot.record.session_id,
                "group_id": snapshot.record.group_id,
                "group_folder": snapshot.record.group_folder,
                "owner_user_id": snapshot.record.owner_user_id,
                "backend": snapshot.record.backend,
                "container_name": snapshot.record.container_name,
                "status": snapshot.record.status,
                "created_at": snapshot.record.created_at.isoformat(),
                "last_attached_at": (
                    snapshot.record.last_attached_at.isoformat()
                    if snapshot.record.last_attached_at is not None
                    else None
                ),
                "reconnect_deadline": (
                    snapshot.record.reconnect_deadline.isoformat()
                    if snapshot.record.reconnect_deadline is not None
                    else None
                ),
            },
            "snapshot_at": snapshot.snapshot_at.isoformat(),
            "output": snapshot.output,
            "output_bytes": snapshot.output_bytes,
            "history_max_bytes": snapshot.history_max_bytes,
            "truncated": snapshot.truncated,
        }

    @staticmethod
    def _write_snapshot_payload(path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temp.replace(path)

    def _load_persisted_history_snapshot(self, group_folder: str) -> TerminalSessionHistorySnapshot | None:
        path = self._history_snapshot_path(group_folder)
        return self._load_persisted_history_snapshot_from_path(path)

    def _load_persisted_history_snapshot_from_path(self, path: Path) -> TerminalSessionHistorySnapshot | None:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            record_payload = payload["record"]
            output = payload["output"]
        except Exception:
            return None
        if not isinstance(record_payload, dict) or not isinstance(output, str):
            return None
        if record_payload.get("backend") != "docker_container":
            return None

        created_at = self._parse_persisted_datetime(record_payload.get("created_at"))
        if created_at is None:
            return None
        status = record_payload.get("status")
        if status not in {"created", "attached", "detached", "closed", "exited"}:
            return None

        record = TerminalSessionRecord(
            session_id=str(record_payload.get("session_id", "")),
            group_id=str(record_payload.get("group_id", "")),
            group_folder=str(record_payload.get("group_folder", "")),
            owner_user_id=str(record_payload.get("owner_user_id", "")),
            backend="docker_container",
            container_name=record_payload.get("container_name")
            if isinstance(record_payload.get("container_name"), str)
            else None,
            status=status,
            created_at=created_at,
            last_attached_at=self._parse_persisted_datetime(record_payload.get("last_attached_at")),
            reconnect_deadline=self._parse_persisted_datetime(record_payload.get("reconnect_deadline")),
        )
        if record.session_id == "" or record.group_id == "" or record.group_folder == "" or record.owner_user_id == "":
            return None

        output_bytes = payload.get("output_bytes")
        if not isinstance(output_bytes, int) or output_bytes < 0:
            output_bytes = len(output.encode("utf-8", errors="ignore"))
        history_max_bytes = payload.get("history_max_bytes")
        if not isinstance(history_max_bytes, int) or history_max_bytes < 0:
            history_max_bytes = self._history_max_bytes
        truncated = payload.get("truncated")
        if not isinstance(truncated, bool):
            truncated = False
        snapshot_at = self._parse_persisted_datetime(payload.get("snapshot_at"))
        if snapshot_at is None:
            snapshot_at = created_at
        return TerminalSessionHistorySnapshot(
            record=record,
            snapshot_at=snapshot_at,
            output=output,
            output_bytes=output_bytes,
            history_max_bytes=history_max_bytes,
            truncated=truncated,
        )

    def _history_snapshot_path(self, group_folder: str) -> Path:
        candidate = (self._history_persist_root / group_folder / _TERMINAL_HISTORY_FILENAME).resolve(strict=False)
        if not validate_path(candidate, [self._history_persist_root]):
            raise ValueError("invalid terminal history root")
        return candidate

    def _history_archive_snapshots_root(self, group_folder: str) -> Path:
        candidate = (
            self._history_persist_root / group_folder / _TERMINAL_HISTORY_SNAPSHOTS_DIRNAME
        ).resolve(strict=False)
        if not validate_path(candidate, [self._history_persist_root]):
            raise ValueError("invalid terminal history root")
        return candidate

    def _history_archive_snapshot_path(self, group_folder: str, session_id: str) -> Path:
        normalized_session_id = session_id.strip()
        if (
            normalized_session_id == ""
            or "/" in normalized_session_id
            or "\\" in normalized_session_id
        ):
            raise ValueError("invalid terminal session id")
        candidate = (
            self._history_archive_snapshots_root(group_folder) / f"{normalized_session_id}.json"
        ).resolve(strict=False)
        if not validate_path(candidate, [self._history_persist_root]):
            raise ValueError("invalid terminal history root")
        return candidate

    def _list_persisted_history_archived_snapshots(self, group_folder: str) -> list[TerminalSessionHistorySnapshot]:
        snapshots_root = self._history_archive_snapshots_root(group_folder)
        if not snapshots_root.exists():
            return []
        try:
            snapshot_paths = sorted(
                (
                    path
                    for path in snapshots_root.iterdir()
                    if path.is_file() and path.suffix == ".json"
                ),
                key=lambda item: item.name,
            )
        except Exception:
            return []
        snapshots: list[TerminalSessionHistorySnapshot] = []
        for snapshot_path in snapshot_paths:
            snapshot = self._load_persisted_history_snapshot_from_path(snapshot_path)
            if snapshot is None:
                continue
            if snapshot.record.group_folder != group_folder:
                continue
            snapshots.append(snapshot)
        return snapshots

    def _load_history_timeline_from_persistence(
        self,
        group_folder: str,
    ) -> tuple[TerminalSessionHistorySnapshot | None, list[TerminalSessionHistorySnapshot]]:
        latest = self._load_persisted_history_snapshot(group_folder)
        archived = self._list_persisted_history_archived_snapshots(group_folder)
        return latest, archived

    @staticmethod
    def _dedupe_timeline_snapshots(
        *,
        in_memory: TerminalSessionHistorySnapshot | None,
        latest: TerminalSessionHistorySnapshot | None,
        archived: list[TerminalSessionHistorySnapshot],
    ) -> list[TerminalSessionHistorySnapshot]:
        snapshots_by_session: dict[str, TerminalSessionHistorySnapshot] = {}
        for snapshot in [in_memory, latest, *archived]:
            if snapshot is None:
                continue
            existing = snapshots_by_session.get(snapshot.record.session_id)
            if existing is None:
                snapshots_by_session[snapshot.record.session_id] = snapshot
                continue
            if snapshot.snapshot_at > existing.snapshot_at:
                snapshots_by_session[snapshot.record.session_id] = snapshot
        return list(snapshots_by_session.values())

    async def _list_merged_history_snapshots_by_group(
        self,
        group_folder: str,
    ) -> list[TerminalSessionHistorySnapshot]:
        async with self._lock:
            managed = self._sessions_by_group.get(group_folder)
            in_memory_snapshot = None if managed is None else self._build_history_snapshot(managed)

        persisted_latest, persisted_archived = await asyncio.to_thread(
            self._load_history_timeline_from_persistence,
            group_folder,
        )
        snapshots = self._dedupe_timeline_snapshots(
            in_memory=in_memory_snapshot,
            latest=persisted_latest,
            archived=persisted_archived,
        )
        if not snapshots:
            raise TerminalSessionNotFoundError("terminal session not found")
        snapshots.sort(
            key=lambda item: (item.snapshot_at, item.record.session_id),
            reverse=True,
        )
        return snapshots

    @staticmethod
    def _filter_history_snapshots(
        snapshots: list[TerminalSessionHistorySnapshot],
        *,
        status: TerminalSessionStatus | None,
        owner_user_id: str | None,
        session_id_prefix: str | None,
        snapshot_from: datetime | None = None,
        snapshot_to: datetime | None = None,
    ) -> list[TerminalSessionHistorySnapshot]:
        normalized_snapshot_from = TerminalSessionService._normalize_snapshot_bound(snapshot_from)
        normalized_snapshot_to = TerminalSessionService._normalize_snapshot_bound(snapshot_to)
        if (
            normalized_snapshot_from is not None
            and normalized_snapshot_to is not None
            and normalized_snapshot_from > normalized_snapshot_to
        ):
            raise ValueError("snapshot_from must be less than or equal to snapshot_to")

        normalized_owner_user_id = None if owner_user_id is None else owner_user_id.strip()
        if normalized_owner_user_id == "":
            normalized_owner_user_id = None
        normalized_session_id_prefix = None if session_id_prefix is None else session_id_prefix.strip()
        if normalized_session_id_prefix == "":
            normalized_session_id_prefix = None

        filtered: list[TerminalSessionHistorySnapshot] = []
        for snapshot in snapshots:
            if status is not None and snapshot.record.status != status:
                continue
            if (
                normalized_owner_user_id is not None
                and snapshot.record.owner_user_id != normalized_owner_user_id
            ):
                continue
            if (
                normalized_session_id_prefix is not None
                and not snapshot.record.session_id.startswith(normalized_session_id_prefix)
            ):
                continue
            if normalized_snapshot_from is not None and snapshot.snapshot_at < normalized_snapshot_from:
                continue
            if normalized_snapshot_to is not None and snapshot.snapshot_at > normalized_snapshot_to:
                continue
            filtered.append(snapshot)
        return filtered

    @staticmethod
    def _normalize_snapshot_bound(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @classmethod
    def _search_history_snapshots(
        cls,
        snapshots: list[TerminalSessionHistorySnapshot],
        *,
        query: str,
        sort: TerminalHistorySearchSort,
        snippet_limit: int,
        snippet_context_chars: int,
    ) -> list[TerminalSessionHistorySearchMatch]:
        query_length = len(query)
        if query_length <= 0:
            return []

        candidates: list[_TerminalSessionHistorySearchCandidate] = []
        for snapshot in snapshots:
            offsets = cls._find_case_insensitive_match_offsets(snapshot.output, query)
            if not offsets:
                continue
            snippet_matches = cls._build_search_snippets(
                snapshot.output,
                offsets,
                query_length=query_length,
                snippet_limit=snippet_limit,
                snippet_context_chars=snippet_context_chars,
            )
            match = TerminalSessionHistorySearchMatch(
                record=snapshot.record,
                snapshot_at=snapshot.snapshot_at,
                match_count=len(offsets),
                snippets=[item.text for item in snippet_matches],
                snippet_matches=snippet_matches,
            )
            candidates.append(
                cls._build_search_candidate(
                    match=match,
                    text=snapshot.output,
                    offsets=offsets,
                    query_length=query_length,
                    output_length=len(snapshot.output),
                )
            )
        return cls._sort_history_search_matches(candidates, sort=sort)

    @staticmethod
    def _build_search_candidate(
        *,
        match: TerminalSessionHistorySearchMatch,
        text: str,
        offsets: list[int],
        query_length: int,
        output_length: int,
    ) -> _TerminalSessionHistorySearchCandidate:
        whole_word_match_count, first_whole_word_offset = TerminalSessionService._count_whole_word_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_whole_word_match_count,
            first_line_start_whole_word_offset,
        ) = TerminalSessionService._count_line_start_whole_word_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_log_marker_match_count,
            first_line_start_log_marker_offset,
        ) = TerminalSessionService._count_line_start_log_marker_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_delimited_log_marker_match_count,
            first_line_start_delimited_log_marker_offset,
        ) = TerminalSessionService._count_line_start_delimited_log_marker_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_punctuation_wrap_match_count,
            first_line_start_punctuation_wrap_offset,
        ) = TerminalSessionService._count_line_start_punctuation_wrap_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_exact_tag_match_count,
            first_line_start_exact_tag_offset,
        ) = TerminalSessionService._count_line_start_exact_tag_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_exact_tag_colon_marker_match_count,
            first_line_start_exact_tag_colon_marker_offset,
        ) = TerminalSessionService._count_line_start_exact_tag_colon_marker_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_square_bracket_exact_tag_dash_marker_match_count,
            first_line_start_square_bracket_exact_tag_dash_marker_offset,
        ) = TerminalSessionService._count_line_start_square_bracket_exact_tag_dash_marker_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_paren_wrapper_marker_match_count,
            first_line_start_paren_wrapper_marker_offset,
        ) = TerminalSessionService._count_line_start_paren_wrapper_marker_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_brace_wrapper_marker_match_count,
            first_line_start_brace_wrapper_marker_offset,
        ) = TerminalSessionService._count_line_start_brace_wrapper_marker_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_non_square_bracket_exact_tag_colon_marker_match_count,
            first_line_start_non_square_bracket_exact_tag_colon_marker_offset,
        ) = TerminalSessionService._count_line_start_non_square_bracket_exact_tag_colon_marker_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_non_square_bracket_exact_tag_dash_marker_match_count,
            first_line_start_non_square_bracket_exact_tag_dash_marker_offset,
        ) = TerminalSessionService._count_line_start_non_square_bracket_exact_tag_dash_marker_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_square_bracket_exact_tag_match_count,
            first_line_start_square_bracket_exact_tag_offset,
        ) = TerminalSessionService._count_line_start_square_bracket_exact_tag_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            _line_start_square_bracket_plain_exact_tag_match_count,
            first_line_start_square_bracket_plain_exact_tag_offset,
        ) = TerminalSessionService._count_line_start_square_bracket_plain_exact_tag_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_paren_wrapper_plain_exact_tag_match_count,
            first_line_start_paren_wrapper_plain_exact_tag_offset,
        ) = TerminalSessionService._count_line_start_paren_wrapper_plain_exact_tag_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_brace_wrapper_plain_exact_tag_match_count,
            first_line_start_brace_wrapper_plain_exact_tag_offset,
        ) = TerminalSessionService._count_line_start_brace_wrapper_plain_exact_tag_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_angle_wrapper_plain_exact_tag_match_count,
            first_line_start_angle_wrapper_plain_exact_tag_offset,
        ) = TerminalSessionService._count_line_start_angle_wrapper_plain_exact_tag_hits(
            text,
            offsets,
            query_length=query_length,
        )
        (
            line_start_plain_exact_tag_single_space_separator_match_count,
            first_line_start_plain_exact_tag_single_space_separator_offset,
        ) = TerminalSessionService._count_line_start_plain_exact_tag_single_space_separator_hits(
            text,
            offsets,
            query_length=query_length,
        )
        line_start_plain_exact_tag_payloadless_separator_match_count = (
            TerminalSessionService._count_line_start_plain_exact_tag_payloadless_separator_hits(
                text,
                offsets,
                query_length=query_length,
            )
        )
        first_line_start_plain_exact_tag_payloadless_separator_offset = (
            TerminalSessionService._first_line_start_plain_exact_tag_payloadless_separator_offset(
                text,
                offsets,
                query_length=query_length,
            )
        )
        first_line_start_non_single_space_plain_exact_tag_separator_offset = (
            TerminalSessionService._first_line_start_non_single_space_plain_exact_tag_separator_offset(
                text,
                offsets,
                query_length=query_length,
            )
        )
        conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset = (
            first_line_start_non_single_space_plain_exact_tag_separator_offset
            if line_start_plain_exact_tag_single_space_separator_match_count > 0
            else _NO_LINE_START_NON_SINGLE_SPACE_PLAIN_EXACT_TAG_SEPARATOR_MATCH_OFFSET
        )
        conditional_line_start_plain_exact_tag_payloadless_separator_match_count = (
            line_start_plain_exact_tag_payloadless_separator_match_count
            if line_start_plain_exact_tag_single_space_separator_match_count > 0
            else 0
        )
        conditional_first_line_start_plain_exact_tag_payloadless_separator_offset = (
            first_line_start_plain_exact_tag_payloadless_separator_offset
            if line_start_plain_exact_tag_single_space_separator_match_count > 0
            else _NO_LINE_START_PLAIN_EXACT_TAG_PAYLOADLESS_SEPARATOR_MATCH_OFFSET
        )
        line_start_plain_exact_tag_tab_prefixed_payload_match_count = (
            TerminalSessionService._count_line_start_plain_exact_tag_tab_prefixed_payload_hits(
                text,
                offsets,
                query_length=query_length,
            )
        )
        conditional_line_start_plain_exact_tag_tab_prefixed_payload_match_count = (
            line_start_plain_exact_tag_tab_prefixed_payload_match_count
            if line_start_plain_exact_tag_single_space_separator_match_count > 0
            else 0
        )
        first_line_start_plain_exact_tag_tab_prefixed_payload_offset = (
            TerminalSessionService._first_line_start_plain_exact_tag_tab_prefixed_payload_offset(
                text,
                offsets,
                query_length=query_length,
            )
        )
        conditional_first_line_start_plain_exact_tag_tab_prefixed_payload_offset = (
            first_line_start_plain_exact_tag_tab_prefixed_payload_offset
            if line_start_plain_exact_tag_single_space_separator_match_count > 0
            else _NO_LINE_START_PLAIN_EXACT_TAG_TAB_PREFIXED_PAYLOAD_MATCH_OFFSET
        )
        line_start_plain_exact_tag_multi_space_payload_match_count = (
            TerminalSessionService._count_line_start_plain_exact_tag_multi_space_payload_hits(
                text,
                offsets,
                query_length=query_length,
            )
        )
        conditional_line_start_plain_exact_tag_multi_space_payload_match_count = (
            line_start_plain_exact_tag_multi_space_payload_match_count
            if line_start_plain_exact_tag_single_space_separator_match_count > 0
            else 0
        )
        first_line_start_plain_exact_tag_multi_space_payload_offset = (
            TerminalSessionService._first_line_start_plain_exact_tag_multi_space_payload_offset(
                text,
                offsets,
                query_length=query_length,
            )
        )
        conditional_first_line_start_plain_exact_tag_multi_space_payload_offset = (
            first_line_start_plain_exact_tag_multi_space_payload_offset
            if line_start_plain_exact_tag_single_space_separator_match_count > 0
            else _NO_LINE_START_PLAIN_EXACT_TAG_MULTI_SPACE_PAYLOAD_MATCH_OFFSET
        )
        line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match_count = (
            TerminalSessionService._count_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_hits(
                text,
                offsets,
                query_length=query_length,
            )
        )
        conditional_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match_count = (
            line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match_count
            if line_start_plain_exact_tag_single_space_separator_match_count > 0
            else 0
        )
        first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset = (
            TerminalSessionService._first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset(
                text,
                offsets,
                query_length=query_length,
            )
        )
        conditional_first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset = (
            first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset
            if line_start_plain_exact_tag_single_space_separator_match_count > 0
            else _NO_LINE_START_PLAIN_EXACT_TAG_SPACE_PREFIXED_MIXED_WHITESPACE_PAYLOAD_MATCH_OFFSET
        )
        line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count = (
            TerminalSessionService._count_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_hits(
                text,
                offsets,
                query_length=query_length,
            )
        )
        conditional_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count = (
            line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count
            if line_start_plain_exact_tag_single_space_separator_match_count > 0
            else 0
        )
        first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset = (
            TerminalSessionService._first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset(
                text,
                offsets,
                query_length=query_length,
            )
        )
        conditional_first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset = (
            first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset
            if line_start_plain_exact_tag_single_space_separator_match_count > 0
            else _NO_LINE_START_PLAIN_EXACT_TAG_OTHER_LEADING_MIXED_WHITESPACE_PAYLOAD_MATCH_OFFSET
        )
        first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset = (
            TerminalSessionService._first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset(
                text,
                offsets,
                query_length=query_length,
            )
        )
        conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset = (
            first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset
            if line_start_plain_exact_tag_single_space_separator_match_count > 0
            else _NO_LINE_START_PLAIN_EXACT_TAG_OTHER_LEADING_WHITESPACE_PAYLOAD_MATCH_OFFSET
        )
        (
            line_start_exact_tag_marker_match_count,
            first_line_start_exact_tag_marker_offset,
        ) = TerminalSessionService._count_line_start_exact_tag_marker_hits(
            text,
            offsets,
            query_length=query_length,
        )
        non_exact_tag_punctuation_wrap_match_count = max(
            0,
            line_start_punctuation_wrap_match_count - line_start_exact_tag_match_count,
        )
        conditional_non_exact_tag_punctuation_wrap_match_count = (
            non_exact_tag_punctuation_wrap_match_count if line_start_exact_tag_match_count > 0 else 0
        )
        non_line_start_whole_word_match_count = (
            whole_word_match_count - line_start_whole_word_match_count
        )
        conditional_non_line_start_whole_word_match_count = (
            non_line_start_whole_word_match_count if line_start_whole_word_match_count > 0 else 0
        )
        first_match_offset = offsets[0]
        cluster_span = offsets[-1] - first_match_offset
        normalized_output_length = max(1, output_length)
        match_density = match.match_count / normalized_output_length
        return _TerminalSessionHistorySearchCandidate(
            match=match,
            line_start_log_marker_match_count=line_start_log_marker_match_count,
            first_line_start_log_marker_offset=first_line_start_log_marker_offset,
            line_start_delimited_log_marker_match_count=line_start_delimited_log_marker_match_count,
            first_line_start_delimited_log_marker_offset=first_line_start_delimited_log_marker_offset,
            line_start_exact_tag_marker_match_count=line_start_exact_tag_marker_match_count,
            first_line_start_exact_tag_marker_offset=first_line_start_exact_tag_marker_offset,
            line_start_exact_tag_colon_marker_match_count=line_start_exact_tag_colon_marker_match_count,
            first_line_start_exact_tag_colon_marker_offset=first_line_start_exact_tag_colon_marker_offset,
            line_start_square_bracket_exact_tag_dash_marker_match_count=line_start_square_bracket_exact_tag_dash_marker_match_count,
            first_line_start_square_bracket_exact_tag_dash_marker_offset=first_line_start_square_bracket_exact_tag_dash_marker_offset,
            line_start_paren_wrapper_marker_match_count=line_start_paren_wrapper_marker_match_count,
            first_line_start_paren_wrapper_marker_offset=first_line_start_paren_wrapper_marker_offset,
            line_start_brace_wrapper_marker_match_count=line_start_brace_wrapper_marker_match_count,
            first_line_start_brace_wrapper_marker_offset=first_line_start_brace_wrapper_marker_offset,
            line_start_non_square_bracket_exact_tag_colon_marker_match_count=line_start_non_square_bracket_exact_tag_colon_marker_match_count,
            first_line_start_non_square_bracket_exact_tag_colon_marker_offset=first_line_start_non_square_bracket_exact_tag_colon_marker_offset,
            line_start_non_square_bracket_exact_tag_dash_marker_match_count=line_start_non_square_bracket_exact_tag_dash_marker_match_count,
            first_line_start_non_square_bracket_exact_tag_dash_marker_offset=first_line_start_non_square_bracket_exact_tag_dash_marker_offset,
            line_start_exact_tag_match_count=line_start_exact_tag_match_count,
            first_line_start_exact_tag_offset=first_line_start_exact_tag_offset,
            line_start_square_bracket_exact_tag_match_count=line_start_square_bracket_exact_tag_match_count,
            first_line_start_square_bracket_exact_tag_offset=first_line_start_square_bracket_exact_tag_offset,
            first_line_start_square_bracket_plain_exact_tag_offset=first_line_start_square_bracket_plain_exact_tag_offset,
            line_start_paren_wrapper_plain_exact_tag_match_count=line_start_paren_wrapper_plain_exact_tag_match_count,
            first_line_start_paren_wrapper_plain_exact_tag_offset=first_line_start_paren_wrapper_plain_exact_tag_offset,
            line_start_brace_wrapper_plain_exact_tag_match_count=line_start_brace_wrapper_plain_exact_tag_match_count,
            first_line_start_brace_wrapper_plain_exact_tag_offset=first_line_start_brace_wrapper_plain_exact_tag_offset,
            line_start_angle_wrapper_plain_exact_tag_match_count=line_start_angle_wrapper_plain_exact_tag_match_count,
            first_line_start_angle_wrapper_plain_exact_tag_offset=first_line_start_angle_wrapper_plain_exact_tag_offset,
            line_start_plain_exact_tag_single_space_separator_match_count=line_start_plain_exact_tag_single_space_separator_match_count,
            first_line_start_plain_exact_tag_single_space_separator_offset=first_line_start_plain_exact_tag_single_space_separator_offset,
            conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset=conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset,
            conditional_line_start_plain_exact_tag_payloadless_separator_match_count=conditional_line_start_plain_exact_tag_payloadless_separator_match_count,
            conditional_first_line_start_plain_exact_tag_payloadless_separator_offset=conditional_first_line_start_plain_exact_tag_payloadless_separator_offset,
            conditional_line_start_plain_exact_tag_tab_prefixed_payload_match_count=conditional_line_start_plain_exact_tag_tab_prefixed_payload_match_count,
            conditional_first_line_start_plain_exact_tag_tab_prefixed_payload_offset=conditional_first_line_start_plain_exact_tag_tab_prefixed_payload_offset,
            conditional_line_start_plain_exact_tag_multi_space_payload_match_count=conditional_line_start_plain_exact_tag_multi_space_payload_match_count,
            conditional_first_line_start_plain_exact_tag_multi_space_payload_offset=conditional_first_line_start_plain_exact_tag_multi_space_payload_offset,
            conditional_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match_count=conditional_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match_count,
            conditional_first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset=conditional_first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset,
            conditional_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count=conditional_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count,
            conditional_first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset=conditional_first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset,
            conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset=conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset,
            conditional_non_exact_tag_punctuation_wrap_match_count=conditional_non_exact_tag_punctuation_wrap_match_count,
            line_start_punctuation_wrap_match_count=line_start_punctuation_wrap_match_count,
            first_line_start_punctuation_wrap_offset=first_line_start_punctuation_wrap_offset,
            whole_word_match_count=whole_word_match_count,
            line_start_whole_word_match_count=line_start_whole_word_match_count,
            conditional_non_line_start_whole_word_match_count=conditional_non_line_start_whole_word_match_count,
            first_line_start_whole_word_offset=first_line_start_whole_word_offset,
            first_whole_word_offset=first_whole_word_offset,
            cluster_span=cluster_span,
            first_match_offset=first_match_offset,
            match_density=match_density,
        )

    @staticmethod
    def _count_whole_word_hits(text: str, offsets: list[int], *, query_length: int) -> tuple[int, int]:
        whole_word_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_whole_word_match(text, offset, query_length=query_length)
        ]
        if not whole_word_offsets:
            return 0, _NO_WHOLE_WORD_MATCH_OFFSET
        return len(whole_word_offsets), whole_word_offsets[0]

    @staticmethod
    def _count_line_start_whole_word_hits(text: str, offsets: list[int], *, query_length: int) -> tuple[int, int]:
        line_start_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_whole_word_match(text, offset, query_length=query_length)
        ]
        if not line_start_offsets:
            return 0, _NO_LINE_START_WHOLE_WORD_MATCH_OFFSET
        return len(line_start_offsets), line_start_offsets[0]

    @staticmethod
    def _count_line_start_log_marker_hits(text: str, offsets: list[int], *, query_length: int) -> tuple[int, int]:
        marker_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_log_marker_match(text, offset, query_length=query_length)
        ]
        if not marker_offsets:
            return 0, _NO_LINE_START_LOG_MARKER_MATCH_OFFSET
        return len(marker_offsets), marker_offsets[0]

    @staticmethod
    def _count_line_start_delimited_log_marker_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        delimited_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_delimited_log_marker_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not delimited_offsets:
            return 0, _NO_LINE_START_DELIMITED_LOG_MARKER_MATCH_OFFSET
        return len(delimited_offsets), delimited_offsets[0]

    @staticmethod
    def _count_line_start_punctuation_wrap_hits(text: str, offsets: list[int], *, query_length: int) -> tuple[int, int]:
        wrapper_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_punctuation_wrap_match(text, offset, query_length=query_length)
        ]
        if not wrapper_offsets:
            return 0, _NO_LINE_START_PUNCTUATION_WRAP_MATCH_OFFSET
        return len(wrapper_offsets), wrapper_offsets[0]

    @staticmethod
    def _count_line_start_exact_tag_hits(text: str, offsets: list[int], *, query_length: int) -> tuple[int, int]:
        exact_tag_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length)
        ]
        if not exact_tag_offsets:
            return 0, _NO_LINE_START_EXACT_TAG_MATCH_OFFSET
        return len(exact_tag_offsets), exact_tag_offsets[0]

    @staticmethod
    def _count_line_start_exact_tag_colon_marker_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        colon_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_exact_tag_colon_marker_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not colon_offsets:
            return 0, _NO_LINE_START_EXACT_TAG_COLON_MARKER_MATCH_OFFSET
        return len(colon_offsets), colon_offsets[0]

    @staticmethod
    def _count_line_start_square_bracket_exact_tag_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        bracket_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_square_bracket_exact_tag_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not bracket_offsets:
            return 0, _NO_LINE_START_SQUARE_BRACKET_EXACT_TAG_MATCH_OFFSET
        return len(bracket_offsets), bracket_offsets[0]

    @staticmethod
    def _count_line_start_square_bracket_plain_exact_tag_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        bracket_plain_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_square_bracket_plain_exact_tag_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not bracket_plain_offsets:
            return 0, _NO_LINE_START_SQUARE_BRACKET_PLAIN_EXACT_TAG_MATCH_OFFSET
        return len(bracket_plain_offsets), bracket_plain_offsets[0]

    @staticmethod
    def _count_line_start_angle_wrapper_plain_exact_tag_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        angle_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_angle_wrapper_plain_exact_tag_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not angle_offsets:
            return 0, _NO_LINE_START_ANGLE_WRAPPER_PLAIN_EXACT_TAG_MATCH_OFFSET
        return len(angle_offsets), angle_offsets[0]

    @staticmethod
    def _count_line_start_plain_exact_tag_single_space_separator_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        single_space_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_plain_exact_tag_single_space_separator_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not single_space_offsets:
            return 0, _NO_LINE_START_PLAIN_EXACT_TAG_SINGLE_SPACE_SEPARATOR_MATCH_OFFSET
        return len(single_space_offsets), single_space_offsets[0]

    @staticmethod
    def _count_line_start_plain_exact_tag_payloadless_separator_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> int:
        return sum(
            1
            for offset in offsets
            if TerminalSessionService._is_line_start_plain_exact_tag_payloadless_separator_match(
                text,
                offset,
                query_length=query_length,
            )
        )

    @staticmethod
    def _first_line_start_non_single_space_plain_exact_tag_separator_offset(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> int:
        for offset in offsets:
            if TerminalSessionService._is_line_start_non_single_space_plain_exact_tag_separator_match(
                text,
                offset,
                query_length=query_length,
            ):
                return offset
        return _NO_LINE_START_NON_SINGLE_SPACE_PLAIN_EXACT_TAG_SEPARATOR_MATCH_OFFSET

    @staticmethod
    def _first_line_start_plain_exact_tag_payloadless_separator_offset(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> int:
        for offset in offsets:
            if TerminalSessionService._is_line_start_plain_exact_tag_payloadless_separator_match(
                text,
                offset,
                query_length=query_length,
            ):
                return offset
        return _NO_LINE_START_PLAIN_EXACT_TAG_PAYLOADLESS_SEPARATOR_MATCH_OFFSET

    @staticmethod
    def _count_line_start_plain_exact_tag_tab_prefixed_payload_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> int:
        return sum(
            1
            for offset in offsets
            if TerminalSessionService._is_line_start_plain_exact_tag_tab_prefixed_payload_match(
                text,
                offset,
                query_length=query_length,
            )
        )

    @staticmethod
    def _first_line_start_plain_exact_tag_tab_prefixed_payload_offset(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> int:
        for offset in offsets:
            if TerminalSessionService._is_line_start_plain_exact_tag_tab_prefixed_payload_match(
                text,
                offset,
                query_length=query_length,
            ):
                return offset
        return _NO_LINE_START_PLAIN_EXACT_TAG_TAB_PREFIXED_PAYLOAD_MATCH_OFFSET

    @staticmethod
    def _count_line_start_plain_exact_tag_multi_space_payload_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> int:
        return sum(
            1
            for offset in offsets
            if TerminalSessionService._is_line_start_plain_exact_tag_multi_space_payload_match(
                text,
                offset,
                query_length=query_length,
            )
        )

    @staticmethod
    def _first_line_start_plain_exact_tag_multi_space_payload_offset(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> int:
        for offset in offsets:
            if TerminalSessionService._is_line_start_plain_exact_tag_multi_space_payload_match(
                text,
                offset,
                query_length=query_length,
            ):
                return offset
        return _NO_LINE_START_PLAIN_EXACT_TAG_MULTI_SPACE_PAYLOAD_MATCH_OFFSET

    @staticmethod
    def _count_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> int:
        return sum(
            1
            for offset in offsets
            if TerminalSessionService._is_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match(
                text,
                offset,
                query_length=query_length,
            )
        )

    @staticmethod
    def _first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> int:
        for offset in offsets:
            if TerminalSessionService._is_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match(
                text,
                offset,
                query_length=query_length,
            ):
                return offset
        return _NO_LINE_START_PLAIN_EXACT_TAG_SPACE_PREFIXED_MIXED_WHITESPACE_PAYLOAD_MATCH_OFFSET

    @staticmethod
    def _first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> int:
        for offset in offsets:
            if TerminalSessionService._is_line_start_plain_exact_tag_other_leading_whitespace_payload_match(
                text,
                offset,
                query_length=query_length,
            ):
                return offset
        return _NO_LINE_START_PLAIN_EXACT_TAG_OTHER_LEADING_WHITESPACE_PAYLOAD_MATCH_OFFSET

    @staticmethod
    def _count_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> int:
        return sum(
            1
            for offset in offsets
            if TerminalSessionService._is_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match(
                text,
                offset,
                query_length=query_length,
            )
        )

    @staticmethod
    def _first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> int:
        for offset in offsets:
            if TerminalSessionService._is_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match(
                text,
                offset,
                query_length=query_length,
            ):
                return offset
        return _NO_LINE_START_PLAIN_EXACT_TAG_OTHER_LEADING_MIXED_WHITESPACE_PAYLOAD_MATCH_OFFSET

    @staticmethod
    def _count_line_start_paren_wrapper_plain_exact_tag_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        paren_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_paren_wrapper_plain_exact_tag_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not paren_offsets:
            return 0, _NO_LINE_START_PAREN_WRAPPER_PLAIN_EXACT_TAG_MATCH_OFFSET
        return len(paren_offsets), paren_offsets[0]

    @staticmethod
    def _count_line_start_brace_wrapper_plain_exact_tag_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        brace_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_brace_wrapper_plain_exact_tag_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not brace_offsets:
            return 0, _NO_LINE_START_BRACE_WRAPPER_PLAIN_EXACT_TAG_MATCH_OFFSET
        return len(brace_offsets), brace_offsets[0]

    @staticmethod
    def _count_line_start_square_bracket_exact_tag_dash_marker_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        dash_marker_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_square_bracket_exact_tag_dash_marker_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not dash_marker_offsets:
            return 0, _NO_LINE_START_SQUARE_BRACKET_EXACT_TAG_DASH_MARKER_MATCH_OFFSET
        return len(dash_marker_offsets), dash_marker_offsets[0]

    @staticmethod
    def _count_line_start_paren_wrapper_marker_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        paren_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_paren_wrapper_marker_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not paren_offsets:
            return 0, _NO_LINE_START_PAREN_WRAPPER_MARKER_MATCH_OFFSET
        return len(paren_offsets), paren_offsets[0]

    @staticmethod
    def _count_line_start_brace_wrapper_marker_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        brace_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_brace_wrapper_marker_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not brace_offsets:
            return 0, _NO_LINE_START_BRACE_WRAPPER_MARKER_MATCH_OFFSET
        return len(brace_offsets), brace_offsets[0]

    @staticmethod
    def _count_line_start_non_square_bracket_exact_tag_colon_marker_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        colon_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_non_square_bracket_exact_tag_colon_marker_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not colon_offsets:
            return 0, _NO_LINE_START_NON_SQUARE_BRACKET_EXACT_TAG_COLON_MARKER_MATCH_OFFSET
        return len(colon_offsets), colon_offsets[0]

    @staticmethod
    def _count_line_start_non_square_bracket_exact_tag_dash_marker_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        dash_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_non_square_bracket_exact_tag_dash_marker_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not dash_offsets:
            return 0, _NO_LINE_START_NON_SQUARE_BRACKET_EXACT_TAG_DASH_MARKER_MATCH_OFFSET
        return len(dash_offsets), dash_offsets[0]

    @staticmethod
    def _count_line_start_exact_tag_marker_hits(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
    ) -> tuple[int, int]:
        marker_offsets = [
            offset
            for offset in offsets
            if TerminalSessionService._is_line_start_exact_tag_marker_match(
                text,
                offset,
                query_length=query_length,
            )
        ]
        if not marker_offsets:
            return 0, _NO_LINE_START_EXACT_TAG_MARKER_MATCH_OFFSET
        return len(marker_offsets), marker_offsets[0]

    @staticmethod
    def _is_whole_word_match(text: str, offset: int, *, query_length: int) -> bool:
        start = offset
        end = offset + query_length
        if start < 0 or end > len(text):
            return False

        prev_char = text[start - 1] if start > 0 else None
        next_char = text[end] if end < len(text) else None
        prev_is_word_char = False if prev_char is None else TerminalSessionService._is_word_char(prev_char)
        next_is_word_char = False if next_char is None else TerminalSessionService._is_word_char(next_char)
        return not prev_is_word_char and not next_is_word_char

    @staticmethod
    def _is_line_start_whole_word_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_whole_word_match(text, offset, query_length=query_length):
            return False
        return offset == 0 or text[offset - 1] == "\n"

    @staticmethod
    def _is_line_start_log_marker_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_whole_word_match(text, offset, query_length=query_length):
            return False
        end = offset + query_length
        return text[end : end + 1] == ":" or text[end : end + 2] == " -"

    @staticmethod
    def _is_line_start_delimited_log_marker_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_log_marker_match(text, offset, query_length=query_length):
            return False

        end = offset + query_length
        if text[end : end + 1] == ":":
            trailing_offset = end + 1
        elif text[end : end + 2] == " -":
            trailing_offset = end + 2
        else:
            return False

        return trailing_offset >= len(text) or text[trailing_offset].isspace()

    @staticmethod
    def _is_line_start_punctuation_wrap_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_whole_word_match(text, offset, query_length=query_length):
            return False
        if offset <= 0:
            return False

        opening = text[offset - 1]
        closing = _LINE_START_PUNCTUATION_WRAP_PAIRS.get(opening)
        if closing is None:
            return False

        opening_offset = offset - 1
        if opening_offset != 0 and text[opening_offset - 1] != "\n":
            return False

        end = offset + query_length
        return text[end : end + 1] == closing

    @staticmethod
    def _is_line_start_exact_tag_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_punctuation_wrap_match(text, offset, query_length=query_length):
            return False

        trailing_offset = offset + query_length + 1
        if trailing_offset >= len(text):
            return True

        trailing_char = text[trailing_offset]
        if trailing_char.isspace():
            return True

        if trailing_char == ":":
            after_colon = text[trailing_offset + 1 : trailing_offset + 2]
            return after_colon == "" or after_colon.isspace()

        if text[trailing_offset : trailing_offset + 2] == " -":
            after_dash = text[trailing_offset + 2 : trailing_offset + 3]
            return after_dash == "" or after_dash.isspace()

        return False

    @staticmethod
    def _is_line_start_exact_tag_marker_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length):
            return False

        trailing_offset = offset + query_length + 1

        if text[trailing_offset : trailing_offset + 1] == ":":
            after_colon = text[trailing_offset + 1 : trailing_offset + 2]
            return after_colon == "" or after_colon.isspace()

        if text[trailing_offset : trailing_offset + 2] == " -":
            after_dash = text[trailing_offset + 2 : trailing_offset + 3]
            return after_dash == "" or after_dash.isspace()

        return False

    @staticmethod
    def _is_line_start_exact_tag_colon_marker_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False

        trailing_offset = offset + query_length + 1
        if text[trailing_offset : trailing_offset + 1] != ":":
            return False

        after_colon = text[trailing_offset + 1 : trailing_offset + 2]
        return after_colon == "" or after_colon.isspace()

    @staticmethod
    def _is_line_start_square_bracket_exact_tag_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length):
            return False
        return text[offset - 1 : offset] == "[" and text[offset + query_length : offset + query_length + 1] == "]"

    @staticmethod
    def _is_line_start_square_bracket_plain_exact_tag_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_square_bracket_exact_tag_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False
        if TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        return True

    @staticmethod
    def _is_line_start_angle_wrapper_plain_exact_tag_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        return text[offset - 1 : offset] == "<" and text[offset + query_length : offset + query_length + 1] == ">"

    @staticmethod
    def _is_line_start_plain_exact_tag_single_space_separator_match(
        text: str,
        offset: int,
        *,
        query_length: int,
    ) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False

        separator_offset = offset + query_length + 1
        if text[separator_offset : separator_offset + 1] != " ":
            return False

        next_char = text[separator_offset + 1 : separator_offset + 2]
        return next_char != "" and not next_char.isspace()

    @staticmethod
    def _is_line_start_plain_exact_tag_payloadless_separator_match(
        text: str,
        offset: int,
        *,
        query_length: int,
    ) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False

        separator_offset = offset + query_length + 1
        if separator_offset >= len(text):
            return True

        cursor = separator_offset
        while cursor < len(text) and text[cursor] != "\n":
            if not text[cursor].isspace():
                return False
            cursor += 1
        return True

    @staticmethod
    def _is_line_start_non_single_space_plain_exact_tag_separator_match(
        text: str,
        offset: int,
        *,
        query_length: int,
    ) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_plain_exact_tag_single_space_separator_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False
        return True

    @staticmethod
    def _is_line_start_plain_exact_tag_tab_prefixed_payload_match(
        text: str,
        offset: int,
        *,
        query_length: int,
    ) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_plain_exact_tag_payloadless_separator_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False

        separator_offset = offset + query_length + 1
        if text[separator_offset : separator_offset + 1] != "\t":
            return False

        cursor = separator_offset
        while cursor < len(text) and text[cursor] != "\n":
            if not text[cursor].isspace():
                return True
            cursor += 1
        return False

    @staticmethod
    def _is_line_start_plain_exact_tag_multi_space_payload_match(
        text: str,
        offset: int,
        *,
        query_length: int,
    ) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_plain_exact_tag_payloadless_separator_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False
        if TerminalSessionService._is_line_start_plain_exact_tag_tab_prefixed_payload_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False

        separator_offset = offset + query_length + 1
        if text[separator_offset : separator_offset + 1] != " ":
            return False
        if text[separator_offset + 1 : separator_offset + 2] != " ":
            return False

        cursor = separator_offset
        while cursor < len(text) and text[cursor] != "\n":
            if not text[cursor].isspace():
                return True
            cursor += 1
        return False

    @staticmethod
    def _is_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match(
        text: str,
        offset: int,
        *,
        query_length: int,
    ) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_plain_exact_tag_payloadless_separator_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False
        if TerminalSessionService._is_line_start_plain_exact_tag_tab_prefixed_payload_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False
        if TerminalSessionService._is_line_start_plain_exact_tag_multi_space_payload_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False

        separator_offset = offset + query_length + 1
        if text[separator_offset : separator_offset + 1] != " ":
            return False

        second_separator = text[separator_offset + 1 : separator_offset + 2]
        if second_separator == "" or not second_separator.isspace() or second_separator == " ":
            return False

        cursor = separator_offset
        while cursor < len(text) and text[cursor] != "\n":
            if not text[cursor].isspace():
                return True
            cursor += 1
        return False

    @staticmethod
    def _is_line_start_plain_exact_tag_other_leading_whitespace_payload_match(
        text: str,
        offset: int,
        *,
        query_length: int,
    ) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_plain_exact_tag_payloadless_separator_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False
        if TerminalSessionService._is_line_start_plain_exact_tag_tab_prefixed_payload_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False
        if TerminalSessionService._is_line_start_plain_exact_tag_multi_space_payload_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False
        if TerminalSessionService._is_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False

        separator_offset = offset + query_length + 1
        leading = text[separator_offset : separator_offset + 1]
        if leading == "" or not leading.isspace() or leading in {" ", "\t"}:
            return False

        cursor = separator_offset
        while cursor < len(text) and text[cursor] != "\n":
            if not text[cursor].isspace():
                return True
            cursor += 1
        return False

    @staticmethod
    def _is_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match(
        text: str,
        offset: int,
        *,
        query_length: int,
    ) -> bool:
        if not TerminalSessionService._is_line_start_plain_exact_tag_other_leading_whitespace_payload_match(
            text,
            offset,
            query_length=query_length,
        ):
            return False

        separator_offset = offset + query_length + 1
        second_separator = text[separator_offset + 1 : separator_offset + 2]
        return second_separator != "" and second_separator.isspace()

    @staticmethod
    def _is_line_start_paren_wrapper_plain_exact_tag_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        return text[offset - 1 : offset] == "(" and text[offset + query_length : offset + query_length + 1] == ")"

    @staticmethod
    def _is_line_start_brace_wrapper_plain_exact_tag_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        return text[offset - 1 : offset] == "{" and text[offset + query_length : offset + query_length + 1] == "}"

    @staticmethod
    def _is_line_start_square_bracket_exact_tag_dash_marker_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        if not TerminalSessionService._is_line_start_square_bracket_exact_tag_match(text, offset, query_length=query_length):
            return False

        trailing_offset = offset + query_length + 1
        if text[trailing_offset : trailing_offset + 2] != " -":
            return False

        after_dash = text[trailing_offset + 2 : trailing_offset + 3]
        return after_dash == "" or after_dash.isspace()

    @staticmethod
    def _is_line_start_paren_wrapper_marker_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        return (
            text[offset - 1 : offset] == "("
            and text[offset + query_length : offset + query_length + 1] == ")"
        )

    @staticmethod
    def _is_line_start_brace_wrapper_marker_match(text: str, offset: int, *, query_length: int) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        return (
            text[offset - 1 : offset] == "{"
            and text[offset + query_length : offset + query_length + 1] == "}"
        )

    @staticmethod
    def _is_line_start_non_square_bracket_exact_tag_colon_marker_match(
        text: str,
        offset: int,
        *,
        query_length: int,
    ) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_colon_marker_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_square_bracket_exact_tag_match(text, offset, query_length=query_length):
            return False
        return True

    @staticmethod
    def _is_line_start_non_square_bracket_exact_tag_dash_marker_match(
        text: str,
        offset: int,
        *,
        query_length: int,
    ) -> bool:
        if not TerminalSessionService._is_line_start_exact_tag_marker_match(text, offset, query_length=query_length):
            return False
        if TerminalSessionService._is_line_start_square_bracket_exact_tag_match(text, offset, query_length=query_length):
            return False

        trailing_offset = offset + query_length + 1
        if text[trailing_offset : trailing_offset + 2] != " -":
            return False

        after_dash = text[trailing_offset + 2 : trailing_offset + 3]
        return after_dash == "" or after_dash.isspace()

    @staticmethod
    def _is_word_char(char: str) -> bool:
        return ("a" <= char <= "z") or ("A" <= char <= "Z") or ("0" <= char <= "9") or char == "_"

    @staticmethod
    def _normalize_search_sort(sort: str | None) -> TerminalHistorySearchSort:
        if sort in {"relevance", "newest", "oldest"}:
            return sort
        raise ValueError("sort must be one of: relevance, newest, oldest")

    @staticmethod
    def _sort_history_search_matches(
        matches: list[_TerminalSessionHistorySearchCandidate],
        *,
        sort: TerminalHistorySearchSort,
    ) -> list[TerminalSessionHistorySearchMatch]:
        if sort == "relevance":
            matches.sort(
                key=lambda item: (
                    -item.match.match_count,
                    -item.line_start_log_marker_match_count,
                    -item.line_start_delimited_log_marker_match_count,
                    -item.line_start_exact_tag_marker_match_count,
                    -item.line_start_exact_tag_colon_marker_match_count,
                    -item.line_start_square_bracket_exact_tag_dash_marker_match_count,
                    -item.line_start_paren_wrapper_marker_match_count,
                    -item.line_start_brace_wrapper_marker_match_count,
                    -item.line_start_non_square_bracket_exact_tag_colon_marker_match_count,
                    -item.line_start_non_square_bracket_exact_tag_dash_marker_match_count,
                    -item.line_start_exact_tag_match_count,
                    -item.line_start_square_bracket_exact_tag_match_count,
                    -item.line_start_paren_wrapper_plain_exact_tag_match_count,
                    -item.line_start_brace_wrapper_plain_exact_tag_match_count,
                    item.line_start_angle_wrapper_plain_exact_tag_match_count,
                    -item.line_start_plain_exact_tag_single_space_separator_match_count,
                    -item.conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset,
                    item.conditional_line_start_plain_exact_tag_payloadless_separator_match_count,
                    -item.conditional_first_line_start_plain_exact_tag_payloadless_separator_offset,
                    item.conditional_line_start_plain_exact_tag_tab_prefixed_payload_match_count,
                    -item.conditional_first_line_start_plain_exact_tag_tab_prefixed_payload_offset,
                    item.conditional_line_start_plain_exact_tag_multi_space_payload_match_count,
                    -item.conditional_first_line_start_plain_exact_tag_multi_space_payload_offset,
                    item.conditional_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match_count,
                    -item.conditional_first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset,
                    item.conditional_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count,
                    -item.conditional_first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset,
                    -item.conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset,
                    item.conditional_non_exact_tag_punctuation_wrap_match_count,
                    -item.line_start_punctuation_wrap_match_count,
                    -item.line_start_whole_word_match_count,
                    item.conditional_non_line_start_whole_word_match_count,
                    -item.whole_word_match_count,
                    item.first_line_start_log_marker_offset,
                    item.first_line_start_delimited_log_marker_offset,
                    item.first_line_start_exact_tag_colon_marker_offset,
                    item.first_line_start_square_bracket_exact_tag_dash_marker_offset,
                    item.first_line_start_paren_wrapper_marker_offset,
                    item.first_line_start_brace_wrapper_marker_offset,
                    item.first_line_start_non_square_bracket_exact_tag_colon_marker_offset,
                    item.first_line_start_non_square_bracket_exact_tag_dash_marker_offset,
                    item.first_line_start_square_bracket_plain_exact_tag_offset,
                    item.first_line_start_paren_wrapper_plain_exact_tag_offset,
                    item.first_line_start_brace_wrapper_plain_exact_tag_offset,
                    item.first_line_start_angle_wrapper_plain_exact_tag_offset,
                    item.first_line_start_plain_exact_tag_single_space_separator_offset,
                    item.first_line_start_exact_tag_marker_offset,
                    item.first_line_start_exact_tag_offset,
                    item.first_line_start_square_bracket_exact_tag_offset,
                    item.first_line_start_punctuation_wrap_offset,
                    item.first_line_start_whole_word_offset,
                    item.first_whole_word_offset,
                    item.cluster_span,
                    item.first_match_offset,
                    -item.match_density,
                    -item.match.snapshot_at.timestamp(),
                    item.match.record.session_id,
                )
            )
            return [item.match for item in matches]
        if sort == "newest":
            matches.sort(
                key=lambda item: (
                    -item.match.snapshot_at.timestamp(),
                    -item.match.match_count,
                    item.match.record.session_id,
                )
            )
            return [item.match for item in matches]
        matches.sort(
            key=lambda item: (
                item.match.snapshot_at.timestamp(),
                -item.match.match_count,
                item.match.record.session_id,
            )
        )
        return [item.match for item in matches]

    @staticmethod
    def _find_case_insensitive_match_offsets(text: str, query: str) -> list[int]:
        if text == "" or query == "":
            return []
        lowered_text = text.lower()
        lowered_query = query.lower()
        offsets: list[int] = []
        position = 0
        while True:
            found = lowered_text.find(lowered_query, position)
            if found < 0:
                break
            offsets.append(found)
            position = found + max(1, len(lowered_query))
        return offsets

    @staticmethod
    def _build_search_snippets(
        text: str,
        offsets: list[int],
        *,
        query_length: int,
        snippet_limit: int,
        snippet_context_chars: int,
    ) -> list[TerminalSessionHistorySearchSnippet]:
        snippets: list[TerminalSessionHistorySearchSnippet] = []
        for match_index, offset in enumerate(offsets[:snippet_limit]):
            start = max(0, offset - snippet_context_chars)
            end = min(len(text), offset + query_length + snippet_context_chars)
            snippet = text[start:end]
            if start > 0:
                snippet = f"...{snippet}"
            if end < len(text):
                snippet = f"{snippet}..."
            snippets.append(
                TerminalSessionHistorySearchSnippet(
                    text=snippet,
                    match_index=match_index,
                    match_offset=offset,
                )
            )
        return snippets

    def _list_persisted_history_snapshots(self) -> list[TerminalSessionHistorySnapshot]:
        if not self._history_persist_root.exists():
            return []
        try:
            workspace_dirs = sorted(
                (path for path in self._history_persist_root.iterdir() if path.is_dir()),
                key=lambda item: item.name,
            )
        except Exception:
            return []

        snapshots: list[TerminalSessionHistorySnapshot] = []
        for workspace_dir in workspace_dirs:
            snapshot = self._load_persisted_history_snapshot(workspace_dir.name)
            if snapshot is not None:
                snapshots.append(snapshot)
        return snapshots

    @staticmethod
    def _to_history_summary(snapshot: TerminalSessionHistorySnapshot) -> TerminalSessionHistorySummary:
        return TerminalSessionHistorySummary(
            record=snapshot.record,
            snapshot_at=snapshot.snapshot_at,
            output_bytes=snapshot.output_bytes,
            history_max_bytes=snapshot.history_max_bytes,
            truncated=snapshot.truncated,
        )

    def _recover_active_sessions_from_persisted_snapshots(self) -> None:
        for snapshot in self._list_persisted_history_snapshots():
            if snapshot is None:
                continue
            if snapshot.record.status not in _ACTIVE_RECOVERABLE_STATUSES:
                continue

            recovered_record = replace(
                snapshot.record,
                status="detached",
                reconnect_deadline=None,
            )
            if recovered_record.group_folder in self._sessions_by_group:
                continue
            if recovered_record.session_id in self._sessions_by_id:
                continue

            managed = _ManagedTerminalSession(
                record=recovered_record,
                bridge=None,
            )
            managed.output_history_truncated = snapshot.truncated
            self._append_output_history(managed, snapshot.output)
            self._sessions_by_group[managed.record.group_folder] = managed
            self._sessions_by_id[managed.record.session_id] = managed

    @staticmethod
    def _parse_persisted_datetime(value: object) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)


__all__ = [
    "TerminalBackendDisabledError",
    "TerminalBackendUnsupportedError",
    "TerminalSessionConflictError",
    "TerminalSessionEvent",
    "TerminalSessionHistorySearchMatch",
    "TerminalSessionHistorySearchPage",
    "TerminalSessionHistorySnapshot",
    "TerminalSessionHistorySummary",
    "TerminalSessionHistoryTimelinePage",
    "TerminalSessionNotFoundError",
    "TerminalSessionOwnershipError",
    "TerminalSessionRecord",
    "TerminalSessionService",
]
