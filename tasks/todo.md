# Session Plan (2026-03-06) - Docs Sync

## Goal
- Sync the latest project state into `docs/progress.md` and `AGENTS.md`, then commit the documentation refresh.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, and recent session state
- [x] Update `docs/progress.md` with the latest restart-oriented status
- [x] Update `AGENTS.md` with the latest baseline and operator notes
- [x] Check doc consistency and diff hygiene
- [x] Commit changes with a detailed message

## Review
- `docs/progress.md` now reflects `M2` fully complete, current start point `M3.1.1`, and the latest provider connectivity verification notes.
- `AGENTS.md` now reflects the correct local HappyClaw reference path, the post-`M2` baseline, and the required `OPENAI_DEFAULT_MODEL=gpt-5.1` note for the tested compatible provider.
- Consistency check: `git diff --check` passed.
- Commit completed: `docs(handoff): refresh progress and agent guidance`.

# Session Plan (2026-03-09) - M5.2.1 Telegram Client

## Goal
- Complete `M5.2.1` by replacing the Telegram placeholder with a minimal async Bot API client skeleton.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and Telegram/Feishu IM slices
- [x] Write `M5.2.1` design and implementation plan docs
- [x] Add Telegram client tests first and verify they fail
- [x] Implement the minimal Telegram client skeleton for `getUpdates`
- [x] Run focused IM tests, full backend regression, and lint
- [x] Update `docs/progress.md` with `M5.2.1` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m5-2-1-telegram-client-design.md` and `docs/plans/2026-03-09-m5-2-1-telegram-client.md` to pin the milestone scope before implementation.
- Replaced the Telegram placeholder with an async `TelegramClient` that supports injected HTTP transport and minimal `get_updates()` polling.
- Added `tests/infra/im/test_telegram.py` covering success, request params, Telegram error payload mapping, and malformed response handling.
- Verification passed: `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`.
- Refreshed `.venv` with `.venv/bin/pip install -e ".[dev]"` before final regression because the environment was missing declared dependency `croniter`.
- Commit completed in this session: `feat(im): complete M5.2.1 telegram client skeleton`.

# Session Plan (2026-03-09) - M5.2.2 Telegram Message Handling

## Goal
- Complete `M5.2.2` by normalizing Telegram `message` updates into a minimal event object without expanding into routing, sending, or Markdown rendering.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `infra/im/telegram.py`, `tests/infra/im/test_telegram.py`, and `infra/im/feishu.py`
- [x] Write `M5.2.2` design and implementation plan docs
- [x] Add Telegram message-handling tests first and verify they fail
- [x] Implement the minimal `TelegramMessageEvent` and `handle_update()`
- [x] Run focused IM tests, full backend regression, and lint
- [x] Update `docs/progress.md` with `M5.2.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m5-2-2-telegram-message-handling-design.md` and `docs/plans/2026-03-09-m5-2-2-telegram-message-handling.md` before implementation to lock the milestone boundary.
- Extended `infra/im/telegram.py` with `TelegramMessageEvent` and a pure `handle_update()` parser that only normalizes top-level `message` updates.
- Expanded `tests/infra/im/test_telegram.py` to cover text normalization, unsupported update families returning `None`, non-text messages preserving IDs with `text=None`, and malformed message payload errors.
- Addressed review findings by rejecting boolean identifiers, wrapping transport / malformed payload failures in `TelegramClientError`, and making unsupported `send_message()` calls fail explicitly instead of silently returning `None`.
- Verification passed: `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`.
- Commit completed in this session: `feat(im): complete M5.2.2 telegram message handling`.

# Session Plan (2026-03-09) - M5.2.3 Telegram Markdown Conversion

## Goal
- Complete `M5.2.3` by adding a minimal Markdown-to-Telegram-HTML conversion helper for outbound text formatting.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `infra/im/telegram.py`, `tests/infra/im/test_telegram.py`, and the latest Telegram design notes
- [x] Write `M5.2.3` design and implementation plan docs
- [x] Add Telegram markdown conversion tests first and verify they fail
- [x] Implement the minimal `markdown_to_html()` helper
- [x] Run focused IM tests, full backend regression, and lint
- [x] Update `docs/progress.md` with `M5.2.3` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m5-2-3-telegram-markdown-conversion-design.md` and `docs/plans/2026-03-09-m5-2-3-telegram-markdown-conversion.md` to fix the Markdown conversion boundary before implementation.
- Extended `infra/im/telegram.py` with a pure `markdown_to_html()` helper that escapes raw HTML, protects code blocks / inline code / unsupported links with placeholders, and only converts the approved Telegram-safe subset.
- Expanded `tests/infra/im/test_telegram.py` to cover HTML escaping, inline formatting, fenced code blocks, incomplete markers, unsupported links, nested emphasis staying plain text, and code-span protection.
- Addressed review findings by making placeholder tokens collision-resistant and by blocking nested / cross-overlapping emphasis from generating invalid Telegram HTML.
- Verification passed: `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`.
- Commit completed in this session: `feat(im): complete M5.2.3 telegram markdown conversion`.

# Session Plan (2026-03-09) - M5.3.1 Unified Message

## Goal
- Complete `M5.3.1` by defining a minimal routeable `UnifiedMessage` DTO and adding Feishu/Telegram conversion helpers without rewiring message routing yet.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `domain/schemas.py`, `infra/im/feishu.py`, `infra/im/telegram.py`, and current message service slices
- [x] Write `M5.3.1` design and implementation plan docs
- [x] Add schema and channel-conversion tests first and verify they fail
- [x] Implement `UnifiedMessage` plus Feishu/Telegram `to_unified_message()` helpers
- [x] Run focused tests, full backend regression, and lint
- [x] Update `docs/progress.md` with `M5.3.1` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m5-3-1-unified-message-design.md` and `docs/plans/2026-03-09-m5-3-1-unified-message.md` to pin the DTO boundary before implementation.
- Added `UnifiedMessage` to `domain/schemas.py` with the minimal routeable fields `channel/chat_jid/sender_id/group_folder/content/message_id/timestamp`.
- Extended `FeishuMessageEvent` and `TelegramMessageEvent` with `timestamp` plus `to_unified_message()` so the current channel contracts remain intact and only gain a thin adapter layer.
- Added `tests/domain/test_schemas.py` and expanded Feishu/Telegram tests to cover text/non-text conversion and timestamp extraction.
- Verification passed: `.venv/bin/pytest -o addopts='' tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`.
- Commit completed in this session: `feat(messages): complete M5.3.1 unified message schema`.

# Session Plan (2026-03-09) - M5.3.2 Message Routing

## Goal
- Complete `M5.3.2` by adding a minimal routing layer that dispatches `UnifiedMessage` instances to injected Feishu, Telegram, or Web handlers.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `domain/schemas.py`, and current IM/message service slices
- [x] Write `M5.3.2` design and implementation plan docs
- [x] Add message-router tests first and verify they fail
- [x] Implement `MessageRouter` plus `MessageRouterError`
- [x] Run focused tests, full backend regression, and lint
- [x] Update `docs/progress.md` with `M5.3.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `services/message_router.py` with minimal injected-channel routing and `MessageRouterError`, without wiring real send paths, API routes, or WebSocket flows.
- Added `tests/services/test_message_router.py` covering Feishu/Telegram/Web dispatch, unknown-channel rejection, and downstream handler exception propagation.
- Verification ran: `.venv/bin/pytest -o addopts='' tests/services/test_message_router.py -q`, `.venv/bin/pytest -o addopts='' tests/services/test_message_router.py tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, and `git diff --check`.
- Code commit completed: `c91e7ee` `feat(messages): add minimal message router`.
