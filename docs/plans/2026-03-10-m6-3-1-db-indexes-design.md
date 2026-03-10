# M6.3.1 Database Indexes Design

## Goal

Complete `M6.3.1` by adding the minimal database indexes already called out in `docs/TODO.md`, and by verifying that fresh database initialization actually creates them.

## Scope

- add an index on `messages.chat_jid`
- add an index on `messages.timestamp`
- add an index on `scheduled_tasks.next_run`
- verify the index declarations at the SQLAlchemy model layer
- verify that `scripts/init_db.py` creates the indexes in a fresh SQLite database

## Out of Scope

- do not add any extra indexes beyond the three TODO-defined targets
- do not introduce Alembic or a migration framework
- do not add benchmark tooling or performance measurements
- do not redesign the current database layer or connection setup

## Design Constraints

- keep the implementation as small as possible and attach the indexes directly to the existing SQLAlchemy models
- preserve the current SQLite-first repository setup
- prefer tests that prove both metadata intent and actual created database state

## Options Considered

### Option A: SQLAlchemy model indexes only

- declare indexes in model metadata
- verify only `__table__.indexes`

Pros:
- smallest implementation

Cons:
- does not prove the initialized SQLite database actually receives the indexes

### Option B: SQLAlchemy model indexes plus SQLite creation verification

- declare indexes in model metadata
- verify model metadata
- run `scripts/init_db.py` against a temporary SQLite file and introspect created indexes

Pros:
- minimal but end-to-end enough for this milestone
- proves the documented initialization path actually materializes the indexes

Cons:
- adds one more test path

### Option C: Raw SQL index creation script

- keep models unchanged
- add custom SQL on database init

Pros:
- explicit control over SQL emitted

Cons:
- duplicates schema intent outside the models
- harder to keep aligned with future model changes
- unnecessary for the current repository setup

## Recommended Design

Choose **Option B**.

## Proposed Changes

### Model Layer

- update `domain/models/message.py` to declare indexes for:
  - `chat_jid`
  - `timestamp`
- update `domain/models/task.py` to declare an index for:
  - `next_run`

### Test Layer

- extend `tests/domain/models/test_models.py` to assert the new index names exist in model metadata
- extend `tests/scripts/test_init_db.py` to initialize a temporary SQLite database and introspect created indexes

### Index Naming

Use stable, explicit names that match the TODO wording:

- `idx_messages_chat_jid`
- `idx_messages_timestamp`
- `idx_tasks_next_run`

## Testing Strategy

- write metadata-level failing tests first
- write SQLite-init failing test first
- implement the minimal model changes
- rerun focused tests
- then run full backend regression, `ruff`, and the existing frontend verification commands for milestone consistency

## Expected Deliverables

- the three TODO-defined indexes exist in SQLAlchemy metadata
- fresh database initialization creates those indexes in SQLite
- `docs/progress.md` and `tasks/todo.md` advance from `M6.3.1` to `M6.3.2`
