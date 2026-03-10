# M6.3.2 Connection Pool Design

## Goal

Complete `M6.3.2` by making the database engine use an explicit, valid connection-pool configuration for the repository's current async SQLAlchemy setup, without broadening the database layer beyond this milestone.

## Scope

- make engine construction in `infra/db/database.py` explicit and testable
- keep the default file-based SQLite URL (`sqlite+aiosqlite:///./data/portex.db`)
- configure file-backed SQLite with an explicit queue-pool size of `20` and `max_overflow=10`
- keep in-memory SQLite on `StaticPool` so test and ephemeral paths stay valid
- preserve the current `AsyncSessionLocal` and `get_db()` public contract
- keep the implementation small enough that `scripts/init_db.py` can reuse the same engine-construction helper when it creates an override engine

## Out of Scope

- do not add a cache layer or start `M6.3.3`
- do not add a migration framework or schema backfill system
- do not benchmark connection throughput or add load-test tooling
- do not redesign repositories, service lifetimes, or FastAPI dependency injection
- do not add new deployment/config knobs unless they are required for the minimal pool implementation

## Design Constraints

- `docs/TODO.md` currently shows `StaticPool` together with `pool_size` and `max_overflow`, but that combination is invalid for the current `sqlite+aiosqlite` setup and fails under SQLAlchemy `2.0.48`
- the default file-backed SQLite URL already resolves to `AsyncAdaptedQueuePool`; this milestone should make the pool sizing explicit and regression-tested rather than silently depending on dialect defaults
- in-memory SQLite must keep using `StaticPool`, otherwise the current test-friendly one-connection behavior changes unnecessarily
- tests should verify concrete pool behavior, not only that `get_db()` yields an `AsyncSession`

## Options Considered

### Option A: Implement the TODO snippet literally

- always pass `poolclass=StaticPool`
- also pass `pool_size=20` and `max_overflow=10`

Pros:
- matches the literal TODO sketch

Cons:
- invalid for the current SQLAlchemy/SQLite combination
- crashes engine construction instead of improving performance

### Option B: Conditional engine builder by database URL

- use `StaticPool` only for in-memory SQLite URLs
- use explicit `pool_size=20` and `max_overflow=10` for file-backed SQLite and other non-memory URLs
- centralize the logic in one helper used by the module-level engine and optional override paths

Pros:
- valid for the current repository setup
- preserves test-friendly in-memory behavior
- keeps the milestone small and easily testable

Cons:
- slightly more code than a one-line engine constructor

### Option C: Generalize into new environment-driven pool settings

- add extra env vars for pool size, overflow, timeout, recycle, and ping
- make all pool behavior configurable

Pros:
- more operational flexibility

Cons:
- expands surface area beyond the TODO requirement
- adds docs and test burden without immediate need

## Recommended Design

Choose **Option B**.

## Proposed Changes

### Engine Construction

- add a small helper in `infra/db/database.py` that:
  - inspects the database URL
  - returns `StaticPool` for in-memory SQLite URLs
  - returns `pool_size=20` and `max_overflow=10` for non-memory URLs
- create the module-level `engine` through that helper
- keep `AsyncSessionLocal` bound to the shared module-level engine

### URL Detection

- use SQLAlchemy URL parsing instead of string slicing
- treat these SQLite URLs as in-memory:
  - `sqlite+aiosqlite://`
  - `sqlite+aiosqlite:///:memory:`
  - `sqlite+aiosqlite:///file::memory:?cache=shared`
  - `sqlite+aiosqlite:///file:memdb1?mode=memory&cache=shared&uri=true`
- treat the current default file path as file-backed SQLite and therefore queue-pooled

### Script Consistency

- reuse the same engine-construction helper in `scripts/init_db.py` when `--database-url` is supplied
- keep the existing default-engine fast path unchanged when no override URL is provided

## Testing Strategy

- extend `tests/infra/db/test_database.py` first
- add a failing test proving the default file-backed SQLite engine uses `AsyncAdaptedQueuePool` with size `20` and `max_overflow=10`
- add a failing test proving an in-memory SQLite engine uses `StaticPool`
- keep the existing `get_db()` session test so the public dependency contract remains covered
- after implementation, run the focused DB tests, then the full backend regression, `ruff`, and frontend `lint/build`

## Expected Deliverables

- explicit and valid pool configuration for the repository's database engine
- regression tests that lock both file-backed and in-memory SQLite behavior
- `docs/progress.md` and `tasks/todo.md` advanced from `M6.3.2` to `M6.3.3`
