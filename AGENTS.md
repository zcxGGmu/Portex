# Repository Guidelines

## Mandatory Development Principles
- On every Codex restart, read `docs/TODO.md` and `docs/progress.md` before any planning or code changes.
- This project is a Python + OpenAI Agents SDK refactor of `https://github.com/riba2534/happyclaw.git`.
- Implement work strictly according to `docs/TODO.md`.
- Record progress and handoff notes in `docs/progress.md`.
- After completing each phase task, commit immediately with a detailed commit message.
- For every completed feature, run feature-level tests and full-flow regression checks to ensure no impact on other features.

## Project Structure & Module Organization
- `portex/` holds core library code; the event contract model is in `portex/contracts/events.py`.
- `pocs/` contains runnable proofs of concept split by concern: `streaming/`, `events/`, and `tools/`.
- `tests/` mirrors runtime modules (`tests/portex/contracts/`, `tests/pocs/...`).
- `docs/` stores planning and research material.

## Agent Startup Context
- At the start of every Codex session, read `docs/progress.md` and `docs/TODO.md` before planning or editing code.
- Quick check: `sed -n '1,220p' docs/progress.md && sed -n '1,220p' docs/TODO.md`.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate env.
- `pip install -e ".[dev]"`: install runtime + dev dependencies.
- `pytest -q`: run all tests.
- `pytest tests/pocs/streaming/test_main.py -q`: run one test module.
- `ruff check .`: lint.
- `python -m pocs.streaming.main --dry-run`: run streaming PoC locally.
- `python -m pocs.tools.main --dry-run --sample-file README.md`: run tools PoC locally.
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

## Commit & Pull Request Guidelines
- Follow `type(scope): summary`.
- Preferred types: `feat`, `fix`, `test`, `docs`, `chore`, `build`.
- Keep commits single-purpose and easy to review.
- PRs should include problem statement, key changes, affected paths, and test commands run.
