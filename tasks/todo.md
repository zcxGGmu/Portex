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
