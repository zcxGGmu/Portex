# M7.2.4 Session Workspace Lifecycle Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Introduce a coordinator-owned workspace/session lifecycle so the default OpenAI execution path can reuse a real persisted session for follow-up turns instead of always running fresh.

**Architecture:** Add a small in-memory workspace lifecycle store keyed by `group_folder`, teach the coordinator to allocate/commit/invalidate session state through that store, and wire `OpenAIAgentsRuntime` to the OpenAI Agents SDK `SQLiteSession` interface. Preserve current queue/cancellation semantics, keep success-only session commits, and add one bounded invalidate-and-retry path for session-resume failure.

**Tech Stack:** Python 3.11, asyncio, OpenAI Agents SDK memory sessions, FastAPI service wiring, pytest

---

### Task 1: Lock The Workspace Lifecycle Rules With Failing Tests

**Files:**
- Create: `tests/services/test_workspace_lifecycle.py`
- Modify: `tests/services/test_execution_coordinator.py`
- Reference: `services/execution_coordinator.py`

**Step 1: Write the failing tests**

Add tests that prove:

- the workspace store reuses the committed session for the same workspace
- `fresh_session=True` previews a new session without overwriting the current one until success
- coordinator only commits a fresh session after a successful run
- a failed fresh run leaves the previous committed session intact

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_workspace_lifecycle.py tests/services/test_execution_coordinator.py -q
```

Expected: FAIL because the workspace lifecycle module does not exist yet and the coordinator still owns only `_session_ids`.

**Step 3: Write minimal implementation**

Implement:

- `services/workspace_lifecycle.py`
- minimal `WorkspaceResolver`
- minimal `WorkspaceSessionStore`
- coordinator integration that replaces raw `_session_ids` usage

Keep the public `ExecutionRequest` contract unchanged.

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_workspace_lifecycle.py tests/services/test_execution_coordinator.py -q
```

Expected: PASS

### Task 2: Lock Real OpenAI Session Persistence And Resume Recovery With Failing Tests

**Files:**
- Modify: `tests/infra/runtime/test_openai.py`
- Modify: `tests/services/test_execution_backends.py`
- Modify: `tests/services/test_execution_coordinator.py`
- Modify: `infra/runtime/openai.py`
- Modify: `services/execution_backends.py`
- Modify: `services/execution_runtime.py` if default runtime construction needs new args

**Step 1: Write the failing tests**

Add tests that prove:

- `OpenAIAgentsRuntime.run_streamed()` passes a real session object into `Runner.run_streamed(...)`
- the default session storage path is stable under `data/sessions/{group_folder}/`
- a backend-reported session-resume failure causes the coordinator to invalidate the stale session and retry once fresh

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/infra/runtime/test_openai.py tests/services/test_execution_backends.py tests/services/test_execution_coordinator.py -q
```

Expected: FAIL because the runtime still ignores `request.session_id` and the coordinator has no resume-retry logic.

**Step 3: Write minimal implementation**

Implement:

- a session factory in `infra/runtime/openai.py` backed by Agents SDK `SQLiteSession`
- a narrow runtime/backend exception for session-resume failure
- one coordinator retry path: invalidate stale session and rerun once fresh

Do not add generic retry loops or provider-specific policy beyond this one lifecycle recovery path.

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/infra/runtime/test_openai.py tests/services/test_execution_backends.py tests/services/test_execution_coordinator.py -q
```

Expected: PASS

### Task 3: Run Focused Verification, Refresh Handoff Docs, And Commit The Slice

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run focused verification**

Run:

```bash
.venv/bin/pytest tests/services/test_workspace_lifecycle.py tests/services/test_execution_coordinator.py tests/services/test_execution_backends.py tests/infra/runtime/test_openai.py tests/services/test_message_dispatch.py tests/services/test_task_service.py -q
```

Expected: PASS

**Step 2: Run broader regression**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/runtime/test_openai.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected: PASS

**Step 3: Update handoff docs**

Refresh:

- `docs/progress.md` with `M7.2.4` completion/evidence/next step
- `tasks/todo.md` checklist/review state and parity backlog checkboxes

Call out explicitly that:

- OpenAI path now has real follow-up session continuity
- host/container still use the shared lifecycle contract but remain effectively stateless in this slice

**Step 4: Commit**

```bash
git add docs/progress.md tasks/todo.md
git commit -m "docs(handoff): record M7.2.4 workspace session lifecycle"
```

Plan complete and saved to `docs/plans/2026-03-13-m7-2-4-session-workspace-lifecycle.md`. Per the current user request, execution continues in this session on the subagent-driven path.
