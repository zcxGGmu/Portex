"""Domain request and response schemas for API routes."""

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RegisterResponse(BaseModel):
    user_id: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
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


class GroupSummaryResponse(BaseModel):
    group_id: str
    name: str


class GroupListResponse(BaseModel):
    groups: list[GroupSummaryResponse]


class SendMessageRequest(BaseModel):
    group_id: str
    content: str = Field(min_length=1)


class SendMessageResponse(BaseModel):
    message_id: str
    status: str


__all__ = [
    "GroupListResponse",
    "GroupSummaryResponse",
    "HealthResponse",
    "LoginRequest",
    "RegisterRequest",
    "RegisterResponse",
    "SendMessageRequest",
    "SendMessageResponse",
    "TokenResponse",
    "UserResponse",
]
