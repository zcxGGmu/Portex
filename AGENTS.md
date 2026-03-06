# Repository Guidelines

## Mandatory Development Principles
- On every Codex restart, read `docs/TODO.md` and `docs/progress.md` before any planning or code changes.
- This project is a Python + OpenAI Agents SDK refactor of `https://github.com/riba2534/happyclaw.git`.
- Local reference implementation path: `/home/zq/work-space/repo/ai-projs/agents/happyclaw`.
- Implement work strictly according to `docs/TODO.md`.
- Record progress and handoff notes in `docs/progress.md`.
- After completing each phase task, commit immediately with a detailed commit message.
- For every completed feature, run feature-level tests and full-flow regression checks to ensure no impact on other features.
- Keep `docs/progress.md` concise and restart-oriented: current phase, latest verification evidence, immediate next task.
- Never commit secrets; if testing a real provider, pass credentials through environment variables only.

## Current Baseline Snapshot (2026-03-07)
- `M2` is complete (`M2.1` ~ `M2.6.1`).
- `M3` progress: `M3.1` ~ `M3.3` are complete.
- Current starting point is `M3.4.1` (container startup).
- If unsure after restart, treat `docs/progress.md` as source of truth and continue from the `当前起点` / `下一位 Codex 直接执行` entries.

## Project Structure & Module Organization
- Backend runtime lives in `app/`, `domain/`, `infra/`, and `services/`.
- Core event contract PoC baseline remains in `portex/contracts/events.py` and `pocs/`.
- Frontend app lives in `web/` (Vite + React + TypeScript).
- Tests are split by concern (`tests/app/`, `tests/services/`, `tests/unit/`, `tests/pocs/`, `tests/portex/`).
- `docs/` stores planning/progress and is the handoff source of truth.

## Agent Startup Context
- At the start of every Codex session, read `docs/progress.md` and `docs/TODO.md` before planning or editing code.
- Quick check: `sed -n '1,220p' docs/progress.md && sed -n '1,220p' docs/TODO.md`.
- If resuming backend work, also skim `app/main.py`, `app/middleware/auth.py`.
- If resuming frontend work, also skim `web/src/App.tsx`, `web/src/stores/auth.ts`.
- If resuming after `M2`, also skim `app/routes/websocket.py`, `web/src/components/chat/ChatPanel.tsx`, and `services/agent_trigger.py` because the current run/cancel flow is split across those files.
- If resuming after `M3.3`, also skim `infra/exec/docker.py`, `infra/exec/security.py`, `container/agent-runner/src/runner.py`, and `container/agent-runner/src/types.py` because `M3.4` container lifecycle work builds directly on those files.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate env.
- `pip install -e ".[dev]"`: install runtime + dev dependencies.
- `.venv/bin/pytest -q`: run all backend tests (preferred, avoid system Python mismatch).
- `.venv/bin/pytest tests/unit/ -v`: run M1 acceptance unit test command.
- `.venv/bin/pytest tests/app/routes/test_websocket_routes.py -q`: run current WS send/cancel acceptance-focused backend test.
- `.venv/bin/pytest tests/services/test_message_service.py tests/services/test_agent_trigger.py -q`: run message + runtime pipeline feature tests.
- `.venv/bin/pytest tests/container/agent_runner -q`: run current Agent Runner containerization tests.
- `.venv/bin/pytest tests/infra/exec/test_docker.py tests/infra/exec/test_security.py -q`: run current container mount / execution safety tests.
- `.venv/bin/ruff check .`: lint.
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
