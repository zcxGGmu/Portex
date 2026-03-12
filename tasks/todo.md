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

- [ ] `M7.2.1` Replace `services/group_queue.py` placeholder logic with a real per-group queue and lifecycle coordinator.
- [ ] `M7.2.2` Connect the existing host/container execution slices to the actual runtime trigger flow instead of leaving them as mostly isolated adapters.
- [ ] `M7.2.3` Define the runtime selection contract so Web chat, IM chat, scheduled tasks, and future sub-session flows all resolve through one execution-plane rule set.
- [ ] `M7.2.4` Introduce session/workspace lifecycle state so one running workspace can accept follow-up messages instead of always behaving like a fresh stateless trigger.
- [ ] `M7.2.5` Implement safe cancellation and timeout handling across the real queue + executor boundary, not only the direct `OpenAIAgentsRuntime` path.
- [ ] `M7.2.6` Add execution status and recovery signals so queued/running/failed states are observable outside the current direct WebSocket stream.
- [ ] `M7.2.7` Add focused tests for queue ordering, executor selection, follow-up injection, cancellation, timeout, and recovery behavior.

#### `M7.3` Workspace And Group Model Parity

- [ ] `M7.3.1` Replace the current demo `group-demo` group list with a real persisted group/workspace listing model.
- [ ] `M7.3.2` Define the Portex equivalent of HappyClaw’s main workspace / bound chat / per-user home workspace model.
- [ ] `M7.3.3` Add explicit workspace ownership and binding metadata so IM chats can be attached to a user’s main workspace or future sub-workspaces.
- [ ] `M7.3.4` Extend the current group/member model so it can represent real working sessions instead of only the minimal membership CRUD boundary.
- [ ] `M7.3.5` Decide whether Portex will support sub-agent / multi-session tabs like HappyClaw, and if yes, add the minimal data model needed for that.
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
