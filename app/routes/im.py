"""IM ingestion routes for Feishu and Telegram."""

from __future__ import annotations

from hashlib import sha1
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from domain.schemas import UnifiedMessage
from infra.db.database import get_db
from infra.im.feishu import FeishuClient, FeishuClientError
from infra.im.telegram import TelegramClient, TelegramClientError
from services.execution_runtime import get_execution_coordinator
from services.message_dispatch import (
    MessageDispatchError,
    MessageDispatchService,
    ResolvedMessageTarget,
)
from services.message_router import MessageRouter
from services.message_service import store_message

router = APIRouter(prefix="/im", tags=["im"])


class IMDispatchResponse(BaseModel):
    status: str
    run_id: str | None = None


def _build_group_folder(chat_jid: str) -> str:
    return f"chat-{sha1(chat_jid.encode('utf-8')).hexdigest()[:12]}"


def _resolve_target(message: UnifiedMessage) -> ResolvedMessageTarget:
    return ResolvedMessageTarget(
        group_folder=_build_group_folder(message.chat_jid),
        chat_jid=message.chat_jid,
    )


async def _noop_web_handler(message: UnifiedMessage) -> None:
    _ = message


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{name} is not configured",
    )


def get_feishu_client() -> FeishuClient:
    return FeishuClient(
        app_id=_require_env("PORTEX_FEISHU_APP_ID"),
        app_secret=_require_env("PORTEX_FEISHU_APP_SECRET"),
        encrypt_key=os.getenv("PORTEX_FEISHU_ENCRYPT_KEY"),
        verification_token=os.getenv("PORTEX_FEISHU_VERIFICATION_TOKEN"),
    )


def get_telegram_client() -> TelegramClient:
    return TelegramClient(
        bot_token=_require_env("PORTEX_TELEGRAM_BOT_TOKEN"),
    )


async def _send_feishu_message(message: UnifiedMessage) -> None:
    client = get_feishu_client()
    await client.send_message(
        receive_id=message.chat_jid.split("feishu:", 1)[-1],
        content={"msg_type": "text", "content": {"text": message.content}},
        receive_id_type="chat_id",
    )


async def _send_telegram_message(message: UnifiedMessage) -> None:
    client = get_telegram_client()
    await client.send_text_message(
        chat_id=message.chat_jid.split("telegram:", 1)[-1],
        text=message.content,
    )


def get_message_dispatch_service(
    db: AsyncSession = Depends(get_db),
) -> MessageDispatchService:
    return MessageDispatchService(
        target_resolver=_resolve_target,
        execution_coordinator=get_execution_coordinator(),
        store_message=lambda **kwargs: store_message(db=db, **kwargs),
        message_router=MessageRouter(
            feishu_handler=_send_feishu_message,
            telegram_handler=_send_telegram_message,
            web_handler=_noop_web_handler,
        ),
    )


@router.post(
    "/feishu/webhook",
    response_model=IMDispatchResponse,
    response_model_exclude_none=True,
    summary="Handle Feishu webhook payload",
)
async def feishu_webhook(
    payload: dict[str, Any],
    client: FeishuClient = Depends(get_feishu_client),
    dispatch_service: MessageDispatchService = Depends(get_message_dispatch_service),
) -> IMDispatchResponse:
    try:
        event = client.handle_webhook_event(payload)
        if event is None:
            return IMDispatchResponse(status="ignored")
        result = await dispatch_service.dispatch_inbound_message(event.to_unified_message())
    except (FeishuClientError, MessageDispatchError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return IMDispatchResponse(status="dispatched", run_id=result.run_id)


@router.post(
    "/telegram/updates",
    response_model=IMDispatchResponse,
    response_model_exclude_none=True,
    summary="Handle Telegram update payload",
)
async def telegram_update(
    payload: dict[str, Any],
    client: TelegramClient = Depends(get_telegram_client),
    dispatch_service: MessageDispatchService = Depends(get_message_dispatch_service),
) -> IMDispatchResponse:
    try:
        event = client.handle_update(payload)
        if event is None or event.text is None or event.text.strip() == "":
            return IMDispatchResponse(status="ignored")
        result = await dispatch_service.dispatch_inbound_message(event.to_unified_message())
    except (TelegramClientError, MessageDispatchError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return IMDispatchResponse(status="dispatched", run_id=result.run_id)


__all__ = [
    "get_feishu_client",
    "get_message_dispatch_service",
    "get_telegram_client",
    "router",
]
