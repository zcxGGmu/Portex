# M4.4.4 Memory MCP Tool Wrapping Design

## Goal

Complete `M4.4.4` by replacing the runner's placeholder memory tools with the smallest useful file-backed memory append/search tools that operate directly on the mounted `/workspace/memory` directory.

## Scope

- Replace `container/agent-runner/src/tools/memory.py` placeholders
- Add:
  - `memory_append_tool(content: str) -> str`
  - `memory_search_tool(query: str) -> list[str]`
- Expose `@function_tool` wrappers in `container/agent-runner/src/tools/__init__.py`
- Include memory tools in `build_default_tools()`
- Add focused runner tool tests
- Update `docs/progress.md` and `docs/TODO.md`

## Out of Scope

- Do not add HTTP/API calls back to the main service
- Do not add MCP server transport changes
- Do not add auth or permission checks in the runner
- Do not add snippets, ranking, or highlighting to search results
- Do not add user-global `AGENTS.md` support in runner tools

## Design Constraints

- Current container memory mount is group-scoped at `/workspace/memory`
- The main service already stores daily memory as `YYYY-MM-DD.md`
- `M4.4.4` should stay local to the runner image and current mount contract

## Design Options

### Option A: Main-service API proxy

- Runner memory tools call back into future Portex memory APIs

Pros:
- Centralizes logic in the main service

Cons:
- Requires new API design, auth, and connectivity assumptions
- Exceeds `M4.4.4`

### Option B: Direct mounted-filesystem tools

- Runner tools read/write `/workspace/memory` directly

Pros:
- Smallest change
- Fits existing container mount contract
- Keeps behavior deterministic and testable

Cons:
- Some logic is duplicated from the main service

### Option C: Hybrid shim with shared library

- Extract a shared library used by both service and runner

Pros:
- Less duplication long-term

Cons:
- Larger refactor than needed now

## Recommended Design

Choose **Option B**.

## Tool Contract

Implement in `container/agent-runner/src/tools/memory.py`:

- module constant `MEMORY_DIR` defaulting to `Path(os.getenv("PORTEX_MEMORY_DIR", "/workspace/memory"))`
- injectable `today_func` / internal helpers for tests
- `memory_append_tool(content)`:
  - append to `MEMORY_DIR/YYYY-MM-DD.md`
  - create parent directories automatically
  - return a short confirmation string
- `memory_search_tool(query)`:
  - blank query returns `[]`
  - recursively scan `MEMORY_DIR/**/*.md`
  - match case-insensitively on file contents
  - return sorted relative paths from `MEMORY_DIR`

## Tool Registry

Update `container/agent-runner/src/tools/__init__.py`:

- add `@function_tool` wrappers:
  - `memory_append`
  - `memory_search`
- include them in `build_default_tools()`

## Testing Strategy

Add `tests/container/agent_runner/test_memory_tools.py` covering:

- append creates today's file and writes content
- repeated append preserves order
- search returns relative markdown paths
- search is case-insensitive
- blank query returns empty list
- default tool registry includes memory tools

## Files

- Modify: `container/agent-runner/src/tools/memory.py`
- Modify: `container/agent-runner/src/tools/__init__.py`
- Create: `tests/container/agent_runner/test_memory_tools.py`
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
