# M2.5.2 Timeout Flow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M2.5.2` by enforcing millisecond-based timeout limits in `trigger_agent_execution()` and emitting a dedicated `run.timeout` event after cancelling the active runtime run.

**Architecture:** Keep timeout policy in `services/agent_trigger.py`, where orchestration already owns `request_id`, WebSocket broadcasting, and runtime lifecycle. Reuse the `M2.5.1` runtime cancel hook instead of adding SDK-specific timeout logic elsewhere, and align backend/frontend/platform event contracts around a new `run.timeout` event type.

**Tech Stack:** Python 3.11+, pytest, asyncio, OpenAI Agents SDK adapter layer, TypeScript discriminated unions

---

### Task 1: Add failing service timeout tests

**Files:**
- Modify: `tests/services/test_agent_trigger.py`
- Reference: `services/agent_trigger.py`

**Step 1: Write the failing test**

Add a test that uses a fake runtime whose `run_streamed()` never finishes on its own, then call:

```python
run_id = await trigger_agent_execution(
    group_folder="group-timeout",
    message="hello",
    user_id="user-timeout",
    websocket_manager=manager,
    runtime_factory=lambda _group: runtime,
    request_id="run-timeout",
    timeout_ms=10,
)
```

Assert:
- `run_id == "run-timeout"`
- `runtime.cancel("run-timeout")` was called exactly once
- the last broadcast event has `event_type == "run.timeout"`
- the payload includes `status == "timeout"` and `timeout_ms == 10`

Add a second test proving a normal fast stream completes without emitting `run.timeout`.

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/services/test_agent_trigger.py -q`

Expected: FAIL because `trigger_agent_execution()` has no `timeout_ms` parameter and never emits `run.timeout`.

**Step 3: Write minimal implementation**

Only change the service layer code needed to:
- accept `timeout_ms`
- convert milliseconds to seconds
- wrap the runtime stream in `asyncio.timeout(...)`
- cancel the active runtime run on timeout
- serialize and broadcast the synthetic timeout event

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/services/test_agent_trigger.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/services/test_agent_trigger.py services/agent_trigger.py
git commit -m "feat(services): add M2.5.2 timeout orchestration"
```

### Task 2: Align event contracts

**Files:**
- Modify: `portex/contracts/events.py`
- Modify: `tests/portex/contracts/test_events.py`
- Modify: `web/src/types/events.ts`

**Step 1: Write the failing contract test**

Extend the event contract test with:

```python
assert EventType.RUN_TIMEOUT.value == "run.timeout"
```

If needed, add a small frontend type-level regression by keeping the existing build/lint step as the verification gate instead of adding a separate TS test.

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/portex/contracts/test_events.py -q`

Expected: FAIL because `RUN_TIMEOUT` does not exist yet.

**Step 3: Write minimal implementation**

Add `RUN_TIMEOUT = "run.timeout"` to the backend event enum and extend the `StreamEvent` union / allowed event list with:

```ts
{ event_type: 'run.timeout'; run_id: string; payload?: { status?: string; timeout_ms?: number } }
```

Do not add UI rendering logic yet.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/portex/contracts/test_events.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add portex/contracts/events.py tests/portex/contracts/test_events.py web/src/types/events.ts
git commit -m "feat(contracts): add run.timeout event type"
```

### Task 3: Run focused and full verification

**Files:**
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run focused verification**

Run:
- `.venv/bin/pytest tests/services/test_agent_trigger.py -q`
- `.venv/bin/pytest tests/portex/contracts/test_events.py -q`

Expected: PASS.

**Step 2: Run broader regression**

Run:
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

Expected: PASS with no new failures.

**Step 3: Update docs**

Record:
- `M2.5.2` complete in `docs/TODO.md`
- verification evidence and next start point `M2.5.3` in `docs/progress.md`
- checklist and review notes in `tasks/todo.md`

**Step 4: Commit**

```bash
git add docs/TODO.md docs/progress.md tasks/todo.md
git commit -m "docs(progress): record M2.5.2 timeout flow"
```
