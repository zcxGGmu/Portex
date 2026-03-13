# M7.3.2 Workspace Topology Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Define Portex's first real home/main workspace topology on top of `registered_groups` without swallowing later IM-binding work.

**Architecture:** Extend `registered_groups` with one explicit `is_home` flag, teach the registry service how to ensure and resolve canonical home/main web workspace rows, create those rows during registration and authenticated read paths, and normalize HTTP `/messages` so home/main dispatch uses canonical `web:*` chat JIDs while execution remains keyed by `group_folder`.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy async sessions, pytest, asyncio, SQLite

---

### Task 1: Lock The Home-Workspace Registry Contract With Failing Tests

**Files:**
- Modify: `tests/services/test_group_registry.py`
- Modify: `tests/domain/models/test_models.py`
- Modify: `tests/scripts/test_init_db.py`
- Modify: `domain/models/group.py`
- Modify: `services/group_registry.py`
- Modify: `scripts/init_db.py`

**Step 1: Write the failing tests**

Add tests that prove:

- `RegisteredGroup` exposes a non-nullable `is_home` column with a false default
- `init_db` backfills `registered_groups.is_home` for existing SQLite tables
- `GroupRegistryService.ensure_home_workspace(...)` creates:
  - `web:main` / `main` for `owner`
  - `web:home-{user_id}` / `home-{user_id}` for `admin` and `member`
- `GroupRegistryService.ensure_home_workspace(...)` is idempotent
- `GroupRegistryService.get_web_workspace_by_folder(...)` prefers canonical `web:*` rows for a workspace folder
- `ensure_registered_group(...)` does not clear existing `created_by` or `is_home` state on repeated writes

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/services/test_group_registry.py tests/domain/models/test_models.py tests/scripts/test_init_db.py -q
```

Expected: FAIL because `is_home`, home-workspace helpers, and init-db backfill do not exist yet.

**Step 3: Write the minimal implementation**

Implement:

- `is_home` on `RegisteredGroup`
- minimal SQLite column backfill in `scripts/init_db.py`
- home-workspace helpers in `GroupRegistryService`
- canonical web-workspace lookup by folder

Keep the service narrow. Do not add `target_main_jid` or `target_agent_id`.

**Step 4: Run the focused tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/services/test_group_registry.py tests/domain/models/test_models.py tests/scripts/test_init_db.py -q
```

Expected: PASS

### Task 2: Lock Registration And Group-Listing Behavior With Failing Route Tests

**Files:**
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `app/routes/auth.py`
- Modify: `app/routes/groups.py`

**Step 1: Write the failing tests**

Add tests that prove:

- `/auth/register` ensures a canonical home/main workspace row for the new user
- `GET /groups` ensures the caller's home/main workspace even for pre-`M7.3.2` users
- `GET /groups` hides unrelated users' home workspaces
- `owner` users can still see the shared `main` workspace even when it was first created by another owner

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_api_routes.py -q
```

Expected: FAIL because registration and group listing do not apply the new home-workspace rules yet.

**Step 3: Write the minimal implementation**

Implement:

- a registry dependency in `app/routes/auth.py`
- home-workspace ensure calls in `register()` and `list_groups()`
- `/groups` filtering for home-row visibility

Do not redesign the response schema yet.

**Step 4: Run the focused tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_api_routes.py -q
```

Expected: PASS

### Task 3: Lock Canonical Home/Main HTTP Dispatch With Failing Tests

**Files:**
- Modify: `tests/app/routes/test_message_routes.py`
- Modify: `app/routes/messages.py`

**Step 1: Write the failing tests**

Add tests that prove:

- `/messages` resolves `group_id="main"` to `chat_jid="web:main"` and `group_folder="main"`
- `/messages` resolves a personal home folder to `chat_jid="web:home-{user_id}"`
- `/messages` keeps the old fallback behavior when no canonical web workspace row exists for the requested folder

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_message_routes.py -q
```

Expected: FAIL because the route still uses `group_id` as both `chat_jid` and `group_folder`.

**Step 3: Write the minimal implementation**

Implement:

- one canonical target-resolution step in `app/routes/messages.py`
- ensure-home call before resolution
- fallback to the existing `group_id -> (chat_jid, group_folder)` behavior when no canonical workspace row exists

Do not rewrite IM ingress or WebSocket routing in this task.

**Step 4: Run the focused tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_message_routes.py -q
```

Expected: PASS

### Task 4: Run Verification, Refresh Handoff Docs, And Commit The Milestone

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run focused verification**

Run:

```bash
.venv/bin/pytest tests/services/test_group_registry.py tests/domain/models/test_models.py tests/scripts/test_init_db.py tests/app/routes/test_api_routes.py tests/app/routes/test_message_routes.py -q
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

- `docs/progress.md` with `M7.3.2` completion, verification evidence, and `M7.3.3` as the next step
- `tasks/todo.md` to mark `M7.3.2` complete

Call out explicitly that:

- `folder` is now the workspace key and canonical home/main web JIDs are persisted in `registered_groups`
- explicit IM binding metadata is still deferred to `M7.3.3`

**Step 4: Commit**

```bash
git add docs/plans/2026-03-13-m7-3-2-workspace-topology-design.md docs/plans/2026-03-13-m7-3-2-workspace-topology.md domain/models/group.py services/group_registry.py scripts/init_db.py app/routes/auth.py app/routes/groups.py app/routes/messages.py tests/services/test_group_registry.py tests/domain/models/test_models.py tests/scripts/test_init_db.py tests/app/routes/test_api_routes.py tests/app/routes/test_message_routes.py docs/progress.md tasks/todo.md
git commit -m "feat(groups): complete M7.3.2 workspace topology parity"
```
