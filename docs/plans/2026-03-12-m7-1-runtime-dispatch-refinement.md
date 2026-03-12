# M7.1 Runtime Dispatch Refinement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the refined `M7.1` path by adding a structured runtime-result contract, a thin dispatch service, and real IM/http dispatch entrypoints without widening scope into WebSocket unification or execution-plane redesign.

**Architecture:** First refine the runtime trigger helper so it can produce structured completion data outside WebSocket broadcasting. Then build `MessageDispatchService` on top of that contract, extend the current message persistence metadata minimally, add IM ingestion routes and Telegram outbound sending, and finally replace the `/messages` placeholder with the real dispatch boundary.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy async, OpenAI Agents SDK adapter layer, httpx, pytest, pytest-asyncio

---

### Task 1: Lock the runtime-result and dispatch-service contracts with failing tests

**Files:**
- Add: `tests/services/test_message_dispatch.py`
- Modify: `tests/services/test_agent_trigger.py`
- Reference: `services/agent_trigger.py`
- Reference: `services/message_service.py`

**Step 1: Write the failing tests**

Add tests that prove:
- the trigger helper can return a structured success result with `run_id`, `status`, and `final_output`
- runtime failure and timeout produce structured failure results
- a new dispatch service can:
  - use explicit `group_folder`
  - fall back to resolver-provided `group_folder`
  - persist inbound metadata
  - create one outbound reply on success
  - avoid fake success replies on failure / timeout

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_agent_trigger.py tests/services/test_message_dispatch.py -q
```

Expected: FAIL because the structured dispatch contract does not exist yet.

### Task 2: Implement the structured runtime-result path and dispatch service

**Files:**
- Add: `services/message_dispatch.py`
- Modify: `services/agent_trigger.py`
- Modify: `services/message_service.py`
- Modify: `domain/schemas.py`
- Modify: `domain/models/message.py`
- Modify: `scripts/init_db.py` if index / metadata backfill behavior needs to pick up new columns
- Test: `tests/services/test_message_dispatch.py`
- Test: `tests/services/test_agent_trigger.py`

**Step 1: Write minimal implementation**

Implement:
- a structured trigger result in `services/agent_trigger.py`
- a runtime event collector that records completion / failure / timeout
- `MessageDispatchService`, `MessageDispatchError`, and minimal target-resolution helpers
- the smallest message persistence metadata expansion needed for run correlation

**Step 2: Run focused tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_agent_trigger.py tests/services/test_message_dispatch.py tests/services/test_message_service.py -q
```

Expected: PASS

### Task 3: Add minimal Feishu/Telegram ingestion adapters and Telegram outbound send

**Files:**
- Add: `app/routes/im.py`
- Modify: `app/main.py`
- Modify: `app/routes/__init__.py`
- Modify: `infra/im/telegram.py`
- Modify: `infra/im/feishu.py` only if a tiny helper extraction is needed for symmetry/testability
- Add: `tests/app/routes/test_im_routes.py`
- Modify: `tests/infra/im/test_telegram.py`

**Step 1: Write the failing tests**

Add tests for:
- Feishu webhook payload -> dispatch service call
- Telegram update payload -> dispatch service call
- unsupported provider payloads -> benign no-op response
- Telegram outbound text helper request shape and error mapping

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_im_routes.py tests/infra/im/test_telegram.py tests/infra/im/test_feishu.py -q
```

Expected: FAIL because the routes and Telegram outbound helper do not exist yet.

**Step 3: Write minimal implementation**

Implement:
- app-level IM ingestion routes
- router registration
- narrow Telegram outbound text send support

**Step 4: Re-run focused tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_im_routes.py tests/infra/im/test_telegram.py tests/infra/im/test_feishu.py -q
```

Expected: PASS

### Task 4: Replace the `/messages` placeholder with real dispatch

**Files:**
- Modify: `app/routes/messages.py`
- Modify: `domain/schemas.py`
- Add: `tests/app/routes/test_message_routes.py`
- Reference: `services/message_dispatch.py`

**Step 1: Write the failing tests**

Add tests that prove:
- `POST /messages` dispatches through the new service
- the route returns dispatch metadata rather than a synthetic queued-only acknowledgement
- dispatch failures map to explicit HTTP errors

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_message_routes.py -q
```

Expected: FAIL because the route is still a placeholder.

**Step 3: Write minimal implementation**

Update the message route and its DTOs to use the dispatch service directly.

**Step 4: Re-run focused tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_message_routes.py -q
```

Expected: PASS

### Task 5: Add one end-to-end integration slice

**Files:**
- Add: `tests/integration/test_message_flow.py`
- Reference: `app/routes/im.py`
- Reference: `services/message_dispatch.py`

**Step 1: Write the failing integration test**

Add at least one integration flow that proves:
- provider payload enters an IM route
- normalization happens
- dispatch service triggers the fake runtime
- outbound handler is invoked

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/integration/test_message_flow.py -q
```

Expected: FAIL because the full chain is not wired yet.

**Step 3: Finish any remaining glue**

Add only the wiring required for this integration slice to pass.

**Step 4: Re-run focused integration**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/integration/test_message_flow.py -q
```

Expected: PASS

### Task 6: Refresh handoff docs and run milestone verification

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`
- Optional: `README.md`
- Optional: `README.zh-CN.md`

**Step 1: Update progress**

Record:
- what part of `M7.1` is complete
- what remains explicitly deferred to `M7.2` / `M7.3`
- fresh verification evidence

**Step 2: Run milestone verification**

Run:

```bash
git diff --check
.venv/bin/pytest -o addopts='' tests/services/test_agent_trigger.py tests/services/test_message_dispatch.py tests/app/routes/test_im_routes.py tests/app/routes/test_message_routes.py tests/integration/test_message_flow.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
```

Expected: PASS
