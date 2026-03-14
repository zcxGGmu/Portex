"""Message dispatch orchestration for M7.1."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, Protocol
from uuid import uuid4

from domain.schemas import UnifiedMessage
from infra.runtime.adapter import RunResult
from services.execution_coordinator import ExecutionRequest
from services.agent_trigger import RuntimeFactory, SessionIdFactory, run_agent_execution

DEFAULT_ASSISTANT_SENDER_ID = "portex"
ExecutionMode = Literal["openai", "host", "container"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class ResolvedMessageTarget:
    group_folder: str
    chat_jid: str


@dataclass(slots=True)
class DispatchResult:
    run_id: str
    status: str
    group_folder: str
    inbound_message_id: str
    outbound_message_id: str | None = None
    final_output: str | None = None
    error: str | None = None


class MessageDispatchError(RuntimeError):
    """Raised when a normalized message cannot be dispatched."""


class MessageRouterProtocol(Protocol):
    async def route_message(self, message: UnifiedMessage) -> None:
        ...


StoreMessageCallable = Callable[..., Awaitable[Any]]
TargetResolver = Callable[[UnifiedMessage], ResolvedMessageTarget | Awaitable[ResolvedMessageTarget]]
RuntimeTrigger = Callable[..., Awaitable[RunResult]]
RegisterTargetCallable = Callable[[UnifiedMessage, ResolvedMessageTarget], Awaitable[Any]]


class ExecutionSubmitter(Protocol):
    async def submit_execution(self, request: ExecutionRequest):
        ...

    async def wait_for_run(self, run_id: str):
        ...


class MessageDispatchService:
    """Dispatch normalized inbound messages through the current runtime path."""

    def __init__(
        self,
        *,
        target_resolver: TargetResolver,
        execution_coordinator: ExecutionSubmitter | None = None,
        runtime_trigger: RuntimeTrigger = run_agent_execution,
        runtime_factory: RuntimeFactory | None = None,
        session_id_factory: SessionIdFactory | None = None,
        register_target: RegisterTargetCallable | None = None,
        store_message: StoreMessageCallable,
        message_router: MessageRouterProtocol,
        assistant_sender_id: str = DEFAULT_ASSISTANT_SENDER_ID,
    ) -> None:
        self._target_resolver = target_resolver
        self._execution_coordinator = execution_coordinator
        self._runtime_trigger = runtime_trigger
        self._runtime_factory = runtime_factory or self._missing_runtime_factory
        self._session_id_factory = session_id_factory
        self._register_target = register_target
        self._store_message = store_message
        self._message_router = message_router
        self._assistant_sender_id = assistant_sender_id

    async def dispatch_inbound_message(
        self,
        message: UnifiedMessage,
        *,
        execution_mode: ExecutionMode | None = None,
    ) -> DispatchResult:
        if message.content.strip() == "":
            raise MessageDispatchError("message content cannot be empty")

        target = await self._resolve_target(message)
        if self._register_target is not None:
            await self._register_target(message, target)
        run_id = uuid4().hex
        slot_id = self._resolve_slot_id(message)

        inbound_record = await self._store_message(
            chat_jid=target.chat_jid,
            sender=message.sender_id,
            content=message.content,
            is_from_me=False,
            slot_id=slot_id,
            channel=message.channel,
            group_folder=target.group_folder,
            run_id=run_id,
            external_message_id=message.message_id,
        )

        if self._execution_coordinator is not None:
            handle = await self._execution_coordinator.submit_execution(
                self._build_execution_request(
                    target,
                    message,
                    run_id=run_id,
                    slot_id=slot_id,
                    execution_mode=execution_mode,
                )
            )
            run_id = handle.run_id
            run_result = await self._execution_coordinator.wait_for_run(run_id)
        else:
            run_result = await self._runtime_trigger(
                group_folder=target.group_folder,
                message=message.content,
                user_id=message.sender_id,
                runtime_factory=self._runtime_factory,
                session_id_factory=self._session_id_factory,
                request_id=run_id,
            )
        result_slot_id = getattr(run_result, "slot_id", slot_id)

        if run_result.status != "completed":
            return DispatchResult(
                run_id=run_result.run_id,
                status=run_result.status,
                group_folder=target.group_folder,
                inbound_message_id=inbound_record.id,
                final_output=run_result.final_output,
                error=run_result.error,
            )

        if run_result.final_output is None or run_result.final_output.strip() == "":
            raise MessageDispatchError("runtime completed without final output")

        outbound_message = UnifiedMessage(
            channel=message.channel,
            chat_jid=target.chat_jid,
            sender_id=self._assistant_sender_id,
            group_folder=target.group_folder,
            slot_id=result_slot_id,
            content=run_result.final_output,
            message_id=f"out-{run_result.run_id}",
            timestamp=_utcnow(),
        )
        await self._message_router.route_message(outbound_message)

        outbound_record = await self._store_message(
            chat_jid=target.chat_jid,
            sender=self._assistant_sender_id,
            content=run_result.final_output,
            is_from_me=True,
            slot_id=result_slot_id,
            channel=message.channel,
            group_folder=target.group_folder,
            run_id=run_result.run_id,
            external_message_id=outbound_message.message_id,
        )

        return DispatchResult(
            run_id=run_result.run_id,
            status=run_result.status,
            group_folder=target.group_folder,
            inbound_message_id=inbound_record.id,
            outbound_message_id=outbound_record.id,
            final_output=run_result.final_output,
        )

    async def _resolve_target(self, message: UnifiedMessage) -> ResolvedMessageTarget:
        if message.group_folder is not None:
            return ResolvedMessageTarget(
                group_folder=message.group_folder,
                chat_jid=message.chat_jid,
            )
        target = self._target_resolver(message)
        if inspect.isawaitable(target):
            return await target
        return target

    def _build_execution_request(
        self,
        target: ResolvedMessageTarget,
        message: UnifiedMessage,
        *,
        run_id: str,
        slot_id: str,
        execution_mode: ExecutionMode | None = None,
    ) -> ExecutionRequest:
        source = "web" if message.channel == "web" else "im"
        return ExecutionRequest(
            request_id=run_id,
            group_folder=target.group_folder,
            chat_jid=target.chat_jid,
            user_id=message.sender_id,
            prompt=message.content,
            source=source,
            slot_id=slot_id,
            requested_mode=execution_mode,
        )

    def _resolve_slot_id(self, message: UnifiedMessage) -> str:
        if message.channel == "web":
            return message.slot_id
        return "main"

    def _missing_runtime_factory(self, group_folder: str):
        _ = group_folder
        raise MessageDispatchError("runtime_factory is required for dispatch")


__all__ = [
    "DEFAULT_ASSISTANT_SENDER_ID",
    "DispatchResult",
    "MessageDispatchError",
    "MessageDispatchService",
    "ResolvedMessageTarget",
]
