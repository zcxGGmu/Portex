# Session Plan (2026-03-06) - M2.5.2

## Goal
- Continue from `docs/progress.md` by completing `M2.5.2` timeout control with millisecond semantics, deterministic timeout events, and full verification.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and `docs/PORTEX_PLAN.md`
- [x] Confirm timeout unit and event design through multi-agent analysis
- [x] Write `M2.5.2` design doc and implementation plan
- [x] Add failing timeout tests in `tests/services/test_agent_trigger.py`
- [x] Implement timeout orchestration in `services/agent_trigger.py`
- [x] Align timeout event contracts used by backend/frontend types
- [x] Run focused tests and full regression
- [x] Update `docs/TODO.md` and `docs/progress.md`
- [x] Append review notes below
- [x] Commit changes with a detailed message

## Review
- Multi-agent design review confirmed `timeout_ms` should keep HappyClaw-compatible millisecond semantics and should emit a dedicated `run.timeout` event.
- TDD RED 1: `.venv/bin/pytest tests/portex/contracts/test_events.py -q` -> failed on missing `EventType.RUN_TIMEOUT`.
- TDD GREEN 1: `.venv/bin/pytest tests/portex/contracts/test_events.py -q` -> `2 passed`.
- TDD RED 2: `.venv/bin/pytest tests/services/test_agent_trigger.py -q` -> failed on missing `timeout_ms` support.
- TDD GREEN 2: `.venv/bin/pytest tests/services/test_agent_trigger.py -q` -> `5 passed`.
- Reviewer 1 caught internal `TimeoutError` misclassification and active-run cancel race; added dedicated regression tests and changed timeout orchestration to background consumer task + explicit cancel.
- Reviewer 2 caught outer cancellation leaking the background consumer task; added a cleanup regression and `_cleanup_consumer_task()` helper.
- Focused verification: `.venv/bin/pytest tests/services/test_agent_trigger.py tests/portex/contracts/test_events.py -q` -> `10 passed`.
- Unit acceptance: `.venv/bin/pytest tests/unit/ -v` -> `1 passed`.
- Full backend regression: `.venv/bin/pytest -q` -> `64 passed`.
- Lint: `.venv/bin/ruff check .` -> `All checks passed!`
- Frontend safety check: `cd web && npm run lint && npm run build` -> pass.
- Commit completed: `feat(services): implement M2.5.2 timeout orchestration`.
