# Repository Guidelines

## Mandatory Development Principles
- On every Codex restart, read `docs/TODO.md` and `docs/progress.md` before any planning or code changes.
- This project is a Python + OpenAI Agents SDK refactor of `https://github.com/riba2534/happyclaw.git`.
- Implement work strictly according to `docs/TODO.md`.
- Record progress and handoff notes in `docs/progress.md`.
- After completing each phase task, commit immediately with a detailed commit message.
- For every completed feature, run feature-level tests and full-flow regression checks to ensure no impact on other features.
- Keep `docs/progress.md` concise and restart-oriented: current phase, latest verification evidence, immediate next task.

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

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate env.
- `pip install -e ".[dev]"`: install runtime + dev dependencies.
- `.venv/bin/pytest -q`: run all backend tests (preferred, avoid system Python mismatch).
- `.venv/bin/pytest tests/unit/ -v`: run M1 acceptance unit test command.
- `.venv/bin/pytest tests/pocs/streaming/test_main.py -q`: run one test module.
- `.venv/bin/ruff check .`: lint.
- `python -m pocs.streaming.main --dry-run`: run streaming PoC locally.
- `python -m pocs.tools.main --dry-run --sample-file README.md`: run tools PoC locally.
- `cd web && npm run lint`: frontend lint.
- `cd web && npm run build`: frontend production build.
- `scripts/commit_push.sh -m "docs: update AGENTS" -d "Explain contributor workflow"`: stage all changes, commit, and push current branch.

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

## Commit & Pull Request Guidelines
- Follow `type(scope): summary`.
- Preferred types: `feat`, `fix`, `test`, `docs`, `chore`, `build`.
- Keep commits single-purpose and easy to review.
- PRs should include problem statement, key changes, affected paths, and test commands run.
