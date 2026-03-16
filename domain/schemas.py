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


class McpServerSummaryResponse(BaseModel):
    server_id: str = Field(
        description="User-local MCP server identifier.",
        examples=["local-cli"],
    )
    transport: Literal["stdio", "http", "sse"] = Field(
        description="Transport family for the MCP server.",
        examples=["stdio"],
    )
    enabled: bool = Field(
        description="Whether the MCP server is currently enabled.",
        examples=[True],
    )
    updated_at: datetime = Field(
        description="Last-updated timestamp for the MCP server config.",
        examples=["2026-03-15T08:00:00Z"],
    )

    @field_validator("updated_at", mode="after")
    @classmethod
    def normalize_mcp_server_summary_updated_at(cls, value: datetime) -> datetime:
        normalized = _normalize_utc_datetime(value)
        if normalized is None:
            raise ValueError("McpServerSummaryResponse.updated_at normalization returned None")
        return normalized


class McpServerListResponse(BaseModel):
    servers: list[McpServerSummaryResponse]


class McpServerDetailResponse(BaseModel):
    server_id: str = Field(
        description="User-local MCP server identifier.",
        examples=["local-cli"],
    )
    transport: Literal["stdio", "http", "sse"] = Field(
        description="Transport family for the MCP server.",
        examples=["stdio"],
    )
    enabled: bool = Field(
        description="Whether the MCP server is currently enabled.",
        examples=[True],
    )
    description: str | None = Field(
        default=None,
        description="Optional operator-facing description for the MCP server.",
        examples=["Local stdio MCP server"],
    )
    created_at: datetime = Field(
        description="Creation timestamp for this MCP server entry.",
        examples=["2026-03-15T08:00:00Z"],
    )
    updated_at: datetime = Field(
        description="Last-updated timestamp for this MCP server entry.",
        examples=["2026-03-15T08:05:00Z"],
    )
    command: str | None = Field(
        default=None,
        description="Stdio transport command when `transport=stdio`.",
        examples=["uvx"],
    )
    args: list[str] | None = Field(
        default=None,
        description="Stdio transport command arguments when `transport=stdio`.",
        examples=[["mcp-server-sqlite"]],
    )
    env: dict[str, str] | None = Field(
        default=None,
        description="Stdio transport environment variables when `transport=stdio`.",
        examples=[{"MCP_ROOT": "/workspace"}],
    )
    url: str | None = Field(
        default=None,
        description="HTTP/SSE transport URL when `transport=http|sse`.",
        examples=["https://example.com/mcp"],
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="HTTP/SSE transport request headers when `transport=http|sse`.",
        examples=[{"Authorization": "Bearer token"}],
    )

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def normalize_mcp_server_detail_datetimes(cls, value: datetime) -> datetime:
        normalized = _normalize_utc_datetime(value)
        if normalized is None:
            raise ValueError("McpServerDetailResponse datetime normalization returned None")
        return normalized


class UpdateMcpServerRequest(BaseModel):
    transport: Literal["stdio", "http", "sse"] = Field(
        description="Target transport for the MCP server entry.",
        examples=["stdio"],
    )
    command: str | None = Field(
        default=None,
        description="Required when `transport=stdio`.",
        examples=["uvx"],
    )
    args: list[str] | None = Field(
        default=None,
        description="Optional stdio arguments when `transport=stdio`.",
        examples=[["mcp-server-sqlite"]],
    )
    env: dict[str, str] | None = Field(
        default=None,
        description="Optional stdio environment variables when `transport=stdio`.",
        examples=[{"MCP_ROOT": "/workspace"}],
    )
    url: str | None = Field(
        default=None,
        description="Required when `transport=http|sse`.",
        examples=["https://example.com/mcp"],
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="Optional HTTP/SSE headers when `transport=http|sse`.",
        examples=[{"Authorization": "Bearer token"}],
    )
    description: str | None = Field(
        default=None,
        description="Optional operator-facing description.",
        examples=["Remote docs MCP"],
    )


class UpdateMcpServerStateRequest(BaseModel):
    enabled: bool = Field(
        description="Target enabled state for the selected MCP server.",
        examples=[False],
    )


class DeleteMcpServerResponse(BaseModel):
    status: str = Field(
        description="Delete result for the selected MCP server.",
        examples=["deleted"],
    )


class SettingsProviderResponse(BaseModel):
    enabled: bool = Field(
        description="Whether user-level provider config is enabled.",
        examples=[True],
    )
    base_url: str = Field(
        description="User-level OpenAI-compatible provider base URL.",
        examples=["https://api.example.com/v1"],
    )
    default_model: str = Field(
        description="Default model used by this user's provider profile.",
        examples=["gpt-5.1"],
    )
    has_api_key: bool = Field(
        description="Whether an API key is currently stored for this user.",
        examples=[True],
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Last-updated timestamp for this user's provider config.",
        examples=["2026-03-15T08:00:00Z"],
    )

    @field_validator("updated_at", mode="after")
    @classmethod
    def normalize_settings_provider_updated_at(cls, value: datetime | None) -> datetime | None:
        return _normalize_utc_datetime(value)


class UpdateSettingsProviderRequest(BaseModel):
    enabled: bool = Field(
        description="Whether user-level provider config should be enabled.",
        examples=[True],
    )
    base_url: str = Field(
        description="User-level OpenAI-compatible provider base URL.",
        examples=["https://api.example.com/v1"],
    )
    default_model: str = Field(
        description="Default model for user-level provider requests.",
        examples=["gpt-5.1"],
    )
    api_key: str | None = Field(
        default=None,
        description=(
            "Optional provider API key update. When omitted or null, the existing "
            "stored key is preserved."
        ),
        examples=["sk-demo"],
    )


class SettingsChannelsResponse(BaseModel):
    feishu_enabled: bool = Field(
        description="Whether Feishu channel config is enabled for this user profile.",
        examples=[False],
    )
    feishu_app_id: str = Field(
        description="Stored Feishu app id for this user profile.",
        examples=["cli_app_id"],
    )
    feishu_has_app_secret: bool = Field(
        description="Whether a Feishu app secret is currently stored.",
        examples=[True],
    )
    feishu_has_encrypt_key: bool = Field(
        description="Whether a Feishu encrypt key is currently stored.",
        examples=[True],
    )
    feishu_has_verification_token: bool = Field(
        description="Whether a Feishu verification token is currently stored.",
        examples=[True],
    )
    telegram_enabled: bool = Field(
        description="Whether Telegram channel config is enabled for this user profile.",
        examples=[True],
    )
    telegram_has_bot_token: bool = Field(
        description="Whether a Telegram bot token is currently stored.",
        examples=[True],
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Last-updated timestamp for this user's channel config.",
        examples=["2026-03-15T08:00:00Z"],
    )

    @field_validator("updated_at", mode="after")
    @classmethod
    def normalize_settings_channels_updated_at(cls, value: datetime | None) -> datetime | None:
        return _normalize_utc_datetime(value)


class UpdateSettingsChannelsRequest(BaseModel):
    feishu_enabled: bool = Field(
        description="Whether Feishu channel config should be enabled.",
        examples=[True],
    )
    feishu_app_id: str = Field(
        description="Feishu app id to store for this user profile.",
        examples=["cli_app_id"],
    )
    feishu_app_secret: str = Field(
        description="Feishu app secret to store for this user profile.",
        examples=["cli_app_secret"],
    )
    feishu_encrypt_key: str = Field(
        description="Feishu encrypt key to store for this user profile.",
        examples=["encrypt-key"],
    )
    feishu_verification_token: str = Field(
        description="Feishu verification token to store for this user profile.",
        examples=["verify-token"],
    )
    telegram_enabled: bool = Field(
        description="Whether Telegram channel config should be enabled.",
        examples=[True],
    )
    telegram_bot_token: str = Field(
        description="Telegram bot token to store for this user profile.",
        examples=["bot-token"],
    )


class SettingsRegistrationResponse(BaseModel):
    allow_registration: bool = Field(
        description="Whether new users are currently allowed to self-register.",
        examples=[True],
    )
    require_invite_code: bool = Field(
        description="Whether registration currently requires an invite code.",
        examples=[False],
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Last-updated timestamp for registration policy.",
        examples=["2026-03-15T08:00:00Z"],
    )

    @field_validator("updated_at", mode="after")
    @classmethod
    def normalize_settings_registration_updated_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return _normalize_utc_datetime(value)


class UpdateSettingsRegistrationRequest(BaseModel):
    allow_registration: bool = Field(
        description="Whether self-registration should be enabled.",
        examples=[True],
    )
    require_invite_code: bool = Field(
        description="Whether self-registration should require invite codes.",
        examples=[True],
    )


class SettingsAppearanceResponse(BaseModel):
    app_name: str = Field(
        description="Display name used for the web application shell.",
        examples=["Portex"],
    )
    ai_name: str = Field(
        description="Assistant display name used in operator surfaces.",
        examples=["Portex Assistant"],
    )
    ai_avatar_emoji: str = Field(
        description="Assistant avatar emoji shown in UI surfaces.",
        examples=["🤖"],
    )
    ai_avatar_color: str = Field(
        description="Assistant avatar accent color shown in UI surfaces.",
        examples=["#0ea5e9"],
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Last-updated timestamp for appearance config.",
        examples=["2026-03-15T08:00:00Z"],
    )

    @field_validator("updated_at", mode="after")
    @classmethod
    def normalize_settings_appearance_updated_at(cls, value: datetime | None) -> datetime | None:
        return _normalize_utc_datetime(value)


class UpdateSettingsAppearanceRequest(BaseModel):
    app_name: str = Field(
        description="Updated application display name.",
        examples=["Portex Ops"],
    )
    ai_name: str = Field(
        description="Updated assistant display name.",
        examples=["Ops Assistant"],
    )
    ai_avatar_emoji: str = Field(
        description="Updated assistant avatar emoji.",
        examples=["🦀"],
    )
    ai_avatar_color: str = Field(
        description="Updated assistant avatar color.",
        examples=["#2563eb"],
    )


class SettingsSystemResponse(BaseModel):
    default_execution_mode: ExecutionMode = Field(
        description="Default execution mode used by operator workflows.",
        examples=["openai"],
    )
    allow_host_execution: bool = Field(
        description="Whether host execution mode is allowed by current system settings.",
        examples=[False],
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Last-updated timestamp for system settings.",
        examples=["2026-03-15T08:00:00Z"],
    )

    @field_validator("updated_at", mode="after")
    @classmethod
    def normalize_settings_system_updated_at(cls, value: datetime | None) -> datetime | None:
        return _normalize_utc_datetime(value)


class UpdateSettingsSystemRequest(BaseModel):
    default_execution_mode: ExecutionMode = Field(
        description="Desired default execution mode.",
        examples=["container"],
    )
    allow_host_execution: bool = Field(
        description="Whether host execution mode should be allowed.",
        examples=[True],
    )


class CreateTerminalSessionRequest(BaseModel):
    requested_mode: ExecutionMode = Field(
        default="container",
        description="Requested execution mode for the terminal session. Terminal v1 only supports container mode.",
        examples=["container"],
    )


class TerminalSessionResponse(BaseModel):
    session_id: str = Field(
        description="Current terminal session identifier.",
        examples=["terminal-session-123"],
    )
    group_id: str = Field(
        description="Workspace identifier that owns the terminal session.",
        examples=["project-alpha"],
    )
    owner_user_id: str = Field(
        description="User identifier that owns the current terminal session.",
        examples=["user-1234567890ab"],
    )
    backend: Literal["docker_container"] = Field(
        description="Execution backend currently used by the terminal session.",
        examples=["docker_container"],
    )
    container_name: str | None = Field(
        default=None,
        description="Docker container name reserved for the current terminal session when known.",
        examples=["portex-terminal-project-alpha-123"],
    )
    status: Literal["created", "attached", "detached", "closed", "exited"] = Field(
        description="Current terminal session lifecycle state.",
        examples=["attached"],
    )
    created_at: datetime = Field(
        description="Terminal session creation timestamp in UTC.",
        examples=["2026-03-15T12:00:00Z"],
    )
    last_attached_at: datetime | None = Field(
        default=None,
        description="Last timestamp when a WebSocket client successfully attached to the session.",
        examples=["2026-03-15T12:01:00Z"],
    )
    reconnect_deadline: datetime | None = Field(
        default=None,
        description="Reconnect deadline while the session is detached, when one exists.",
        examples=["2026-03-15T12:01:30Z"],
    )

    @field_validator("created_at", "last_attached_at", "reconnect_deadline", mode="after")
    @classmethod
    def normalize_terminal_session_datetimes(cls, value: datetime | None) -> datetime | None:
        return _normalize_utc_datetime(value)


class TerminalSessionHistoryResponse(BaseModel):
    session: TerminalSessionResponse = Field(
        description="Current terminal session snapshot associated with this history payload.",
    )
    output: str = Field(
        description="Buffered terminal output text for the current session in chronological order.",
        examples=["$ pwd\n/workspace/group\n"],
    )
    output_bytes: int = Field(
        description="Current buffered output size in UTF-8 bytes.",
        examples=[2048],
    )
    history_max_bytes: int = Field(
        description="Configured maximum number of UTF-8 bytes retained in memory for output history.",
        examples=[32768],
    )
    truncated: bool = Field(
        description="Whether older history chunks were dropped due to the configured history size cap.",
        examples=[False],
    )


class TerminalSessionHistorySummaryResponse(BaseModel):
    session: TerminalSessionResponse = Field(
        description="Terminal session snapshot associated with this history summary.",
    )
    output_bytes: int = Field(
        description="Buffered terminal output size in UTF-8 bytes for this workspace snapshot.",
        examples=[2048],
    )
    history_max_bytes: int = Field(
        description="Configured maximum retained history bytes for this workspace snapshot.",
        examples=[32768],
    )
    truncated: bool = Field(
        description="Whether older history was truncated under the configured cap for this workspace snapshot.",
        examples=[False],
    )


class TerminalSessionHistoryTimelineResponse(BaseModel):
    limit: int = Field(
        description="Maximum number of timeline entries requested for this page.",
        examples=[20],
    )
    offset: int = Field(
        description="Zero-based starting offset into the workspace terminal-history timeline.",
        examples=[0],
    )
    has_more: bool = Field(
        description="Whether additional timeline entries are available after this page.",
        examples=[True],
    )
    items: list[TerminalSessionHistorySummaryResponse] = Field(
        description="Paginated terminal-history timeline entries ordered by newest snapshot first.",
    )


class TerminalWorkspaceSummaryResponse(BaseModel):
    group_id: str = Field(
        description="Workspace identifier represented in the terminal overview.",
        examples=["project-alpha"],
    )
    group_name: str = Field(
        description="Workspace display name represented in the terminal overview.",
        examples=["Project Alpha"],
    )
    chat_accessible: bool = Field(
        description="Whether the current operator can open this workspace in chat.",
        examples=[True],
    )
    session: TerminalSessionResponse | None = Field(
        default=None,
        description="Current terminal session snapshot for this workspace when one exists.",
    )
    history: TerminalSessionHistorySummaryResponse | None = Field(
        default=None,
        description="Latest terminal history summary for this workspace when a snapshot exists.",
    )


class TerminalWorkspaceListResponse(BaseModel):
    items: list[TerminalWorkspaceSummaryResponse]


class DeleteTerminalSessionResponse(BaseModel):
    status: Literal["closed"] = Field(
        description="Result of the terminal-session close operation.",
        examples=["closed"],
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


class UsageSummaryResponse(BaseModel):
    total_messages: int = Field(
        description="Total number of messages in the selected usage window.",
        examples=[128],
    )
    total_runs: int = Field(
        description="Total number of distinct run identifiers observed in the selected window.",
        examples=[42],
    )
    total_user_messages: int = Field(
        description="Number of inbound user messages in the selected window.",
        examples=[64],
    )
    total_assistant_messages: int = Field(
        description="Number of assistant/outbound messages in the selected window.",
        examples=[64],
    )
    total_active_days: int = Field(
        description="Number of days with at least one message in the selected window.",
        examples=[6],
    )


class UsageDailyBreakdownResponse(BaseModel):
    date: str = Field(
        description="UTC calendar date for the aggregated usage row.",
        examples=["2026-03-15"],
    )
    message_count: int = Field(
        description="Total message count on this day.",
        examples=[18],
    )
    run_count: int = Field(
        description="Distinct run count observed on this day.",
        examples=[9],
    )
    user_message_count: int = Field(
        description="Inbound user message count on this day.",
        examples=[10],
    )
    assistant_message_count: int = Field(
        description="Assistant message count on this day.",
        examples=[8],
    )


class UsageChannelBreakdownResponse(BaseModel):
    channel: Literal["web", "feishu", "telegram"] = Field(
        description="Channel identifier used for usage aggregation.",
        examples=["web"],
    )
    message_count: int = Field(
        description="Total message count observed on this channel.",
        examples=[80],
    )
    run_count: int = Field(
        description="Distinct run count observed on this channel.",
        examples=[31],
    )


class UsageStatsResponse(BaseModel):
    days: int = Field(
        description="Effective usage window in days after server-side normalization.",
        examples=[7],
    )
    summary: UsageSummaryResponse
    daily: list[UsageDailyBreakdownResponse]
    channels: list[UsageChannelBreakdownResponse]


class AuditMessageResponse(BaseModel):
    message_id: str = Field(
        description="Message record identifier.",
        examples=["msg-123abc"],
    )
    chat_jid: str = Field(
        description="Chat transport identifier for this message.",
        examples=["web:project-alpha"],
    )
    group_id: str = Field(
        description="Resolved workspace/group identifier used by operator surfaces.",
        examples=["project-alpha"],
    )
    channel: Literal["web", "feishu", "telegram"] = Field(
        description="Resolved message channel.",
        examples=["web"],
    )
    run_id: str | None = Field(
        default=None,
        description="Correlated execution run identifier when available.",
        examples=["run-abcdef123456"],
    )
    external_message_id: str | None = Field(
        default=None,
        description="Transport-side message identifier when available.",
        examples=["out-run-abcdef123456"],
    )
    sender: str = Field(
        description="Message sender identifier.",
        examples=["portex"],
    )
    is_from_me: bool = Field(
        description="Whether this record was emitted by the assistant/runtime side.",
        examples=[True],
    )
    slot_id: str = Field(
        description="Conversation slot identifier for this message.",
        examples=["main"],
    )
    content: str | None = Field(
        default=None,
        description="Stored message content.",
        examples=["hello from Portex"],
    )
    timestamp: datetime = Field(
        description="Stored message timestamp normalized to UTC.",
        examples=["2026-03-15T10:00:00Z"],
    )

    @field_validator("timestamp", mode="after")
    @classmethod
    def normalize_audit_timestamp(cls, value: datetime) -> datetime:
        normalized = _normalize_utc_datetime(value)
        if normalized is None:
            raise ValueError("AuditMessageResponse.timestamp normalization returned None")
        return normalized


class AuditMessageListResponse(BaseModel):
    limit: int = Field(
        description="Effective limit after server-side normalization.",
        examples=[100],
    )
    group_id: str | None = Field(
        default=None,
        description="Optional workspace/group filter applied to this response.",
        examples=["project-alpha"],
    )
    has_more: bool = Field(
        description="Whether additional records remain beyond the current page limit.",
        examples=[False],
    )
    items: list[AuditMessageResponse]


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
    "AuditMessageListResponse",
    "AuditMessageResponse",
    "CreateTerminalSessionRequest",
    "CreateGroupMemberRequest",
    "DeleteTaskResponse",
    "DeleteTerminalSessionResponse",
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
    "TerminalSessionHistoryResponse",
    "TerminalSessionHistorySummaryResponse",
    "TerminalSessionHistoryTimelineResponse",
    "TerminalSessionResponse",
    "TerminalWorkspaceListResponse",
    "TerminalWorkspaceSummaryResponse",
    "TokenResponse",
    "UnifiedMessage",
    "UpdateUserRequest",
    "UsageChannelBreakdownResponse",
    "UsageDailyBreakdownResponse",
    "UsageStatsResponse",
    "UsageSummaryResponse",
    "UserListResponse",
    "UserResponse",
]
