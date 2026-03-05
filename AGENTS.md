# Repository Guidelines

## Project Structure & Module Organization
- This repository is a Python + OpenAI Agents SDK refactor of `/home/zq/work-space/repo/ai-projs/agents/happyclaw`.
- `portex/` holds core library code; the event contract model is in `portex/contracts/events.py`.
- `pocs/` contains runnable proofs of concept split by concern: `streaming/`, `events/`, and `tools/`.
- `tests/` mirrors runtime modules (`tests/portex/contracts/`, `tests/pocs/...`).
- `docs/` stores planning and research material; treat it as reference, not production runtime code.
- Scaffolded directories (`app/`, `services/`, `infra/`, `web/`) are reserved for future implementation and should stay feature-organized.

## Agent Startup Context
- At the start of every Codex session, read `docs/cc-codex/v1/progress.md` before planning or editing code.
- Use it as the authoritative handoff state (milestone, completed work, test baseline, and workspace caveats).
- Quick check: `sed -n '1,220p' docs/cc-codex/v1/progress.md`, then align with `docs/cc-codex/v1/TODO.md`.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate a local Python environment.
- `pip install -e ".[dev]"`: install the package plus development tools from `pyproject.toml`.
- `pytest -q`: run the full test suite (default options are defined in `pyproject.toml`).
- `pytest tests/pocs/streaming/test_main.py -q`: run a focused test module while iterating.
- `ruff check .`: run lint checks before opening a PR.
- `python -m pocs.streaming.main --dry-run`: validate streaming PoC output without API calls.
- `python -m pocs.tools.main --dry-run --sample-file README.md`: validate tool-calling PoC locally.

## Coding Style & Naming Conventions
- Target Python `>=3.11`, use 4-space indentation, and add explicit type hints for public functions.
- Follow PEP 8 naming: `snake_case` for modules/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep mappers deterministic and branch-explicit (see `pocs/events/mapper.py` for the preferred pattern).
- Prefer small, single-purpose modules and avoid unnecessary cross-imports across PoCs.

## Testing Guidelines
- Use `pytest`; introduce `pytest-asyncio` markers only when async behavior is tested.
- Name files `test_*.py` and test functions `test_*`.
- Mirror source layout in tests (example: `pocs/tools/main.py` -> `tests/pocs/tools/test_tools_main.py`).
- Cover both happy paths and unknown/edge event handling for event mapping changes.

## Commit & Pull Request Guidelines
- Follow the repository’s commit style: `type(scope): summary` (examples in history: `feat(m0.4.2): ...`, `docs: ...`).
- Preferred types: `feat`, `fix`, `test`, `docs`, `chore`, `build`.
- Keep commits single-purpose and easy to review.
- PRs should include a concise problem statement, key changes, affected paths, test commands run, and relevant output/log snippets for behavior changes.
