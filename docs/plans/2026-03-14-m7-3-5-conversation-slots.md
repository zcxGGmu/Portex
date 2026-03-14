# M7.3.5 Conversation Slots Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the minimal persistent conversation-slot data model so one workspace can own more than one conversation context without yet implementing full slot management APIs, IM-to-slot binding, or frontend tab UI.

**Architecture:** Introduce a new `conversation_slots` table plus one required `main` slot per workspace, and thread `slot_id` through message persistence and execution/session identity while keeping workspace membership, IM binding, files, and memory at the workspace level. Existing callers continue to default to `slot_id="main"` so current single-conversation flows stay stable until `M7.3.6` and `M7.5` expose the extra slots.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy async sessions, SQLite, pytest

---

### Task 1: Lock The Conversation-Slot And Message-Slot Schema Contract

**Files:**
- Create: `domain/models/conversation_slot.py`
- Modify: `domain/models/__init__.py`
- Modify: `domain/models/message.py`
- Modify: `tests/domain/models/test_models.py`
- Modify: `scripts/init_db.py`
- Modify: `tests/scripts/test_init_db.py`

**Step 1: Write the failing tests**

Add tests that prove:

- `ConversationSlot` exists in shared metadata
- `conversation_slots` uses `(workspace_folder, slot_id)` as its primary identity
- `messages` has a first-class `slot_id` column instead of relying only on JSON `attachments`
- `scripts/init_db.py` backfills old SQLite databases by adding `messages.slot_id` with `main`
- `scripts/init_db.py` creates `conversation_slots` and can seed/repair the `main` slot contract

```python
def test_conversation_slot_model_has_workspace_folder_and_slot_id() -> None:
    columns = ConversationSlot.__table__.columns.keys()
    assert "workspace_folder" in columns
    assert "slot_id" in columns
    assert "title" in columns

def test_message_model_has_slot_id_column() -> None:
    assert "slot_id" in Message.__table__.columns.keys()
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py -q
```

Expected: FAIL because `ConversationSlot` does not exist and `messages.slot_id` is not present.

**Step 3: Write minimal implementation**

Implement:

- `domain/models/conversation_slot.py`
- export it from `domain/models/__init__.py`
- `Message.slot_id` with a non-null default of `"main"`
- SQLite compatibility in `scripts/init_db.py` for old `messages` tables and the new `conversation_slots` table

Keep the table narrow. Do not add `kind`, `target_agent_id`, or slot-management metadata in this task.

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add domain/models/conversation_slot.py domain/models/__init__.py domain/models/message.py tests/domain/models/test_models.py scripts/init_db.py tests/scripts/test_init_db.py
git commit -m "feat(slots): persist conversation slot schema"
```

### Task 2: Add A DB-Backed Conversation Slot Service

**Files:**
- Create: `services/conversation_slot_service.py`
- Create: `tests/services/test_conversation_slot_service.py`
- Modify: `services/group_registry.py`
- Modify: `tests/services/test_group_registry.py`

**Step 1: Write the failing tests**

Add tests that prove:

- `ensure_main_slot(workspace_folder, created_by)` inserts one reserved `main` slot and is idempotent
- `create_slot(...)` can add a non-main conversation slot under an existing workspace
- `list_slots(workspace_folder)` sorts `main` first, then other slots deterministically
- `get_slot(workspace_folder, slot_id)` returns `None` for missing slots
- when a canonical workspace is ensured or looked up through the registry, the minimal `main` slot can also be ensured without adding routes yet

```python
@pytest.mark.asyncio
async def test_ensure_main_slot_is_idempotent(db_session: AsyncSession) -> None:
    service = ConversationSlotService(db=db_session)
    first = await service.ensure_main_slot("project-alpha", created_by="owner-1")
    second = await service.ensure_main_slot("project-alpha", created_by="owner-1")
    assert first.slot_id == "main"
    assert second.slot_id == "main"
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_conversation_slot_service.py tests/services/test_group_registry.py -q
```

Expected: FAIL because there is no conversation-slot service and the registry has no slot-awareness.

**Step 3: Write minimal implementation**

Implement:

- async `ConversationSlotService(db: AsyncSession)`
- `ensure_main_slot(...)`
- `create_slot(...)`
- `list_slots(...)`
- `get_slot(...)`

Keep the service internal-only for now. Do not add HTTP routes in this task.

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_conversation_slot_service.py tests/services/test_group_registry.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add services/conversation_slot_service.py tests/services/test_conversation_slot_service.py services/group_registry.py tests/services/test_group_registry.py
git commit -m "feat(slots): add conversation slot service"
```

### Task 3: Thread `slot_id` Into Execution And Session Identity

**Files:**
- Modify: `services/execution_coordinator.py`
- Modify: `services/workspace_lifecycle.py`
- Modify: `domain/schemas.py`
- Modify: `app/routes/executions.py`
- Modify: `tests/services/test_workspace_lifecycle.py`
- Modify: `tests/services/test_execution_coordinator.py`
- Modify: `tests/app/routes/test_execution_routes.py`

**Step 1: Write the failing tests**

Add tests that prove:

- `ExecutionRequest` can carry `slot_id` and defaults to `"main"`
- two requests with the same `group_folder` but different `slot_id` resolve to different session keys
- execution snapshots expose `slot_id`
- `/executions/{run_id}` returns the run's `slot_id`
- existing runs without an explicit slot still behave as `main`

```python
@pytest.mark.asyncio
async def test_workspace_session_store_separates_slots() -> None:
    store = WorkspaceSessionStore()
    main = store.preview_session_id("project-alpha#slot:main", backend="openai")
    draft = store.preview_session_id("project-alpha#slot:draft", backend="openai")
    assert main != draft
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_workspace_lifecycle.py tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py -q
```

Expected: FAIL because execution/session contracts still know only `group_folder`.

**Step 3: Write minimal implementation**

Implement:

- `slot_id: str = "main"` on execution request/snapshot-facing contracts
- one helper that derives a slot-aware workspace/session key from `(group_folder, slot_id)`
- snapshot/schema updates so read-side status returns `slot_id`

Do not redesign queue ownership or permissions in this task. Slot identity is only a finer session boundary under the same workspace.

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_workspace_lifecycle.py tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add services/execution_coordinator.py services/workspace_lifecycle.py domain/schemas.py app/routes/executions.py tests/services/test_workspace_lifecycle.py tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py
git commit -m "feat(execution): add slot-aware session identity"
```

### Task 4: Thread `slot_id` Through Message Persistence And Dispatch Defaults

**Files:**
- Modify: `domain/schemas.py`
- Modify: `services/message_service.py`
- Modify: `services/message_dispatch.py`
- Modify: `app/routes/messages.py`
- Modify: `app/routes/im.py`
- Modify: `tests/services/test_message_service.py`
- Modify: `tests/services/test_message_dispatch.py`
- Modify: `tests/app/routes/test_message_routes.py`
- Modify: `tests/app/routes/test_im_routes.py`

**Step 1: Write the failing tests**

Add tests that prove:

- `UnifiedMessage` and `SendMessageRequest` accept optional `slot_id` and default it to `main`
- `store_message(...)` persists `slot_id`
- Web `/messages` can dispatch to an explicit existing slot
- Web `/messages` defaults to `main` when omitted
- IM dispatch always resolves to `main` even for bound workspaces
- missing or inaccessible non-main slots return `404` on Web routes

```python
@pytest.mark.asyncio
async def test_store_message_persists_slot_id(db_session: AsyncSession) -> None:
    message = await store_message(
        db=db_session,
        chat_jid="web:project-alpha",
        sender="alice",
        content="hello",
        group_folder="project-alpha",
        slot_id="draft",
    )
    assert message.slot_id == "draft"
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_message_service.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py tests/app/routes/test_im_routes.py -q
```

Expected: FAIL because message persistence and dispatch still have no slot concept.

**Step 3: Write minimal implementation**

Implement:

- `slot_id` on `UnifiedMessage`, `SendMessageRequest`, and any dispatch/result schema that now needs it
- `store_message(...)` support for `slot_id`
- Web route resolution that validates a slot under the current workspace
- IM route behavior that always uses `main`

Keep `IM -> slot` binding out of scope. Only support explicit Web slot targeting plus `main` defaults.

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_message_service.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py tests/app/routes/test_im_routes.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add domain/schemas.py services/message_service.py services/message_dispatch.py app/routes/messages.py app/routes/im.py tests/services/test_message_service.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py tests/app/routes/test_im_routes.py
git commit -m "feat(messages): add conversation slot defaults"
```

### Task 5: Refresh Handoff Docs And Run Full Verification

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`
- Review: `docs/plans/2026-03-14-m7-3-5-conversation-slots-design.md`
- Review: `docs/plans/2026-03-14-m7-3-5-conversation-slots.md`

**Step 1: Update docs for the completed milestone**

Record:

- `M7.3.5` complete
- the chosen scope: persistent conversation slots only
- deferred items: task-agent persistence, IM-to-slot binding, slot CRUD APIs, frontend tab UI, WebSocket slot routing/auth
- the next entrypoint becomes `M7.3.6`

**Step 2: Run focused verification**

Run:

```bash
.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py tests/services/test_conversation_slot_service.py tests/services/test_group_registry.py tests/services/test_workspace_lifecycle.py tests/services/test_execution_coordinator.py tests/services/test_message_service.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py tests/app/routes/test_execution_routes.py tests/app/routes/test_im_routes.py -q
```

Expected: PASS

**Step 3: Run broader regression**

Run:

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
git diff --check
```

Expected: PASS, `All checks passed!`, and `exit 0`

**Step 4: Commit**

```bash
git add docs/progress.md tasks/todo.md docs/plans/2026-03-14-m7-3-5-conversation-slots-design.md docs/plans/2026-03-14-m7-3-5-conversation-slots.md
git commit -m "feat(slots): complete M7.3.5 conversation slot model"
```
