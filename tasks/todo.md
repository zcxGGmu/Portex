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

# Session Plan (2026-03-09) - M5.4 Acceptance

## Goal
- Complete `M5.4` by verifying `M5.1` through `M5.3` against the acceptance checklist and updating the restart handoff to begin `M6.1.1`.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current IM/message slices, and prior acceptance patterns
- [x] Write `M5.4` design and implementation plan docs
- [x] Run focused `M5` acceptance verification
- [x] Run full backend regression, `ruff`, and frontend lint/build
- [x] Update `docs/progress.md` with `M5.4` evidence, conclusion, and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m5-4-acceptance-design.md` and `docs/plans/2026-03-09-m5-4-acceptance.md` to pin the acceptance scope before execution.
- Reused the existing Feishu, Telegram, `UnifiedMessage`, and `MessageRouter` test suite as the `M5` acceptance matrix, without extending the current IM runtime boundary.
- Verification ran: `.venv/bin/pytest -o addopts='' tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py tests/services/test_message_router.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, and `cd web && npm run build`.
- Acceptance commit message for this milestone: `docs(acceptance): complete M5.4 milestone verification`.

# Session Plan (2026-03-09) - M6.1.1 Unit Tests

## Goal
- Complete `M6.1.1` by aligning `tests/unit/` with the TODO layout and filling it with focused pure-logic unit tests.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current test layout, and pure-logic candidate modules
- [x] Write `M6.1.1` design and implementation plan docs
- [x] Add `tests/unit/test_auth.py`, `tests/unit/test_models.py`, and `tests/unit/test_services.py`
- [x] Remove the legacy `tests/unit/test_auth_unit.py` filename
- [x] Fix any focused/full-suite collection issues introduced by the new layout
- [x] Run `tests/unit/ -v`, full backend regression, and `ruff`
- [x] Update `docs/progress.md` with `M6.1.1` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m6-1-1-unit-tests-design.md` and `docs/plans/2026-03-09-m6-1-1-unit-tests.md` to pin the unit-test scope before implementation.
- Replaced `tests/unit/test_auth_unit.py` with `tests/unit/test_auth.py`, and added new `tests/unit/test_models.py` plus `tests/unit/test_services.py` so `tests/unit/` now matches the TODO layout.
- Added `tests/unit/__init__.py` after full regression exposed a pytest import-name collision between `tests/unit/test_models.py` and `tests/domain/models/test_models.py`.
- Verification ran: `.venv/bin/pytest tests/unit/test_auth.py -v`, `.venv/bin/pytest tests/unit/ -v`, `.venv/bin/pytest -o addopts='' -q`, and `.venv/bin/ruff check .`.
- Commit message for this milestone: `test(unit): complete M6.1.1 unit test suite`.

# Session Plan (2026-03-09) - M6.1.2 Integration Tests

## Goal
- Complete `M6.1.2` by aligning `tests/integration/` with the TODO layout and adding the smallest meaningful API and WebSocket integration tests.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current app wiring, and existing route tests
- [x] Write `M6.1.2` design and implementation plan docs
- [x] Add `tests/integration/test_api.py`
- [x] Add `tests/integration/test_websocket.py`
- [x] Run focused integration verification
- [x] Run spec review and code-quality review on the new integration slice
- [x] Run full backend regression and `ruff`
- [x] Update `docs/progress.md` with `M6.1.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m6-1-2-integration-tests-design.md` and `docs/plans/2026-03-09-m6-1-2-integration-tests.md` to pin the integration-test scope before implementation.
- Added `tests/integration/test_api.py` for `GET /health` plus `register -> login -> /users/me` through the real FastAPI app wiring.
- Added `tests/integration/test_websocket.py` for the real `/ws/{group_folder}` route, covering a deterministic `run.started` event and same-socket cancel -> `run.failed` under fake runtime control.
- Verification ran: `.venv/bin/pytest -o addopts='' tests/integration/test_api.py tests/integration/test_websocket.py -q`, `.venv/bin/pytest -o addopts='' -q`, and `.venv/bin/ruff check .`.
- Review agents reported `spec-compliant` and `no findings`; residual risk remains intentionally narrow API coverage plus fake-runtime-backed WebSocket integration.
- Commit message for this milestone: `test(integration): complete M6.1.2 integration test suite`.

# Session Plan (2026-03-09) - M6.1.3 CI/CD

## Goal
- Complete `M6.1.3` by adding the minimal GitHub Actions workflow needed to run the current backend and frontend verification commands on push and pull_request.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current verification commands, and root/web dependency config
- [x] Write `M6.1.3` design and implementation plan docs
- [x] Add `.github/workflows/test.yml`
- [x] Add `pytest-cov` to `pyproject.toml` dev dependencies
- [x] Run spec review and code-quality review on the CI slice
- [x] Install updated dev dependencies locally
- [x] Run workflow-equivalent backend and frontend commands locally
- [x] Update `docs/progress.md` with `M6.1.3` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m6-1-3-ci-cd-design.md` and `docs/plans/2026-03-09-m6-1-3-ci-cd.md` to pin the CI scope before implementation.
- Added `.github/workflows/test.yml` with two minimal jobs: backend (`pytest tests/ -v --cov`, `ruff check .`) and frontend (`npm ci`, `npm run lint`, `npm run build`).
- Added `pytest-cov>=6.0.0` to `pyproject.toml` so the TODO-specified backend CI command is valid.
- Verification ran: `.venv/bin/python -m pip install -e ".[dev]"`, `.venv/bin/pytest tests/ -v --cov`, `.venv/bin/ruff check .`, `cd web && npm ci`, `cd web && npm run lint`, and `cd web && npm run build`.
- Review agents reported `spec-compliant` and `no findings`; remaining risk is only that the workflow has been validated locally, not executed on a remote GitHub Actions runner in this environment.
- Commit message for this milestone: `build(ci): complete M6.1.3 workflow setup`.

# Session Plan (2026-03-10) - M6.2.1 README

## Goal
- Complete `M6.2.1` by replacing the placeholder root README with a practical project entrypoint for readers, operators, and contributors.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current repository commands, and the existing README
- [x] Write `M6.2.1` design and implementation plan docs
- [x] Rewrite `README.md` using the approved layered structure
- [x] Run spec review and code-quality review on the README slice
- [x] Run backend regression, `ruff`, and frontend lint/build
- [x] Update `docs/progress.md` with `M6.2.1` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-10-m6-2-1-readme-design.md` and `docs/plans/2026-03-10-m6-2-1-readme.md` to pin the README scope before implementation.
- Replaced the placeholder `README.md` with a layered project entrypoint covering positioning, current status, features, quick start, development commands, project structure, architecture, current boundaries, document links, and upstream reference.
- Review agents reported `spec-compliant` and `no findings`; wording stays conservative around IM maturity, Docker verification, and GitHub Actions remote execution evidence.
- Verification ran: `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, and `cd web && npm run build`.
- Commit message for this milestone: `docs(readme): complete M6.2.1 project readme`.

# Session Plan (2026-03-10) - M6.2.2 API Docs

## Goal
- Complete `M6.2.2` by making the current FastAPI-generated `/docs` useful for the existing HTTP API surface without creating a separate API portal.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current FastAPI routes, and current schema/test coverage
- [x] Write `M6.2.2` design and implementation plan docs
- [x] Add OpenAPI-focused tests first and verify they fail
- [x] Enrich app/route/schema OpenAPI metadata for the current HTTP API
- [x] Run spec review and code-quality review on the API docs slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.2.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-10-m6-2-2-api-docs-design.md` and `docs/plans/2026-03-10-m6-2-2-api-docs.md` to pin the API-docs scope before implementation.
- Added `app/openapi.py` plus app/route/schema metadata so `/docs` now exposes a real HTTP API description, stable tag groupings, documented error responses, and clearer DTO field semantics.
- Added `/openapi.json` contract coverage to `tests/app/routes/test_api_routes.py`, covering global description, tag descriptions, route error responses, placeholder message semantics, key schema descriptions, and the concrete group-member delete response model.
- Multi-agent exploration was used for scope discovery; two review-agent follow-ups timed out under interrupt, so the final spec/code-quality pass was completed with manual diff review plus fresh verification evidence.
- Verification ran: `.venv/bin/pytest tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Commit message for this milestone: `docs(api): complete M6.2.2 api docs`.

# Session Plan (2026-03-10) - M6.2.3 Deployment Docs

## Goal
- Complete `M6.2.3` by adding a deployment guide for the currently verified local process setup, while clearly marking Docker Compose as an unverified draft.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `README.md`, and the current runtime/config entrypoints
- [x] Write `M6.2.3` design and implementation plan docs
- [x] Add a failing test for the invite `expires_at` doc-accuracy fix
- [x] Add a failing test for direct `scripts/init_db.py` execution
- [x] Correct the invite `expires_at` API-doc wording to match current behavior
- [x] Fix `scripts/init_db.py` so the documented direct command works
- [x] Write the deployment guide and update README links/status wording as needed
- [x] Run multi-agent spec/code-quality review on the deployment-doc slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.2.3` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-10-m6-2-3-deployment-docs-design.md` and `docs/plans/2026-03-10-m6-2-3-deployment-docs.md` to pin the deployment-doc scope before implementation, then re-planned once deployment smoke verification exposed that `scripts/init_db.py` was not directly executable as documented.
- Added `docs/deployment.md` covering prerequisites, runtime environment variables, verified local process deployment steps, smoke verification, data/persistence notes, and an explicitly unverified Docker Compose draft.
- Corrected the invite `expires_at` API-doc wording in `domain/schemas.py` and locked it with an OpenAPI test in `tests/app/routes/test_api_routes.py`.
- Fixed `scripts/init_db.py` so the documented direct command works from the repository root and added a subprocess-level regression test in `tests/scripts/test_init_db.py`.
- Multi-agent scope/spec review returned `spec-compliant`; the code-quality reviewer timed out under interrupt, so the final quality pass was completed with manual diff review plus fresh verification evidence.
- Verification ran: `.venv/bin/pytest tests/app/routes/test_api_routes.py tests/scripts/test_init_db.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, `.venv/bin/python scripts/init_db.py`, backend `/health` smoke against live `uvicorn`, frontend `/` smoke against `npm run preview`, and `git diff --check`.
- Commit message for this milestone: `docs(deploy): complete M6.2.3 deployment guide`.

# Session Plan (2026-03-10) - M6.3.1 Database Indexes

## Goal
- Complete `M6.3.1` by adding the three TODO-defined database indexes and verifying that fresh SQLite initialization creates them.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current model definitions, and DB init tests
- [x] Write `M6.3.1` design and implementation plan docs
- [x] Add failing tests for model metadata indexes and SQLite-created indexes
- [x] Implement the minimal model-level index declarations
- [x] Run multi-agent spec/code-quality review on the index slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.3.1` evidence and next step
- [ ] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-10-m6-3-1-db-indexes-design.md` and `docs/plans/2026-03-10-m6-3-1-db-indexes.md` to pin the index scope before implementation.
- Added the three TODO-defined indexes at the model layer: `idx_messages_chat_jid`, `idx_messages_timestamp`, and `idx_tasks_next_run`.
- Extended `tests/domain/models/test_models.py` to assert the new SQLAlchemy metadata indexes and `tests/scripts/test_init_db.py` to verify fresh SQLite initialization creates the named indexes on the expected columns.
- Multi-agent spec review returned `spec-compliant`; a later code-quality review correctly identified that existing SQLite tables were not backfilling the new indexes, so `scripts/init_db.py` was updated and a regression test was added for the existing-table upgrade path.
- Verification ran: `.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, and `cd web && npm run build`.
- Commit message for this milestone: `perf(db): complete M6.3.1 indexes`.

# Session Plan (2026-03-10) - M6.3.2 Connection Pool

## Goal
- Complete `M6.3.2` by making the async SQLAlchemy engine use an explicit, valid connection-pool configuration for the current SQLite-first repository setup.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current DB engine/session files, and the latest DB milestone notes
- [x] Write `M6.3.2` design and implementation plan docs
- [x] Add failing tests for the default file-backed SQLite pool contract and in-memory SQLite behavior
- [x] Implement the minimal engine-construction helper and reuse it for override engines
- [x] Run multi-agent spec/code-quality review on the DB pool slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.3.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-10-m6-3-2-connection-pool-design.md` and `docs/plans/2026-03-10-m6-3-2-connection-pool.md` to pin the milestone boundary before implementation.
- Extended `tests/infra/db/test_database.py` with a red-green cycle for the default file-backed SQLite pool contract plus four in-memory SQLite URL variants; the first green pass exposed a review-found gap around `sqlite+aiosqlite://` and `file:...mode=memory`, which was then locked with a second red-green cycle.
- Added `create_database_engine()` in `infra/db/database.py` so the repository now uses explicit `20/10` queue-pool sizing for file-backed SQLite while keeping in-memory SQLite variants on `StaticPool`; `scripts/init_db.py` now reuses the same helper for override engines.
- Multi-agent review was used for scope discovery and code review. The first review round found the missing in-memory URL variants and checklist/doc alignment gap; after that fix, follow-up quick reviewers timed out, so the final pass used manual diff review plus fresh verification evidence.
- Verification ran: `.venv/bin/pytest tests/infra/db/test_database.py tests/scripts/test_init_db.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Commit message for this milestone: `perf(db): complete M6.3.2 connection pool`.

# Session Plan (2026-03-10) - M6.3.3 User Memory Cache

## Goal
- Complete `M6.3.3` by adding the smallest justified cache layer: a process-local read cache for user-global `AGENTS.md` memory.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current memory-service code, and current cache-related repository boundaries
- [x] Brainstorm scope and alternatives for `M6.3.3`
- [x] Write `M6.3.3` design and implementation plan docs
- [x] Add failing tests for user-memory cache miss, hit, and write-through behavior
- [x] Implement the minimal `MemoryService` cache
- [x] Run multi-agent spec/code-quality review on the memory-cache slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.3.3` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-10-m6-3-3-user-memory-cache-design.md` and `docs/plans/2026-03-10-m6-3-3-user-memory-cache.md` to pin the milestone boundary before implementation.
- Extended `tests/services/test_memory_service.py` with a red-green cycle for three cache behaviors: missing-file cache miss, existing-file cache hit, and `update_user_memory()` write-through refresh. These tests first failed for the intended reasons before the implementation was added.
- Updated `services/memory.py` with a private `_user_memory_cache` so `get_user_memory()` now acts as a read-through cache and `update_user_memory()` refreshes the cache after a successful file write; `append_daily_memory()` and `search_memory()` remain unchanged.
- Multi-agent implementation/review was used for Task 1 red tests and Task 2 spec review. Several quality-review agents timed out, so the final quality pass was completed with manual diff review plus fresh verification evidence.
- Verification ran: `.venv/bin/pytest tests/services/test_memory_service.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, and `cd web && npm run build`.
- Commit message for this milestone: `perf(memory): complete M6.3.3 user memory cache`.

# Session Plan (2026-03-11) - M6.4.1 Security Scan

## Goal
- Complete `M6.4.1` by adding the smallest repository-local security scanning workflow that is executable in the current environment and wired into the existing verification flow.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, and `docs/TODO.md`
- [x] Brainstorm the `M6.4.1` scope and confirm the minimal approach with the user
- [x] Write `M6.4.1` design and implementation plan docs
- [x] Add failing tests for the security-scan entrypoint
- [x] Implement the minimal scan script and current finding cleanup
- [x] Run multi-agent spec/code-quality review on the security-scan slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.4.1` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-11-m6-4-1-security-scanning-design.md` and `docs/plans/2026-03-11-m6-4-1-security-scanning.md` to pin the milestone boundary before implementation.
- Added `tests/scripts/test_security_scan.py` and `scripts/security_scan.py` so the repository now has a local Python entrypoint for Ruff `S`-rule scanning of runtime-oriented code directories.
- Updated `.github/workflows/test.yml`, `README.md`, and `AGENTS.md` so backend CI and local operator docs all point at the same `scripts/security_scan.py` command.
- Replaced two `assert`-based schema guards in `domain/schemas.py` with explicit `ValueError` checks, and added a narrow inline suppression for the `EventType.TOKEN_DELTA` false positive in `portex/contracts/events.py`.
- Multi-agent implementation and review were used for the scan-entrypoint and runtime-finding slices. Two broader review agents timed out under interrupt; a follow-up quick review reported no blocking findings, and the final quality pass was completed with manual diff review plus fresh verification evidence.
- Verification ran: `.venv/bin/pytest tests/scripts/test_security_scan.py tests/domain/test_schemas.py -v`, `.venv/bin/python scripts/security_scan.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/python -m pip install -e ".[dev]"`, `.venv/bin/pytest tests/ -v --cov`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Commit message for this milestone: `build(security): complete M6.4.1 security scan`.

# Session Plan (2026-03-11) - M6.4.2 Dependency Audit

## Goal
- Complete `M6.4.2` by adding the smallest repository-local Python dependency-audit workflow using `pip-audit`, while preserving the `M6.4.1` static security scan chain.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and the latest `M6.4.1` docs
- [x] Brainstorm the `M6.4.2` scope and confirm the repo-local `pip-audit` approach with the user
- [x] Write `M6.4.2` design and implementation plan docs
- [x] Add failing tests for the dependency-audit entrypoint
- [x] Implement the minimal audit script and dev dependency wiring
- [x] Run multi-agent spec/code-quality review on the dependency-audit slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.4.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-11-m6-4-2-dependency-audit-design.md` and `docs/plans/2026-03-11-m6-4-2-dependency-audit.md` to pin the milestone boundary before implementation.
- Added `tests/scripts/test_dependency_audit.py` and `scripts/dependency_audit.py` so the repository now has a local Python entrypoint for `pip-audit` against the current project dependency set.
- Updated `pyproject.toml` to include `pip-audit>=2.9.0`, refreshed `.venv`, and wired the new command into `.github/workflows/test.yml`, `README.md`, and `AGENTS.md`.
- Fresh `pip-audit` initially reported `ecdsa 0.19.1 / CVE-2024-23342` with no fix version. `pip index versions ecdsa` still showed `0.19.1` as latest, so the final script now carries one explicit ignore constant instead of hiding the exception in CI-only config.
- Multi-agent review returned `spec-compliant` and `no findings`; the only recorded residual risk is the explicit `ecdsa/CVE-2024-23342` ignore, which is now documented for future revisit.
- Verification ran: `.venv/bin/pytest tests/scripts/test_dependency_audit.py -v`, `.venv/bin/python scripts/dependency_audit.py`, `.venv/bin/python scripts/security_scan.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/pytest tests/ -v --cov`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Commit message for this milestone: `build(security): complete M6.4.2 dependency audit`.

# Session Plan (2026-03-11) - M6.4.3 Security Headers

## Goal
- Complete `M6.4.3` by adding the smallest useful HTTP security-header middleware to the current FastAPI app without expanding into CSP or broader browser policy work.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and the latest security milestone docs
- [x] Brainstorm the `M6.4.3` scope and confirm the minimal-header approach with the user
- [x] Write `M6.4.3` design and implementation plan docs
- [x] Add failing tests for the header contract
- [x] Implement the minimal security-header middleware and app wiring
- [x] Run multi-agent spec/code-quality review on the security-header slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.4.3` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-11-m6-4-3-security-headers-design.md` and `docs/plans/2026-03-11-m6-4-3-security-headers.md` to pin the milestone boundary before implementation.
- Extended `tests/app/routes/test_api_routes.py` and `tests/integration/test_api.py` with a red-green cycle that locked the new security-header contract on `/health` plus CORS preflight responses.
- Added `app/middleware/security.py` with a lightweight ASGI `SecurityHeadersMiddleware`, exported it via `app/middleware/__init__.py`, and registered it in `app/main.py` outside the current CORS layer so preflight responses inherit the same headers.
- Spec review returned `spec-compliant`; the broader code-review subagent timed out under interrupt, so the final quality pass used manual diff review plus fresh verification evidence.
- Verification ran: `.venv/bin/pytest tests/app/routes/test_api_routes.py tests/integration/test_api.py -q`, `.venv/bin/python scripts/security_scan.py`, `.venv/bin/python scripts/dependency_audit.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/pytest tests/ -v --cov`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Commit message for this milestone: `feat(security): complete M6.4.3 security headers`.

# Session Plan (2026-03-11) - M6.5.1 Version Planning

## Goal
- Complete `M6.5.1` by documenting the first release-version strategy without creating tags, changing package/runtime version strings, or building release artifacts.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `README.md`, and current version metadata
- [x] Brainstorm the `M6.5.1` scope and confirm the planning-only approach with the user
- [x] Write `M6.5.1` design and implementation plan docs
- [x] Update repo-facing docs with the chosen version strategy
- [x] Run review plus repository verification
- [x] Update `docs/progress.md` with `M6.5.1` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-11-m6-5-1-version-planning-design.md` and `docs/plans/2026-03-11-m6-5-1-version-planning.md` to pin the milestone boundary before implementation.
- Kept `pyproject.toml` and runtime version strings unchanged at `0.1.0`, and documented the planning decision that the first formal release tag target is `v1.0.0`.
- Updated `README.md`, `AGENTS.md`, and `docs/progress.md` so restart-oriented docs now distinguish planned release tag `v1.0.0` from current package/runtime version `0.1.0`, and move the next starting point to `M6.5.2`.
- Verification ran: `rg -n "M6\\.5\\.1|M6\\.5\\.2|v1\\.0\\.0|0\\.1\\.0" README.md AGENTS.md docs/progress.md`, `git diff --check`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, and `cd web && npm run build`.
- Commit message for this milestone: `docs(release): complete M6.5.1 version planning`.

# Session Plan (2026-03-11) - M6.5.2 Release Tag

## Goal
- Complete `M6.5.2` by updating milestone handoff docs, creating the annotated release tag `v1.0.0`, and moving the next starting point to `M6.5.3` without starting artifact-building work.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, release-planning docs, and current git/tag state
- [x] Write `M6.5.2` design and implementation plan docs
- [x] Update repo-facing docs and session tracking for post-`M6.5.2` state
- [x] Run repository verification and prepare the `M6.5.2` completion commit
- [x] Create and verify local annotated tag `v1.0.0`
- [x] Push and verify remote tag `v1.0.0`
- [x] Update `docs/progress.md` with `M6.5.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-11-m6-5-2-release-tag-design.md` and `docs/plans/2026-03-11-m6-5-2-release-tag.md` to pin the milestone boundary before executing the tag.
- Updated `README.md` and `AGENTS.md` so repo-facing restart guidance now advances from `M6.5.2` to `M6.5.3` while keeping the intentional `v1.0.0` tag versus `0.1.0` runtime/package split visible.
- Verification ran: `git diff --check`, `git rev-parse --verify refs/tags/v1.0.0` (before creation), `git ls-remote --tags origin v1.0.0 v1.0.0^{}` (before and after push), `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git show --stat --oneline v1.0.0`.
- Local annotated tag `v1.0.0` currently points to `dba45f3` (`docs(release): complete M6.5.2 release tag`), and `origin` now exposes `refs/tags/v1.0.0` plus `refs/tags/v1.0.0^{}` for the same commit.
- Note: the release tag was pushed first so `v1.0.0` stays anchored on `dba45f3`; any later `main` commits in this slice are handoff-only follow-ups.

# Session Plan (2026-03-11) - M6.5.3 Release Artifacts

## Goal
- Advance `M6.5.3` by adding a repository-root release-image build path, preserving the frontend `web/dist/` artifact flow, and recording any remaining Docker-runtime blocker explicitly.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, release docs, and current git/runtime environment
- [x] Brainstorm the `M6.5.3` scope and choose the minimal root-image approach under the current no-Docker environment
- [x] Write `M6.5.3` design and implementation plan docs
- [x] Add failing tests for the root Docker build path and build wrapper
- [x] Implement the root Docker artifact path (`Dockerfile`, `.dockerignore`, `scripts/build_docker.py`, `Makefile`)
- [x] Update release/deployment docs for the new artifact boundary
- [x] Run static verification, full regression, and frontend artifact checks
- [x] Attempt real Docker verification and record blocker or success
- [x] Update `docs/progress.md` with `M6.5.3` evidence and next step
- [x] Commit the phase result with a detailed message

## Review
- Added `docs/plans/2026-03-11-m6-5-3-release-artifacts-design.md` and `docs/plans/2026-03-11-m6-5-3-release-artifacts.md` to pin the milestone boundary before implementation.
- Added `tests/scripts/test_build_docker.py` and extended `tests/container/agent_runner/test_container_files.py` so the root release-image path, `.dockerignore`, and wrapper CLI contract are all statically locked.
- Added a root `Dockerfile` and `.dockerignore`, replaced the placeholder `scripts/build_docker.py` with a real wrapper, and updated `Makefile` to expose both `build-release-image` and runner-specific image builds.
- Updated `README.md`, `AGENTS.md`, and `docs/deployment.md` so operator docs now point at the new release-image build entrypoint and explicitly state that real Docker verification still depends on local Docker availability.
- Verification ran: `git diff --check`, `.venv/bin/pytest tests/scripts/test_build_docker.py tests/container/agent_runner/test_container_files.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, `test -f web/dist/index.html`, `docker version --format '{{.Client.Version}}|{{.Server.Version}}'`, `docker build -t portex:v1.0.0 .`, and `docker image inspect portex:v1.0.0 --format '{{.Id}}'`.
- Review gates: spec review returned `no blocking spec findings`; the quality-review subagent timed out, so the final quality pass used manual diff review plus focused/full verification evidence, with no blocking issues found.
- Current blocker: the repository-root image build path is implemented, but this environment still lacks the `docker` command, so `docker build -t portex:v1.0.0 .` and image inspection remain unverified and `M6.5.3` cannot yet be honestly marked complete.

# Session Plan (2026-03-11) - README Refresh

## Goal
- Refresh the public README so it explains the Portex name and product positioning, replaces internal milestone references with a public support/todo view, adds architecture/workflow diagrams, and ships a Chinese counterpart README.

## Checklist
- [x] Re-read `README.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and the runtime/message slices that determine the current public architecture story
- [x] Brainstorm the README refresh direction and get approval on the layered bilingual approach
- [x] Write the README refresh design doc
- [x] Write the README refresh implementation plan doc
- [x] Rewrite `README.md` with the naming story, public capability matrix, public todo list, and Mermaid diagrams
- [x] Add `README.zh-CN.md` as a near-parity Chinese counterpart with language switch links
- [x] Run review plus repository verification for the documentation slice
- [x] Update `docs/progress.md` and this session review
- [x] Commit the documentation refresh with a detailed message

## Review
- Added `docs/plans/2026-03-11-readme-refresh-design.md` and `docs/plans/2026-03-11-readme-refresh.md` to lock the public README refresh scope before editing.
- Rewrote `README.md` around `Portex = Portal + Codex`, public-facing support and todo lists, and three Mermaid diagrams that reflect the current web runtime and IM normalization boundary.
- Added `README.zh-CN.md` as a near-parity Chinese counterpart with language switch links and the same overall information architecture.
- Review outcome: one doc-quality reviewer found no blocking issues; one technical reviewer caught two Mermaid overstatements, and both were corrected before final verification.
- Fresh repository verification exposed a pre-existing duplicate test definition in `tests/scripts/test_build_docker.py`; removed the stale duplicate so both `pytest` and `ruff` returned to green.
- Verification ran: `rg -n "M[0-9]" README.md README.zh-CN.md`, `git diff --check`, `.venv/bin/pytest tests/scripts/test_build_docker.py -q`, `.venv/bin/ruff check tests/scripts/test_build_docker.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, and `cd web && npm run build`.
- Commit message: `docs(readme): refresh public project entrypoint`

# Session Plan (2026-03-11) - README Project Icon

## Goal
- Add a technical-styled cartoon crab icon for Portex and surface it at the top of the English and Chinese README files.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, current README files, and recent repo state
- [x] Brainstorm the icon direction with the user and get approval on the `Portal Crab` concept
- [x] Write the project-icon design and implementation plan docs
- [x] Add a focused failing test for the shared README/logo contract
- [x] Create the shared SVG logo asset
- [x] Integrate the icon into `README.md` and `README.zh-CN.md`
- [x] Run focused verification and diff hygiene checks
- [x] Update `docs/progress.md` with the README logo follow-up
- [x] Commit the documentation/logo update with a detailed message

## Review
- Added `docs/plans/2026-03-11-portex-project-icon-design.md` and `docs/plans/2026-03-11-portex-project-icon.md` to pin the README icon scope before implementation.
- Added the shared logo asset `assets/portex-crab-logo.svg` in the approved `Portal Crab` direction and surfaced it near the top of both README entrypoints.
- Updated the README repository maps so the new root `assets/` directory is explicitly documented in both languages.
- Extended `tests/container/agent_runner/test_container_files.py` with README/logo static contract checks after an initial test-first spike showed this repo-root file-contract suite was the better long-term home than `tests/scripts/`.
- Verification ran: `rg -n "assets/portex-crab-logo\\.svg|Portex project logo" README.md README.zh-CN.md`, `.venv/bin/pytest tests/container/agent_runner/test_container_files.py -v`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check tests/container/agent_runner/test_container_files.py`, `.venv/bin/ruff check .`, and `git diff --check`.
- Review note: two independent code-review explorer subagents timed out on the working tree; the final quality gate used manual diff review plus the fresh focused/full verification evidence above, with no blocking issues found.
- Commit message: `docs(readme): add Portex project icon`

# Session Plan (2026-03-11) - Portex vs HappyClaw Gap Audit

## Goal
- Compare the current Portex implementation against `/home/zcxggmu/workspace/hello-projs/agents/happyclaw` and turn the remaining product gap into a restart-friendly backlog.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `README.md`, and key Portex runtime / route / frontend files
- [x] Re-read the HappyClaw README plus representative backend/frontend files for routes, chat UX, config, IM, tasks, memory, skills, MCP, and monitoring
- [x] Identify what Portex already matches versus what is still intentionally minimal
- [x] Group the remaining differences into priority buckets that can guide the next implementation phases
- [x] Record the comparison result in `tasks/todo.md`

## Review
- Portex already aligns on the broad foundation: Python backend + React frontend, Web chat, WebSocket run/stream/cancel flow, auth/invites/RBAC, task CRUD + logs, file-backed memory primitives, Feishu/Telegram client foundations, unified message DTO + minimal router, CI/tests/security scan/dependency audit, and the root release-image build entrypoint.
- Portex is still materially behind HappyClaw on the primary product chain: end-to-end IM delivery is not wired, `/messages` is still a queued placeholder, the current Web happy path still runs directly through `OpenAIAgentsRuntime`, and the queue / host-mode / container-mode execution plane is not yet integrated into a full per-user workspace runtime.
- HappyClaw also has a much broader admin/product surface that Portex does not yet expose: file-management APIs and UI, Web terminal, monitoring/status APIs, usage stats, richer settings/config flows, memory management APIs/UI, skill management, MCP server management, IM binding flows, and setup wizard pages.
- HappyClaw currently supports an additional QQ channel plus a larger set of IM/runtime behaviors (pairing, slash commands, long-message handling, richer attachments, reaction/card-style responses). Portex currently only has Feishu + Telegram foundations, and even Telegram outbound send is still intentionally unimplemented.
- Frontend completeness is one of the largest visible gaps: Portex currently has `chat/login/register/settings`, while HappyClaw has setup pages, monitor/usage/memory/skills/MCP/users pages, a much richer chat view with files/skills/members/terminal panels, and explicit mobile/PWA optimizations.
- Portex is stronger than HappyClaw in engineering hygiene: explicit milestone docs, restart-oriented handoff discipline, OpenAPI contract coverage, a large Python test suite, repo-local security scan/dependency audit, and verified CI-equivalent commands. The gap is mostly product/runtime breadth, not basic project rigor.

### Recommended Order

- First finish `M6.5.3` on a machine with Docker so the current milestone is honestly closed.
- Then prioritize the product gaps in this order: end-to-end IM chain, real execution plane, workspace/group model, operator surfaces, richer frontend.

### Proposed Milestones

#### `M7` HappyClaw Parity Alignment

**Goal**
- Turn the current Portex scaffold into a product that closes the major runtime and operator-surface gaps versus HappyClaw, while preserving Portex’s Python + OpenAI Agents SDK architecture.

**Milestone Map**
- `M7.1` Main runtime chain parity
- `M7.2` Execution plane parity
- `M7.3` Workspace and group model parity
- `M7.4` Operator surface parity
- `M7.5` Chat and frontend parity
- `M7.6` Channel and ecosystem parity decisions

#### `M7.1` Main Runtime Chain Parity

- [x] `M7.1.1` Replace the current `/messages` queued placeholder with a real dispatch entry that can route a normalized inbound message into the active execution path.
- [x] `M7.1.2` Define the source-of-truth mapping from inbound channel message -> `group_folder` / `chat_jid` / execution target instead of stopping at the current `UnifiedMessage` DTO boundary.
- [x] `M7.1.3` Wire Feishu inbound message events into the real trigger path, not only the current normalization/test layer.
- [x] `M7.1.4` Wire Telegram inbound message events into the real trigger path, not only the current normalization/test layer.
- [x] `M7.1.5` Implement outbound Telegram reply delivery so the inbound -> agent -> outbound loop can actually close.
- [x] `M7.1.6` Replace the current “minimal message router only” boundary with a real per-channel response fan-out path.
- [x] `M7.1.7` Persist enough request/run metadata to correlate one inbound IM message with one agent run and one outbound response.
- [x] `M7.1.8` Add integration coverage for the end-to-end IM delivery chain instead of stopping at DTO/router contracts.

#### `M7.2` Execution Plane Parity

- [x] `M7.2.1` Replace `services/group_queue.py` placeholder logic with a real per-group queue and lifecycle coordinator.
- [x] `M7.2.2` Connect the existing host/container execution slices to the actual runtime trigger flow instead of leaving them as mostly isolated adapters.
- [x] `M7.2.3` Define the runtime selection contract so Web chat, IM chat, scheduled tasks, and future sub-session flows all resolve through one execution-plane rule set.
- [x] `M7.2.4` Introduce session/workspace lifecycle state so one running workspace can accept follow-up messages instead of always behaving like a fresh stateless trigger.
- [x] `M7.2.5` Implement safe cancellation and timeout handling across the real queue + executor boundary, not only the direct `OpenAIAgentsRuntime` path.
- [x] `M7.2.6` Add execution status and recovery signals so queued/running/failed states are observable outside the current direct WebSocket stream.
- [x] `M7.2.7` Add focused tests for queue ordering, executor selection, follow-up injection, cancellation, timeout, and recovery behavior.

#### `M7.3` Workspace And Group Model Parity

- [x] `M7.3.1` Replace the current demo `group-demo` group list with a real persisted group/workspace listing model.
- [x] `M7.3.2` Define the Portex equivalent of HappyClaw’s main workspace / bound chat / per-user home workspace model.
- [x] `M7.3.3` Add explicit workspace ownership and binding metadata so IM chats can be attached to a user’s main workspace or future sub-workspaces.
- [x] `M7.3.4` Extend the current group/member model so it can represent real working sessions instead of only the minimal membership CRUD boundary.
- [x] `M7.3.5` Decide whether Portex will support sub-agent / multi-session tabs like HappyClaw, and if yes, add the minimal data model needed for that.
- [ ] `M7.3.6` Add API routes for listing, creating, updating, and binding workspaces/groups that reflect the chosen model.

#### `M7.4` Operator Surface Parity

- [ ] `M7.4.1` Add a real monitor/status API and page for queue state, executor state, and runtime health instead of only `/health`.
- [ ] `M7.4.2` Add file-management APIs for workspace browsing, upload, download, preview, edit, and delete with the same path-safety rigor as the current execution security model.
- [ ] `M7.4.3` Add memory-management APIs/UI on top of the current file-backed memory service instead of leaving memory as a backend/runner-only primitive.
- [ ] `M7.4.4` Add skills-management APIs/UI instead of relying only on runner-side default tool registration.
- [ ] `M7.4.5` Add MCP server management APIs/UI if Portex intends to match HappyClaw’s user-managed MCP surface.
- [ ] `M7.4.6` Expand settings/configuration flows beyond the current account summary page: provider config, channel config, registration policy, appearance, and system settings.
- [ ] `M7.4.7` Add usage/audit/operator pages where Portex wants parity, or explicitly mark them as intentionally out of scope.

#### `M7.5` Chat And Frontend Parity

- [ ] `M7.5.1` Expand the current `ChatPanel` from a narrow message/thinking/tool view into a richer workspace shell with room for files, members, skills, and execution controls.
- [ ] `M7.5.2` Add file upload and attachment UX to Web chat, not just text-only message submission.
- [ ] `M7.5.3` Add richer room/workspace switching UX instead of the current fixed `group-demo` WebSocket target.
- [ ] `M7.5.4` Add IM binding UX if Portex will bind external chats to internal workspaces like HappyClaw.
- [ ] `M7.5.5` Decide whether to add a terminal panel; if yes, define the execution-mode and permission boundaries first.
- [ ] `M7.5.6` Add setup/onboarding pages if Portex wants parity with HappyClaw’s multi-step first-run experience.
- [ ] `M7.5.7` Add mobile/PWA work only after the core operator/runtime surfaces stop being placeholders.

#### `M7.6` Channel And Ecosystem Parity Decisions

- [ ] `M7.6.1` Decide explicitly whether QQ is part of Portex parity scope or intentionally excluded.
- [ ] `M7.6.2` If QQ is in scope, define the minimal parity target first: C2C, group @Bot, pairing/binding, outbound reply, and image handling.
- [ ] `M7.6.3` Decide how much of HappyClaw’s slash-command behavior should exist in Portex versus staying out of scope.
- [ ] `M7.6.4` Decide whether Portex needs richer IM artifacts like Feishu cards, reactions, and long-message chunking parity.
- [ ] `M7.6.5` Decide which HappyClaw-specific surfaces should remain intentionally unmatched because Portex uses a different runtime stack or product direction.

### Sequencing Notes

- `M7.1` and `M7.2` are the actual parity-critical gaps. Without them, Portex still has strong scaffolding but not the same product-grade execution system.
- `M7.3` is the bridge between “minimal demo routes” and a real multi-user workspace product.
- `M7.4` and `M7.5` are the largest visible product-surface differences when comparing the two repositories side by side.
- `M7.6` should not be started until the project explicitly decides which HappyClaw features are true parity targets versus reference-only inspiration.

# Session Plan (2026-03-11) - M7.1 Main Runtime Chain Planning

## Goal
- Define the first real post-`M6` parity milestone by turning `M7.1` into concrete design and implementation docs without accidentally swallowing `M7.2` queue work or `M7.3` workspace-model work.

## Checklist
- [x] Re-read the current message/runtime boundaries in `app/routes/messages.py`, `app/routes/websocket.py`, `services/agent_trigger.py`, `services/message_router.py`, `domain/schemas.py`, and the earlier `M5.3.2` routing docs
- [x] Confirm the `M7.1` scope choice: close the IM runtime chain on top of the current runtime stack, but defer queue/workspace redesign
- [x] Write the `M7.1` design doc
- [x] Write the `M7.1` implementation plan doc

## Review
- Added `docs/plans/2026-03-11-m7-1-main-runtime-chain-parity-design.md` to lock `M7.1` as “close the current inbound -> runtime -> outbound chain on top of today’s runtime,” explicitly excluding full queue/workspace parity.
- Added `docs/plans/2026-03-11-m7-1-main-runtime-chain-parity.md` with task-by-task execution guidance for a future implementation session.
- The chosen design keeps `M7.1` narrow on purpose: add a real dispatch service, add minimal channel ingestion adapters, add Telegram outbound delivery, replace the `/messages` placeholder, and add focused/integration coverage.
- Explicitly deferred from `M7.1`: real per-group execution plane lifecycle (`M7.2`), final workspace/group topology (`M7.3`), richer operator surfaces (`M7.4`), and frontend product-surface expansion (`M7.5`).
- Suggested future implementation order inside `M7.1`: dispatch service -> IM ingestion adapters -> real `/messages` dispatch -> integration coverage -> docs/handoff refresh.

# Session Plan (2026-03-12) - M6.5.3 Release Artifact Completion

## Goal
- Close formal `M6.5.3` by stabilizing the Docker-missing blocker path, independently re-verifying the real release-image build on the current host, and refreshing restart docs with the final evidence.

## Checklist
- [x] Re-read the current `M6.5.3` build wrapper, tests, and blocker notes
- [x] Add or tighten the failing test for a stable missing-Docker error message
- [x] Implement the minimal `scripts/build_docker.py` change to normalize the message
- [x] Run focused verification for the build wrapper and static release-artifact slice
- [x] Run the broader backend/frontend regression commands relevant to this milestone
- [x] Independently verify the current host rootless Docker path and fresh release-image build
- [x] Update `docs/TODO.md`, `docs/progress.md`, `AGENTS.md`, `README.md`, `README.zh-CN.md`, and `docs/deployment.md` with the final `M6.5.3` state
- [x] Commit the milestone-completion result cleanly

## Review
- Tightened `tests/scripts/test_build_docker.py` so the missing-Docker path now matches the real `subprocess.run()` failure shape (`FileNotFoundError(2, ..., "docker")`) instead of a synthetic message-only exception, and normalized `scripts/build_docker.py` stderr to the stable operator-facing string `docker command not found` while preserving the existing `127` exit code.
- Independent verification overturned the old blocker assumption: the current host already has a working user-space rootless Docker path under `~/bin`, with `DOCKER_HOST=unix:///run/user/1000/docker.sock`; fresh `docker version`, `.venv/bin/python scripts/build_docker.py --tag portex:v1.0.0`, `docker image ls --no-trunc`, and `docker image inspect` all succeeded.
- Refreshed `docs/TODO.md`, `docs/progress.md`, `AGENTS.md`, `README.md`, `README.zh-CN.md`, and `docs/deployment.md` so the repository now consistently records `M6.5.3` and `M6` as complete, while keeping `M7.1` as a user-gated next step rather than an automatic continuation.
- Final verification ran fresh after the doc sync: `git diff --check`; `.venv/bin/pytest tests/scripts/test_build_docker.py tests/container/agent_runner/test_container_files.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`; `test -f web/dist/index.html`; `PATH="$HOME/bin:$PATH" DOCKER_HOST=unix:///run/user/1000/docker.sock docker version --format '{{.Client.Version}}|{{.Server.Version}}'`; `PATH="$HOME/bin:$PATH" DOCKER_HOST=unix:///run/user/1000/docker.sock .venv/bin/python scripts/build_docker.py --tag portex:v1.0.0`; `PATH="$HOME/bin:$PATH" DOCKER_HOST=unix:///run/user/1000/docker.sock docker image inspect portex:v1.0.0 --format '{{.Id}}'`.
- Commit completed in this session: `docs(release): complete M6.5.3 artifact verification`.

# Session Plan (2026-03-12) - M7.1 Runtime Dispatch Refinement

## Goal
- Start `M7.1` on the user-approved narrow path: add a structured runtime-result boundary, then close the inbound IM/http -> runtime -> outbound reply chain without absorbing WebSocket unification or execution-plane redesign.

## Checklist
- [x] Re-read the current runtime, IM, message route, and persistence slices
- [x] Write the refined `M7.1` design doc
- [x] Write the refined `M7.1` implementation plan doc
- [x] Commit the design/plan refinement
- [x] Add failing tests for the structured runtime-result and dispatch-service contract
- [x] Implement the first `M7.1` batch and verify it

## Review
- Added `docs/plans/2026-03-12-m7-1-runtime-dispatch-refinement-design.md` and `docs/plans/2026-03-12-m7-1-runtime-dispatch-refinement.md` to lock the user-approved narrower `M7.1` execution order: structured runtime-result path first, then dispatch/IM adapters, without swallowing WebSocket unification or `M7.2`.
- Added `services/message_dispatch.py` plus a structured `run_agent_execution()` path in `services/agent_trigger.py`, so non-WebSocket callers can reuse the current runtime stack and receive `run_id/status/final_output/error/timeout_ms` without parsing broadcast strings.
- Added app-level Feishu and Telegram ingestion routes in `app/routes/im.py`, real Telegram outbound text sending, a real `/messages` dispatch path, and minimal message-correlation metadata persisted through `services/message_service.py` into the existing `attachments` field.
- Added `tests/services/test_message_dispatch.py`, `tests/app/routes/test_im_routes.py`, `tests/app/routes/test_message_routes.py`, and `tests/integration/test_message_flow.py`, and extended existing runtime/route/Telegram tests to lock the `M7.1` chain end to end.
- Fresh verification ran: `git diff --check`; `.venv/bin/pytest -o addopts='' tests/services/test_agent_trigger.py tests/services/test_message_dispatch.py tests/services/test_message_service.py tests/app/routes/test_im_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/im/test_telegram.py tests/infra/im/test_feishu.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`.
- Session commits completed: `docs(plans): refine M7.1 runtime dispatch design`, `feat(messages): add main runtime dispatch service`, `feat(messages): persist dispatch metadata`, `feat(im): add M7.1 ingestion adapters`, `feat(messages): replace message placeholder route`, `test(messages): add M7.1 integration coverage`, `docs(handoff): record M7.1 completion`.

# Session Plan (2026-03-12) - M7.2 Execution Plane Parity

## Goal
- Start `M7.2` on the approved coordinator-first path: add one per-group execution coordinator, one backend-selection policy, and one shared submission contract for Web/IM/tasks without swallowing `M7.3` workspace-model work or `M7.4` operator surfaces.

## Checklist
- [x] Re-read the current execution-plane entrypoints and backend helpers
- [x] Write the `M7.2` design doc
- [x] Write the `M7.2` implementation plan doc
- [x] Commit the `M7.2` planning docs
- [x] Add failing tests for the coordinator/policy contract
- [x] Implement the first `M7.2` batch and verify it

## Review
- Added `docs/plans/2026-03-12-m7-2-execution-plane-parity-design.md` and `docs/plans/2026-03-12-m7-2-execution-plane-parity.md` to lock the approved coordinator-first `M7.2` scope: one in-process execution coordinator, one backend policy, and one shared submission contract for Web/IM/tasks, while explicitly deferring workspace topology and operator UI.
- Added `services/execution_coordinator.py`, `services/execution_policy.py`, and replaced the old `services/group_queue.py` placeholder with a compatibility alias to the real coordinator core.
- Added `tests/services/test_execution_coordinator.py` and `tests/services/test_execution_policy.py`, covering per-group FIFO, different-group independence, session reuse, fresh session creation, queued and running cancellation, timeout, invalid mode failure, and missing-backend failure.
- Hardened running cancellation so the coordinator records terminal `cancelled` state immediately, cancels the in-flight execution task, and only performs backend cancellation as a best-effort background action; also added minimal completed-run retention so coordinator-owned state does not grow without bound in the obvious happy path.
- Fresh verification ran: `git diff --check`; `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_message_dispatch.py tests/integration/test_websocket.py -q`.
- Session commits completed so far: `docs(plans): define M7.2 execution plane parity`, `feat(execution): add M7.2 coordinator core`, `fix(execution): harden coordinator cancellation`.

# Session Plan (2026-03-12) - M7.2.2 Execution Backend Adapters

## Goal
- Continue from the documented parity handoff point by connecting the current in-process, host-process, and container runner slices to the coordinator contract, and rewire WebSocket plus IM/HTTP dispatch through that coordinator without swallowing scheduled-task execution in the same pass.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, the `M7.2` design docs, and the current execution/runtime entrypoints
- [x] Write the focused `M7.2.2` design doc
- [x] Write the focused `M7.2.2` implementation plan doc
- [x] Add failing tests for execution backends and coordinator-backed entrypoint wiring
- [x] Implement unified execution backends and default coordinator wiring
- [x] Rewire WebSocket and default IM/HTTP dispatch through the coordinator
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review
- [x] Commit the `M7.2.2` slice with a detailed message

## Review
- Added `docs/plans/2026-03-12-m7-2-2-execution-backend-adapters-design.md` to lock this slice as “backend adapters + Web/IM/HTTP rewiring”, explicitly deferring scheduled-task submission to the next execution-plane sub-step.
- Added `docs/plans/2026-03-12-m7-2-2-execution-backend-adapters.md` with a TDD-first implementation order: backend tests first, then adapter implementation, then route/service rewiring, then verification and handoff refresh.
- Added `services/execution_backends.py` and `services/execution_runtime.py`, so the coordinator now owns three request-scoped backends: OpenAI runtime reuse, host-process runner parsing, and `docker run -i` container execution parsing.
- Rewired `app/routes/websocket.py` and default `MessageDispatchService` wiring in `app/routes/im.py` to submit `ExecutionRequest` objects through the coordinator instead of calling direct runtime helpers.
- Extended focused coverage with `tests/services/test_execution_backends.py`, coordinator-backed dispatch tests, WebSocket coordinator-route tests, message-route default wiring tests, integration WebSocket parity checks, and the new `ProcessExecutor.cancel()` test.
- Fixed three review-driven regressions before final verification: inbound-message persistence now happens before coordinator submission, WebSocket now synthesizes `run.failed` for OpenAI-backed failed results that never streamed a terminal event, and outer cancellation now calls `runtime.cancel()` before tearing down the consumer task.
- Fresh verification ran: `git diff --check`; `.venv/bin/pytest -o addopts='' tests/services/test_agent_trigger.py tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py tests/app/routes/test_im_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/exec/test_process.py tests/infra/exec/test_container_manager.py tests/infra/exec/test_docker.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`.
- Session commit completed: `feat(execution): complete M7.2.2 backend adapters`.

# Session Plan (2026-03-13) - M7.2.3 Execution Selection And Scheduled Tasks

## Goal
- Continue from the documented parity handoff point by routing scheduled tasks through the coordinator and by letting current request-body callers pass a real execution-mode preference into the execution plane, without expanding into group/workspace execution-mode persistence or WebSocket protocol redesign.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, the `M7.2` docs, and current task/message execution slices
- [x] Write the focused `M7.2.3` design doc
- [x] Write the focused `M7.2.3` implementation plan doc
- [x] Add failing tests for `execution_mode` propagation and scheduled-task coordinator wiring
- [x] Implement the minimal schema/service/route updates
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review
- [x] Commit the `M7.2.3` slice with a detailed message

## Review
- Added `docs/plans/2026-03-13-m7-2-3-scheduled-tasks-and-mode-inputs-design.md` and `docs/plans/2026-03-13-m7-2-3-scheduled-tasks-and-mode-inputs.md` to lock this slice as “request-level execution-mode propagation + scheduled-task coordinator wiring”, explicitly deferring group/workspace execution-mode persistence and WebSocket payload changes.
- Extended `domain/models/task.py`, `domain/schemas.py`, `app/routes/messages.py`, `app/routes/tasks.py`, `services/message_dispatch.py`, and `services/task_service.py` so HTTP `/messages` plus scheduled-task contracts now accept optional `execution_mode`, and scheduled tasks execute through `ExecutionCoordinator` with `source="scheduled"`.
- Expanded `tests/services/test_message_dispatch.py`, `tests/services/test_task_service.py`, `tests/app/routes/test_message_routes.py`, `tests/app/routes/test_api_routes.py`, and `tests/domain/models/test_models.py` to lock explicit mode propagation, task execution-plane wiring, task-log timeout/error mapping, and the persisted task `execution_mode` contract.
- Fresh verification ran: `git diff --check`; `.venv/bin/pytest tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/domain/models/test_models.py -q` (`75 passed, 38 warnings in 8.12s`); `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/domain/models/test_models.py tests/integration/test_message_flow.py -q` (`98 passed, 38 warnings in 10.03s`); `.venv/bin/pytest -o addopts='' -q` (`353 passed, 53 warnings in 13.90s`); `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`.
- Commit for this slice: `feat(execution): complete M7.2.3 scheduled task mode inputs`.

# Session Plan (2026-03-13) - M7.2.4 Session Workspace Lifecycle

## Goal
- Continue from the current parity handoff point by introducing a minimal coordinator-owned workspace/session lifecycle so follow-up turns reuse a real persisted execution session in the default OpenAI path, without expanding into `M7.3`'s persistent workspace model or new reset APIs.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, the `M7.2` docs, and the current execution/runtime slices
- [x] Compare the current Portex lifecycle behavior against the HappyClaw reference implementation
- [x] Write the focused `M7.2.4` design doc
- [x] Write the focused `M7.2.4` implementation plan doc
- [x] Add failing tests for workspace lifecycle state and real session persistence
- [x] Implement coordinator-owned lifecycle state plus OpenAI session persistence/retry
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review
- [x] Commit the `M7.2.4` slice with a detailed message

## Review
- Added `docs/plans/2026-03-13-m7-2-4-session-workspace-lifecycle-design.md` and `docs/plans/2026-03-13-m7-2-4-session-workspace-lifecycle.md` to lock this slice as “coordinator-owned workspace/session lifecycle + default OpenAI runtime real session persistence”, explicitly deferring `M7.3` persistent workspace topology and any new reset API.
- Added `services/workspace_lifecycle.py` and rewired `services/execution_coordinator.py` to replace the old `_session_ids` string cache with explicit workspace lifecycle state: preview session, success-only commit, invalidate, and one fresh retry after session-resume failure.
- Extended `infra/runtime/openai.py` to pass a real Agents SDK `SQLiteSession` into `Runner.run_streamed(...)`, storing session data under `data/sessions/{group_folder}/agents-sdk.sqlite3`; `services/execution_backends.py` now maps startup-time session-resume failures into a dedicated lifecycle error without misclassifying stream-time tool errors.
- Added `tests/services/test_workspace_lifecycle.py`, and expanded `tests/services/test_execution_coordinator.py`, `tests/infra/runtime/test_openai.py`, `tests/services/test_execution_backends.py`, and `tests/services/test_agent_trigger.py` to lock success-only commit, invalidate+retry, real session injection, and hermetic test behavior without repo-local `data/sessions/` pollution.
- Multi-agent review found one real risk in the first draft: stream-time `OSError/sqlite3.Error` was too broad and could trigger a false session reset. The implementation was tightened so only session initialization/startup failures can drive the fresh-retry path; no additional findings remained in the coordinator/workspace slice.
- Fresh verification ran: `git diff --check`; `.venv/bin/pytest tests/services/test_workspace_lifecycle.py tests/services/test_execution_coordinator.py tests/services/test_execution_backends.py tests/infra/runtime/test_openai.py tests/services/test_message_dispatch.py tests/services/test_task_service.py -q`; `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_workspace_lifecycle.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/runtime/test_openai.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`.
- Session commits completed: `docs(plans): define M7.2.4 session workspace lifecycle`, `feat(execution): complete M7.2.4 workspace session lifecycle`.

# Session Plan (2026-03-13) - M7.2.5 Cancel Timeout Boundary

## Goal
- Continue from the current parity handoff point by hardening cancellation and timeout semantics across the real queue + executor boundary, so host/container cleanup remains reachable after outer coroutine cancellation and timeout no longer degrades into generic `failed` states.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, the `M7.2` docs, and the current execution/runtime slices
- [x] Compare the current Portex cancel/timeout boundary against the HappyClaw reference implementation
- [x] Write the focused `M7.2.5` design doc
- [x] Write the focused `M7.2.5` implementation plan doc
- [x] Add failing tests for cleanup-aware cancel/timeout handling
- [x] Implement backend handle retention plus timeout normalization
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review
- [x] Commit the `M7.2.5` slice with a detailed message

## Review
- Added `docs/plans/2026-03-13-m7-2-5-cancel-timeout-boundary-design.md` and `docs/plans/2026-03-13-m7-2-5-cancel-timeout-boundary.md` to lock this slice as “cleanup-aware queue/executor boundary”, explicitly deferring `M7.2.6` state/recovery surfaces and HappyClaw’s wider `_interrupt` / `_close` protocol.
- Extended `services/execution_coordinator.py` so timeout no longer blocks on synchronous `await backend.cancel(...)`; the user-visible `timeout` result is now stored immediately and backend cleanup continues in the background, matching the existing running-cancel queue-release rule.
- Extended `infra/exec/process.py` and `services/execution_backends.py` so host/container cleanup remains reachable after outer coroutine cancellation: host outer cancel now sends an immediate kill signal, host/container active handles survive long enough for cleanup, and cleanup waits are bounded instead of hanging indefinitely on `process.wait()` / docker wrapper waits.
- Added `ProcessExecutionTimeoutError` and normalized host executor timeout into a real `timeout` result in `HostProcessBackend`, rather than leaking back out as a generic `failed`.
- Expanded `tests/services/test_execution_coordinator.py`, `tests/services/test_execution_backends.py`, and `tests/infra/exec/test_process.py` to lock timeout queue release, outer-cancel cleanup reachability, bounded cleanup waits, and stable timeout background-cancel assertions.
- Multi-agent review found two real follow-ups after the first implementation: cleanup waits were still unbounded, and outer host cancellation still depended on a second-step cancel call to stop the child. Both were fixed before final verification. An additional coordinator review pointed out that the old timeout test had become timing-dependent after moving cancel to the background, so the assertion was stabilized accordingly.
- Fresh verification ran: `git diff --check`; `.venv/bin/pytest tests/services/test_execution_backends.py tests/services/test_execution_coordinator.py tests/infra/exec/test_process.py -q`; `.venv/bin/pytest tests/integration/test_websocket.py tests/app/routes/test_websocket_routes.py tests/services/test_task_service.py -q`; `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_workspace_lifecycle.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/runtime/test_openai.py tests/infra/exec/test_process.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`.
- Session commits completed: `docs(plans): define M7.2.5 cancel timeout boundary`, `fix(execution): complete M7.2.5 cancel timeout boundary`, `fix(execution): bound M7.2.5 cleanup waits`.

# Session Plan (2026-03-13) - M7.2.6 Status Recovery Signaling

## Goal
- Continue from the current parity handoff point by exposing execution status and minimal recovery signals outside the current direct WebSocket stream, without expanding into `M7.3` workspace persistence or `M7.4` operator dashboards.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, the `M7.2` docs, and current execution/runtime/routes slices
- [x] Write the focused `M7.2.6` design doc
- [x] Write the focused `M7.2.6` implementation plan doc
- [x] Add failing tests for coordinator run snapshots and external status query route
- [x] Implement minimal coordinator status/recovery snapshot surface and read-only execution status API
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review
- [x] Commit the `M7.2.6` slice with a detailed message

## Review
- Added `docs/plans/2026-03-13-m7-2-6-status-recovery-signaling-design.md` and `docs/plans/2026-03-13-m7-2-6-status-recovery-signaling.md` to lock this slice as “coordinator snapshot + read-only status query”, explicitly deferring monitor surfaces and run persistence.
- Extended `services/execution_coordinator.py` with `ExecutionRunSnapshot` plus `get_run_snapshot()` and lifecycle updates (`queued/running/terminal`) including minimal recovery signaling (`recovery_attempted/recovery_reason/recovery_succeeded`) on resume-retry paths.
- Added `app/routes/executions.py` (`GET /executions/{run_id}`) and wired it through `app/main.py`/`app/routes/__init__.py`; extended `domain/schemas.py` and `app/openapi.py` with execution-status response contracts and OpenAPI tag metadata.
- Expanded `tests/services/test_execution_coordinator.py`, added `tests/app/routes/test_execution_routes.py`, and extended `tests/app/routes/test_api_routes.py` to lock snapshot lifecycle, recovery flags, auth/404 behavior, and OpenAPI contracts.
- Added a regression guard for invalid `requested_mode` snapshots: `GET /executions/{run_id}` now normalizes unknown mode values to `None` instead of throwing a response-validation `500`; covered by `test_execution_status_route_tolerates_unknown_requested_mode`.
- Added resource-level read protection for execution snapshots: only the run owner or `owner/admin` role can read `/executions/{run_id}`; non-owner authenticated requests now return `404`, covered by `test_execution_status_route_hides_other_users_runs`.
- Fresh verification ran: `.venv/bin/pytest tests/app/routes/test_execution_routes.py::test_execution_status_route_tolerates_unknown_requested_mode -q`; `.venv/bin/pytest tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py tests/app/routes/test_api_routes.py -q -ra`; `.venv/bin/pytest tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_websocket.py -q`; `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_workspace_lifecycle.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/app/routes/test_execution_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/runtime/test_openai.py tests/infra/exec/test_process.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`; `git diff --check`.
- Commit for this slice: `feat(execution): complete M7.2.6 status recovery signaling`.

# Session Plan (2026-03-13) - M7.2.7 Focused Execution-Plane Tests

## Goal
- Continue from `M7.2.6` by adding focused tests for queue ordering, executor selection, follow-up/session behavior, cancellation edges, timeout payload contract, and recovery signaling behavior, without expanding into new runtime features.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and current `M7.2` execution-plane slices
- [x] Write the focused `M7.2.7` design doc
- [x] Write the focused `M7.2.7` implementation plan doc
- [x] Add failing tests for queue ordering, executor selection, cancellation edges, timeout payload, and recovery behavior
- [x] Implement only minimal fixes required by red tests
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review
- [x] Commit the `M7.2.7` slice with a detailed message

## Review
- Added `docs/plans/2026-03-13-m7-2-7-focused-tests-design.md` and `docs/plans/2026-03-13-m7-2-7-focused-tests.md` to lock this slice as “focused behavior parity tests” without expanding into new execution features.
- Expanded `tests/services/test_execution_coordinator.py` with focused tests for same-group head-failure queue progression, cross-source serialization, requested-mode backend observability via snapshots, cancellation idempotent edges, recovery-retry failure signaling, and fresh-session no-retry signaling.
- Expanded `tests/app/routes/test_websocket_routes.py` with timeout payload contract coverage (`run.timeout` with `status=timeout` and `timeout_ms`).
- No production-code changes were needed for `M7.2.7`; new focused tests passed on top of the `M7.2.6` implementation.
- Fresh verification ran: `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/app/routes/test_websocket_routes.py`; `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_websocket.py`; `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_workspace_lifecycle.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/app/routes/test_execution_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/runtime/test_openai.py tests/infra/exec/test_process.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`; `git diff --check`.
- Commit for this slice: `test(execution): complete M7.2.7 focused parity coverage`.

# Session Plan (2026-03-13) - M7.3.1 Persisted Group Listing

## Goal
- Continue from the current parity handoff point by replacing the hard-coded `/groups` demo output with a real persisted registered-group listing model, and by lazily registering resolved HTTP/IM targets into that registry without defining the final workspace/home/binding topology.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, the `M7.1`/`M7.2` design docs, and current group/message/IM slices
- [x] Compare the current Portex group/workspace surface against the HappyClaw reference implementation
- [x] Write the focused `M7.3.1` design doc
- [x] Write the focused `M7.3.1` implementation plan doc
- [x] Add failing tests for the registry service, `/groups` listing, and dispatch registration hook
- [x] Implement the minimal persisted registry service and route/dispatch wiring
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review

## Review
- Added `docs/plans/2026-03-13-m7-3-1-persisted-group-listing-design.md` and `docs/plans/2026-03-13-m7-3-1-persisted-group-listing.md` to lock this slice as “DB-backed registered-group list + lazy auto-registration”, explicitly deferring home workspace, IM binding metadata, and richer workspace APIs.
- Added `services/group_registry.py` plus `tests/services/test_group_registry.py`, turning `domain.models.group.RegisteredGroup` into a real async service boundary with `list_registered_groups()` and idempotent `ensure_registered_group(...)`.
- Rewired `app/routes/groups.py` so `GET /groups` now reads the registry instead of returning hard-coded `group-demo`, while preserving the current `group_id/name` response shape by mapping `group_id` to the persisted `folder`.
- Extended `services/message_dispatch.py` with an optional registration hook and rewired the default dependency path in `app/routes/im.py` so HTTP and IM dispatch lazily persist the current `chat_jid -> group_folder` target into `registered_groups` before execution continues.
- Expanded `tests/services/test_message_dispatch.py`, `tests/app/routes/test_message_routes.py`, and `tests/app/routes/test_api_routes.py` to lock registration order, default HTTP dispatch wiring, and the route-level registry-backed list contract.
- Fresh verification ran: `.venv/bin/pytest tests/services/test_group_registry.py tests/app/routes/test_api_routes.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py -q`; `.venv/bin/pytest tests/services/test_group_registry.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/app/routes/test_im_routes.py tests/integration/test_message_flow.py tests/integration/test_api.py tests/integration/test_websocket.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `git diff --check`.

# Session Plan (2026-03-16) - M8.3 Terminal Operator UX Implementation On Main

## Goal
- Continue from the current handoff state by implementing `M8.3` directly on `main`: add a read-only terminal overview API, a standalone `/terminals` operator page, and minimal `/chat?workspace=...` deep-link support, while preserving existing terminal control boundaries.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and `M8.3` design/plan docs
- [x] Add failing tests for terminal session listing read helper
- [x] Implement `TerminalSessionService.list_sessions()` and make focused service tests pass
- [x] Add failing route/OpenAPI tests for `GET /terminals`
- [x] Implement `GET /terminals` aggregation route and schemas
- [x] Add frontend red stage for `/terminals` route and navigation
- [x] Implement frontend terminals overview page + API hook/client
- [x] Add minimal `ChatPanel` workspace deep-link behavior
- [x] Run focused verification + repo regression + lint/build + diff hygiene
- [x] Update `docs/progress.md` and complete this review section
- [x] Commit milestone result with a detailed message

## Review
- Backend `M8.3` read surface is now on `main`: `TerminalSessionService.list_sessions()` + `GET /terminals` terminal overview route + `TerminalWorkspaceSummaryResponse`/`TerminalWorkspaceListResponse` schemas.
- Added dedicated route coverage in `tests/app/routes/test_terminal_monitor_routes.py`, expanded service coverage in `tests/services/test_terminal_sessions.py`, and extended OpenAPI contract coverage in `tests/app/routes/test_api_routes.py`.
- Frontend `M8.3` surface is now on `main`: `/terminals` page, operator-only navigation entry, `getTerminalOverview` client + `useTerminalOverviewQuery`, and minimal `/chat?workspace=...` initial workspace deep-link behavior in `ChatPanel`.
- `docs/progress.md` has been refreshed to move `M8.3` to completed-on-`main` state and reset restart guidance to post-`M8.3` continuation options.
- Fresh verification commands executed in this session:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`
  - `.venv/bin/pytest tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q`
  - `cd web && npm ci`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `.venv/bin/pytest -o addopts='' -q` (`564 passed`)
  - `.venv/bin/ruff check .`
  - `git diff --check`

# Session Plan (2026-03-16) - M8.4 Terminal Light Controls

## Goal
- Continue post-`M8.3` by adding minimal terminal operator control actions on top of the new overview surface: allow operators to close their own active sessions and force-close active sessions through a dedicated API, without expanding into TTY fidelity/session persistence scope.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and `M8.3` docs
- [x] Write focused `M8.4` design doc
- [x] Write focused `M8.4` implementation plan doc
- [x] Add failing tests for force-close service and route contract
- [x] Implement backend force-close session capability and route
- [x] Add failing frontend build stage for terminals control actions
- [x] Implement `/terminals` close/force-close actions and API client updates
- [x] Run focused verification + frontend lint/build + full regression + hygiene checks
- [x] Update `docs/progress.md` and complete this review section
- [x] Commit milestone result with a detailed message

## Review
- Added `docs/plans/2026-03-16-m8-4-terminal-light-controls-design.md` and `docs/plans/2026-03-16-m8-4-terminal-light-controls.md` to lock M8.4 scope as “light control actions only”, explicitly deferring fidelity/session-persistence work.
- Extended backend terminal lifecycle with `TerminalSessionService.force_close_session_by_group()` and exposed `DELETE /terminals/{group_id}/sessions/force` in `app/routes/terminals.py`, preserving existing role/access gates and response contracts.
- Expanded backend coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py`; retained compatibility with existing terminal overview tests.
- Upgraded `web/src/pages/Terminals.tsx` from read-only to light-control UI: row-level `Close` (own active session) and `Force Close` (operator action), with action loading states and inline notice/error; wired via new `apiClient.forceCloseCurrentTerminalSession()` in `web/src/api/client.ts`.
- Recorded frontend red-green evidence for this slice: first introduced `forceCloseCurrentTerminalSession` call in page (missing client method) and confirmed `cd web && npm run build` failed; then implemented client + UI wiring and restored build green.
- Refreshed `docs/progress.md` to mark `M8.4` complete on `main` and move restart guidance to post-`M8.4` fidelity/session-management continuation.
- Fresh verification commands executed in this session:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
  - `cd web && npm run build` (red stage expected fail before client method)
  - `cd web && npm run lint`
  - `cd web && npm run build` (green stage)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`566 passed`)
  - `.venv/bin/ruff check .`
  - `git diff --check`

# Session Plan (2026-03-16) - M8.5.1 Terminal Output Replay On Reconnect

## Goal
- Start post-`M8.4` terminal fidelity/session-management work with a minimal high-value slice: keep recent terminal output in-memory per session and replay it on reconnect, so users can recover context after websocket reconnects without introducing persistent terminal storage.

## Checklist
- [x] Re-read terminal runtime slices and existing websocket/terminal panel behavior
- [x] Write focused `M8.5.1` design doc
- [x] Write focused `M8.5.1` implementation plan doc
- [x] Add failing tests for output history replay and bounded history behavior
- [x] Implement terminal session output history buffer + replay on attach
- [x] Integrate frontend transcript behavior for reconnect replay (avoid duplicate transcript buildup)
- [x] Run focused verification + frontend lint/build + full regression + hygiene checks
- [x] Update `docs/progress.md` and complete this review section
- [x] Commit milestone result with a detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-1-terminal-output-replay-design.md` and `docs/plans/2026-03-16-m8-5-1-terminal-output-replay.md` to lock this slice as “bounded in-memory output replay on reconnect”, explicitly deferring persistent transcript storage and wider TTY fidelity changes.
- Expanded `tests/services/test_terminal_sessions.py` with red-first coverage for reconnect replay and history-cap eviction; initial run failed as expected due missing `history_max_bytes`/replay logic.
- Implemented bounded output history in `services/terminal_sessions.py` by extending managed session state with rolling chunk buffer + byte accounting, recording output chunks in bridge-event handling, and replaying buffered output on `attach_session()`.
- Updated `web/src/components/chat/TerminalPanel.tsx` so reconnect clears the current workspace transcript before socket attach, letting server replay repopulate content without duplicate local buildup.
- Refreshed `docs/progress.md` to mark `M8.5.1` complete and move restart guidance to post-`M8.5.1` fidelity sub-slices.
- Fresh verification commands executed in this session:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py -q` (red and green cycles)
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`568 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint && npm run build`
  - `git diff --check`

# Session Plan (2026-03-16) - M8.5.2 Terminal Resize Fidelity

## Goal
- Continue post-`M8.5.1` fidelity work by replacing terminal resize no-op behavior with real PTY size propagation and dynamic frontend resize emission, while keeping current terminal ownership/session boundaries unchanged.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and `M8.5.1`/terminal runtime slices
- [x] Write focused `M8.5.2` design doc
- [x] Write focused `M8.5.2` implementation plan doc
- [x] Add failing bridge-focused tests for TTY startup and resize propagation
- [x] Implement PTY-backed `DockerExecTerminalBridge` resize behavior
- [x] Keep terminal service/websocket resize forwarding coverage green
- [x] Improve `TerminalPanel` to emit panel-based dynamic resize events
- [x] Run focused terminal verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md` with `M8.5.2` evidence and next-step guidance
- [x] Add session review notes in `tasks/todo.md`
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-2-terminal-resize-fidelity-design.md` and `docs/plans/2026-03-16-m8-5-2-terminal-resize-fidelity.md` to lock `M8.5.2` scope before implementation.
- Added `tests/services/test_terminal_bridge.py` with red-green coverage for interactive TTY startup flags and PTY resize ioctl propagation.
- Refactored `services/terminal_bridge.py` from pipe/no-op resize to PTY-backed bridge (`docker exec -it` + PTY output forwarding + `TIOCSWINSZ` resize).
- Updated `web/src/components/chat/TerminalPanel.tsx` to emit dynamic resize dimensions (ready + delayed ready + window resize throttling with dedupe), replacing fixed `120x32`.
- Updated `docs/progress.md` to move restart baseline to post-`M8.5.2`.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_bridge.py -q` (red first, then green)
  - `.venv/bin/pytest tests/services/test_terminal_bridge.py tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`570 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Commit: `87322e1` (`feat(terminal): complete M8.5.2 resize fidelity`).

# Session Plan (2026-03-16) - M8.5.3 Terminal History Read Surface

## Goal
- Continue post-`M8.5.2` session-management work by adding a minimal read-only terminal history API for the current workspace session, reusing existing bounded in-memory output history.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and latest terminal slices
- [x] Write focused `M8.5.3` design doc
- [x] Write focused `M8.5.3` implementation plan doc
- [x] Add failing tests for service history snapshot behavior
- [x] Add failing route tests for terminal history read endpoint
- [x] Add failing OpenAPI assertions for the new route contract
- [x] Implement `TerminalSessionService` history snapshot read helper
- [x] Add `TerminalSessionHistoryResponse` schema and wire route response model
- [x] Implement `GET /terminals/{group_id}/sessions/current/history`
- [x] Run focused terminal/backend verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md` with `M8.5.3` evidence and next-step guidance
- [x] Add session review notes in `tasks/todo.md`
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-3-terminal-history-read-surface-design.md` and `docs/plans/2026-03-16-m8-5-3-terminal-history-read-surface.md` to lock this slice as “terminal history read surface only,” explicitly deferring cross-process persistence.
- Extended `services/terminal_sessions.py` with `TerminalSessionHistorySnapshot` and `get_history_by_group()` to expose a lock-protected in-memory history snapshot (`output`, `output_bytes`, `history_max_bytes`, `truncated`) for the current workspace session.
- Added `TerminalSessionHistoryResponse` in `domain/schemas.py` and exported it for OpenAPI/schema use.
- Added route `GET /terminals/{group_id}/sessions/current/history` in `app/routes/terminals.py`, reusing existing terminal role + workspace access checks and existing terminal error mapping.
- Expanded tests in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` with red-green coverage for service snapshot behavior, route auth/success/not-found behavior, and OpenAPI route contract.
- Updated `docs/progress.md` to mark `M8.5.3` complete and move next-step guidance to post-`M8.5.3` persistence.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q` (red then green)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`574 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Commit: `010cc40` (`feat(terminal): complete M8.5.3 history read surface`).

# Session Plan (2026-03-16) - M8.5.4 Terminal History Persistence Fallback

## Goal
- Continue post-`M8.5.3` session-management work by persisting latest terminal history snapshots and enabling `current/history` reads to fall back after process restart.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and latest terminal slices
- [x] Write focused `M8.5.4` design doc
- [x] Write focused `M8.5.4` implementation plan doc
- [x] Add failing tests for history persistence fallback across fresh service instances
- [x] Implement safe terminal history snapshot persistence helpers in `TerminalSessionService`
- [x] Persist snapshot on output updates and terminal-state transitions
- [x] Add disk fallback logic to `get_history_by_group()`
- [x] Run focused terminal/backend verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md` with `M8.5.4` evidence and next-step guidance
- [x] Add session review notes in `tasks/todo.md`
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-4-terminal-history-persistence-fallback-design.md` and `docs/plans/2026-03-16-m8-5-4-terminal-history-persistence-fallback.md` to lock `M8.5.4` scope as “history persistence fallback only,” explicitly deferring active session recovery.
- Extended `services/terminal_sessions.py` with safe file-backed snapshot persistence under `data/terminal-history/<workspace>/latest.json`, including atomic write + path validation guardrails.
- Updated `TerminalSessionService.get_history_by_group()` to fall back to persisted snapshot when no in-memory session exists, preserving existing route/DTO contract.
- Wired snapshot refresh on output changes and terminal-state transitions (`closed`/`exited`) so persisted history reflects latest bounded buffer and status.
- Expanded `tests/services/test_terminal_sessions.py` with red-green restart-like fallback coverage (fresh service instance loads persisted snapshot).
- Updated `docs/progress.md` to mark `M8.5.4` complete and move next-step guidance to active session persistence/recovery.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py -q` (red then green)
  - `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`575 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Commit: `0563192` (`feat(terminal): complete M8.5.4 history persistence fallback`).

# Session Plan (2026-03-16) - M8.5.5 Terminal Active Session Persistence/Recovery

## Goal
- Continue from `M8.5.4` by adding active terminal session persistence/recovery across process restart, while keeping existing HTTP/WebSocket contracts unchanged.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and latest terminal slices
- [x] Write focused `M8.5.5` design doc
- [x] Write focused `M8.5.5` implementation plan doc
- [x] Add failing tests for active-session restart recovery semantics (service + route)
- [x] Implement active session recovery in `TerminalSessionService` (startup rehydrate + lazy attach bridge + fallback close)
- [x] Persist snapshot on active lifecycle transitions (`created`/`attached`/`detached`)
- [x] Run focused terminal/backend verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md` and complete this review section
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-5-terminal-active-session-recovery-design.md` and `docs/plans/2026-03-16-m8-5-5-terminal-active-session-recovery.md` to lock `M8.5.5` scope as “active session persistence/recovery only,” explicitly deferring persistence-aware multi-session inventory.
- Extended `services/terminal_sessions.py` with optional startup recovery (`recover_active_sessions`) that rehydrates persisted active snapshots as detached in-memory sessions, and with recovered-session lazy bridge attach + attach-failure close fallback.
- Added active lifecycle snapshot persistence for `created`/`attached`/`detached`, keeping restart semantics consistent even without fresh terminal output.
- Updated `services/execution_runtime.py` so runtime default terminal service enables active recovery, while `TerminalSessionService` default remains recovery-off to keep test isolation deterministic.
- Expanded `tests/services/test_terminal_sessions.py` and `tests/app/routes/test_terminal_routes.py` with red-green coverage for active-session restart recovery, owner attach of recovered sessions, cross-owner conflict continuity, and attach-failure fallback behavior.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py -q` (red then green)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`581 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`

# Session Plan (2026-03-16) - M8.5.6 Persistence-Aware Terminal History Inventory

## Goal
- Continue from `M8.5.5` by exposing persisted terminal history inventory in the existing `/terminals` operator overview, without adding a new standalone inventory route.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and latest terminal slices
- [x] Write focused `M8.5.6` design doc
- [x] Write focused `M8.5.6` implementation plan doc
- [x] Add failing tests for history inventory contract (service + monitor route + openapi)
- [x] Implement backend inventory read model (`TerminalSessionService` + schemas + `/terminals` mapping)
- [x] Update frontend `/terminals` page to render history inventory metadata
- [x] Run focused terminal/backend verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md` and complete this review section
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-6-terminal-history-inventory-design.md` and `docs/plans/2026-03-16-m8-5-6-terminal-history-inventory.md` to lock scope as “overview additive history inventory,” explicitly deferring dedicated inventory route and timeline/pagination.
- Extended `services/terminal_sessions.py` with `TerminalSessionHistorySummary` and `list_history_summaries()`, merging in-memory and persisted (`latest.json`) history metadata per workspace without returning transcript text.
- Extended `domain/schemas.py` and `app/routes/terminals.py` with additive overview `history` contract (`TerminalSessionHistorySummaryResponse`) and route mapping for `/terminals`.
- Updated `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so the operator page renders history metadata columns (`history session`, `history bytes`, `history truncated`) while preserving existing actions.
- Added red-green coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_monitor_routes.py`, and `tests/app/routes/test_api_routes.py` for merged inventory behavior, route payload mapping, and OpenAPI schema exposure.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q` (red then green)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`582 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`

# Session Plan (2026-03-16) - M8.5.7 Terminal History Timeline/Pagination

## Goal
- Continue from `M8.5.6` by adding a multi-snapshot terminal history timeline with pagination for each workspace, while keeping existing `latest.json` and `/sessions/current/history` contracts backward-compatible.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and latest terminal slices
- [x] Write focused `M8.5.7` design doc
- [x] Write focused `M8.5.7` implementation plan doc
- [x] Add failing tests for timeline pagination contract (service + route + openapi)
- [x] Implement backend multi-snapshot persistence/timeline read model with `latest.json` compatibility
- [x] Implement `GET /terminals/{group_id}/sessions/history` with `limit/offset` pagination
- [x] Add minimal frontend timeline query + `/terminals` on-demand timeline view
- [x] Run focused terminal/backend verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-7-terminal-history-timeline-pagination-design.md` and `docs/plans/2026-03-16-m8-5-7-terminal-history-timeline-pagination.md` to lock scope as “multi-snapshot timeline/pagination,” explicitly preserving `latest.json` and `/sessions/current/history` compatibility.
- Extended `services/terminal_sessions.py` with snapshot archiving under `data/terminal-history/<workspace>/snapshots/`, timeline dedupe merge (`in-memory + latest + archived`), and paginated `list_history_timeline_by_group(limit, offset)` read model.
- Extended `domain/schemas.py` and `app/routes/terminals.py` with `TerminalSessionHistoryTimelineResponse` and `GET /terminals/{group_id}/sessions/history` (query `limit/offset`) while reusing existing terminal role/workspace access/error mapping.
- Extended `web/src/api/client.ts`, `web/src/hooks/useApi.ts`, `web/src/pages/Terminals.tsx`, and `web/src/index.css` with on-demand timeline fetch, per-workspace `View Timeline` action, and simple `Previous/Next` pagination controls.
- Added red-green timeline coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for pagination ordering, latest+archive dedupe, malformed archive tolerance, route auth/404 behavior, and OpenAPI path/schema exposure.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q` (red then green)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`588 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`

# Session Plan (2026-03-16) - M8.5.8 Terminal History Filters/Detail

## Goal
- Continue from `M8.5.7` by adding server-side timeline filters plus per-session history detail, while keeping existing `latest.json` and `/sessions/current/history` contracts backward-compatible.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and latest terminal slices
- [x] Write focused `M8.5.8` design doc
- [x] Write focused `M8.5.8` implementation plan doc
- [x] Add failing service tests for timeline filters and detail lookup
- [x] Implement backend timeline filters/detail read model
- [x] Add failing route/OpenAPI tests for filter/detail surface
- [x] Implement timeline filter query params and history detail route/schema
- [x] Drive frontend RED by referencing new filter/detail contract
- [x] Implement typed client/hooks and `/terminals` filter/detail UI
- [x] Run focused terminal/backend verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-8-terminal-history-filters-detail-design.md` and `docs/plans/2026-03-16-m8-5-8-terminal-history-filters-detail.md` to lock scope as “timeline filters + session detail,” explicitly preserving `latest.json` and `/sessions/current/history` compatibility while deferring full-text search.
- Extended `services/terminal_sessions.py` with additive `status` / `owner_user_id` / `session_id_prefix` server-side filters on `list_history_timeline_by_group(...)`, shared merged snapshot lookup, and `get_history_snapshot_by_group(...)` so timeline and detail reuse the same dedupe behavior across `in-memory + latest + archived`.
- Extended `domain/schemas.py` and `app/routes/terminals.py` with additive `snapshot_at` summary data, `TerminalSessionHistoryDetailResponse`, `GET /terminals/{group_id}/sessions/history/{session_id}`, and timeline filter query params. Added a compatibility fallback so legacy overview fake summaries without `snapshot_at` still serialize safely.
- Extended `web/src/api/client.ts`, `web/src/hooks/useApi.ts`, and `web/src/pages/Terminals.tsx` with timeline filter options, history detail query support, `snapshot_at` rendering, and an in-page detail panel on `/terminals`.
- Added red-green coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for service-level filtering/detail lookup, route filter passthrough, detail `404` mapping, and OpenAPI filter/detail contracts.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py -q` (red then green)
  - `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q` (red then green)
  - `cd web && npm run build` (red then green after API/hook/page implementation)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`596 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`

# Session Plan (2026-03-17) - M8.5.11 Terminal Search Pagination/Cross-Session Match Navigation

## Goal
- Continue from the current `M8.5.8` main baseline by adding output search with paginated results and cross-session match navigation in terminal history detail, while preserving existing RBAC and history compatibility boundaries.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and `tasks/lessons.md`
- [x] Write focused `M8.5.11` design doc
- [x] Write focused `M8.5.11` implementation plan doc
- [x] Add failing backend tests for search service/route/openapi contracts
- [x] Implement backend search service model + schema + route
- [x] Drive frontend RED for search pagination/cross-session navigation
- [x] Implement frontend search panel and cross-session match navigation behavior
- [x] Run focused terminal regression suite
- [x] Run full backend/frontend verification plus diff hygiene
- [x] Update `docs/progress.md` and complete review notes
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-17-m8-5-11-terminal-search-pagination-cross-session-navigation-design.md` and `docs/plans/2026-03-17-m8-5-11-terminal-search-pagination-cross-session-navigation.md` to lock scope as “search-result pagination + cross-session match navigation,” while preserving `latest.json` and `/sessions/current/history` compatibility.
- Extended `services/terminal_sessions.py` with additive search read models (`TerminalSessionHistorySearchMatch`, `TerminalSessionHistorySearchPage`) plus `search_history_by_group(...)`, case-insensitive matching, snippet extraction, and deterministic result ordering/pagination.
- Extended `domain/schemas.py` and `app/routes/terminals.py` with additive search DTOs and `GET /terminals/{group_id}/sessions/history/search`, reusing existing terminal role/workspace access gates and error mapping.
- Extended terminal coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` with RED/GREEN assertions for search behavior, route contracts, and OpenAPI exposure.
- Extended frontend terminal search/navigation surface in `web/src/api/client.ts`, `web/src/hooks/useApi.ts`, and `web/src/pages/Terminals.tsx`: workspace output search panel, paginated search results, detail keyword highlighting, and previous/next traversal that can jump across matched sessions/pages.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q` (red then green)
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`602 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`

# Session Plan (2026-03-17) - M8.5.12 Terminal Snippet-to-Offset Deep Link

## Goal
- Continue post-`M8.5.11` by adding snippet-level deep links so operators can jump from a specific search snippet directly to its corresponding match location in terminal history detail, while preserving RBAC and history compatibility boundaries.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and current terminal search/detail slices
- [x] Write focused `M8.5.12` design doc
- [x] Write focused `M8.5.12` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing backend tests for snippet position metadata (service + route + OpenAPI)
- [x] Implement additive backend snippet metadata contracts (`match_index`, `match_offset`, `text`)
- [x] Implement frontend snippet click deep link to exact detail match
- [x] Run focused terminal regression suite
- [x] Run full backend/frontend verification plus diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-17-m8-5-12-terminal-snippet-offset-deeplink-design.md` and `docs/plans/2026-03-17-m8-5-12-terminal-snippet-offset-deeplink.md` to lock scope as “snippet-to-offset deep link,” while preserving `latest.json` and `/sessions/current/history` compatibility.
- Extended `services/terminal_sessions.py` with additive snippet metadata in search results: `snippet_matches` (`text`, `match_index`, `match_offset`) while keeping compatibility `snippets`.
- Extended `domain/schemas.py` and `app/routes/terminals.py` with `TerminalSessionHistorySearchSnippetResponse` and additive `snippet_matches` mapping for `GET /terminals/{group_id}/sessions/history/search`.
- Added red-green coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for service metadata, route payload contract, and OpenAPI schema exposure.
- Extended `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so search snippets are clickable and deep-link detail selection by `match_offset` with `match_index` fallback.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q` (red then green)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`602 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Commit: completed in this session with `feat(terminal): complete M8.5.12 snippet offset deep links`.

# Session Plan (2026-03-17) - M8.5.13 Terminal Search Filter Alignment

## Goal
- Continue post-`M8.5.12` by aligning terminal-history search with the existing timeline filters (`status`, `owner_user_id`, `session_id_prefix`) while preserving RBAC and history compatibility boundaries.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and current terminal search/timeline slices
- [x] Write focused `M8.5.13` design doc
- [x] Write focused `M8.5.13` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing backend tests for filtered search behavior (service + route + OpenAPI)
- [x] Implement additive backend search filter contracts
- [x] Drive frontend RED for filter-aligned search query state
- [x] Implement frontend search filter alignment on `/terminals`
- [x] Run focused terminal regression suite
- [x] Run full backend/frontend verification plus diff hygiene
- [ ] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [ ] Commit milestone changes with a detailed message

## Review
- Extended `services/terminal_sessions.py` so `search_history_by_group(...)` accepts additive `status`, `owner_user_id`, and `session_id_prefix` filters and reuses `_filter_history_snapshots(...)` before output matching; filtered-empty snapshot sets now preserve the intended `TerminalSessionNotFoundError` path.
- Extended `app/routes/terminals.py` so `GET /terminals/{group_id}/sessions/history/search` accepts the same three optional query parameters as the timeline route and forwards them without changing the response DTO shape.
- Added backend coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for independent service filter behavior, filtered-empty `404`, route pass-through, and OpenAPI parameter exposure.
- Extended `web/src/api/client.ts`, `web/src/hooks/useApi.ts`, and `web/src/pages/Terminals.tsx` so terminal-history search reuses the current timeline filter state, includes those filters in the query key/request params, and resets search pagination/navigation state when filters change.
- Verification executed:
  - `npm run build` in `web/` RED before frontend wiring: TypeScript rejected extra `status` property on `useTerminalHistorySearchQuery(...)` options.
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`606 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
