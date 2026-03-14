# Repository Guidelines

## Mandatory Development Principles
- On every Codex restart, read `docs/TODO.md` and `docs/progress.md` before any planning or code changes.
- This project is a Python + OpenAI Agents SDK refactor of `https://github.com/riba2534/happyclaw.git`.
- Local reference implementation path: `/home/zcxggmu/workspace/hello-projs/agents/happyclaw`.
- Implement work strictly according to `docs/TODO.md`.
- Record progress and handoff notes in `docs/progress.md`.
- After completing each phase task, commit immediately with a detailed commit message.
- For every completed feature, run feature-level tests and full-flow regression checks to ensure no impact on other features.
- Keep `docs/progress.md` concise and restart-oriented: current phase, latest verification evidence, immediate next task.
- Never commit secrets; if testing a real provider, pass credentials through environment variables only.

## Current Baseline Snapshot (2026-03-14)
- `M2` is complete (`M2.1` ~ `M2.6.1`).
- `M3` is complete (`M3.1` ~ `M3.6`).
- `M4` is complete (`M4.1` ~ `M4.5`).
- `M5` is complete (`M5.1` ~ `M5.4`).
- `M6.1.1` is complete (Unit tests).
- `M6.1.2` is complete (Integration tests).
- `M6.1.3` is complete (CI workflow setup).
- `M6.2.1` is complete (Project README).
- `M6.2.2` is complete (API docs).
- `M6.2.3` is complete (Deployment docs).
- `M6.3.1` is complete (Database indexes).
- `M6.3.2` is complete (Connection pool).
- `M6.3.3` is complete (User memory cache).
- `M6.4.1` is complete (Security scanning).
- `M6.4.2` is complete (Dependency audit).
- `M6.4.3` is complete (Security headers).
- `M6.5.1` is complete (Version planning).
- `M6.5.2` is complete (Release tag creation).
- `M6.5.3` is complete (Release artifact building).
- `M6` is complete (`M6.1.1` ~ `M6.5.3`).
- `M7.1` is complete in the parity backlog (main runtime chain parity).
- `M7.2` is complete in the parity backlog (`M7.2.1` ~ `M7.2.7`), including coordinator/policy core, backend adapters, scheduled-task + caller-facing mode inputs, workspace/session lifecycle, cancel-timeout boundary hardening, status/recovery signaling, and focused execution-plane parity coverage.
- `M7.3.1` is complete in the parity backlog (persisted group/workspace listing).
- `M7.3.2` is complete in the parity backlog (workspace topology / per-user home workspace parity).
- `M7.3.3` is complete in the parity backlog (IM workspace binding metadata parity).
- `M7.3.4` is complete in the parity backlog (workspace membership / working-session parity).
- `M7.3.5` is complete in the parity backlog (minimal persistent conversation slots under a workspace).
- `M7.3.5` implementation is split across commits `1e312f6`, `73b1bdd`, `be03ddd`, `f7a083a`, and `5ee93e6`.
- First release tag is `v1.0.0`; package/runtime version intentionally remains `0.1.0` until a later explicit sync decision.
- The repository-root release-image build path is now fully verified on the current host. Repro path: export `PATH="$HOME/bin:$PATH"` and `DOCKER_HOST=unix:///run/user/1000/docker.sock`, then run `.venv/bin/python scripts/build_docker.py --tag portex:v1.0.0` and `docker image inspect portex:v1.0.0 --format '{{.Id}}'`.
- Proposed post-`M6` parity milestones `M7.1` ~ `M7.6` now live in `tasks/todo.md`, but `docs/TODO.md` remains the formal source of truth and still stops at `M6.5.3`.
- `M7.1` planning docs now exist (`docs/plans/2026-03-11-m7-1-main-runtime-chain-parity-design.md`, `docs/plans/2026-03-11-m7-1-main-runtime-chain-parity.md`) and were refined by `docs/plans/2026-03-12-m7-1-runtime-dispatch-refinement-design.md` plus `docs/plans/2026-03-12-m7-1-runtime-dispatch-refinement.md` before implementation.
- The formal `M6` roadmap is exhausted. If the user continues parity work, the next real entrypoint is `M7.3.6`, not `M7.1`.
- Likely local-only file in the worktree: `data/portex.db`. Do not stage it accidentally.
- If unsure after restart, treat `docs/progress.md` as source of truth and continue from the `当前起点` / `下一位 Codex 直接执行` entries.

## Project Structure & Module Organization
- Backend runtime lives in `app/`, `domain/`, `infra/`, and `services/`.
- Core event contract PoC baseline remains in `portex/contracts/events.py` and `pocs/`.
- Frontend app lives in `web/` (Vite + React + TypeScript).
- Tests are split by concern (`tests/app/`, `tests/domain/`, `tests/services/`, `tests/unit/`, `tests/pocs/`, `tests/portex/`).
- `docs/` stores planning/progress and is the handoff source of truth.

## Agent Startup Context
- At the start of every Codex session, read `docs/progress.md` and `docs/TODO.md` before planning or editing code.
- Quick check: `sed -n '1,220p' docs/progress.md && sed -n '1,220p' docs/TODO.md`.
- If resuming backend work, also skim `app/main.py`, `app/middleware/auth.py`.
- If resuming frontend work, also skim `web/src/App.tsx`, `web/src/stores/auth.ts`.
- If resuming after `M2`, also skim `app/routes/websocket.py`, `web/src/components/chat/ChatPanel.tsx`, and `services/agent_trigger.py` because the current run/cancel flow is split across those files.
- If resuming after `M3.3`, also skim `infra/exec/docker.py`, `infra/exec/security.py`, `container/agent-runner/src/runner.py`, and `container/agent-runner/src/types.py` because `M3.4` container lifecycle work builds directly on those files.
- If resuming after `M4.1.3`, also skim `app/routes/auth.py`, `app/routes/users.py`, `services/auth.py`, `domain/models/invite_code.py`, and `domain/schemas.py` because `M4.2` RBAC work now builds directly on the current in-memory user + invite contracts.
- If resuming after `M4.2.1`, also skim `domain/permissions.py` and `tests/domain/test_permissions.py` because `M4.2.2` must reuse the static role template contract instead of re-defining permission rules elsewhere.
- If resuming after `M4.3.1`, also skim `services/scheduler.py`, `app/routes/tasks.py`, `domain/models/task.py`, `domain/schemas.py`, and `tests/services/test_scheduler.py` because `M4.3.2` task CRUD work now builds directly on the injected-executor scheduler core and the current `ScheduledTask` contract.
- If resuming after `M4.4.4`, also skim `services/memory.py`, `container/agent-runner/src/tools/memory.py`, `tests/services/test_memory_service.py`, and `tests/container/agent_runner/test_memory_tools.py` because memory now spans both service-side files and runner-side tool wrappers.
- If resuming after `M5.1.1`, also skim `infra/im/feishu.py`, `tests/infra/im/test_feishu.py`, and `infra/im/base.py` because Feishu auth, signature verification, decrypt helpers, event parsing, and send-message logic now all live in that slice.
- If resuming after `M5.3.1`, also skim `domain/schemas.py`, `infra/im/feishu.py`, `infra/im/telegram.py`, `tests/domain/test_schemas.py`, `docs/plans/2026-03-09-m5-3-2-message-routing-design.md`, and `docs/plans/2026-03-09-m5-3-2-message-routing.md` because `M5.3.2` now builds directly on the `UnifiedMessage` DTO, the current `chat_jid` semantics, and the already-written routing design/plan docs.
- If resuming after `M6.1.2`, also skim `tests/integration/test_api.py` and `tests/integration/test_websocket.py` because the current integration boundary now spans both the HTTP baseline and the fake-runtime-backed WebSocket flow.
- If resuming after `M6.1.3`, also skim `.github/workflows/test.yml`, `pyproject.toml`, and `web/package-lock.json` because CI now depends on `pytest-cov` plus the current npm lockfile and verified frontend commands.
- If resuming after `M6.2.1`, also skim `README.md` because the root project entrypoint now carries the current quick-start, command set, and boundary wording that `M6.2.2` should stay aligned with.
- If resuming after `M6.3.3`, also skim `services/memory.py`, `tests/services/test_memory_service.py`, `docs/plans/2026-03-10-m6-3-3-user-memory-cache-design.md`, and `docs/plans/2026-03-10-m6-3-3-user-memory-cache.md` because the current minimal cache boundary now lives in the memory service and the next phase must not overread it as a general cache layer.
- If resuming after `M6.4.1`, also skim `scripts/security_scan.py`, `tests/scripts/test_security_scan.py`, and `.github/workflows/test.yml` because `M6.4.2` should build on the current repo-local static scan chain instead of replacing it accidentally.
- If resuming after `M6.4.2`, also skim `scripts/dependency_audit.py`, `tests/scripts/test_dependency_audit.py`, `pyproject.toml`, and `.github/workflows/test.yml` because `M6.4.3` should preserve both the current `pip-audit` chain and the explicit `ecdsa/CVE-2024-23342` ignore rationale.
- If resuming after `M6.4.3`, also skim `app/middleware/security.py`, `app/main.py`, `tests/app/routes/test_api_routes.py`, and `tests/integration/test_api.py` because the current HTTP security-header contract now lives in those files and later phases should not regress it accidentally.
- If resuming after `M6.5.3`, also skim `docs/plans/2026-03-11-m6-5-1-version-planning-design.md`, `docs/plans/2026-03-11-m6-5-1-version-planning.md`, `docs/plans/2026-03-11-m6-5-2-release-tag-design.md`, `docs/plans/2026-03-11-m6-5-2-release-tag.md`, `docs/plans/2026-03-11-m6-5-3-release-artifacts-design.md`, `docs/plans/2026-03-11-m6-5-3-release-artifacts.md`, `Dockerfile`, `.dockerignore`, `scripts/build_docker.py`, `Makefile`, `docs/deployment.md`, `tests/scripts/test_build_docker.py`, and `tests/container/agent_runner/test_container_files.py` because the first release tag is `v1.0.0`, the repository-root image build path is verified, and future work should not accidentally regress the release-artifact contract.
- If you need to reproduce the current host-side Docker verification, check `docs/progress.md` first and export `PATH="$HOME/bin:$PATH"` plus `DOCKER_HOST=unix:///run/user/1000/docker.sock` before running release-image commands.
- If resuming after `M7.1`, also skim `app/routes/im.py`, `app/routes/messages.py`, `services/message_dispatch.py`, `services/message_service.py`, `tests/app/routes/test_im_routes.py`, `tests/app/routes/test_message_routes.py`, `tests/integration/test_message_flow.py`, `docs/plans/2026-03-12-m7-1-runtime-dispatch-refinement-design.md`, and `docs/plans/2026-03-12-m7-1-runtime-dispatch-refinement.md` because `M7.1` now spans real IM ingress, real `/messages` dispatch, structured runtime results, Telegram outbound text sending, and minimal message-correlation metadata.
- If resuming after `M7.2`, also skim `services/workspace_lifecycle.py`, `services/execution_coordinator.py`, `services/execution_policy.py`, `services/execution_backends.py`, `services/execution_runtime.py`, `services/group_queue.py`, `infra/runtime/openai.py`, `infra/exec/process.py`, `app/routes/executions.py`, `tests/services/test_workspace_lifecycle.py`, `tests/services/test_execution_coordinator.py`, `tests/services/test_execution_policy.py`, `tests/services/test_execution_backends.py`, `tests/app/routes/test_execution_routes.py`, `tests/app/routes/test_websocket_routes.py`, `tests/infra/runtime/test_openai.py`, `tests/infra/exec/test_process.py`, `docs/plans/2026-03-12-m7-2-execution-plane-parity-design.md`, `docs/plans/2026-03-12-m7-2-execution-plane-parity.md`, `docs/plans/2026-03-12-m7-2-2-execution-backend-adapters-design.md`, `docs/plans/2026-03-12-m7-2-2-execution-backend-adapters.md`, `docs/plans/2026-03-13-m7-2-3-scheduled-tasks-and-mode-inputs-design.md`, `docs/plans/2026-03-13-m7-2-4-session-workspace-lifecycle-design.md`, `docs/plans/2026-03-13-m7-2-5-cancel-timeout-boundary-design.md`, `docs/plans/2026-03-13-m7-2-6-status-recovery-signaling-design.md`, and `docs/plans/2026-03-13-m7-2-7-focused-tests-design.md` because the next real step is `M7.3.6` on top of the now-complete execution plane plus the completed `M7.3.1` ~ `M7.3.5` workspace, membership, IM binding, and conversation-slot work.
- If resuming after `M7.3.2`, also skim `services/group_registry.py`, `domain/models/group.py`, `scripts/init_db.py`, `app/routes/auth.py`, `app/routes/groups.py`, `app/routes/messages.py`, `app/routes/im.py`, `services/message_dispatch.py`, `tests/services/test_group_registry.py`, `tests/domain/models/test_models.py`, `tests/scripts/test_init_db.py`, `tests/app/routes/test_api_routes.py`, `tests/app/routes/test_message_routes.py`, `tests/app/routes/test_im_routes.py`, `docs/plans/2026-03-13-m7-3-1-persisted-group-listing-design.md`, `docs/plans/2026-03-13-m7-3-1-persisted-group-listing.md`, `docs/plans/2026-03-13-m7-3-2-workspace-topology-design.md`, `docs/plans/2026-03-13-m7-3-2-workspace-topology.md`, `docs/plans/2026-03-14-m7-3-3-im-workspace-binding-design.md`, and `docs/plans/2026-03-14-m7-3-3-im-workspace-binding.md` because `M7.3.3` builds directly on the canonical `is_home` / `web:*` workspace topology and adds binding-aware IM workspace resolution.
- If resuming after `M7.3.3`, also skim `domain/models/group_member.py`, `services/group_member_service.py`, `services/group_registry.py`, `scripts/init_db.py`, `app/routes/groups.py`, `app/routes/messages.py`, `app/routes/executions.py`, `tests/services/test_group_member_service.py`, `tests/services/test_group_registry.py`, `tests/app/routes/test_api_routes.py`, `tests/app/routes/test_message_routes.py`, `tests/app/routes/test_execution_routes.py`, `docs/plans/2026-03-14-m7-3-4-workspace-membership-design.md`, and `docs/plans/2026-03-14-m7-3-4-workspace-membership.md` because `M7.3.4` makes `group_members` the workspace membership source of truth and wires that boundary into canonical web workspace access control.
- If resuming after `M7.3.4`, also skim `services/workspace_lifecycle.py`, `services/execution_coordinator.py`, `services/message_dispatch.py`, `app/routes/im.py`, `app/routes/messages.py`, `app/routes/executions.py`, `tests/services/test_execution_coordinator.py`, `tests/app/routes/test_message_routes.py`, `tests/app/routes/test_execution_routes.py`, `docs/plans/2026-03-14-m7-3-5-conversation-slots-design.md`, and `docs/plans/2026-03-14-m7-3-5-conversation-slots.md` because `M7.3.5` now starts from an approved minimal conversation-slots design that must layer on the current workspace/session/message boundaries without expanding workspace-level permissions or IM binding scope.
- If resuming after `M7.3.5`, also skim `domain/models/conversation_slot.py`, `services/conversation_slot_service.py`, `services/workspace_lifecycle.py`, `services/execution_coordinator.py`, `services/message_service.py`, `services/message_dispatch.py`, `app/routes/im.py`, `app/routes/messages.py`, `app/routes/executions.py`, `tests/services/test_conversation_slot_service.py`, `tests/services/test_workspace_lifecycle.py`, `tests/services/test_execution_coordinator.py`, `tests/services/test_message_service.py`, `tests/services/test_message_dispatch.py`, `tests/app/routes/test_message_routes.py`, `tests/app/routes/test_execution_routes.py`, `tests/app/routes/test_im_routes.py`, `docs/plans/2026-03-14-m7-3-5-conversation-slots-design.md`, and `docs/plans/2026-03-14-m7-3-5-conversation-slots.md` because `M7.3.6` now starts from the completed conversation-slot model and should only add management/API surface on top of the existing workspace/session/message boundaries.
- If the user explicitly chooses to continue parity work past `M7.1`, resume from `M7.3.6` after skimming `services/workspace_lifecycle.py`, `services/execution_coordinator.py`, `services/execution_policy.py`, `services/execution_backends.py`, `services/execution_runtime.py`, `services/group_queue.py`, `infra/runtime/openai.py`, `infra/exec/process.py`, `app/routes/executions.py`, `services/group_registry.py`, `services/group_member_service.py`, `services/conversation_slot_service.py`, `domain/models/group.py`, `domain/models/group_member.py`, `domain/models/conversation_slot.py`, `scripts/init_db.py`, `app/routes/auth.py`, `app/routes/groups.py`, `app/routes/im.py`, `app/routes/messages.py`, `tests/services/test_workspace_lifecycle.py`, `tests/services/test_execution_coordinator.py`, `tests/services/test_execution_policy.py`, `tests/services/test_execution_backends.py`, `tests/services/test_group_registry.py`, `tests/services/test_group_member_service.py`, `tests/services/test_conversation_slot_service.py`, `tests/app/routes/test_execution_routes.py`, `tests/app/routes/test_websocket_routes.py`, `tests/app/routes/test_im_routes.py`, `tests/app/routes/test_api_routes.py`, `tests/app/routes/test_message_routes.py`, `tests/infra/runtime/test_openai.py`, `tests/infra/exec/test_process.py`, `tests/domain/models/test_models.py`, `tests/scripts/test_init_db.py`, `docs/plans/2026-03-12-m7-2-execution-plane-parity-design.md`, `docs/plans/2026-03-12-m7-2-2-execution-backend-adapters-design.md`, `docs/plans/2026-03-13-m7-2-3-scheduled-tasks-and-mode-inputs-design.md`, `docs/plans/2026-03-13-m7-2-4-session-workspace-lifecycle-design.md`, `docs/plans/2026-03-13-m7-2-5-cancel-timeout-boundary-design.md`, `docs/plans/2026-03-13-m7-2-6-status-recovery-signaling-design.md`, `docs/plans/2026-03-13-m7-2-7-focused-tests-design.md`, `docs/plans/2026-03-13-m7-3-1-persisted-group-listing-design.md`, `docs/plans/2026-03-13-m7-3-1-persisted-group-listing.md`, `docs/plans/2026-03-13-m7-3-2-workspace-topology-design.md`, `docs/plans/2026-03-13-m7-3-2-workspace-topology.md`, `docs/plans/2026-03-14-m7-3-3-im-workspace-binding-design.md`, `docs/plans/2026-03-14-m7-3-4-workspace-membership-design.md`, and `docs/plans/2026-03-14-m7-3-5-conversation-slots-design.md`.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate env.
- `pip install -e ".[dev]"`: install runtime + dev dependencies.
- `.venv/bin/pytest -q`: run all backend tests (preferred, avoid system Python mismatch).
- `.venv/bin/pytest tests/unit/ -v`: run M1 acceptance unit test command.
- `.venv/bin/pytest tests/app/routes/test_websocket_routes.py -q`: run current WS send/cancel acceptance-focused backend test.
- `.venv/bin/pytest tests/services/test_message_service.py tests/services/test_agent_trigger.py -q`: run message + runtime pipeline feature tests.
- `.venv/bin/pytest tests/services/test_memory_service.py -q`: run the current memory-service acceptance-focused suite.
- `.venv/bin/pytest -o addopts='' tests/services/test_scheduler.py -q`: run current scheduler-focused backend test.
- `.venv/bin/pytest -o addopts='' tests/domain/models/test_models.py tests/services/test_auth_service.py tests/app/routes/test_api_routes.py -q`: run current user / auth / invite acceptance-focused backend tests.
- `.venv/bin/pytest -o addopts='' tests/domain/test_permissions.py -q`: run current RBAC permission-template focused test.
- `.venv/bin/pytest tests/container/agent_runner -q`: run current Agent Runner containerization tests.
- `.venv/bin/pytest tests/infra/exec/test_docker.py tests/infra/exec/test_security.py -q`: run current container mount / execution safety tests.
- `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py -q`: run current Feishu client acceptance-focused tests.
- `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`: run current IM client acceptance-focused tests.
- `.venv/bin/pytest -o addopts='' tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`: run current unified-message + IM acceptance-focused tests.
- `.venv/bin/pytest -o addopts='' tests/integration/test_api.py tests/integration/test_websocket.py -q`: run the current integration-focused API + WebSocket suite.
- `.venv/bin/pytest -o addopts='' tests/services/test_workspace_lifecycle.py tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/infra/runtime/test_openai.py tests/infra/exec/test_process.py -q`: run the current `M7.2` lifecycle/coordinator/backend/process focused suite.
- `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py tests/app/routes/test_websocket_routes.py -q`: run the current `M7.2.6` + `M7.2.7` status/recovery + timeout focused suite.
- `.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py tests/services/test_group_member_service.py tests/services/test_group_registry.py tests/app/routes/test_api_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_execution_routes.py -q`: run the current `M7.3.4` workspace membership focused suite.
- `.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py tests/services/test_conversation_slot_service.py tests/services/test_group_registry.py tests/services/test_workspace_lifecycle.py tests/services/test_execution_coordinator.py tests/services/test_message_service.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py tests/app/routes/test_execution_routes.py tests/app/routes/test_im_routes.py -q`: run the current `M7.3.5` conversation-slot focused suite.
- `.venv/bin/pytest tests/ -v --cov`: run the current backend CI-equivalent test command with coverage.
- `.venv/bin/python scripts/security_scan.py`: run the repository-local backend security scan (Ruff `S` rules on runtime code).
- `.venv/bin/python scripts/dependency_audit.py`: run the repository-local backend dependency audit (`pip-audit` on the Python project).
- `.venv/bin/python scripts/build_docker.py --tag portex:v1.0.0`: run the repository-root release-image build entrypoint. On the current host, export `PATH="$HOME/bin:$PATH"` and `DOCKER_HOST=unix:///run/user/1000/docker.sock` to reuse the verified rootless Docker daemon.
- `.venv/bin/ruff check .`: lint.
- `cd web && npm ci`: install frontend dependencies from the committed lockfile.
- `cd web && npm run lint`: frontend lint.
- `cd web && npm run build`: frontend production build.
- `OPENAI_API_KEY=... OPENAI_BASE_URL=... OPENAI_DEFAULT_MODEL=gpt-5.1 OPENAI_AGENTS_DISABLE_TRACING=1 .venv/bin/python pocs/streaming/main.py --input "请只回复：测试通过"`: real provider streaming sanity check for OpenAI-compatible endpoints.
- `scripts/commit_push.sh -m "docs: update AGENTS" -d "Explain contributor workflow"`: stage all changes, commit, and push current branch.

## OpenAI-Compatible Provider Notes
- The local environment often does not have `OPENAI_API_KEY`; when absent, prefer dry-run PoCs or fake-runtime acceptance harnesses.
- For the tested compatible provider setup, use:
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL`
  - `OPENAI_DEFAULT_MODEL=gpt-5.1`
- Do not rely on the Agents SDK default model under compatible providers unless it has been explicitly verified; the SDK default is `gpt-4.1`, which was not available in the latest provider test.

## Chat Shortcut Convention
- Use `/commit <subject>` to ask Codex to run a commit-and-push flow for the current branch.
- Optional description form: `/commit <subject> --desc <description>`.
- Codex maps this shortcut to `scripts/commit_push.sh` for consistent behavior.
- Use `/sync` to ask Codex to refresh `docs/progress.md` and `AGENTS.md` with the latest restart-oriented project state, run minimal diff hygiene, and create a local commit for that handoff update.
- `/sync` is a chat workflow shortcut, not a shell command or repo script alias.
- Commit subject should follow `type(scope): summary` when possible.

## Coding Style & Naming Conventions
- Target Python `>=3.11`, use 4-space indentation, and add explicit type hints for public functions.
- Follow PEP 8 naming: `snake_case` for modules/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep mappers deterministic and branch-explicit (see `pocs/events/mapper.py` for the preferred pattern).
- Prefer small, single-purpose modules.

## Testing Guidelines
- Use `pytest`; introduce `pytest-asyncio` markers only when async behavior is tested.
- Name files `test_*.py` and test functions `test_*`.
- Mirror source layout in tests (example: `pocs/tools/main.py` -> `tests/pocs/tools/test_tools_main.py`).
- When a TODO-defined acceptance command targets a test directory, ensure at least one meaningful test exists in that directory.
- Before claiming a phase is complete, pair focused feature tests with full regression and, when relevant, frontend lint/build.

## Commit & Pull Request Guidelines
- Follow `type(scope): summary`.
- Preferred types: `feat`, `fix`, `test`, `docs`, `chore`, `build`.
- Keep commits single-purpose and easy to review.
- PRs should include problem statement, key changes, affected paths, and test commands run.
