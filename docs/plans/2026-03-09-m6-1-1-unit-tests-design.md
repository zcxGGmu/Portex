# M6.1.1 Unit Tests Design

## Goal

Complete `M6.1.1` by establishing the minimal `tests/unit/` layout promised in `docs/TODO.md` and filling it with meaningful pure-logic tests that do not depend on API routes, database sessions, or runtime integration flows.

## Scope

- Add the expected `tests/unit/` entry points:
  - `tests/unit/test_auth.py`
  - `tests/unit/test_models.py`
  - `tests/unit/test_services.py`
- Retire the mismatched legacy filename `tests/unit/test_auth_unit.py`
- Reuse existing pure logic in:
  - `services/auth.py`
  - `domain/models/*`
  - `services/execution_mode.py`
  - `services/memory.py`
- Run focused unit verification plus full regression and lint

## Out of Scope

- Do not start `M6.1.2` integration tests
- Do not add `tests/integration/test_api.py`, `tests/integration/test_websocket.py`, or `tests/e2e/test_chat.py` in this milestone
- Do not re-partition the existing `tests/domain/`, `tests/services/`, or `tests/app/` suites
- Do not modify runtime, API, DB, or frontend behavior unless a real regression is discovered during verification

## Design Constraints

- Keep `tests/unit/` focused on pure or near-pure logic with small fixtures
- Avoid broad duplication of existing service and domain suites; prefer complementary checks over wholesale re-testing
- Preserve the current restart-friendly workflow: design doc, implementation plan, focused verification, regression, handoff update

## Options Considered

### Option A: Minimal `tests/unit/` completion

- Create the three expected `tests/unit/` files
- Keep coverage focused on helpers, metadata contracts, and small pure services

Pros:
- Matches `docs/TODO.md` directly
- Smallest safe change set
- Keeps `M6.1.1` clearly separate from later milestones

Cons:
- Does not improve integration/e2e coverage yet

### Option B: Preserve old naming and only add missing files

- Keep `tests/unit/test_auth_unit.py`
- Add `test_models.py` and `test_services.py`

Pros:
- Slightly smaller diff

Cons:
- Leaves `tests/unit/` inconsistent with the TODO layout
- Makes the suite harder to reason about for the next session

### Option C: Reorganize all test layers now

- Move and rename existing tests across unit/integration/e2e

Pros:
- Cleaner long-term taxonomy

Cons:
- Turns `M6.1.1` into test-suite refactoring
- High churn with low milestone-specific value

## Recommended Design

Choose **Option A**.

## Test Slice Design

### `tests/unit/test_auth.py`

Cover:
- password hash / verify roundtrip
- `_read_positive_int_env()` fallback behavior for missing, invalid, and non-positive values
- low-level token encode/decode helper behavior without needing the global singleton service

### `tests/unit/test_models.py`

Cover:
- lightweight metadata/default contracts for representative SQLAlchemy models
- defaults and nullability for `User`, `Message`, `InviteCode`, `ScheduledTask`, and `Session`
- table metadata checks only; no DB session or migrations

### `tests/unit/test_services.py`

Cover:
- `get_execution_mode()` pure role/config selection rules
- `MemoryService` path helpers and blank-query early return
- keep assertions deterministic and filesystem-light

## Expected Deliverables

- `tests/unit/` contains the three expected files from `docs/TODO.md`
- `.venv/bin/pytest tests/unit/ -v` passes
- full backend regression and `ruff` remain green
- `docs/progress.md` and `tasks/todo.md` advance `M6.1.1` and point to `M6.1.2`
