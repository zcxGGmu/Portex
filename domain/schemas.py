"""Domain request and response schemas for API routes."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ExecutionMode = Literal["openai", "host", "container"]


def _normalize_utc_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=1,
        description="Unique username for the new Portex account.",
        examples=["alice"],
    )
    password: str = Field(
        min_length=1,
        description="Plain-text password that will be hashed by the auth service.",
        examples=["secret"],
    )
    invite_code: str | None = Field(
        default=None,
        description="Optional invite code that applies the invited role on registration.",
        examples=["owner-lite-2026"],
    )


class RegisterResponse(BaseModel):
    user_id: str = Field(
        description="Identifier assigned to the newly created user.",
        examples=["user-1234567890ab"],
    )


class LoginRequest(BaseModel):
    username: str = Field(
        min_length=1,
        description="Existing username to authenticate.",
        examples=["alice"],
    )
    password: str = Field(
        min_length=1,
        description="Plain-text password for the requested user.",
        examples=["secret"],
    )


class TokenResponse(BaseModel):
    access_token: str = Field(
        description="Bearer token used on authenticated HTTP routes.",
        examples=["eyJhbGciOi..."],
    )
    token_type: str = Field(
        default="bearer",
        description="Token scheme expected by the HTTP API.",
        examples=["bearer"],
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    role: str
    status: str
    avatar_emoji: str | None = None
    avatar_color: str | None = None
    ai_name: str | None = None
    ai_avatar_emoji: str | None = None
    must_change_password: bool = False
    last_login_at: datetime | None = None
    disable_reason: str | None = None
    notes: str | None = None


class UserListResponse(BaseModel):
    users: list[UserResponse]


class UpdateUserRequest(BaseModel):
    role: str | None = Field(default=None, min_length=1)
    status: str | None = Field(default=None, min_length=1)
    avatar_emoji: str | None = None
    avatar_color: str | None = None
    ai_name: str | None = None
    ai_avatar_emoji: str | None = None
    must_change_password: bool | None = None
    disable_reason: str | None = None
    notes: str | None = None


class CreateInviteCodeRequest(BaseModel):
    code: str | None = Field(
        default=None,
        min_length=1,
        description="Optional fixed invite code. When omitted, the service generates one.",
        examples=["owner-lite-2026"],
    )
    role: str = Field(
        default="member",
        min_length=1,
        description="Role applied to the invited user when the code is redeemed.",
        examples=["member"],
    )
    permission_template: str | None = Field(
        default=None,
        description="Optional permission template granted in addition to the role.",
        examples=["owner-lite"],
    )
    expires_at: datetime | None = Field(
        default=None,
        description=(
            "Optional timezone-aware expiration timestamp. Portex preserves the "
            "provided offset."
        ),
        examples=["2026-03-10T12:00:00Z"],
    )


class InviteCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    created_by: str
    role: str
    permission_template: str | None = None
    expires_at: datetime | None = Field(
        default=None,
        description="Optional expiration timestamp returned with its stored timezone information.",
        examples=["2026-03-10T12:00:00+08:00"],
    )
    used_by: str | None = None
    used_at: datetime | None = None


class InviteCodeListResponse(BaseModel):
    invites: list[InviteCodeResponse]


class GroupSummaryResponse(BaseModel):
    group_id: str
    name: str


class GroupListResponse(BaseModel):
    groups: list[GroupSummaryResponse]


class CreateGroupRequest(BaseModel):
    group_id: str = Field(
        min_length=1,
        description="Folder-style identifier for the new shared workspace.",
        examples=["project-alpha"],
    )
    name: str = Field(
        min_length=1,
        description="Display name for the new shared workspace.",
        examples=["Project Alpha"],
    )


class UpdateGroupRequest(BaseModel):
    name: str = Field(
        min_length=1,
        description="Updated display name for the existing shared workspace.",
        examples=["Project Renamed"],
    )


class CreateGroupMemberRequest(BaseModel):
    user_id: str = Field(
        min_length=1,
        description="Existing user identifier to add to the group.",
        examples=["user-1234567890ab"],
    )
    role: str = Field(
        default="member",
        min_length=1,
        description="Group-scoped role for the member. Owner-role transfer is not supported.",
        examples=["member"],
    )


class GroupMemberResponse(BaseModel):
    group_id: str
    user_id: str
    role: str
    joined_at: datetime


class GroupMemberListResponse(BaseModel):
    members: list[GroupMemberResponse]


class DeleteGroupMemberResponse(BaseModel):
    status: str = Field(
        description="Removal result for the group-member delete operation.",
        examples=["removed"],
    )


class WorkspaceFileEntryResponse(BaseModel):
    name: str = Field(
        description="File or directory name relative to its parent listing.",
        examples=["readme.txt"],
    )
    path: str = Field(
        description="Workspace-relative path for the file or directory.",
        examples=["docs/readme.txt"],
    )
    type: Literal["file", "directory"] = Field(
        description="Filesystem entry type.",
        examples=["file"],
    )
    size: int = Field(
        description="Entry size in bytes.",
        examples=[128],
    )
    modified_at: datetime = Field(
        description="Last-modified timestamp in UTC.",
        examples=["2026-03-14T08:00:00Z"],
    )

    @field_validator("modified_at", mode="after")
    @classmethod
    def normalize_workspace_file_modified_at(cls, value: datetime) -> datetime:
        normalized = _normalize_utc_datetime(value)
        if normalized is None:
            raise ValueError("WorkspaceFileEntryResponse.modified_at normalization returned None")
        return normalized


class WorkspaceFileListResponse(BaseModel):
    current_path: str = Field(
        description="Current workspace-relative directory path. Empty string means workspace root.",
        examples=["docs"],
    )
    entries: list[WorkspaceFileEntryResponse]


class WorkspaceFileUploadResponse(BaseModel):
    files: list[str] = Field(
        description="Workspace-relative paths for the uploaded files.",
        examples=[["notes.txt"]],
    )


class WorkspaceFileContentResponse(BaseModel):
    path: str = Field(
        description="Workspace-relative path for the text file.",
        examples=["notes.txt"],
    )
    content: str = Field(
        description="UTF-8 text content read from the workspace file.",
        examples=["hello workspace"],
    )
    size: int = Field(
        description="Text file size in bytes.",
        examples=[15],
    )


class UpdateWorkspaceFileContentRequest(BaseModel):
    content: str = Field(
        description="Replacement UTF-8 text content for the target workspace file.",
        examples=["updated text"],
    )


class DeleteWorkspaceFileResponse(BaseModel):
    status: str = Field(
        description="Delete result for the target workspace file or directory.",
        examples=["deleted"],
    )


class MemoryGlobalResponse(BaseModel):
    content: str = Field(
        description="Current user-global memory content from AGENTS.md.",
        examples=["Always answer in concise bullet points."],
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Last-updated timestamp for the global memory file.",
        examples=["2026-03-15T08:00:00Z"],
    )
    size: int = Field(
        description="Global memory file size in bytes.",
        examples=[42],
    )

    @field_validator("updated_at", mode="after")
    @classmethod
    def normalize_memory_global_updated_at(cls, value: datetime | None) -> datetime | None:
        return _normalize_utc_datetime(value)


class UpdateMemoryGlobalRequest(BaseModel):
    content: str = Field(
        description="Replacement UTF-8 content for the current user's global memory file.",
        examples=["Prefer UTC timestamps in all responses."],
    )


class WorkspaceMemoryFileEntryResponse(BaseModel):
    path: str = Field(
        description="Workspace-memory-relative markdown path.",
        examples=["2026-03-15.md"],
    )
    name: str = Field(
        description="Markdown file name.",
        examples=["2026-03-15.md"],
    )
    updated_at: datetime = Field(
        description="Last-updated timestamp for the markdown memory file.",
        examples=["2026-03-15T08:00:00Z"],
    )
    size: int = Field(
        description="Markdown memory file size in bytes.",
        examples=[128],
    )

    @field_validator("updated_at", mode="after")
    @classmethod
    def normalize_workspace_memory_file_updated_at(cls, value: datetime) -> datetime:
        normalized = _normalize_utc_datetime(value)
        if normalized is None:
            raise ValueError("WorkspaceMemoryFileEntryResponse.updated_at normalization returned None")
        return normalized


class WorkspaceMemoryFileListResponse(BaseModel):
    files: list[WorkspaceMemoryFileEntryResponse]


class WorkspaceMemoryFileResponse(BaseModel):
    path: str = Field(
        description="Workspace-memory-relative markdown path.",
        examples=["notes/today.md"],
    )
    content: str = Field(
        description="UTF-8 markdown memory content.",
        examples=["project launch checklist"],
    )
    updated_at: datetime | None = Field(
        default=None,
        description=(
            "Last-updated timestamp for the markdown memory file. "
            "Null means the file does not exist yet."
        ),
        examples=["2026-03-15T08:00:00Z"],
    )
    size: int = Field(
        description="Markdown memory file size in bytes.",
        examples=[24],
    )

    @field_validator("updated_at", mode="after")
    @classmethod
    def normalize_workspace_memory_file_response_updated_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return _normalize_utc_datetime(value)


class UpdateWorkspaceMemoryFileRequest(BaseModel):
    path: str = Field(
        min_length=1,
        description="Workspace-memory-relative markdown file path to update or create.",
        examples=["notes/today.md"],
    )
    content: str = Field(
        description="Replacement UTF-8 markdown content for the target memory file.",
        examples=["remember: ship checklist first"],
    )


class WorkspaceMemorySearchHitResponse(BaseModel):
    path: str = Field(
        description="Workspace-memory-relative markdown path that matched the query.",
        examples=["notes/today.md"],
    )


class WorkspaceMemorySearchResponse(BaseModel):
    hits: list[WorkspaceMemorySearchHitResponse]


class SkillSummaryResponse(BaseModel):
    skill_id: str = Field(
        description="User-local skill identifier.",
        examples=["writer-guide"],
    )
    enabled: bool = Field(
        description="Whether the skill is currently enabled.",
        examples=[True],
    )
    updated_at: datetime = Field(
        description="Last-updated timestamp for the skill file.",
        examples=["2026-03-15T08:00:00Z"],
    )
    size: int = Field(
        description="Skill file size in bytes.",
        examples=[512],
    )

    @field_validator("updated_at", mode="after")
    @classmethod
    def normalize_skill_summary_updated_at(cls, value: datetime) -> datetime:
        normalized = _normalize_utc_datetime(value)
        if normalized is None:
            raise ValueError("SkillSummaryResponse.updated_at normalization returned None")
        return normalized


class SkillListResponse(BaseModel):
    skills: list[SkillSummaryResponse]


class SkillDetailResponse(BaseModel):
    skill_id: str = Field(
        description="User-local skill identifier.",
        examples=["writer-guide"],
    )
    enabled: bool = Field(
        description="Whether the skill is currently enabled.",
        examples=[True],
    )
    updated_at: datetime = Field(
        description="Last-updated timestamp for the skill file.",
        examples=["2026-03-15T08:00:00Z"],
    )
    size: int = Field(
        description="Skill file size in bytes.",
        examples=[512],
    )
    content: str = Field(
        description="Raw markdown content of the skill file.",
        examples=["# Writer Guide\nAlways explain tradeoffs."],
    )

    @field_validator("updated_at", mode="after")
    @classmethod
    def normalize_skill_detail_updated_at(cls, value: datetime) -> datetime:
        normalized = _normalize_utc_datetime(value)
        if normalized is None:
            raise ValueError("SkillDetailResponse.updated_at normalization returned None")
        return normalized


class UpdateSkillRequest(BaseModel):
    content: str = Field(
        description="Replacement markdown content for the user-owned skill file.",
        examples=["# Writer Guide\nAlways clarify assumptions."],
    )


class UpdateSkillStateRequest(BaseModel):
    enabled: bool = Field(
        description="Target enabled state for the selected skill.",
        examples=[False],
    )


class DeleteSkillResponse(BaseModel):
    status: str = Field(
        description="Delete result for the selected skill.",
        examples=["deleted"],
    )


class CreateConversationSlotRequest(BaseModel):
    slot_id: str = Field(
        min_length=1,
        description="Persistent identifier for the new conversation slot.",
        examples=["draft"],
    )
    title: str = Field(
        min_length=1,
        description="Display title shown for the slot within the workspace.",
        examples=["Draft"],
    )


class ConversationSlotResponse(BaseModel):
    group_id: str = Field(
        description="Workspace identifier that owns the conversation slot.",
        examples=["project-alpha"],
    )
    slot_id: str = Field(
        description="Persistent conversation-slot identifier within the workspace.",
        examples=["main"],
    )
    title: str = Field(
        description="Human-readable slot title.",
        examples=["Main"],
    )
    created_by: str | None = Field(
        default=None,
        description="User identifier that created the slot when recorded.",
        examples=["user-1234567890ab"],
    )
    created_at: datetime = Field(
        description="Creation timestamp for the slot.",
        examples=["2026-03-14T08:00:00Z"],
    )

    @field_validator("created_at", mode="after")
    @classmethod
    def normalize_created_at(cls, value: datetime) -> datetime:
        normalized = _normalize_utc_datetime(value)
        if normalized is None:
            raise ValueError("ConversationSlotResponse.created_at normalization returned None")
        return normalized


class ConversationSlotListResponse(BaseModel):
    slots: list[ConversationSlotResponse]


class GroupIMBindingResponse(BaseModel):
    im_jid: str = Field(
        description="Raw IM endpoint identifier.",
        examples=["telegram:chat-1"],
    )
    name: str = Field(
        description="Display name recorded for the IM endpoint.",
        examples=["Telegram Chat"],
    )
    channel: Literal["telegram", "feishu"] = Field(
        description="IM channel family for the endpoint row.",
        examples=["telegram"],
    )
    fallback_group_id: str = Field(
        description="Fallback isolated workspace folder used when this endpoint is unbound.",
        examples=["chat-a1b2c3"],
    )
    binding_state: Literal["unbound", "bound", "orphaned"] = Field(
        description="Current binding state for the IM endpoint.",
        examples=["bound"],
    )
    target_group_id: str | None = Field(
        default=None,
        description="Canonical workspace identifier when the binding currently resolves.",
        examples=["project-alpha"],
    )
    target_group_name: str | None = Field(
        default=None,
        description="Canonical workspace display name when the binding currently resolves.",
        examples=["Project Alpha"],
    )
    bound_to_current_group: bool = Field(
        description="Whether this IM endpoint is currently bound to the workspace route being queried.",
        examples=[True],
    )


class GroupIMBindingListResponse(BaseModel):
    bindings: list[GroupIMBindingResponse]


class SendMessageRequest(BaseModel):
    group_id: str = Field(
        description="Target group/workspace identifier for the dispatched message.",
        examples=["group-demo"],
    )
    content: str = Field(
        min_length=1,
        description="Message content to dispatch through the current runtime chain.",
        examples=["hello from HTTP"],
    )
    slot_id: str = Field(
        default="main",
        min_length=1,
        description=(
            "Conversation slot identifier under the target workspace. When omitted, "
            "the workspace main slot is used."
        ),
        examples=["main"],
    )
    execution_mode: ExecutionMode | None = Field(
        default=None,
        description=(
            "Optional execution backend preference for this request. When omitted, "
            "the current default execution policy is used."
        ),
        examples=["host"],
    )


class SendMessageResponse(BaseModel):
    message_id: str = Field(
        description="Generated identifier for the normalized inbound message.",
        examples=["msg-abcdef123456"],
    )
    run_id: str | None = Field(
        default=None,
        description="Runtime run identifier associated with the dispatched message.",
        examples=["run-abcdef123456"],
    )
    status: str = Field(
        description="Dispatch result status returned by the current runtime chain.",
        examples=["completed"],
    )
    final_output: str | None = Field(
        default=None,
        description="Final assistant reply when the dispatch completed successfully.",
        examples=["hello from Portex"],
    )


class ExecutionRecoveryResponse(BaseModel):
    attempted: bool = Field(
        description="Whether coordinator recovery logic was attempted for this run.",
        examples=[False],
    )
    reason: str | None = Field(
        default=None,
        description="Recovery trigger reason when a retry path was attempted.",
        examples=["resume failed"],
    )
    succeeded: bool | None = Field(
        default=None,
        description="Recovery outcome when attempted: true for recovered, false for unrecovered.",
        examples=[True],
    )


class MonitorBackendHealthResponse(BaseModel):
    backend: str = Field(
        description="Execution backend identifier.",
        examples=["openai_runtime"],
    )
    status: Literal["ok", "error"] = Field(
        description="Best-effort health state for the backend.",
        examples=["ok"],
    )
    detail: str = Field(
        description="Human-readable backend health detail.",
        examples=["runtime factory available"],
    )


class MonitorHealthResponse(BaseModel):
    api_status: str = Field(
        description="Top-level API process health summary.",
        examples=["ok"],
    )
    version: str = Field(
        description="Current Portex API version string.",
        examples=["0.1.0"],
    )
    coordinator_status: str = Field(
        description="Execution coordinator read-side availability summary.",
        examples=["ok"],
    )
    backends: list[MonitorBackendHealthResponse]


class MonitorQueueGroupResponse(BaseModel):
    group_id: str = Field(
        description="Workspace folder currently represented in the execution queue snapshot.",
        examples=["project-alpha"],
    )
    queued_runs: int = Field(
        description="Number of queued runs waiting behind the active run for this workspace.",
        examples=[2],
    )
    running_runs: int = Field(
        description="Number of currently running runs for this workspace.",
        examples=[1],
    )
    active_run_id: str | None = Field(
        default=None,
        description="Current active run identifier for this workspace when one exists.",
        examples=["run-abcdef123456"],
    )
    active_backend: str | None = Field(
        default=None,
        description="Backend currently executing the active run when one exists.",
        examples=["openai_runtime"],
    )


class MonitorQueueResponse(BaseModel):
    groups: list[MonitorQueueGroupResponse]


class MonitorRunSummaryResponse(BaseModel):
    run_id: str = Field(
        description="Execution run identifier.",
        examples=["run-abcdef123456"],
    )
    group_id: str = Field(
        description="Workspace folder associated with the run.",
        examples=["project-alpha"],
    )
    chat_jid: str = Field(
        description="Transport chat identifier associated with the run.",
        examples=["web:project-alpha"],
    )
    user_id: str = Field(
        description="Caller user identifier carried by the run request.",
        examples=["user-1234567890ab"],
    )
    source: Literal["web", "im", "scheduled"] = Field(
        description="Execution source that submitted the run.",
        examples=["web"],
    )
    slot_id: str = Field(
        description="Conversation slot identifier for the run.",
        examples=["main"],
    )
    status: Literal["queued", "running", "completed", "failed", "cancelled", "timeout"] = Field(
        description="Current or terminal execution status.",
        examples=["running"],
    )
    backend: str | None = Field(
        default=None,
        description="Selected execution backend when known.",
        examples=["host_process"],
    )
    requested_mode: ExecutionMode | None = Field(
        default=None,
        description="Requested execution mode when one was supplied and recognized.",
        examples=["host"],
    )
    created_at: datetime = Field(
        description="Coordinator timestamp when the run entered tracking.",
        examples=["2026-03-14T08:00:00Z"],
    )
    started_at: datetime | None = Field(
        default=None,
        description="Timestamp when execution started.",
        examples=["2026-03-14T08:00:01Z"],
    )
    finished_at: datetime | None = Field(
        default=None,
        description="Timestamp when execution reached a terminal state.",
        examples=["2026-03-14T08:00:05Z"],
    )
    error: str | None = Field(
        default=None,
        description="Error detail for failed or timeout runs when available.",
        examples=["docker unavailable"],
    )
    timeout_ms: int | None = Field(
        default=None,
        description="Requested timeout in milliseconds for timeout runs.",
        examples=[30000],
    )
    recovery: ExecutionRecoveryResponse

    @field_validator("created_at", "started_at", "finished_at", mode="after")
    @classmethod
    def normalize_monitor_datetimes(cls, value: datetime | None) -> datetime | None:
        return _normalize_utc_datetime(value)


class MonitorRunListResponse(BaseModel):
    items: list[MonitorRunSummaryResponse]


class MonitorResponse(BaseModel):
    health: MonitorHealthResponse
    queue: MonitorQueueResponse
    runs: MonitorRunListResponse


class ExecutionRunStatusResponse(BaseModel):
    run_id: str = Field(
        description="Execution run identifier.",
        examples=["run-abcdef123456"],
    )
    status: Literal["queued", "running", "completed", "failed", "cancelled", "timeout"] = Field(
        description="Current execution status tracked by the execution coordinator.",
        examples=["running"],
    )
    group_folder: str = Field(
        description="Group/workspace folder associated with this run.",
        examples=["group-demo"],
    )
    chat_jid: str = Field(
        description="Chat identifier associated with this run.",
        examples=["group-demo"],
    )
    user_id: str = Field(
        description="Caller user identifier carried by the execution request.",
        examples=["user-1234567890ab"],
    )
    source: Literal["web", "im", "scheduled"] = Field(
        description="Execution source that submitted the run.",
        examples=["web"],
    )
    slot_id: str = Field(
        description="Conversation slot identifier within the workspace.",
        examples=["main"],
    )
    requested_mode: ExecutionMode | None = Field(
        default=None,
        description="Optional backend preference from the original request.",
        examples=["host"],
    )
    backend: str | None = Field(
        default=None,
        description="Selected backend once execution has started.",
        examples=["openai_runtime"],
    )
    session_id: str | None = Field(
        default=None,
        description="Session identifier used by the selected backend.",
        examples=["group-demo"],
    )
    created_at: datetime = Field(
        description="Coordinator timestamp when the run entered the queue.",
        examples=["2026-03-13T08:00:00Z"],
    )
    started_at: datetime | None = Field(
        default=None,
        description="Timestamp when the run entered execution.",
        examples=["2026-03-13T08:00:01Z"],
    )
    finished_at: datetime | None = Field(
        default=None,
        description="Timestamp when the run reached a terminal state.",
        examples=["2026-03-13T08:00:05Z"],
    )
    final_output: str | None = Field(
        default=None,
        description="Final output for successful runs when available.",
        examples=["hello from Portex"],
    )
    error: str | None = Field(
        default=None,
        description="Error text for failed or timeout runs when available.",
        examples=["execution failed"],
    )
    timeout_ms: int | None = Field(
        default=None,
        description="Requested timeout in milliseconds for timeout runs.",
        examples=[30000],
    )
    recovery: ExecutionRecoveryResponse

    @field_validator("created_at", "started_at", "finished_at", mode="after")
    @classmethod
    def normalize_execution_datetimes(cls, value: datetime | None) -> datetime | None:
        return _normalize_utc_datetime(value)


class UnifiedMessage(BaseModel):
    channel: Literal["web", "feishu", "telegram"]
    chat_jid: str = Field(min_length=1)
    sender_id: str = Field(min_length=1)
    group_folder: str | None = None
    slot_id: str = Field(default="main", min_length=1)
    content: str
    message_id: str = Field(min_length=1)
    timestamp: datetime

    @field_validator("timestamp", mode="after")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        normalized = _normalize_utc_datetime(value)
        if normalized is None:
            raise ValueError("UnifiedMessage.timestamp normalization returned None")
        return normalized


class CreateTaskRequest(BaseModel):
    group_folder: str = Field(
        min_length=1,
        description="Group workspace folder used by the scheduler and runner.",
        examples=["group-demo"],
    )
    chat_jid: str = Field(
        min_length=1,
        description="Chat identifier associated with the scheduled task.",
        examples=["group-demo"],
    )
    prompt: str = Field(
        min_length=1,
        description="Prompt that will be sent to the agent when the task runs.",
        examples=["send scheduled prompt"],
    )
    execution_mode: ExecutionMode | None = Field(
        default=None,
        description=(
            "Optional execution backend preference for this task. When omitted, the "
            "task uses the default execution policy."
        ),
        examples=["container"],
    )
    schedule_type: Literal["cron", "interval", "once"] = Field(
        description="Scheduling mode for the task.",
        examples=["once"],
    )
    schedule_value: str | None = Field(
        default=None,
        description="Required for `cron` and `interval` tasks; omitted for `once`.",
        examples=["0 * * * *"],
    )
    next_run: datetime | None = Field(
        default=None,
        description=(
            "Required for one-off tasks and interpreted in UTC in the public API."
        ),
        examples=["2026-03-10T12:00:00Z"],
    )

    @field_validator("next_run", mode="after")
    @classmethod
    def normalize_next_run(cls, value: datetime | None) -> datetime | None:
        return _normalize_utc_datetime(value)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Unique task identifier.", examples=["task-1234567890ab"])
    group_folder: str = Field(
        description="Group workspace folder associated with the task.",
        examples=["group-demo"],
    )
    chat_jid: str = Field(
        description="Chat identifier associated with the task.",
        examples=["group-demo"],
    )
    prompt: str = Field(
        description="Prompt executed when the task runs.",
        examples=["send scheduled prompt"],
    )
    execution_mode: ExecutionMode | None = Field(
        default=None,
        description="Optional execution backend preference stored on the task.",
        examples=["host"],
    )
    schedule_type: Literal["cron", "interval", "once"] = Field(
        description="Scheduling mode for the task.",
        examples=["once"],
    )
    schedule_value: str | None = Field(
        default=None,
        description="Schedule expression or interval value when applicable.",
        examples=["0 * * * *"],
    )
    next_run: datetime | None = Field(
        default=None,
        description="Next scheduled run time returned in UTC.",
        examples=["2026-03-10T12:00:00Z"],
    )
    status: str = Field(
        description="Current task status in the scheduler.",
        examples=["active"],
    )
    created_at: datetime = Field(
        description="Task creation time returned in UTC.",
        examples=["2026-03-10T11:55:00Z"],
    )

    @field_validator("next_run", "created_at", mode="after")
    @classmethod
    def normalize_datetime_fields(cls, value: datetime | None) -> datetime | None:
        return _normalize_utc_datetime(value)


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]


class DeleteTaskResponse(BaseModel):
    status: str


class TaskRunLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    run_at: datetime
    duration_ms: int
    status: Literal["success", "error", "timeout"]
    result: str | None = None
    error: str | None = None

    @field_validator("run_at", mode="after")
    @classmethod
    def normalize_run_at(cls, value: datetime) -> datetime:
        normalized = _normalize_utc_datetime(value)
        if normalized is None:
            raise ValueError("TaskRunLogResponse.run_at normalization returned None")
        return normalized


class TaskRunLogListResponse(BaseModel):
    logs: list[TaskRunLogResponse]


__all__ = [
    "CreateGroupMemberRequest",
    "DeleteTaskResponse",
    "DeleteGroupMemberResponse",
    "ExecutionRecoveryResponse",
    "ExecutionRunStatusResponse",
    "GroupListResponse",
    "GroupMemberListResponse",
    "GroupMemberResponse",
    "GroupSummaryResponse",
    "HealthResponse",
    "CreateInviteCodeRequest",
    "InviteCodeListResponse",
    "InviteCodeResponse",
    "LoginRequest",
    "RegisterRequest",
    "RegisterResponse",
    "SendMessageRequest",
    "SendMessageResponse",
    "CreateTaskRequest",
    "TaskListResponse",
    "TaskRunLogListResponse",
    "TaskRunLogResponse",
    "TaskResponse",
    "TokenResponse",
    "UnifiedMessage",
    "UpdateUserRequest",
    "UserListResponse",
    "UserResponse",
]
