# M7.3.1 Persisted Group Listing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the demo `/groups` response with a real DB-backed registry and lazily register runtime-resolved targets into that registry.

**Architecture:** Add a thin async registry service around `RegisteredGroup`, wire `GET /groups` to that service, and extend `MessageDispatchService` with one optional registration callback that persists the current `chat_jid -> group_folder` mapping before execution continues. Keep the existing identifier rules intact and defer richer workspace/binding semantics to later `M7.3.x` milestones.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy async sessions, pytest, asyncio

---

### Task 1: Lock The Registry Contract With Failing Service Tests

**Files:**
- Create: `tests/services/test_group_registry.py`
- Modify: `domain/models/group.py` only if test coverage reveals a model-field mismatch
- Modify: `services/group_registry.py`

**Step 1: Write the failing tests**

Add tests that prove:

- ensuring a new target inserts a `RegisteredGroup` row
- ensuring an existing target is idempotent and preserves the original `added_at`
- listing groups returns deterministic persisted summaries

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_group_registry.py -q
```

Expected: FAIL because the registry service does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- `services/group_registry.py`
- one thin async service around `RegisteredGroup`

Keep the service narrow. Do not add binding or ownership logic.

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_group_registry.py -q
```

Expected: PASS

### Task 2: Lock Route And Dispatch Registration Behavior With Failing Tests

**Files:**
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `tests/services/test_message_dispatch.py`
- Modify: `tests/app/routes/test_message_routes.py`
- Modify: `app/routes/groups.py`
- Modify: `services/message_dispatch.py`
- Modify: `app/routes/im.py`

**Step 1: Write the failing tests**

Add tests that prove:

- `GET /groups` uses a dependency-backed registry result instead of hard-coded demo data
- message dispatch calls the registration hook for explicit `group_folder`
- message dispatch calls the registration hook for resolver-derived `group_folder`
- the default message-dispatch dependency path can register a web target before execution

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_api_routes.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py -q
```

Expected: FAIL because the route is still hard-coded and the dispatch service has no registration hook.

**Step 3: Write minimal implementation**

Implement:

- a registry dependency in `app/routes/groups.py`
- a registration callback path in `services/message_dispatch.py`
- default registry wiring in `app/routes/im.py`

Do not redesign the route schema or the target resolver.

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_api_routes.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py -q
```

Expected: PASS

### Task 3: Run Focused Verification, Refresh Handoff Docs, And Commit The Slice

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md` only if the parity checklist needs a completion mark

**Step 1: Run focused verification**

Run:

```bash
.venv/bin/pytest tests/services/test_group_registry.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py -q
```

Expected: PASS

**Step 2: Run broader regression**

Run:

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
git diff --check
```

Expected: PASS

**Step 3: Update handoff docs**

Refresh:

- `docs/progress.md` with `M7.3.1` completion, verification evidence, and `M7.3.2` as the next step
- `tasks/todo.md` if the `M7.3.1` checkbox is the current parity source used by the repo

Call out explicitly that:

- `registered_groups` is now the current persisted listing source of truth
- the current `chat_jid -> group_folder` persistence rule is still temporary and does not define the final workspace/binding model

**Step 4: Commit**

```bash
git add docs/plans/2026-03-13-m7-3-1-persisted-group-listing-design.md docs/plans/2026-03-13-m7-3-1-persisted-group-listing.md services/group_registry.py app/routes/groups.py app/routes/im.py services/message_dispatch.py tests/services/test_group_registry.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py docs/progress.md tasks/todo.md
git commit -m "feat(groups): complete M7.3.1 persisted group listing"
```

Plan complete and saved to `docs/plans/2026-03-13-m7-3-1-persisted-group-listing.md`. Per the current user request, execution continues in this session on the subagent-driven path.
