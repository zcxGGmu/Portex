"""Terminal session routes."""

from __future__ import annotations

import asyncio
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from app.middleware.auth import get_current_user
from app.openapi import openapi_error_responses
from app.routes.groups import get_group_registry_service
from domain.schemas import (
    CreateTerminalSessionRequest,
    DeleteTerminalSessionResponse,
    TerminalSessionHistoryDetailResponse,
    TerminalSessionHistorySearchMatchResponse,
    TerminalSessionHistorySearchSnippetResponse,
    TerminalSessionHistorySearchResponse,
    TerminalSessionHistoryResponse,
    TerminalSessionHistorySummaryResponse,
    TerminalSessionHistoryTimelineResponse,
    TerminalSessionResponse,
    TerminalWorkspaceListResponse,
    TerminalWorkspaceSummaryResponse,
    UserResponse,
)
from services.auth import auth_service
from services.group_registry import GroupRegistryService
from services.execution_runtime import get_terminal_session_service
from services.terminal_sessions import (
    TerminalBackendDisabledError,
    TerminalBackendUnsupportedError,
    TerminalSessionConflictError,
    TerminalSessionEvent,
    TerminalSessionHistorySearchMatch,
    TerminalSessionHistorySummary,
    TerminalSessionNotFoundError,
    TerminalSessionOwnershipError,
    TerminalSessionRecord,
    TerminalSessionService,
)

router = APIRouter(tags=["terminals"])
_ACTIVE_TERMINAL_STATUSES = {"created", "attached", "detached"}


def _to_terminal_session_response(item: TerminalSessionRecord) -> TerminalSessionResponse:
    return TerminalSessionResponse(
        session_id=item.session_id,
        group_id=item.group_id,
        owner_user_id=item.owner_user_id,
        backend=item.backend,
        container_name=item.container_name,
        status=item.status,
        created_at=item.created_at,
        last_attached_at=item.last_attached_at,
        reconnect_deadline=item.reconnect_deadline,
    )


def _to_terminal_history_summary_response(item: TerminalSessionHistorySummary) -> TerminalSessionHistorySummaryResponse:
    snapshot_at = getattr(item, "snapshot_at", item.record.created_at)
    return TerminalSessionHistorySummaryResponse(
        session=_to_terminal_session_response(item.record),
        snapshot_at=snapshot_at,
        output_bytes=item.output_bytes,
        history_max_bytes=item.history_max_bytes,
        truncated=item.truncated,
    )


def _to_terminal_history_search_match_response(
    item: TerminalSessionHistorySearchMatch,
) -> TerminalSessionHistorySearchMatchResponse:
    return TerminalSessionHistorySearchMatchResponse(
        session=_to_terminal_session_response(item.record),
        snapshot_at=item.snapshot_at,
        match_count=item.match_count,
        snippets=list(item.snippets),
        snippet_matches=[
            TerminalSessionHistorySearchSnippetResponse(
                text=snippet.text,
                match_index=snippet.match_index,
                match_offset=snippet.match_offset,
            )
            for snippet in item.snippet_matches
        ],
    )


def _to_terminal_history_detail_response(item) -> TerminalSessionHistoryDetailResponse:
    return TerminalSessionHistoryDetailResponse(
        session=_to_terminal_session_response(item.record),
        snapshot_at=item.snapshot_at,
        output=item.output,
        output_bytes=item.output_bytes,
        history_max_bytes=item.history_max_bytes,
        truncated=item.truncated,
    )


def _is_web_workspace(group: object) -> bool:
    jid = getattr(group, "jid", None)
    return isinstance(jid, str) and jid.startswith("web:")


def _terminal_workspace_sort_key(item: TerminalWorkspaceSummaryResponse) -> tuple[int, str, str]:
    if item.session is None:
        bucket = 2
    elif item.session.status in _ACTIVE_TERMINAL_STATUSES:
        bucket = 0
    else:
        bucket = 1
    return (bucket, item.group_name.lower(), item.group_id)


def _require_terminal_role(current_user: UserResponse) -> None:
    if current_user.role not in {"owner", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission denied",
        )


async def _require_accessible_workspace(
    *,
    group_id: str,
    current_user: UserResponse,
    group_registry: GroupRegistryService,
):
    workspace = await group_registry.get_web_workspace_by_folder(group_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group not found",
        )
    if not await group_registry.user_can_access_group(
        user_id=current_user.id,
        user_role=current_user.role,
        group=workspace,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="group not found",
        )
    return workspace


def _map_terminal_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TerminalSessionNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, (TerminalSessionConflictError, TerminalSessionOwnershipError)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, (TerminalBackendDisabledError, TerminalBackendUnsupportedError)):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="terminal operation failed")


def _authenticate_websocket(websocket: WebSocket) -> UserResponse | None:
    authorization = websocket.headers.get("authorization")
    token = ""
    if authorization:
        scheme, _, header_token = authorization.partition(" ")
        if scheme.lower() == "bearer" and header_token:
            token = header_token
    if token == "":
        token = websocket.query_params.get("access_token", "")
    if token == "":
        return None
    user_id = auth_service.decode_access_token(token)
    if user_id is None:
        return None
    return auth_service.get_user_by_id(user_id)


def _resolve_terminal_service_for_websocket(websocket: WebSocket) -> TerminalSessionService:
    override = getattr(websocket.app, "dependency_overrides", {}).get(get_terminal_session_service)
    if override is not None:
        return override()
    return get_terminal_session_service()


def _terminal_error_payload(detail: str) -> str:
    return json.dumps({"type": "terminal.error", "error": detail})


async def _forward_terminal_events(
    websocket: WebSocket,
    queue: asyncio.Queue[TerminalSessionEvent],
) -> None:
    while True:
        event = await queue.get()
        payload: dict[str, object] = {"type": event.event_type}
        if event.data is not None:
            payload["data"] = event.data
        if event.exit_code is not None:
            payload["exit_code"] = event.exit_code
        if event.error is not None:
            payload["error"] = event.error
        await websocket.send_text(json.dumps(payload))
        if event.event_type == "terminal.exit":
            return


@router.get(
    "/terminals",
    response_model=TerminalWorkspaceListResponse,
    summary="List terminal overview",
    description="Return read-only terminal-session overview across canonical web workspaces.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def list_terminal_overview(
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: TerminalSessionService = Depends(get_terminal_session_service),
) -> TerminalWorkspaceListResponse:
    _require_terminal_role(current_user)

    workspaces = [
        workspace
        for workspace in await group_registry.list_registered_groups()
        if _is_web_workspace(workspace)
    ]
    sessions_by_folder = {item.group_folder: item for item in service.list_sessions()}
    histories_by_folder = {item.record.group_folder: item for item in service.list_history_summaries()}

    items: list[TerminalWorkspaceSummaryResponse] = []
    for workspace in workspaces:
        group_id = str(getattr(workspace, "folder", ""))
        if group_id == "":
            continue
        group_name = str(getattr(workspace, "name", group_id))
        session = sessions_by_folder.get(group_id)
        history = histories_by_folder.get(group_id)
        chat_accessible = await group_registry.user_can_access_group(
            user_id=current_user.id,
            user_role=current_user.role,
            group=workspace,
        )
        items.append(
            TerminalWorkspaceSummaryResponse(
                group_id=group_id,
                group_name=group_name,
                chat_accessible=chat_accessible,
                session=_to_terminal_session_response(session) if session is not None else None,
                history=_to_terminal_history_summary_response(history) if history is not None else None,
            )
        )

    items.sort(key=_terminal_workspace_sort_key)
    return TerminalWorkspaceListResponse(items=items)


@router.post(
    "/terminals/{group_id}/sessions",
    response_model=TerminalSessionResponse,
    summary="Create terminal session",
    description="Create or reuse the current owner's terminal session for one accessible workspace.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
    ),
)
async def create_terminal_session(
    group_id: str,
    request: CreateTerminalSessionRequest,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: TerminalSessionService = Depends(get_terminal_session_service),
) -> TerminalSessionResponse:
    _require_terminal_role(current_user)
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )

    try:
        record = await service.create_session(
            group_id=group_id,
            group_folder=workspace.folder,
            owner_user_id=current_user.id,
            requested_mode=request.requested_mode,
        )
    except Exception as exc:
        raise _map_terminal_error(exc) from exc
    return _to_terminal_session_response(record)


@router.get(
    "/terminals/{group_id}/sessions/current",
    response_model=TerminalSessionResponse,
    summary="Get current terminal session",
    description="Return the current terminal session state for one accessible workspace when it exists.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def get_current_terminal_session(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: TerminalSessionService = Depends(get_terminal_session_service),
) -> TerminalSessionResponse:
    _require_terminal_role(current_user)
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    session = service.get_current_session(workspace.folder)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="terminal session not found",
        )
    return _to_terminal_session_response(session)


@router.get(
    "/terminals/{group_id}/sessions/current/history",
    response_model=TerminalSessionHistoryResponse,
    summary="Get current terminal session history",
    description="Return the bounded buffered output history for the current terminal session on one accessible workspace.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def get_current_terminal_session_history(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: TerminalSessionService = Depends(get_terminal_session_service),
) -> TerminalSessionHistoryResponse:
    _require_terminal_role(current_user)
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        snapshot = await service.get_history_by_group(workspace.folder)
    except Exception as exc:
        raise _map_terminal_error(exc) from exc
    return TerminalSessionHistoryResponse(
        session=_to_terminal_session_response(snapshot.record),
        output=snapshot.output,
        output_bytes=snapshot.output_bytes,
        history_max_bytes=snapshot.history_max_bytes,
        truncated=snapshot.truncated,
    )


@router.get(
    "/terminals/{group_id}/sessions/history",
    response_model=TerminalSessionHistoryTimelineResponse,
    summary="Get terminal history timeline",
    description="Return paginated terminal-history timeline metadata for one accessible workspace.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def get_terminal_history_timeline(
    group_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: Literal["created", "attached", "detached", "closed", "exited"] | None = Query(
        default=None,
        alias="status",
    ),
    owner_user_id: str | None = Query(default=None),
    session_id_prefix: str | None = Query(default=None),
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: TerminalSessionService = Depends(get_terminal_session_service),
) -> TerminalSessionHistoryTimelineResponse:
    _require_terminal_role(current_user)
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        page = await service.list_history_timeline_by_group(
            workspace.folder,
            limit=limit,
            offset=offset,
            status=status_filter,
            owner_user_id=owner_user_id,
            session_id_prefix=session_id_prefix,
        )
    except Exception as exc:
        raise _map_terminal_error(exc) from exc
    return TerminalSessionHistoryTimelineResponse(
        limit=page.limit,
        offset=page.offset,
        has_more=page.has_more,
        items=[_to_terminal_history_summary_response(item) for item in page.items],
    )


@router.get(
    "/terminals/{group_id}/sessions/history/search",
    response_model=TerminalSessionHistorySearchResponse,
    summary="Search terminal history output",
    description="Search one accessible workspace terminal-history output and return paginated session-level matches.",
    responses=openapi_error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def search_terminal_history_output(
    group_id: str,
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: Literal["created", "attached", "detached", "closed", "exited"] | None = Query(
        default=None,
        alias="status",
    ),
    owner_user_id: str | None = Query(default=None),
    session_id_prefix: str | None = Query(default=None),
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: TerminalSessionService = Depends(get_terminal_session_service),
) -> TerminalSessionHistorySearchResponse:
    _require_terminal_role(current_user)
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        page = await service.search_history_by_group(
            workspace.folder,
            query=q,
            limit=limit,
            offset=offset,
            status=status_filter,
            owner_user_id=owner_user_id,
            session_id_prefix=session_id_prefix,
        )
    except Exception as exc:
        raise _map_terminal_error(exc) from exc
    return TerminalSessionHistorySearchResponse(
        query=page.query,
        limit=page.limit,
        offset=page.offset,
        total=page.total,
        has_more=page.has_more,
        items=[_to_terminal_history_search_match_response(item) for item in page.items],
    )


@router.get(
    "/terminals/{group_id}/sessions/history/{session_id}",
    response_model=TerminalSessionHistoryDetailResponse,
    summary="Get terminal history detail",
    description="Return one terminal-history snapshot detail for an accessible workspace session.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)
async def get_terminal_history_detail(
    group_id: str,
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: TerminalSessionService = Depends(get_terminal_session_service),
) -> TerminalSessionHistoryDetailResponse:
    _require_terminal_role(current_user)
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        snapshot = await service.get_history_snapshot_by_group(workspace.folder, session_id)
    except Exception as exc:
        raise _map_terminal_error(exc) from exc
    return _to_terminal_history_detail_response(snapshot)


@router.delete(
    "/terminals/{group_id}/sessions/current",
    response_model=DeleteTerminalSessionResponse,
    summary="Close current terminal session",
    description="Close the current terminal session for one accessible workspace.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
    ),
)
async def delete_current_terminal_session(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: TerminalSessionService = Depends(get_terminal_session_service),
) -> DeleteTerminalSessionResponse:
    _require_terminal_role(current_user)
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        await service.close_session_by_group(
            workspace.folder,
            owner_user_id=current_user.id,
        )
    except Exception as exc:
        raise _map_terminal_error(exc) from exc
    return DeleteTerminalSessionResponse(status="closed")


@router.delete(
    "/terminals/{group_id}/sessions/force",
    response_model=DeleteTerminalSessionResponse,
    summary="Force close terminal session",
    description="Force-close the current terminal session for one accessible workspace regardless of current session owner.",
    responses=openapi_error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
    ),
)
async def force_delete_current_terminal_session(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user),
    group_registry: GroupRegistryService = Depends(get_group_registry_service),
    service: TerminalSessionService = Depends(get_terminal_session_service),
) -> DeleteTerminalSessionResponse:
    _require_terminal_role(current_user)
    workspace = await _require_accessible_workspace(
        group_id=group_id,
        current_user=current_user,
        group_registry=group_registry,
    )
    try:
        await service.force_close_session_by_group(workspace.folder)
    except Exception as exc:
        raise _map_terminal_error(exc) from exc
    return DeleteTerminalSessionResponse(status="closed")


@router.websocket("/ws/terminals/{session_id}")
async def terminal_websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    current_user = _authenticate_websocket(websocket)
    if current_user is None:
        await websocket.close(code=1008)
        return

    service = _resolve_terminal_service_for_websocket(websocket)
    output_task: asyncio.Task[None] | None = None
    explicitly_closed = False

    try:
        record, queue = await service.attach_session(
            session_id,
            owner_user_id=current_user.id,
        )
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await websocket.send_text(
        json.dumps(
            {
                "type": "terminal.ready",
                "session_id": record.session_id,
                "backend": record.backend,
                "status": record.status,
            }
        )
    )

    output_task = asyncio.create_task(_forward_terminal_events(websocket, queue))

    try:
        while True:
            message = await websocket.receive_text()
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send_text(_terminal_error_payload("invalid terminal message payload"))
                continue

            if not isinstance(payload, dict):
                await websocket.send_text(_terminal_error_payload("invalid terminal message payload"))
                continue

            message_type = payload.get("type")
            if message_type == "terminal.input":
                data = payload.get("data")
                if not isinstance(data, str):
                    await websocket.send_text(_terminal_error_payload("terminal.input requires string data"))
                    continue
                await service.send_input(session_id, owner_user_id=current_user.id, data=data)
                continue

            if message_type == "terminal.resize":
                cols = payload.get("cols")
                rows = payload.get("rows")
                if not isinstance(cols, int) or not isinstance(rows, int) or cols <= 0 or rows <= 0:
                    await websocket.send_text(_terminal_error_payload("terminal.resize requires positive integer cols and rows"))
                    continue
                await service.resize(session_id, owner_user_id=current_user.id, cols=cols, rows=rows)
                continue

            if message_type == "terminal.close":
                explicitly_closed = True
                await service.close_session(session_id, owner_user_id=current_user.id)
                break

            await websocket.send_text(_terminal_error_payload("unsupported terminal message type"))
    except WebSocketDisconnect:
        pass
    finally:
        if output_task is not None:
            if not output_task.done():
                output_task.cancel()
            await asyncio.gather(output_task, return_exceptions=True)
        if not explicitly_closed:
            try:
                await service.detach_session(session_id, owner_user_id=current_user.id)
            except Exception:
                pass


__all__ = [
    "get_group_registry_service",
    "get_terminal_session_service",
    "router",
]
