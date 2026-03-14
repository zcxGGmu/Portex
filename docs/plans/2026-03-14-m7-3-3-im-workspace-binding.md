# M7.3.3 IM Workspace Binding Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add explicit IM-to-workspace binding metadata so external chats can remain unbound in isolated fallback workspaces or reuse one canonical Portex workspace without changing reply addressing.

**Architecture:** Extend `registered_groups` with one nullable `target_workspace_jid`, teach the registry service how to backfill/read/resolve IM endpoint bindings, make IM dispatch choose execution `group_folder` from binding metadata while preserving the original IM `chat_jid`, and keep `/groups` limited to canonical web workspaces instead of raw IM endpoint rows.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy async sessions, pytest, asyncio, SQLite

---

### Task 1: Lock The Binding Metadata Contract With Failing Model And Service Tests

**Files:**
- Modify: `tests/domain/models/test_models.py`
- Modify: `tests/scripts/test_init_db.py`
- Modify: `tests/services/test_group_registry.py`
- Modify: `domain/models/group.py`
- Modify: `services/group_registry.py`
- Modify: `scripts/init_db.py`

**Step 1: Write the failing tests**

Add tests that prove:

- `RegisteredGroup` exposes nullable `target_workspace_jid`
- `init_db` backfills `registered_groups.target_workspace_jid` for old SQLite tables
- `GroupRegistryService.ensure_registered_group(...)` preserves an existing non-null `target_workspace_jid` on repeat writes unless explicitly updated
- the registry service can resolve:
  - an unbound IM endpoint to its own fallback folder
  - a bound IM endpoint to the target workspace folder
  - an orphaned binding back to the fallback folder

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py tests/services/test_group_registry.py -q
```

Expected: FAIL because `target_workspace_jid` and binding-resolution helpers do not exist yet.

**Step 3: Write the minimal implementation**

Implement:

- `target_workspace_jid` on `RegisteredGroup`
- SQLite backfill in both `scripts/init_db.py` and `GroupRegistryService._ensure_schema()`
- narrow registry helpers for:
  - loading one row by `jid`
  - ensuring an IM endpoint row
  - resolving the effective execution workspace for an IM endpoint

Keep the service narrow. Do not add `target_agent_id`, UI payloads, or automatic binding rules.

**Step 4: Run the focused tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py tests/services/test_group_registry.py -q
```

Expected: PASS

### Task 2: Lock Binding-Aware IM Dispatch With Failing Service And Route Tests

**Files:**
- Modify: `tests/services/test_message_dispatch.py`
- Modify: `tests/app/routes/test_im_routes.py`
- Modify: `services/message_dispatch.py`
- Modify: `app/routes/im.py`

**Step 1: Write the failing tests**

Add tests that prove:

- an unbound IM message still executes in its fallback `chat-<hash>` workspace
- a bound IM message executes in the bound workspace folder instead of the fallback folder
- an orphaned binding falls back to the IM endpoint's own folder
- outbound replies still use the original IM `chat_jid` even when execution used a bound workspace folder
- the default IM route wiring consults the binding-aware registry path before submitting execution

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/services/test_message_dispatch.py tests/app/routes/test_im_routes.py -q
```

Expected: FAIL because IM dispatch still resolves only `chat_jid -> chat-<hash>` and does not read binding metadata.

**Step 3: Write the minimal implementation**

Implement:

- one binding-aware IM target-resolution path in `app/routes/im.py`
- the smallest `MessageDispatchService` adjustment needed so IM dispatch can use the resolved workspace folder while preserving the original IM transport JID
- no changes to HTTP `/messages` behavior

Prefer keeping reply routing unchanged and limiting the new behavior to IM ingress.

**Step 4: Run the focused tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/services/test_message_dispatch.py tests/app/routes/test_im_routes.py -q
```

Expected: PASS

### Task 3: Lock Workspace-Only Group Listing With Failing Route Tests

**Files:**
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `app/routes/groups.py`

**Step 1: Write the failing tests**

Add tests that prove:

- `/groups` continues to show canonical `web:*` home/main workspaces under the existing visibility rules
- `/groups` no longer lists raw IM endpoint rows such as `telegram:*` or `feishu:*`
- existing main/home visibility behavior from `M7.3.2` does not regress

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_api_routes.py -q
```

Expected: FAIL because `/groups` still includes non-home IM endpoint rows.

**Step 3: Write the minimal implementation**

Implement:

- one route-level filter in `app/routes/groups.py` so `/groups` only exposes canonical web workspace rows
- preserve the existing `is_home` visibility checks on top of that filter

Do not redesign the response schema or add a new endpoint inventory API.

**Step 4: Run the focused tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_api_routes.py -q
```

Expected: PASS

### Task 4: Run Verification, Refresh Handoff Docs, And Commit The Milestone

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run focused verification**

Run:

```bash
.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py tests/services/test_group_registry.py tests/services/test_message_dispatch.py tests/app/routes/test_im_routes.py tests/app/routes/test_api_routes.py -q
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

- `docs/progress.md` with `M7.3.3` completion, verification evidence, and `M7.3.4` as the next start point
- `tasks/todo.md` to mark `M7.3.3` complete

Call out explicitly that:

- IM chats now carry explicit workspace-binding metadata through `target_workspace_jid`
- unbound IM chats still use isolated fallback folders
- user-facing bind/unbind APIs are still deferred to `M7.3.6`

**Step 4: Commit**

```bash
git add docs/plans/2026-03-14-m7-3-3-im-workspace-binding-design.md docs/plans/2026-03-14-m7-3-3-im-workspace-binding.md domain/models/group.py services/group_registry.py scripts/init_db.py services/message_dispatch.py app/routes/im.py app/routes/groups.py tests/domain/models/test_models.py tests/scripts/test_init_db.py tests/services/test_group_registry.py tests/services/test_message_dispatch.py tests/app/routes/test_im_routes.py tests/app/routes/test_api_routes.py docs/progress.md tasks/todo.md
git commit -m "feat(groups): complete M7.3.3 IM workspace binding parity"
```
