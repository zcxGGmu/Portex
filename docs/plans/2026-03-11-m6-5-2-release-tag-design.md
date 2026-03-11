# M6.5.2 Release Tag Design

## Goal

Complete `M6.5.2` by creating the first formal release tag `v1.0.0` on the verified milestone-completion commit, while keeping package/runtime version strings at `0.1.0` and leaving release-artifact work for `M6.5.3`.

## Scope

- verify the repository and remote are ready for `v1.0.0`
- add `M6.5.2` design/plan docs and session tracking
- update restart-oriented docs so the next starting point becomes `M6.5.3`
- create an annotated git tag `v1.0.0` on the final `M6.5.2` commit
- verify the created tag locally and, if executed, on `origin`

## Out of Scope

- do not change `pyproject.toml` from `0.1.0`
- do not change runtime/API version strings from `0.1.0`
- do not build Docker images, frontend release bundles, or other release artifacts
- do not create a GitHub Release, release notes generator, or release automation workflow
- do not expand this milestone into `M6.5.3`

## Design Constraints

- `docs/TODO.md` defines `M6.5.2` as `git tag -a v1.0.0 -m "Release v1.0.0"` followed by `git push origin v1.0.0`
- `M6.5.1` intentionally separated the planned release tag `v1.0.0` from the current package/runtime version `0.1.0`, and that boundary must remain visible in `M6.5.2`
- the tag should point to the final milestone-completion commit for `M6.5.2`, not to an earlier planning-only or handoff-only commit
- the remote must be checked for an existing `v1.0.0` tag before any push attempt

## Options Considered

### Option A: Tag the final `M6.5.2` completion commit and keep runtime/package versions unchanged

Pros:
- cleanest match to the current milestone definition
- keeps release execution distinct from artifact building
- preserves the explicit `v1.0.0` tag versus `0.1.0` runtime boundary documented in `M6.5.1`

Cons:
- release tag and runtime/package version remain intentionally different until later work

### Option B: Synchronize package/runtime version strings to `1.0.0` before tagging

Pros:
- reduces visible version mismatch immediately

Cons:
- overlaps with later release execution phases
- expands scope beyond `M6.5.2`

### Option C: Skip repo doc updates and tag the current HEAD as-is

Pros:
- fastest path to a tag

Cons:
- leaves restart-oriented docs behind the actual phase state
- risks tagging the wrong commit boundary for this milestone

## Recommended Design

Choose **Option A**.

## Proposed Changes

### Preflight checks

- confirm the worktree is clean enough to start the phase
- confirm `refs/tags/v1.0.0` does not already exist locally
- confirm `origin` does not already expose `v1.0.0`

### Repo tracking updates

- add dedicated `M6.5.2` design and implementation-plan docs
- append the session checklist to `tasks/todo.md`
- update `README.md`, `AGENTS.md`, and `docs/progress.md` so they move from "next step `M6.5.2`" to "next step `M6.5.3`" while still stating that runtime/package versions remain `0.1.0`

### Tag creation flow

- run fresh repository verification before the release commit/tag
- commit the approved `M6.5.2` documentation and handoff changes
- create annotated tag `v1.0.0` on that commit
- verify the tag locally with `git show` / `git tag -n`
- if remote execution is performed, push `v1.0.0` to `origin` and verify the remote ref exists

## Risks and Boundaries

- `v1.0.0` is a git/release label only at this stage; the application still reports `0.1.0`
- verification commands such as frontend `build` remain evidence only and do not count as `M6.5.3` release-artifact completion
- if the remote push is skipped or deferred, the milestone remains only partially executed versus the strict TODO definition

## Expected Deliverables

- `docs/plans/2026-03-11-m6-5-2-release-tag-design.md`
- `docs/plans/2026-03-11-m6-5-2-release-tag.md`
- updated `README.md`, `AGENTS.md`, `docs/progress.md`, and `tasks/todo.md`
- local annotated tag `v1.0.0`
- remote `origin` tag `v1.0.0` if push is executed
