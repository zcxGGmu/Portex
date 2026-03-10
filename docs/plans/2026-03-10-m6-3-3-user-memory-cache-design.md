# M6.3.3 User Memory Cache Design

## Goal

Complete `M6.3.3` by adding the smallest useful cache layer to the current repository: a process-local read cache for user-global `AGENTS.md` memory reads.

## Scope

- extend `services/memory.py` with a private in-process cache for user-global memory content
- cache reads performed by `get_user_memory(user_id)`
- keep `update_user_memory(user_id, content)` and the cache synchronized in the same process
- cache missing-file reads as empty strings so repeated lookups do not keep probing the filesystem
- verify the new behavior in `tests/services/test_memory_service.py`

## Out of Scope

- do not introduce Redis or any external cache service
- do not add a generic cache abstraction shared across the repository
- do not cache `append_daily_memory()` or `search_memory()`
- do not add TTL, LRU, size limits, background refresh, or eviction policies
- do not add cross-process or cross-container cache consistency
- do not add benchmark tooling or performance measurements

## Design Constraints

- `docs/TODO.md` marks `M6.3.3` as “如需要”, so the implementation must stay minimal and easy to justify
- the repository already uses in-memory state as runtime source of truth in several services; this milestone must not blur the line between “runtime state” and “cache”
- `MemoryService.search_memory()` is a larger I/O hotspot, but caching it now would create stale-read risk because runner-side tools can mutate group memory files directly
- user-global `AGENTS.md` reads have the simplest invalidation model because the same service already owns the write path

## Options Considered

### Option A: No cache for M6.3.3

- document that current evidence does not justify a cache layer
- skip code changes

Pros:
- lowest risk
- fully consistent with the TODO wording

Cons:
- leaves `M6.3.3` with no concrete repository artifact
- misses a low-risk opportunity to establish a minimal cache pattern

### Option B: Process-local user memory read cache

- cache `get_user_memory(user_id)` results in `MemoryService`
- update the cache on `update_user_memory(user_id, content)`
- leave group memory paths unchanged

Pros:
- smallest concrete cache implementation in the current codebase
- clear invalidation model
- no new infrastructure
- low regression risk

Cons:
- modest performance benefit
- only consistent within one process

### Option C: Cache group memory search results

- cache `search_memory(group_folder, query)` results or scanned file content

Pros:
- higher theoretical I/O savings

Cons:
- stale reads become likely because group memory can be mutated outside this service
- invalidation would require broader design work
- too much complexity for the current milestone

## Recommended Design

Choose **Option B**.

## Proposed Changes

### MemoryService internals

- add a private dictionary on `MemoryService`, keyed by `user_id`
- store the latest known `AGENTS.md` content as the cache value
- keep the cache entirely internal to the service

### Read path

- `get_user_memory(user_id)` first checks the cache
- if the user is cached, return the cached content immediately
- if not cached:
  - check whether the `AGENTS.md` file exists
  - return `""` when absent and cache `""`
  - otherwise read the file, cache the content, and return it

### Write path

- `update_user_memory(user_id, content)` keeps its current filesystem behavior
- after the file write succeeds, update the in-memory cache to the same `content`
- write failures continue to raise as they do today

### Non-goals preserved

- `append_daily_memory()` stays file-backed only
- `search_memory()` keeps scanning live markdown files
- no public `invalidate()` or `clear()` API is added in this milestone

## Testing Strategy

- extend `tests/services/test_memory_service.py` first
- add a failing test proving a missing `AGENTS.md` path only checks filesystem once across repeated reads
- add a failing test proving an existing file is read once and then served from cache
- add a failing test proving `update_user_memory()` refreshes the cache so a later read does not return stale content
- keep the existing daily-memory and search tests unchanged to verify the cache does not leak into those paths
- after implementation, run focused memory tests, then the full backend regression, `ruff`, and frontend `lint/build`

## Risks and Boundaries

- this is a single-process cache only; another process can still change `AGENTS.md` without this process noticing
- that limitation is acceptable for the current milestone because no multi-process invalidation contract exists elsewhere in the repository either
- if user-global memory later becomes cross-process or API-shared state, invalidation rules will need a separate design

## Expected Deliverables

- a minimal process-local cache in `MemoryService`
- regression tests covering cache hit, miss, and write-through behavior
- `docs/progress.md` and `tasks/todo.md` advanced from `M6.3.3` toward `M6.4.1`
