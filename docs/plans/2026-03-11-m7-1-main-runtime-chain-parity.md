# M7.1 Main Runtime Chain Parity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the current Portex main runtime gap by wiring normalized inbound messages to the existing runtime path and sending real outbound replies for the currently supported channels.

**Architecture:** Add one thin dispatch service that accepts `UnifiedMessage`, resolves a temporary execution target, persists inbound/outbound messages, and reuses `trigger_agent_execution()` through a collector broadcaster. Keep the current browser WebSocket happy path intact, add minimal Feishu/Telegram app-level ingestion adapters, and stop short of queue/workspace redesign work that belongs to `M7.2` and `M7.3`.

**Tech Stack:** Python 3.11, FastAPI, OpenAI Agents SDK, httpx, pytest, pytest-asyncio

---

### Task 1: Lock the dispatch-service contract with failing tests

**Files:**
- Add: `tests/services/test_message_dispatch.py`
- Reference: `domain/schemas.py`
- Reference: `services/agent_trigger.py`
- Reference: `services/message_router.py`
- Reference: `services/message_service.py`

**Step 1: Write the failing tests**

Add tests covering:

- successful inbound dispatch with explicit `group_folder`
- successful inbound dispatch with resolver-provided `group_folder`
- runtime completion leading to one outbound reply
- runtime failure leading to a structured dispatch failure without a fake success reply
- runtime timeout leading to the same behavior
- correct channel handler selection through the real router boundary
- inbound/outbound persistence calls receiving the expected metadata

Use fakes for:

- target resolver
- runtime trigger / collector result
- persistence layer
- outbound router

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_message_dispatch.py -q
```

Expected: FAIL because `services/message_dispatch.py` does not exist yet.

### Task 2: Implement the dispatch service and reply collector

**Files:**
- Add: `services/message_dispatch.py`
- Modify: `services/agent_trigger.py`
- Modify: `services/message_service.py`
- Modify: `domain/schemas.py`
- Test: `tests/services/test_message_dispatch.py`

**Step 1: Write minimal implementation**

Implement in `services/message_dispatch.py`:

- `MessageDispatchError`
- `ResolvedMessageTarget`
- `DispatchResult`
- `RuntimeReplyCollector`
- `MessageDispatchService`

Extend `services/agent_trigger.py` only as needed to support the collector path cleanly without breaking the current WebSocket flow.

Extend `services/message_service.py` only enough to persist inbound/outbound messages plus correlation metadata required by the tests.

Add the smallest schema changes needed for the dispatch boundary if the service contract benefits from typed request/response helpers.

**Step 2: Run focused tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_message_dispatch.py -q
```

Expected: PASS

**Step 3: Commit**

```bash
git add services/message_dispatch.py services/agent_trigger.py services/message_service.py domain/schemas.py tests/services/test_message_dispatch.py
git commit -m "feat(messages): add main runtime dispatch service"
```

### Task 3: Add minimal Feishu and Telegram ingestion adapters

**Files:**
- Add: `app/routes/im.py`
- Modify: `app/main.py`
- Modify: `infra/im/feishu.py`
- Modify: `infra/im/telegram.py`
- Add: `tests/app/routes/test_im_routes.py`

**Step 1: Write the failing route tests**

Add tests covering:

- Feishu webhook payload -> normalized event -> dispatch service call
- Telegram update payload -> normalized event -> dispatch service call
- unsupported/non-message payloads return a benign no-op response
- Telegram outbound helper sends a real Bot API request shape for text replies

Use dependency injection / monkeypatching so the tests do not hit a real runtime or real network.

**Step 2: Run focused tests to verify they fail**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_im_routes.py tests/infra/im/test_telegram.py tests/infra/im/test_feishu.py -q
```

Expected: FAIL because the app-level IM adapters and Telegram outbound helper do not exist yet.

**Step 3: Write minimal implementation**

Implement:

- `app/routes/im.py` with one Feishu webhook endpoint and one Telegram update-ingest endpoint
- `app/main.py` router registration
- a narrow Telegram outbound text-send helper
- any small Feishu helper needed to keep the channel send boundary symmetric and testable

**Step 4: Re-run focused tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_im_routes.py tests/infra/im/test_telegram.py tests/infra/im/test_feishu.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/im.py app/main.py infra/im/feishu.py infra/im/telegram.py tests/app/routes/test_im_routes.py
git commit -m "feat(im): add M7.1 ingestion adapters"
```

### Task 4: Replace the `/messages` placeholder with real dispatch

**Files:**
- Modify: `app/routes/messages.py`
- Modify: `domain/schemas.py`
- Add: `tests/app/routes/test_message_routes.py`
- Reference: `services/message_dispatch.py`

**Step 1: Write the failing route tests**

Add tests covering:

- `POST /messages` now dispatches through the real message-dispatch service
- request validation reflects the new runtime-chain contract
- success response returns real dispatch metadata instead of a synthetic queued-only acknowledgement
- dispatch failures map to explicit HTTP errors

**Step 2: Run focused tests to verify they fail**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_message_routes.py -q
```

Expected: FAIL because the route is still a placeholder.

**Step 3: Write minimal implementation**

Update the route and schemas to use the new dispatch service directly.

**Step 4: Re-run focused tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_message_routes.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/messages.py domain/schemas.py tests/app/routes/test_message_routes.py
git commit -m "feat(messages): replace message placeholder route"
```

### Task 5: Add integration coverage for the end-to-end chain

**Files:**
- Add: `tests/integration/test_message_flow.py`
- Reference: `app/main.py`
- Reference: `app/routes/im.py`
- Reference: `services/message_dispatch.py`

**Step 1: Write the failing integration tests**

Add at least one integration test for:

- Feishu or Telegram payload
- app-level ingest route
- dispatch service
- fake runtime completion
- outbound handler invocation

Keep the runtime fake and the outbound transport fake. The test should prove wiring, not real provider behavior.

**Step 2: Run focused integration tests to verify they fail**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/integration/test_message_flow.py -q
```

Expected: FAIL because the full chain is not wired yet.

**Step 3: Finish the minimal glue needed**

Complete any remaining wiring required for the integration path to pass, without widening scope into `M7.2`.

**Step 4: Re-run focused integration tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/integration/test_message_flow.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/integration/test_message_flow.py
git commit -m "test(messages): add M7.1 integration coverage"
```

### Task 6: Refresh handoff docs and run milestone verification

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`
- Optional: `README.md` if the public boundary wording needs to change after wiring

**Step 1: Update milestone status**

Record:

- what part of `M7.1` is now complete
- the exact remaining boundary before `M7.2`
- fresh verification evidence

**Step 2: Run focused and regression verification**

Run:

```bash
git diff --check
.venv/bin/pytest -o addopts='' tests/services/test_message_dispatch.py tests/app/routes/test_im_routes.py tests/app/routes/test_message_routes.py tests/integration/test_message_flow.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
```

Expected: all PASS

**Step 3: Record this session in `tasks/todo.md`**

Add the checklist completion and review summary.

**Step 4: Commit**

```bash
git add docs/progress.md tasks/todo.md README.md
git commit -m "docs(handoff): record M7.1 runtime chain progress"
```
