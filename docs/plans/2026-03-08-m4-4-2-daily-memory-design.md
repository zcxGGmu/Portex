# M4.4.2 Daily Memory Design

## Goal

Complete `M4.4.2` by extending the file-backed memory service with the smallest useful daily memory append capability for group folders.

## Scope

- Extend `services/memory.py`
- Implement `append_daily_memory(group_folder: str, content: str) -> None`
- Persist daily memory under `data/memory/{group_folder}/YYYY-MM-DD.md`
- Add focused service tests
- Update `docs/TODO.md` and `docs/progress.md`

## Out of Scope

- Do not implement search
- Do not add API routes
- Do not wire memory into runner / MCP tools
- Do not add DB-backed storage
- Do not change user-global `AGENTS.md` behavior

## Design Constraints

- Build on the current `AGENTS.md`-based user-global memory service
- Keep the milestone service-only
- Make the “today” value injectable for tests

## Recommended Design

- Add constructor dependency `today_func: Callable[[], date] | None`
- Daily memory path: `data/memory/{group_folder}/YYYY-MM-DD.md`
- `append_daily_memory()` creates parent directories as needed
- Appends content as a simple newline-delimited block, preserving prior entries

## Testing Strategy

Add focused tests for:

- new daily file creation at the expected date path
- repeated appends accumulate content in order
- different group folders are isolated
- user-global `AGENTS.md` storage remains unaffected

## Files

- Modify: `services/memory.py`
- Modify: `tests/services/test_memory_service.py`
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`
