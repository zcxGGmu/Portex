# M4.4.1 User `AGENTS.md` Memory Design

## Goal

Complete `M4.4.1` by replacing the placeholder memory service with the smallest useful user-global memory file manager, using `AGENTS.md` instead of `CLAUDE.md` as the persisted file name.

## Scope

- Replace `services/memory.py` placeholder storage with file-backed user memory methods
- Implement:
  - `get_user_memory(user_id: str) -> str`
  - `update_user_memory(user_id: str, content: str) -> None`
- Store user-global memory at `data/memory/user-global/{user_id}/AGENTS.md`
- Add focused service tests
- Update `docs/TODO.md` and `docs/progress.md` to reflect the `AGENTS.md` decision

## Out of Scope

- Do not implement daily memory
- Do not implement memory search
- Do not add memory API routes
- Do not wire memory into runner / MCP tools
- Do not add DB-backed persistence

## Design Constraints

- User explicitly requested `AGENTS.md` instead of `CLAUDE.md`
- Keep the milestone limited to service-layer file management
- Remain compatible with the current in-memory user/auth baseline
- Avoid broad refactors of older planning docs beyond the current handoff sources

## Design Options

### Option A: Keep in-memory placeholder

Pros:
- No file I/O complexity

Cons:
- Does not satisfy `M4.4.1`
- No persisted memory contract

### Option B: Minimal file-backed service

- Persist one `AGENTS.md` per user under `data/memory/user-global/{user_id}/`
- Support read and overwrite write
- Inject data root for tests

Pros:
- Smallest useful implementation
- Easy to test
- Leaves later milestones open

Cons:
- Only covers user-global memory for now

### Option C: Full memory subsystem now

- Add daily memory, search, and API/runner hooks in one pass

Pros:
- Closer to full product behavior

Cons:
- Explicitly exceeds `M4.4.1`

## Recommended Design

Choose **Option B**.

## Service Contract

Implement `MemoryService` in `services/memory.py` with:

- constructor parameter for `data_dir`
- `async def get_user_memory(user_id: str) -> str`
- `async def update_user_memory(user_id: str, content: str) -> None`

### Path contract

- user root: `data/memory/user-global/{user_id}/`
- memory file: `AGENTS.md`

### Runtime rules

- missing file returns `""`
- writes create parent directories automatically
- writes overwrite existing content
- different users are isolated by directory

## Testing Strategy

Add `tests/services/test_memory_service.py` covering:

- missing user memory returns empty string
- update then get returns stored content
- update creates `AGENTS.md` at the expected path
- update overwrites existing content
- user directories remain isolated

## Files

- Modify: `services/memory.py`
- Create: `tests/services/test_memory_service.py`
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`
