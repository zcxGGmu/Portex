"""Operator-facing usage and audit read helpers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.message import Message

_DEFAULT_DAYS = 7
_MAX_DAYS = 365
_MIN_DAYS = 1
_DEFAULT_LIMIT = 100
_MAX_LIMIT = 200
_MIN_LIMIT = 1


@dataclass(frozen=True, slots=True)
class UsageSummarySnapshot:
    total_messages: int
    total_runs: int
    total_user_messages: int
    total_assistant_messages: int
    total_active_days: int


@dataclass(frozen=True, slots=True)
class UsageDailyBreakdownSnapshot:
    date: str
    message_count: int
    run_count: int
    user_message_count: int
    assistant_message_count: int


@dataclass(frozen=True, slots=True)
class UsageChannelBreakdownSnapshot:
    channel: str
    message_count: int
    run_count: int


@dataclass(frozen=True, slots=True)
class UsageStatsSnapshot:
    days: int
    summary: UsageSummarySnapshot
    daily: list[UsageDailyBreakdownSnapshot]
    channels: list[UsageChannelBreakdownSnapshot]


@dataclass(frozen=True, slots=True)
class AuditMessageSnapshot:
    message_id: str
    chat_jid: str
    group_id: str
    channel: str
    run_id: str | None
    external_message_id: str | None
    sender: str
    is_from_me: bool
    slot_id: str
    content: str | None
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class AuditMessageListSnapshot:
    items: list[AuditMessageSnapshot]
    limit: int
    group_id: str | None
    has_more: bool


@dataclass(frozen=True, slots=True)
class _MessageMetadata:
    channel: str
    group_id: str
    run_id: str | None
    external_message_id: str | None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_days(days: int) -> int:
    return max(_MIN_DAYS, min(_MAX_DAYS, days))


def _normalize_limit(limit: int) -> int:
    return max(_MIN_LIMIT, min(_MAX_LIMIT, limit))


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_attachments(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return parsed


def _as_non_empty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _infer_channel(chat_jid: str, attachments: dict[str, object]) -> str:
    channel = _as_non_empty_string(attachments.get("channel"))
    if channel in {"web", "feishu", "telegram"}:
        return channel
    if chat_jid.startswith("feishu:"):
        return "feishu"
    if chat_jid.startswith("telegram:"):
        return "telegram"
    return "web"


def _infer_group_id(chat_jid: str, attachments: dict[str, object]) -> str:
    attachment_group = _as_non_empty_string(attachments.get("group_folder"))
    if attachment_group is not None:
        return attachment_group
    if chat_jid.startswith("web:"):
        web_group = chat_jid.split(":", 1)[1]
        return web_group or chat_jid
    return chat_jid


class UsageAuditService:
    """Read-side service for operator usage and audit views."""

    def __init__(
        self,
        *,
        db: AsyncSession,
        now_func: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._db = db
        self._now_func = now_func

    async def get_usage_stats(self, *, days: int = _DEFAULT_DAYS) -> UsageStatsSnapshot:
        normalized_days = _normalize_days(days)
        now = _normalize_timestamp(self._now_func())
        first_day = (now - timedelta(days=normalized_days - 1)).date()
        window_start = datetime(
            year=first_day.year,
            month=first_day.month,
            day=first_day.day,
        )

        result = await self._db.execute(
            select(Message)
            .where(Message.timestamp >= window_start)
            .order_by(Message.timestamp.asc(), Message.id.asc())
        )
        messages = list(result.scalars().all())

        total_user_messages = 0
        total_assistant_messages = 0
        run_ids: set[str] = set()

        daily_message_counts: dict[str, int] = defaultdict(int)
        daily_user_counts: dict[str, int] = defaultdict(int)
        daily_assistant_counts: dict[str, int] = defaultdict(int)
        daily_run_ids: dict[str, set[str]] = defaultdict(set)

        channel_message_counts: dict[str, int] = defaultdict(int)
        channel_run_ids: dict[str, set[str]] = defaultdict(set)

        for message in messages:
            timestamp = _normalize_timestamp(message.timestamp)
            date_key = timestamp.date().isoformat()
            metadata = self._extract_metadata(message)

            daily_message_counts[date_key] += 1
            channel_message_counts[metadata.channel] += 1

            if message.is_from_me:
                total_assistant_messages += 1
                daily_assistant_counts[date_key] += 1
            else:
                total_user_messages += 1
                daily_user_counts[date_key] += 1

            if metadata.run_id is not None:
                run_ids.add(metadata.run_id)
                daily_run_ids[date_key].add(metadata.run_id)
                channel_run_ids[metadata.channel].add(metadata.run_id)

        daily = [
            UsageDailyBreakdownSnapshot(
                date=date_key,
                message_count=daily_message_counts[date_key],
                run_count=len(daily_run_ids[date_key]),
                user_message_count=daily_user_counts[date_key],
                assistant_message_count=daily_assistant_counts[date_key],
            )
            for date_key in sorted(daily_message_counts)
        ]

        channels = [
            UsageChannelBreakdownSnapshot(
                channel=channel,
                message_count=channel_message_counts[channel],
                run_count=len(channel_run_ids[channel]),
            )
            for channel in sorted(
                channel_message_counts,
                key=lambda item: (-channel_message_counts[item], item),
            )
        ]

        return UsageStatsSnapshot(
            days=normalized_days,
            summary=UsageSummarySnapshot(
                total_messages=len(messages),
                total_runs=len(run_ids),
                total_user_messages=total_user_messages,
                total_assistant_messages=total_assistant_messages,
                total_active_days=len(daily_message_counts),
            ),
            daily=daily,
            channels=channels,
        )

    async def list_audit_messages(
        self,
        *,
        limit: int = _DEFAULT_LIMIT,
        group_id: str | None = None,
    ) -> AuditMessageListSnapshot:
        normalized_limit = _normalize_limit(limit)
        normalized_group_id = group_id.strip() if group_id is not None else None
        if normalized_group_id == "":
            normalized_group_id = None

        statement = select(Message).order_by(Message.timestamp.desc(), Message.id.desc())
        if normalized_group_id is None:
            statement = statement.limit(normalized_limit + 1)

        result = await self._db.execute(statement)
        candidates = list(result.scalars().all())

        items: list[AuditMessageSnapshot] = []
        for message in candidates:
            metadata = self._extract_metadata(message)
            if normalized_group_id is not None and metadata.group_id != normalized_group_id:
                continue
            items.append(
                AuditMessageSnapshot(
                    message_id=message.id,
                    chat_jid=message.chat_jid,
                    group_id=metadata.group_id,
                    channel=metadata.channel,
                    run_id=metadata.run_id,
                    external_message_id=metadata.external_message_id,
                    sender=message.sender,
                    is_from_me=message.is_from_me,
                    slot_id=message.slot_id,
                    content=message.content,
                    timestamp=_normalize_timestamp(message.timestamp),
                )
            )
            if len(items) >= normalized_limit + 1:
                break

        has_more = len(items) > normalized_limit

        return AuditMessageListSnapshot(
            items=items[:normalized_limit],
            limit=normalized_limit,
            group_id=normalized_group_id,
            has_more=has_more,
        )

    def _extract_metadata(self, message: Message) -> _MessageMetadata:
        attachments = _parse_attachments(message.attachments)
        return _MessageMetadata(
            channel=_infer_channel(message.chat_jid, attachments),
            group_id=_infer_group_id(message.chat_jid, attachments),
            run_id=_as_non_empty_string(attachments.get("run_id")),
            external_message_id=_as_non_empty_string(attachments.get("external_message_id")),
        )


__all__ = [
    "AuditMessageListSnapshot",
    "AuditMessageSnapshot",
    "UsageAuditService",
    "UsageChannelBreakdownSnapshot",
    "UsageDailyBreakdownSnapshot",
    "UsageStatsSnapshot",
    "UsageSummarySnapshot",
]
