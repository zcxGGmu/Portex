"""Domain request and response schemas for API routes."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    invite_code: str | None = None


class RegisterResponse(BaseModel):
    user_id: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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
    code: str | None = Field(default=None, min_length=1)
    role: str = Field(default="member", min_length=1)
    permission_template: str | None = None
    expires_at: datetime | None = None


class InviteCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    created_by: str
    role: str
    permission_template: str | None = None
    expires_at: datetime | None = None
    used_by: str | None = None
    used_at: datetime | None = None


class InviteCodeListResponse(BaseModel):
    invites: list[InviteCodeResponse]


class GroupSummaryResponse(BaseModel):
    group_id: str
    name: str


class GroupListResponse(BaseModel):
    groups: list[GroupSummaryResponse]


class CreateGroupMemberRequest(BaseModel):
    user_id: str = Field(min_length=1)
    role: str = Field(default="member", min_length=1)


class GroupMemberResponse(BaseModel):
    group_id: str
    user_id: str
    role: str
    joined_at: datetime


class GroupMemberListResponse(BaseModel):
    members: list[GroupMemberResponse]


class SendMessageRequest(BaseModel):
    group_id: str
    content: str = Field(min_length=1)


class SendMessageResponse(BaseModel):
    message_id: str
    status: str


__all__ = [
    "CreateGroupMemberRequest",
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
    "TokenResponse",
    "UpdateUserRequest",
    "UserListResponse",
    "UserResponse",
]
