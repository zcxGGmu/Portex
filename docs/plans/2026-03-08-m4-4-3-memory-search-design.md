# M4.4.3 Memory Search Design

## Goal

Complete `M4.4.3` by extending the existing file-backed memory service with the smallest useful group-memory search capability.

## Scope

- Extend `services/memory.py`
- Implement `search_memory(group_folder: str, query: str) -> list[str]`
- Search only markdown files under `data/memory/{group_folder}/`
- Add focused service tests
- Update `docs/TODO.md` and `docs/progress.md`

## Out of Scope

- Do not add API routes
- Do not add result snippets or highlighting
- Do not search user-global `AGENTS.md`
- Do not add full-text indexing or ranking
- Do not wire memory search into runner / MCP tools

## Design Constraints

- Build on the current `AGENTS.md` + daily memory file service
- Keep the milestone service-only and file-backed
- Return plain path strings as the minimal result contract

## Recommended Design

- Add `async def search_memory(group_folder: str, query: str) -> list[str]`
- Treat blank queries as empty-result input
- Recursively scan `data/memory/{group_folder}/**/*.md`
- Match case-insensitively on file content
- Return matched file paths as sorted strings for deterministic tests

## Testing Strategy

Add focused tests for:

- matching markdown files in the target group folder
- case-insensitive matching
- blank query returns empty list
- results do not include files from other groups
- results do not include user-global `AGENTS.md`

## Files

- Modify: `services/memory.py`
- Modify: `tests/services/test_memory_service.py`
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`
